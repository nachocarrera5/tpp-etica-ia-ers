"""Contrato de almacenamiento de ERS y su implementacion en memoria."""

from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Protocol
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
    DocumentoNoEncontradoError,
    DocumentoYaRegistradoError,
    TextoNormalizadoInvalidoError,
)
from .trazabilidad import RegistroDeTrazabilidad, TrazabilidadEnMemoria, crear_evento


def ahora() -> datetime:
    return datetime.now(timezone.utc)


class RepositorioDeDocumentos(Protocol):
    """Almacenamiento basico de ERS cargadas y del estado de su analisis."""

    def guardar(self, documento: DocumentoERS) -> RegistroDocumento:
        """Registra un documento nuevo en estado CARGADO."""
        ...

    def obtener(self, id_documento: UUID) -> RegistroDocumento:
        """Devuelve el documento completo, incluido su contenido extraido."""
        ...

    def buscar_por_hash(self, hash_contenido: str) -> Optional[ResumenDocumento]:
        """Devuelve el registro mas antiguo con ese hash, o None."""
        ...

    def listar(self) -> List[ResumenDocumento]:
        """Resumenes ordenados por fecha de carga, sin contenido textual."""
        ...

    def actualizar_estado(
        self,
        id_documento: UUID,
        estado: EstadoAnalisis,
    ) -> ResumenDocumento:
        ...

    def guardar_texto_normalizado(
        self,
        id_documento: UUID,
        texto_normalizado: TextoNormalizado,
    ) -> ResumenDocumento:
        """Guarda la normalizacion y deja el documento en estado NORMALIZADO."""
        ...

    def obtener_texto_normalizado(
        self,
        id_documento: UUID,
    ) -> Optional[TextoNormalizado]:
        """Devuelve la normalizacion guardada, o None si todavia no hay."""
        ...

    def eliminar(self, id_documento: UUID) -> None:
        ...


