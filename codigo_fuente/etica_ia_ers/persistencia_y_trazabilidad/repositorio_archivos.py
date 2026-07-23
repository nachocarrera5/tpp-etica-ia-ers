"""Repositorio de ERS persistido en el sistema de archivos.

Cada documento ocupa una carpeta con su registro en JSON y su contenido
extraido en texto plano, de modo que lo almacenado sea inspeccionable sin
herramientas adicionales:

    <directorio_base>/
    ├── documentos/
    │   └── <id>/
    │       ├── documento.json
    │       └── contenido.txt
    └── trazabilidad.jsonl
"""

import os
import shutil
from dataclasses import replace
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID

from etica_ia_ers.dominio import (
    AccionTrazabilidad,
    DocumentoERS,
    EstadoAnalisis,
    RegistroDocumento,
    ResumenDocumento,
    TextoNormalizado,
)

from .errores import (
    AlmacenamientoCorruptoError,
    DocumentoNoEncontradoError,
    DocumentoYaRegistradoError,
    ErrorAlmacenamiento,
)
from .repositorio import ahora, validar_texto_normalizado
from .serializacion import (
    ARCHIVO_CONTENIDO,
    ARCHIVO_TEXTO_NORMALIZADO,
    deserializar_json,
    dict_a_normalizacion,
    dict_a_registro,
    dict_a_resumen,
    normalizacion_a_dict,
    registro_a_dict,
    serializar_json,
)
from .trazabilidad import (
    RegistroDeTrazabilidad,
    TrazabilidadEnArchivo,
    crear_evento,
)

DIRECTORIO_ALMACENAMIENTO = Path("datos/almacenamiento")

_ARCHIVO_REGISTRO = "documento.json"
_ARCHIVO_NORMALIZACION = "normalizacion.json"
_ARCHIVO_TRAZABILIDAD = "trazabilidad.jsonl"
_CARPETA_DOCUMENTOS = "documentos"


