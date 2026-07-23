"""Traduccion entre entidades de dominio y su representacion en JSON."""

import json
from datetime import datetime
from typing import Any, Dict
from uuid import UUID

from etica_ia_ers.dominio import (
    AccionTrazabilidad,
    DocumentoERS,
    EstadoAnalisis,
    EventoTrazabilidad,
    FormatoDocumento,
    RegistroDocumento,
    ResumenDocumento,
    TextoNormalizado,
)

from .errores import AlmacenamientoCorruptoError, ErrorAlmacenamiento

VERSION_FORMATO = 1
ARCHIVO_CONTENIDO = "contenido.txt"
ARCHIVO_TEXTO_NORMALIZADO = "texto_normalizado.txt"

_ERRORES_DE_LECTURA = (AttributeError, KeyError, TypeError, ValueError)


def serializar_json(datos: Dict[str, Any], contexto: str, indentado: bool = False) -> str:
    try:
        return json.dumps(
            datos,
            ensure_ascii=False,
            sort_keys=True,
            indent=2 if indentado else None,
        )
    except (TypeError, ValueError) as error:
        raise ErrorAlmacenamiento(
            f"No se pudo serializar {contexto} a JSON: {error}"
        ) from error


def deserializar_json(texto: str, origen: str) -> Dict[str, Any]:
    try:
        datos = json.loads(texto)
    except json.JSONDecodeError as error:
        raise AlmacenamientoCorruptoError(
            f"El contenido de {origen} no es JSON valido."
        ) from error
    if not isinstance(datos, dict):
        raise AlmacenamientoCorruptoError(
            f"El contenido de {origen} no es un objeto JSON."
        )
    return datos


def registro_a_dict(registro: RegistroDocumento) -> Dict[str, Any]:
    documento = registro.documento
    return {
        "version_formato": VERSION_FORMATO,
        "id": str(documento.id),
        "nombre_original": documento.nombre_original,
        "formato_origen": documento.formato_origen.value,
        "hash_contenido": documento.hash_contenido,
        "fecha_carga": documento.fecha_carga.isoformat(),
        "estado": registro.estado.value,
        "fecha_actualizacion": registro.fecha_actualizacion.isoformat(),
        "metadatos": dict(documento.metadatos),
        "archivo_contenido": ARCHIVO_CONTENIDO,
    }


def dict_a_resumen(datos: Dict[str, Any], origen: str) -> ResumenDocumento:
    _validar_version(datos, origen)
    try:
        return ResumenDocumento(
            id=UUID(datos["id"]),
            nombre_original=datos["nombre_original"],
            formato_origen=FormatoDocumento(datos["formato_origen"]),
            hash_contenido=datos["hash_contenido"],
            fecha_carga=_a_fecha(datos["fecha_carga"]),
            estado=EstadoAnalisis(datos["estado"]),
            fecha_actualizacion=_a_fecha(datos["fecha_actualizacion"]),
            metadatos=dict(datos.get("metadatos") or {}),
        )
    except _ERRORES_DE_LECTURA as error:
        raise AlmacenamientoCorruptoError(
            f"El registro almacenado en {origen} es invalido: {error}"
        ) from error


def dict_a_registro(
    datos: Dict[str, Any],
    contenido_extraido: str,
    origen: str,
) -> RegistroDocumento:
    resumen = dict_a_resumen(datos, origen)
    documento = DocumentoERS(
        id=resumen.id,
        nombre_original=resumen.nombre_original,
        formato_origen=resumen.formato_origen,
        contenido_extraido=contenido_extraido,
        hash_contenido=resumen.hash_contenido,
        fecha_carga=resumen.fecha_carga,
        metadatos=resumen.metadatos,
    )
    return RegistroDocumento(
        documento=documento,
        estado=resumen.estado,
        fecha_actualizacion=resumen.fecha_actualizacion,
    )


def normalizacion_a_dict(
    texto_normalizado: TextoNormalizado,
    fecha: datetime,
) -> Dict[str, Any]:
    return {
        "version_formato": VERSION_FORMATO,
        "fecha": fecha.isoformat(),
        "pasos_aplicados": list(texto_normalizado.pasos_aplicados),
        "archivo_texto": ARCHIVO_TEXTO_NORMALIZADO,
    }


def dict_a_normalizacion(
    datos: Dict[str, Any],
    original: str,
    normalizado: str,
    origen: str,
) -> TextoNormalizado:
    _validar_version(datos, origen)
    try:
        return TextoNormalizado(
            original=original,
            normalizado=normalizado,
            pasos_aplicados=list(datos["pasos_aplicados"]),
        )
    except _ERRORES_DE_LECTURA as error:
        raise AlmacenamientoCorruptoError(
            f"La normalizacion almacenada en {origen} es invalida: {error}"
        ) from error


def evento_a_dict(evento: EventoTrazabilidad) -> Dict[str, Any]:
    return {
        "version_formato": VERSION_FORMATO,
        "id_documento": str(evento.id_documento),
        "accion": evento.accion.value,
        "fecha": evento.fecha.isoformat(),
        "detalle": dict(evento.detalle),
    }


def dict_a_evento(datos: Dict[str, Any], origen: str) -> EventoTrazabilidad:
    _validar_version(datos, origen)
    try:
        return EventoTrazabilidad(
            id_documento=UUID(datos["id_documento"]),
            accion=AccionTrazabilidad(datos["accion"]),
            fecha=_a_fecha(datos["fecha"]),
            detalle=dict(datos.get("detalle") or {}),
        )
    except _ERRORES_DE_LECTURA as error:
        raise AlmacenamientoCorruptoError(
            f"El evento almacenado en {origen} es invalido: {error}"
        ) from error


def _validar_version(datos: Dict[str, Any], origen: str) -> None:
    version = datos.get("version_formato")
    if version != VERSION_FORMATO:
        raise AlmacenamientoCorruptoError(
            f"Version de formato no soportada en {origen}: {version!r}. "
            f"Esta version del prototipo escribe y lee la version {VERSION_FORMATO}."
        )


def _a_fecha(valor: str) -> datetime:
    if valor.endswith("Z"):
        valor = valor[:-1] + "+00:00"
    return datetime.fromisoformat(valor)