class RepositorioEnMemoria:
    """Repositorio volatil, util para pruebas y para el endpoint en desarrollo."""

    def __init__(self, trazabilidad: Optional[RegistroDeTrazabilidad] = None) -> None:
        self.trazabilidad: RegistroDeTrazabilidad = trazabilidad or TrazabilidadEnMemoria()
        self._registros: Dict[UUID, RegistroDocumento] = {}
        self._normalizaciones: Dict[UUID, TextoNormalizado] = {}

    def guardar(self, documento: DocumentoERS) -> RegistroDocumento:
        if documento.id in self._registros:
            raise DocumentoYaRegistradoError(
                f"Ya existe un documento almacenado con id {documento.id}."
            )
        registro = RegistroDocumento(
            documento=_copiar_documento(documento),
            estado=EstadoAnalisis.CARGADO,
            fecha_actualizacion=ahora(),
        )
        self._registros[registro.id] = registro
        self.trazabilidad.registrar(
            crear_evento(
                registro.id,
                AccionTrazabilidad.CARGA,
                _detalle_de_carga(registro),
            )
        )
        return registro

    def obtener(self, id_documento: UUID) -> RegistroDocumento:
        registro = self._registros.get(id_documento)
        if registro is None:
            raise DocumentoNoEncontradoError(
                f"No hay un documento almacenado con id {id_documento}."
            )
        return replace(registro, documento=_copiar_documento(registro.documento))

    def buscar_por_hash(self, hash_contenido: str) -> Optional[ResumenDocumento]:
        for registro in self._ordenados():
            if registro.documento.hash_contenido == hash_contenido:
                return registro.resumen
        return None

    def listar(self) -> List[ResumenDocumento]:
        return [registro.resumen for registro in self._ordenados()]

    def actualizar_estado(
        self,
        id_documento: UUID,
        estado: EstadoAnalisis,
    ) -> ResumenDocumento:
        registro = self._registros.get(id_documento)
        if registro is None:
            raise DocumentoNoEncontradoError(
                f"No hay un documento almacenado con id {id_documento}."
            )
        estado_anterior = registro.estado
        actualizado = replace(registro, estado=estado, fecha_actualizacion=ahora())
        self._registros[id_documento] = actualizado
        self.trazabilidad.registrar(
            crear_evento(
                id_documento,
                AccionTrazabilidad.CAMBIO_ESTADO,
                _detalle_de_cambio(estado_anterior, estado),
            )
        )
        return actualizado.resumen

    def guardar_texto_normalizado(
        self,
        id_documento: UUID,
        texto_normalizado: TextoNormalizado,
    ) -> ResumenDocumento:
        registro = self._registros.get(id_documento)
        if registro is None:
            raise DocumentoNoEncontradoError(
                f"No hay un documento almacenado con id {id_documento}."
            )
        validar_texto_normalizado(registro.documento, texto_normalizado)

        estado_anterior = registro.estado
        actualizado = replace(
            registro,
            estado=EstadoAnalisis.NORMALIZADO,
            fecha_actualizacion=ahora(),
        )
        self._registros[id_documento] = actualizado
        self._normalizaciones[id_documento] = replace(
            texto_normalizado,
            pasos_aplicados=list(texto_normalizado.pasos_aplicados),
        )
        self.trazabilidad.registrar(
            crear_evento(
                id_documento,
                AccionTrazabilidad.NORMALIZACION,
                _detalle_de_normalizacion(estado_anterior, texto_normalizado),
            )
        )
        return actualizado.resumen

    def obtener_texto_normalizado(
        self,
        id_documento: UUID,
    ) -> Optional[TextoNormalizado]:
        if id_documento not in self._registros:
            raise DocumentoNoEncontradoError(
                f"No hay un documento almacenado con id {id_documento}."
            )
        texto_normalizado = self._normalizaciones.get(id_documento)
        if texto_normalizado is None:
            return None
        return replace(
            texto_normalizado,
            pasos_aplicados=list(texto_normalizado.pasos_aplicados),
        )

    def eliminar(self, id_documento: UUID) -> None:
        if id_documento not in self._registros:
            raise DocumentoNoEncontradoError(
                f"No hay un documento almacenado con id {id_documento}."
            )
        del self._registros[id_documento]
        self._normalizaciones.pop(id_documento, None)
        self.trazabilidad.registrar(
            crear_evento(id_documento, AccionTrazabilidad.ELIMINACION)
        )

    def _ordenados(self) -> List[RegistroDocumento]:
        return sorted(
            self._registros.values(),
            key=lambda registro: (registro.documento.fecha_carga, str(registro.id)),
        )


def validar_texto_normalizado(
    documento: DocumentoERS,
    texto_normalizado: TextoNormalizado,
) -> None:
    """El original normalizado debe ser el texto extraido del propio documento.

    Sin esta comprobacion, lo guardado como normalizacion podria pertenecer a
    otra ERS y la trazabilidad entre documento y texto dejaria de ser cierta.
    """
    if texto_normalizado.original != documento.contenido_extraido:
        raise TextoNormalizadoInvalidoError(
            f"El texto original normalizado no coincide con el contenido "
            f"extraido del documento {documento.id}."
        )


def _copiar_documento(documento: DocumentoERS) -> DocumentoERS:
    """Aisla los metadatos mutables del documento respecto de quien lo usa."""
    return replace(documento, metadatos=deepcopy(documento.metadatos))


def _detalle_de_carga(registro: RegistroDocumento) -> Dict[str, str]:
    return {
        "nombre_original": registro.documento.nombre_original,
        "formato_origen": registro.documento.formato_origen.value,
        "hash_contenido": registro.documento.hash_contenido,
        "estado": registro.estado.value,
    }


def _detalle_de_cambio(
    estado_anterior: EstadoAnalisis,
    estado_nuevo: EstadoAnalisis,
) -> Dict[str, str]:
    return {
        "estado_anterior": estado_anterior.value,
        "estado_nuevo": estado_nuevo.value,
    }


def _detalle_de_normalizacion(
    estado_anterior: EstadoAnalisis,
    texto_normalizado: TextoNormalizado,
) -> Dict[str, Any]:
    return {
        "estado_anterior": estado_anterior.value,
        "estado_nuevo": EstadoAnalisis.NORMALIZADO.value,
        "pasos_aplicados": list(texto_normalizado.pasos_aplicados),
    }
