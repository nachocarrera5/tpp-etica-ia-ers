from __future__ import annotations

import re
import unicodedata
from typing import Iterable, List, Optional, Pattern, Sequence, Tuple

from etica_ia_ers.dominio import (
    FragmentoClasificado,
    FragmentoDocumental,
    TipoClasificacionFragmento,
    TipoFragmento,
)


Regla = Tuple[str, Pattern[str]]


def _regla(nombre: str, patron: str) -> Regla:
    return nombre, re.compile(patron)


_REGLAS_RESTRICCION: Tuple[Regla, ...] = (
    _regla(
        "prohibicion explicita",
        r"\b(?:no (?:debe|deben|debera|deberan|podra|podran)|"
        r"se prohibe|queda prohibid[oa]|prohibid[oa]s?)\b",
    ),
    _regla(
        "limite de uso",
        r"\b(?:unicamente|solo podra|fuera de alcance|limitad[oa] a|"
        r"se restringe|restriccion de uso)\b",
    ),
)

_REGLAS_NO_FUNCIONAL: Tuple[Regla, ...] = (
    _regla(
        "seguridad o privacidad",
        r"\b(?:seguridad|privacidad|confidencialidad|cifrad[oa]|"
        r"autenticacion|autorizacion|control de acceso)\b",
    ),
    _regla(
        "rendimiento",
        r"\b(?:rendimiento|latencia|tiempo de respuesta|milisegundos?|"
        r"segundos?|transacciones por|solicitudes por)\b",
    ),
    _regla(
        "disponibilidad",
        r"\b(?:disponibilidad|tiempo de actividad|tolerancia a fallos?|"
        r"recuperacion ante fallos?)\b",
    ),
    _regla(
        "usabilidad o accesibilidad",
        r"\b(?:usabilidad|accesibilidad|comprensible|facil de usar|"
        r"lector de pantalla)\b",
    ),
    _regla(
        "fiabilidad o robustez",
        r"\b(?:fiabilidad|confiabilidad|robustez|resiliencia|"
        r"degradacion|continuidad)\b",
    ),
    _regla(
        "calidad tecnica",
        r"\b(?:escalabilidad|mantenibilidad|interoperabilidad|precision|"
        r"exactitud|tasa de error)\b",
    ),
)

_REGLAS_FUNCIONAL: Tuple[Regla, ...] = (
    _regla(
        "comportamiento requerido",
        r"\b(?:debe|deben|debera|deberan|permitira|registrara|generara|"
        r"procesara|mostrara|notificara|calculara|validara|almacenara|"
        r"enviara|recibira|consultara|actualizara|eliminara|clasificara|"
        r"identificara|detectara)\b",
    ),
)

_REGLAS_CONTEXTO: Tuple[Regla, ...] = (
    _regla(
        "proposito o alcance",
        r"\b(?:objetivo|proposito|finalidad|alcance|uso previsto|"
        r"fuera del alcance)\b",
    ),
    _regla(
        "contexto de aplicacion",
        r"\b(?:contexto|dominio|entorno operativo|antecedentes|"
        r"destinad[oa] a|usuarios previstos|descripcion general|supuesto)\b",
    ),
)

_REGLAS_SECCION: Tuple[
    Tuple[TipoClasificacionFragmento, Tuple[Regla, ...]], ...
] = (
    (
        TipoClasificacionFragmento.RESTRICCION,
        (_regla("seccion de restricciones", r"\brestricciones?\b"),),
    ),
    (
        TipoClasificacionFragmento.REQUISITO_NO_FUNCIONAL,
        (
            _regla(
                "seccion de requisitos no funcionales",
                r"\b(?:requisitos? no funcionales?|calidad|seguridad|"
                r"rendimiento)\b",
            ),
        ),
    ),
    (
        TipoClasificacionFragmento.REQUISITO_FUNCIONAL,
        (
            _regla(
                "seccion de requisitos funcionales",
                r"\brequisitos? funcionales?\b",
            ),
        ),
    ),
    (
        TipoClasificacionFragmento.CONTEXTO,
        (
            _regla(
                "seccion de contexto",
                r"\b(?:introduccion|objetivos?|proposito|alcance|contexto|"
                r"descripcion general)\b",
            ),
        ),
    ),
)

