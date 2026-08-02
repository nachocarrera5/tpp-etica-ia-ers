from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Callable, List, Sequence

from etica_ia_ers.dominio import TextoNormalizado
from etica_ia_ers.procesamiento_textual_y_nlp.errores import (
    ErrorEnPasoDeNormalizacion,
    PasoDesconocidoError,
    TextoVacioError,
)


def normalizar_unicode(texto: str) -> str:

    return unicodedata.normalize("NFC", texto)


def eliminar_caracteres_de_control(texto: str) -> str:

    return "".join(
        ch for ch in texto
        if ch in ("\n", "\t") or not unicodedata.category(ch).startswith("C")
    )


def normalizar_saltos_de_linea(texto: str) -> str:

    texto = texto.replace("\r\n", "\n").replace("\r", "\n")
    return re.sub(r"\n{3,}", "\n\n", texto)


def normalizar_comillas(texto: str) -> str:

    reemplazos = {
        "\u201c": '"',  # "
        "\u201d": '"',  # "
        "\u2018": "'",  # '
        "\u2019": "'",  # '
        "\u00ab": '"',  # «
        "\u00bb": '"',  # »
    }
    for original, reemplazo in reemplazos.items():
        texto = texto.replace(original, reemplazo)
    return texto


def normalizar_guiones(texto: str) -> str:

    return texto.replace("\u2014", "-").replace("\u2013", "-")


def normalizar_vinetas(texto: str) -> str:

    caracteres_vineta = r"[•◦▪▸▹●○■□►▻‣⁃∙]"
    return re.sub(
        rf"^\s*{caracteres_vineta}\s*", "- ", texto, flags=re.MULTILINE
    )


def colapsar_espacios(texto: str) -> str:

    lineas = texto.split("\n")
    lineas_normalizadas = [
        re.sub(r"[ \t]+", " ", linea.strip()) for linea in lineas
    ]
    return "\n".join(lineas_normalizadas)


def colapsar_lineas_en_blanco(texto: str) -> str:
    """Reduce líneas en blanco consecutivas a una sola separación."""
    return re.sub(r"\n\s*\n", "\n\n", texto)


def eliminar_marcadores_de_pagina(texto: str) -> str:
    return re.sub(
        r"^\s*(Página|Page)\s+\d+\s+(de|of)\s+\d+\s*$",
        "",
        texto,
        flags=re.MULTILINE | re.IGNORECASE,
    )


def normalizar_numeracion(texto: str) -> str:

    texto = re.sub(
        r"^(\s*\d+(?:\.\d+)*)[)\-]\s*",
        r"\1. ",
        texto,
        flags=re.MULTILINE,
    )
    return texto


FuncionNormalizacion = Callable[[str], str]


@dataclass
class PasoNormalizacion:

    nombre: str
    funcion: FuncionNormalizacion



PASOS_POR_DEFECTO: List[PasoNormalizacion] = [
    PasoNormalizacion("normalizar_unicode", normalizar_unicode),
    PasoNormalizacion("eliminar_caracteres_de_control", eliminar_caracteres_de_control),
    PasoNormalizacion("normalizar_saltos_de_linea", normalizar_saltos_de_linea),
    PasoNormalizacion("normalizar_comillas", normalizar_comillas),
    PasoNormalizacion("normalizar_guiones", normalizar_guiones),
    PasoNormalizacion("normalizar_vinetas", normalizar_vinetas),
    PasoNormalizacion("eliminar_marcadores_de_pagina", eliminar_marcadores_de_pagina),
    PasoNormalizacion("normalizar_numeracion", normalizar_numeracion),
    PasoNormalizacion("colapsar_espacios", colapsar_espacios),
    PasoNormalizacion("colapsar_lineas_en_blanco", colapsar_lineas_en_blanco),
]




@dataclass
class NormalizadorDeTexto:

    pasos: List[PasoNormalizacion] = field(
        default_factory=lambda: list(PASOS_POR_DEFECTO)
    )

    
    def normalizar(self, texto: str) -> TextoNormalizado:

        if not texto or not texto.strip():
            raise TextoVacioError(
                "El texto a normalizar esta vacio o solo contiene espacios."
            )

        actual = texto
        aplicados: List[str] = []

        for paso in self.pasos:
            try:
                actual = paso.funcion(actual)
            except Exception as error:
                raise ErrorEnPasoDeNormalizacion(paso.nombre, error) from error
            aplicados.append(paso.nombre)

        return TextoNormalizado(
            original=texto, normalizado=actual, pasos_aplicados=aplicados
        )



    @classmethod
    def con_pasos(cls, nombres: Sequence[str]) -> "NormalizadorDeTexto":

        disponibles = {p.nombre: p for p in PASOS_POR_DEFECTO}
        seleccionados: List[PasoNormalizacion] = []
        for nombre in nombres:
            if nombre not in disponibles:
                raise PasoDesconocidoError(
                    f"Paso desconocido: '{nombre}'. "
                    f"Disponibles: {sorted(disponibles.keys())}"
                )
            seleccionados.append(disponibles[nombre])
        return cls(pasos=seleccionados)

    @classmethod
    def sin_pasos(cls, nombres: Sequence[str]) -> "NormalizadorDeTexto":
        excluidos = set(nombres)
        return cls(
            pasos=[p for p in PASOS_POR_DEFECTO if p.nombre not in excluidos]
        )
