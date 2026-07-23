"""Bitacora append-only de acciones sobre los documentos almacenados."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Union
from uuid import UUID

from etica_ia_ers.dominio import AccionTrazabilidad, EventoTrazabilidad

from .errores import ErrorAlmacenamiento
from .serializacion import deserializar_json, dict_a_evento, evento_a_dict, serializar_json


def crear_evento(
    id_documento: UUID,
    accion: AccionTrazabilidad,
    detalle: Optional[Dict[str, Any]] = None,
) -> EventoTrazabilidad:
    return EventoTrazabilidad(
        id_documento=id_documento,
        accion=accion,
        fecha=datetime.now(timezone.utc),
        detalle=dict(detalle or {}),
    )


class RegistroDeTrazabilidad(Protocol):
    """Contrato de la bitacora que acompana al repositorio."""

    def registrar(self, evento: EventoTrazabilidad) -> None:
        ...

    def eventos(self, id_documento: Optional[UUID] = None) -> List[EventoTrazabilidad]:
        """Eventos en orden cronologico de registro, opcionalmente filtrados."""
        ...


class TrazabilidadEnMemoria:
    """Bitacora volatil, pensada para pruebas y ejecuciones exploratorias."""

    def __init__(self) -> None:
        self._eventos: List[EventoTrazabilidad] = []

    def registrar(self, evento: EventoTrazabilidad) -> None:
        self._eventos.append(evento)

    def eventos(self, id_documento: Optional[UUID] = None) -> List[EventoTrazabilidad]:
        return [
            evento
            for evento in self._eventos
            if id_documento is None or evento.id_documento == id_documento
        ]


class TrazabilidadEnArchivo:
    """Bitacora persistente en formato JSON Lines (un evento por linea)."""

    def __init__(self, ruta: Union[str, Path]) -> None:
        self.ruta = Path(ruta)
        self.ruta.parent.mkdir(parents=True, exist_ok=True)

    def registrar(self, evento: EventoTrazabilidad) -> None:
        linea = serializar_json(evento_a_dict(evento), "el evento de trazabilidad")
        try:
            with self.ruta.open("a", encoding="utf-8", newline="\n") as archivo:
                archivo.write(linea + "\n")
        except OSError as error:
            raise ErrorAlmacenamiento(
                f"No se pudo escribir la bitacora {self.ruta}: {error}"
            ) from error

    def eventos(self, id_documento: Optional[UUID] = None) -> List[EventoTrazabilidad]:
        if not self.ruta.is_file():
            return []
        try:
            with self.ruta.open("r", encoding="utf-8", newline="\n") as archivo:
                lineas = archivo.readlines()
        except OSError as error:
            raise ErrorAlmacenamiento(
                f"No se pudo leer la bitacora {self.ruta}: {error}"
            ) from error

        encontrados = []
        for numero, linea in enumerate(lineas, start=1):
            if not linea.strip():
                continue
            origen = f"{self.ruta}:{numero}"
            evento = dict_a_evento(deserializar_json(linea, origen), origen)
            if id_documento is None or evento.id_documento == id_documento:
                encontrados.append(evento)
        return encontrados