_REGLAS_TEXTO: Tuple[
    Tuple[TipoClasificacionFragmento, Tuple[Regla, ...]], ...
] = (
    (TipoClasificacionFragmento.RESTRICCION, _REGLAS_RESTRICCION),
    (
        TipoClasificacionFragmento.REQUISITO_NO_FUNCIONAL,
        _REGLAS_NO_FUNCIONAL,
    ),
    (TipoClasificacionFragmento.REQUISITO_FUNCIONAL, _REGLAS_FUNCIONAL),
    (TipoClasificacionFragmento.CONTEXTO, _REGLAS_CONTEXTO),
)

_NOMBRES_CLASIFICACION = {
    TipoClasificacionFragmento.REQUISITO_FUNCIONAL: "requisito funcional",
    TipoClasificacionFragmento.REQUISITO_NO_FUNCIONAL: (
        "requisito no funcional"
    ),
    TipoClasificacionFragmento.RESTRICCION: "restriccion",
    TipoClasificacionFragmento.CONTEXTO: "contexto",
    TipoClasificacionFragmento.OTRO: "otro",
}


def clasificar_fragmento(fragmento: FragmentoDocumental) -> FragmentoClasificado:
    if fragmento.tipo_fragmento == TipoFragmento.ENCABEZADO:
        return FragmentoClasificado(
            fragmento=fragmento,
            clasificacion=TipoClasificacionFragmento.OTRO,
            senales=("encabezado documental",),
            justificacion=(
                "El fragmento es un encabezado y no aporta por si solo "
                "evidencia suficiente para una categoria semantica."
            ),
        )

    texto_normalizado = _normalizar_para_busqueda(fragmento.texto)
    resultado = _clasificar_por_reglas(texto_normalizado, _REGLAS_TEXTO)
    if resultado is not None:
        clasificacion, senales = resultado
        return _crear_resultado(fragmento, clasificacion, senales, "texto")

    seccion_normalizada = _normalizar_para_busqueda(
        fragmento.seccion_origen or ""
    )
    resultado = _clasificar_por_reglas(seccion_normalizada, _REGLAS_SECCION)
    if resultado is not None:
        clasificacion, senales = resultado
        return _crear_resultado(fragmento, clasificacion, senales, "seccion")

    return FragmentoClasificado(
        fragmento=fragmento,
        clasificacion=TipoClasificacionFragmento.OTRO,
        senales=(),
        justificacion=(
            "No se detectaron senales suficientes para asignar una "
            "categoria semantica."
        ),
    )


def clasificar_fragmentos(
    fragmentos: Iterable[FragmentoDocumental],
) -> List[FragmentoClasificado]:
    return [clasificar_fragmento(fragmento) for fragmento in fragmentos]


def _normalizar_para_busqueda(texto: str) -> str:
    descompuesto = unicodedata.normalize("NFD", texto.casefold())
    sin_acentos = "".join(
        caracter
        for caracter in descompuesto
        if unicodedata.category(caracter) != "Mn"
    )
    return re.sub(r"\s+", " ", sin_acentos).strip()


def _clasificar_por_reglas(
    texto: str,
    grupos: Sequence[
        Tuple[TipoClasificacionFragmento, Sequence[Regla]]
    ],
) -> Optional[Tuple[TipoClasificacionFragmento, Tuple[str, ...]]]:
    for clasificacion, reglas in grupos:
        senales = tuple(
            nombre for nombre, patron in reglas if patron.search(texto)
        )
        if senales:
            return clasificacion, senales
    return None


def _crear_resultado(
    fragmento: FragmentoDocumental,
    clasificacion: TipoClasificacionFragmento,
    senales: Tuple[str, ...],
    origen: str,
) -> FragmentoClasificado:
    nombre = _NOMBRES_CLASIFICACION[clasificacion]
    detalle = ", ".join(senales)
    return FragmentoClasificado(
        fragmento=fragmento,
        clasificacion=clasificacion,
        senales=senales,
        justificacion=(
            f"Clasificado como {nombre} por senales en {origen}: {detalle}."
        ),
    )