class RepositorioEnArchivos:
    """Almacenamiento basico de ERS sobre disco, sin motor de base de datos."""

    def __init__(
        self,
        directorio_base: Union[str, Path] = DIRECTORIO_ALMACENAMIENTO,
        trazabilidad: Optional[RegistroDeTrazabilidad] = None,
    ) -> None:
        self.directorio_base = Path(directorio_base)
        self._documentos = self.directorio_base / _CARPETA_DOCUMENTOS
        try:
            self._documentos.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            raise ErrorAlmacenamiento(
                f"No se pudo preparar el directorio {self.directorio_base}: {error}"
            ) from error
        self.trazabilidad: RegistroDeTrazabilidad = trazabilidad or TrazabilidadEnArchivo(
            self.directorio_base / _ARCHIVO_TRAZABILIDAD
        )

    def guardar(self, documento: DocumentoERS) -> RegistroDocumento:
        carpeta = self._carpeta(documento.id)
        if carpeta.exists():
            raise DocumentoYaRegistradoError(
                f"Ya existe un documento almacenado con id {documento.id}."
            )

        registro = RegistroDocumento(
            documento=documento,
            estado=EstadoAnalisis.CARGADO,
            fecha_actualizacion=ahora(),
        )
        # Se serializa antes de tocar el disco: si los metadatos no son
        # representables en JSON, no queda una carpeta a medio escribir.
        contenido_registro = serializar_json(
            registro_a_dict(registro), "el registro del documento", indentado=True
        )

        try:
            carpeta.mkdir(parents=True)
            _escribir_atomico(carpeta / ARCHIVO_CONTENIDO, documento.contenido_extraido)
            _escribir_atomico(carpeta / _ARCHIVO_REGISTRO, contenido_registro)
        except OSError as error:
            shutil.rmtree(carpeta, ignore_errors=True)
            raise ErrorAlmacenamiento(
                f"No se pudo almacenar el documento {documento.id}: {error}"
            ) from error

        self.trazabilidad.registrar(
            crear_evento(
                registro.id,
                AccionTrazabilidad.CARGA,
                {
                    "nombre_original": documento.nombre_original,
                    "formato_origen": documento.formato_origen.value,
                    "hash_contenido": documento.hash_contenido,
                    "estado": registro.estado.value,
                },
            )
        )
        return registro

    def obtener(self, id_documento: UUID) -> RegistroDocumento:
        datos, carpeta = self._leer_registro(id_documento)
        ruta_contenido = carpeta / str(datos.get("archivo_contenido") or ARCHIVO_CONTENIDO)
        if not ruta_contenido.is_file():
            raise AlmacenamientoCorruptoError(
                f"Falta el contenido extraido del documento {id_documento} "
                f"(se esperaba {ruta_contenido})."
            )
        return dict_a_registro(
            datos,
            _leer_texto(ruta_contenido),
            str(carpeta / _ARCHIVO_REGISTRO),
        )

    def buscar_por_hash(self, hash_contenido: str) -> Optional[ResumenDocumento]:
        for resumen in self.listar():
            if resumen.hash_contenido == hash_contenido:
                return resumen
        return None

    def listar(self) -> List[ResumenDocumento]:
        resumenes = []
        for carpeta in sorted(self._documentos.iterdir()):
            ruta_registro = carpeta / _ARCHIVO_REGISTRO
            if not ruta_registro.is_file():
                continue
            origen = str(ruta_registro)
            resumenes.append(
                dict_a_resumen(deserializar_json(_leer_texto(ruta_registro), origen), origen)
            )
        return sorted(resumenes, key=lambda resumen: (resumen.fecha_carga, str(resumen.id)))

    def actualizar_estado(
        self,
        id_documento: UUID,
        estado: EstadoAnalisis,
    ) -> ResumenDocumento:
        datos, carpeta = self._leer_registro(id_documento)
        ruta_registro = carpeta / _ARCHIVO_REGISTRO
        anterior = dict_a_resumen(datos, str(ruta_registro))

        datos["estado"] = estado.value
        datos["fecha_actualizacion"] = ahora().isoformat()
        try:
            _escribir_atomico(
                ruta_registro,
                serializar_json(datos, "el registro del documento", indentado=True),
            )
        except OSError as error:
            raise ErrorAlmacenamiento(
                f"No se pudo actualizar el estado del documento {id_documento}: {error}"
            ) from error

        self.trazabilidad.registrar(
            crear_evento(
                id_documento,
                AccionTrazabilidad.CAMBIO_ESTADO,
                {
                    "estado_anterior": anterior.estado.value,
                    "estado_nuevo": estado.value,
                },
            )
        )
        return dict_a_resumen(datos, str(ruta_registro))

    def guardar_texto_normalizado(
        self,
        id_documento: UUID,
        texto_normalizado: TextoNormalizado,
    ) -> ResumenDocumento:
        registro = self.obtener(id_documento)
        validar_texto_normalizado(registro.documento, texto_normalizado)

        actualizado = replace(
            registro,
            estado=EstadoAnalisis.NORMALIZADO,
            fecha_actualizacion=ahora(),
        )
        contenido_normalizacion = serializar_json(
            normalizacion_a_dict(texto_normalizado, actualizado.fecha_actualizacion),
            "la normalizacion del documento",
            indentado=True,
        )
        contenido_registro = serializar_json(
            registro_a_dict(actualizado), "el registro del documento", indentado=True
        )

        carpeta = self._carpeta(id_documento)
        try:
            _escribir_atomico(
                carpeta / ARCHIVO_TEXTO_NORMALIZADO, texto_normalizado.normalizado
            )
            _escribir_atomico(carpeta / _ARCHIVO_NORMALIZACION, contenido_normalizacion)
            _escribir_atomico(carpeta / _ARCHIVO_REGISTRO, contenido_registro)
        except OSError as error:
            raise ErrorAlmacenamiento(
                f"No se pudo almacenar la normalizacion del documento "
                f"{id_documento}: {error}"
            ) from error

        self.trazabilidad.registrar(
            crear_evento(
                id_documento,
                AccionTrazabilidad.NORMALIZACION,
                {
                    "estado_anterior": registro.estado.value,
                    "estado_nuevo": EstadoAnalisis.NORMALIZADO.value,
                    "pasos_aplicados": list(texto_normalizado.pasos_aplicados),
                },
            )
        )
        return actualizado.resumen

    def obtener_texto_normalizado(
        self,
        id_documento: UUID,
    ) -> Optional[TextoNormalizado]:
        registro = self.obtener(id_documento)
        carpeta = self._carpeta(id_documento)
        ruta_normalizacion = carpeta / _ARCHIVO_NORMALIZACION
        if not ruta_normalizacion.is_file():
            return None

        origen = str(ruta_normalizacion)
        datos = deserializar_json(_leer_texto(ruta_normalizacion), origen)
        ruta_texto = carpeta / str(datos.get("archivo_texto") or ARCHIVO_TEXTO_NORMALIZADO)
        if not ruta_texto.is_file():
            raise AlmacenamientoCorruptoError(
                f"Falta el texto normalizado del documento {id_documento} "
                f"(se esperaba {ruta_texto})."
            )
        return dict_a_normalizacion(
            datos,
            registro.documento.contenido_extraido,
            _leer_texto(ruta_texto),
            origen,
        )

    def eliminar(self, id_documento: UUID) -> None:
        carpeta = self._carpeta(id_documento)
        if not carpeta.is_dir():
            raise DocumentoNoEncontradoError(
                f"No hay un documento almacenado con id {id_documento}."
            )
        try:
            shutil.rmtree(carpeta)
        except OSError as error:
            raise ErrorAlmacenamiento(
                f"No se pudo eliminar el documento {id_documento}: {error}"
            ) from error
        self.trazabilidad.registrar(
            crear_evento(id_documento, AccionTrazabilidad.ELIMINACION)
        )

    def _carpeta(self, id_documento: UUID) -> Path:
        return self._documentos / str(id_documento)

    def _leer_registro(self, id_documento: UUID) -> Tuple[Dict[str, Any], Path]:
        carpeta = self._carpeta(id_documento)
        ruta_registro = carpeta / _ARCHIVO_REGISTRO
        if not ruta_registro.is_file():
            raise DocumentoNoEncontradoError(
                f"No hay un documento almacenado con id {id_documento}."
            )
        origen = str(ruta_registro)
        return deserializar_json(_leer_texto(ruta_registro), origen), carpeta


def _leer_texto(ruta: Path) -> str:
    try:
        with ruta.open("r", encoding="utf-8", newline="\n") as archivo:
            return archivo.read()
    except OSError as error:
        raise ErrorAlmacenamiento(f"No se pudo leer {ruta}: {error}") from error
    except UnicodeDecodeError as error:
        raise AlmacenamientoCorruptoError(
            f"El archivo {ruta} no esta codificado en UTF-8."
        ) from error


def _escribir_atomico(ruta: Path, texto: str) -> None:
    """Escribe el archivo completo o no lo modifica: nunca deja un estado parcial."""
    temporal = ruta.with_name(ruta.name + ".tmp")
    with temporal.open("w", encoding="utf-8", newline="\n") as archivo:
        archivo.write(texto)
        archivo.flush()
        os.fsync(archivo.fileno())
    os.replace(temporal, ruta)
