"""Exportacion del reporte de cobertura etica documental.

El exportador no vuelve a evaluar la ERS ni recalcula indicadores: recibe el
reporte ya serializado por `serializar_reporte_resultados` y lo entrega en un
formato transportable.

    JSON      intercambio con otras herramientas, equivalente al endpoint;
    MARKDOWN  lectura y revision humana, versionable junto al informe;
    HTML      documento autocontenido y listo para imprimir o guardar en PDF
              desde el navegador.

Lo exportado es un diagnostico documental preliminar: no acredita cumplimiento
ni certifica el sistema descripto por la ERS.
"""

from __future__ import annotations

import html
import json
import os
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence, Union
from uuid import UUID

from etica_ia_ers.dominio import (
    DominioAplicacion,
    NivelCobertura,
    PrioridadDocumental,
)

from .errores import (
    ErrorEscrituraReporte,
    FormatoExportacionNoSoportadoError,
    ReporteInvalidoError,
)

DIRECTORIO_SALIDA = Path("datos/salida")

VERSION_FORMATO_REPORTE = 1

AVISO_ALCANCE = (
    "Este reporte es un diagnostico documental preliminar sobre la cobertura "
    "etica de la ERS analizada. Es un asistente de deteccion temprana: no "
    "constituye una certificacion etica, no acredita cumplimiento normativo y "
    "no evalua el comportamiento real del sistema descripto."
)

_CLAVES_REQUERIDAS = (
    "metadatos",
    "resumen_ejecutivo",
    "lectura_global",
    "indicadores",
    "resultados_dimension",
    "hallazgos",
    "advertencias",
)

_CLAVES_REQUERIDAS_METADATOS = (
    "analisis_id",
    "documento_id",
    "nombre_documento",
)

_ETIQUETAS_NIVEL = {
    NivelCobertura.AUSENTE.value: "Ausente",
    NivelCobertura.PARCIAL.value: "Parcial",
    NivelCobertura.EXPLICITO.value: "Explícito",
}

_ETIQUETAS_PRIORIDAD = {
    PrioridadDocumental.BAJA.value: "Baja",
    PrioridadDocumental.MEDIA.value: "Media",
    PrioridadDocumental.ALTA.value: "Alta",
}

_NOMBRES_DOMINIO = {
    DominioAplicacion.CREDITICIO.value: "Crédito y finanzas",
    DominioAplicacion.SALUD.value: "Salud",
    DominioAplicacion.EMPLEO.value: "Empleo",
    DominioAplicacion.EDUCACION.value: "Educación",
    DominioAplicacion.SECTOR_PUBLICO.value: "Sector público",
    DominioAplicacion.RECOMENDACION.value: "Recomendación y contenidos",
}

_ETIQUETAS_INDICADOR = (
    ("total_dimensiones", "Dimensiones del modelo"),
    ("dimensiones_ausentes", "Dimensiones ausentes"),
    ("dimensiones_parciales", "Dimensiones parciales"),
    ("dimensiones_explicitas", "Dimensiones explícitas"),
    ("porcentaje_cobertura_explicita", "Cobertura explícita (%)"),
    ("porcentaje_cobertura_no_ausente", "Cobertura no ausente (%)"),
    ("porcentaje_cobertura_ponderada", "Cobertura ponderada (%)"),
    ("total_hallazgos", "Hallazgos registrados"),
    ("total_alertas", "Alertas generadas"),
    ("total_recomendaciones", "Recomendaciones generadas"),
    ("recomendaciones_alta_prioridad", "Recomendaciones de prioridad alta"),
    ("hallazgos_con_revision_humana", "Hallazgos que requieren revisión humana"),
    ("porcentaje_revision_humana", "Hallazgos con revisión humana (%)"),
    ("hallazgos_prioridad_alta", "Hallazgos de prioridad alta"),
    ("hallazgos_prioridad_media", "Hallazgos de prioridad media"),
    ("hallazgos_prioridad_baja", "Hallazgos de prioridad baja"),
    ("guardrails_aplicados", "Guardrails aplicados"),
    ("guardrails_no_aplicables", "Guardrails no aplicables"),
    ("guardrails_con_error", "Guardrails con error"),
)

_PREFIJO_ARCHIVO = "reporte-etico"
_LARGO_SUFIJO_ANALISIS = 8
_NOMBRE_POR_DEFECTO = "ers"
_LARGO_MAXIMO_SLUG = 60

_PATRON_NO_ALFANUMERICO = re.compile(r"[^a-z0-9]+")


class FormatoExportacion(str, Enum):
    """Formatos en los que puede entregarse el reporte."""

    JSON = "JSON"
    MARKDOWN = "MARKDOWN"
    HTML = "HTML"

    @classmethod
    def desde_texto(cls, valor: str) -> "FormatoExportacion":
        """Acepta el nombre del formato o su extension, sin distinguir mayusculas."""
        clave = (valor or "").strip().lower().lstrip(".")
        formato = _ALIAS_FORMATO.get(clave)
        if formato is None:
            raise FormatoExportacionNoSoportadoError(
                "Formato de exportacion no soportado: "
                f"{valor!r}. Formatos disponibles: {', '.join(formatos_disponibles())}."
            )
        return formato

    @property
    def extension(self) -> str:
        return _EXTENSIONES[self]

    @property
    def tipo_contenido(self) -> str:
        return _TIPOS_CONTENIDO[self]


_EXTENSIONES = {
    FormatoExportacion.JSON: ".json",
    FormatoExportacion.MARKDOWN: ".md",
    FormatoExportacion.HTML: ".html",
}

_TIPOS_CONTENIDO = {
    FormatoExportacion.JSON: "application/json; charset=utf-8",
    FormatoExportacion.MARKDOWN: "text/markdown; charset=utf-8",
    FormatoExportacion.HTML: "text/html; charset=utf-8",
}

_ALIAS_FORMATO = {
    "json": FormatoExportacion.JSON,
    "markdown": FormatoExportacion.MARKDOWN,
    "md": FormatoExportacion.MARKDOWN,
    "html": FormatoExportacion.HTML,
    "htm": FormatoExportacion.HTML,
}


def formatos_disponibles() -> List[str]:
    """Alias aceptados por `FormatoExportacion.desde_texto`, en orden estable."""
    return list(_ALIAS_FORMATO)


@dataclass(frozen=True)
class ReporteExportado:
    """Reporte listo para transportar: contenido, nombre y tipo de archivo."""

    formato: FormatoExportacion
    nombre_archivo: str
    tipo_contenido: str
    contenido: str
    fecha_generacion: datetime
    analisis_id: str
    documento_id: str

    @property
    def bytes_contenido(self) -> bytes:
        return self.contenido.encode("utf-8")


def exportar_reporte(
    reporte: Mapping[str, Any],
    formato: Union[FormatoExportacion, str] = FormatoExportacion.JSON,
) -> ReporteExportado:
    """Convierte un reporte serializado en un archivo descargable.

    `reporte` es la salida de `serializar_reporte_resultados`. La exportacion no
    agrega, filtra ni reinterpreta hallazgos: solo cambia su presentacion.
    """
    formato_elegido = (
        formato
        if isinstance(formato, FormatoExportacion)
        else FormatoExportacion.desde_texto(formato)
    )
    metadatos = _metadatos_validados(reporte)
    fecha_generacion = datetime.now(timezone.utc)

    if formato_elegido is FormatoExportacion.JSON:
        contenido = _exportar_json(reporte, formato_elegido, fecha_generacion)
    elif formato_elegido is FormatoExportacion.MARKDOWN:
        contenido = _exportar_markdown(reporte, metadatos, fecha_generacion)
    else:
        contenido = _exportar_html(reporte, metadatos, fecha_generacion)

    return ReporteExportado(
        formato=formato_elegido,
        nombre_archivo=_nombre_archivo(metadatos, formato_elegido),
        tipo_contenido=formato_elegido.tipo_contenido,
        contenido=contenido,
        fecha_generacion=fecha_generacion,
        analisis_id=str(metadatos["analisis_id"]),
        documento_id=str(metadatos["documento_id"]),
    )


def escribir_reporte(
    reporte_exportado: ReporteExportado,
    directorio: Union[str, Path] = DIRECTORIO_SALIDA,
) -> Path:
    """Guarda el reporte en `directorio` y devuelve la ruta escrita.

    La escritura es atomica: el archivo queda completo o no se modifica.
    """
    carpeta = Path(directorio)
    ruta = carpeta / reporte_exportado.nombre_archivo
    try:
        carpeta.mkdir(parents=True, exist_ok=True)
        _escribir_atomico(ruta, reporte_exportado.contenido)
    except OSError as error:
        raise ErrorEscrituraReporte(
            f"No se pudo escribir el reporte en {ruta}: {error}"
        ) from error
    return ruta


def _escribir_atomico(ruta: Path, texto: str) -> None:
    temporal = ruta.with_name(ruta.name + ".tmp")
    with temporal.open("w", encoding="utf-8", newline="\n") as archivo:
        archivo.write(texto)
        archivo.flush()
        os.fsync(archivo.fileno())
    os.replace(temporal, ruta)


def _metadatos_validados(reporte: Mapping[str, Any]) -> Mapping[str, Any]:
    faltantes = [clave for clave in _CLAVES_REQUERIDAS if clave not in reporte]
    if faltantes:
        raise ReporteInvalidoError(
            "El reporte no respeta el formato de resultados esperado; "
            f"faltan las claves: {', '.join(faltantes)}."
        )

    metadatos = reporte["metadatos"]
    if not isinstance(metadatos, Mapping):
        raise ReporteInvalidoError("Los metadatos del reporte deben ser un objeto.")

    faltantes_metadatos = [
        clave for clave in _CLAVES_REQUERIDAS_METADATOS if clave not in metadatos
    ]
    if faltantes_metadatos:
        raise ReporteInvalidoError(
            "Los metadatos del reporte estan incompletos; faltan las claves: "
            f"{', '.join(faltantes_metadatos)}."
        )
    return metadatos


def _nombre_archivo(
    metadatos: Mapping[str, Any],
    formato: FormatoExportacion,
) -> str:
    partes = [_PREFIJO_ARCHIVO, _slug(str(metadatos["nombre_documento"]))]
    sufijo = _sufijo_analisis(metadatos["analisis_id"])
    if sufijo:
        partes.append(sufijo)
    return "-".join(partes) + formato.extension


def _sufijo_analisis(analisis_id: Any) -> str:
    """Distingue reportes del mismo documento sin exponer el UUID completo."""
    try:
        return UUID(str(analisis_id)).hex[:_LARGO_SUFIJO_ANALISIS]
    except (AttributeError, TypeError, ValueError):
        return _slug(str(analisis_id))[:_LARGO_SUFIJO_ANALISIS]


def _slug(texto: str) -> str:
    """Nombre de archivo seguro: sin acentos, separadores ni recorridos de ruta."""
    sin_extension = Path(texto.strip()).stem
    sin_acentos = unicodedata.normalize("NFKD", sin_extension)
    ascii_plano = sin_acentos.encode("ascii", "ignore").decode("ascii").lower()
    limpio = _PATRON_NO_ALFANUMERICO.sub("-", ascii_plano).strip("-")
    return limpio[:_LARGO_MAXIMO_SLUG].strip("-") or _NOMBRE_POR_DEFECTO


def _exportar_json(
    reporte: Mapping[str, Any],
    formato: FormatoExportacion,
    fecha_generacion: datetime,
) -> str:
    """Mismo contenido que el endpoint de resultados, con su sello de exportacion."""
    documento: Dict[str, Any] = dict(reporte)
    documento["exportacion"] = {
        "formato": formato.value,
        "version_formato": VERSION_FORMATO_REPORTE,
        "fecha_exportacion": fecha_generacion.isoformat(),
        "aviso_alcance": AVISO_ALCANCE,
    }
    try:
        return json.dumps(documento, ensure_ascii=False, indent=2) + "\n"
    except (TypeError, ValueError) as error:
        raise ReporteInvalidoError(
            f"El reporte contiene valores que no pueden serializarse a JSON: {error}"
        ) from error


_SIN_DATO = "—"


def _texto(valor: Any) -> str:
    if valor is None:
        return _SIN_DATO
    if isinstance(valor, bool):
        return "Sí" if valor else "No"
    if isinstance(valor, float):
        return f"{valor:.1f}".rstrip("0").rstrip(".")
    # `str()` de un Enum devuelve "Clase.MIEMBRO": se toma su valor, para que
    # el reporte se lea igual venga de la serializacion o del dominio.
    texto = str(_valor_plano(valor)).strip()
    return texto or _SIN_DATO


def _valor_plano(valor: Any) -> Any:
    return valor.value if isinstance(valor, Enum) else valor


def _lista(valores: Any, separador: str = ", ") -> str:
    if not isinstance(valores, Sequence) or isinstance(valores, str):
        return _texto(valores)
    elementos = [_texto(valor) for valor in valores]
    return separador.join(elementos) if elementos else _SIN_DATO


def _etiqueta_nivel(valor: Any) -> str:
    return _ETIQUETAS_NIVEL.get(str(_valor_plano(valor)), _texto(valor))


def _etiqueta_prioridad(valor: Any) -> str:
    return _ETIQUETAS_PRIORIDAD.get(str(_valor_plano(valor)), _texto(valor))


def _dominio(metadatos: Mapping[str, Any]) -> str:
    aplicado = metadatos.get("dominio_aplicacion")
    if aplicado:
        nombre = _NOMBRES_DOMINIO.get(str(_valor_plano(aplicado)), _texto(aplicado))
        return f"{nombre} (con guardrails específicos)"
    declarado = metadatos.get("dominio_declarado")
    if declarado:
        return f"{_texto(declarado)} (sin guardrails específicos)"
    return "Sin especificar"


def _cobertura_ponderada(resultado: Mapping[str, Any]) -> str:
    valor = resultado.get("porcentaje_cobertura_ponderada")
    return _SIN_DATO if valor is None else f"{_texto(valor)}%"


def _revision_humana(elemento: Mapping[str, Any]) -> str:
    if not elemento.get("requiere_revision_humana"):
        return "No"
    motivo = elemento.get("motivo_revision_humana")
    return f"Sí — {_texto(motivo)}" if motivo else "Sí"


def _filas_indicadores(indicadores: Mapping[str, Any]) -> List[List[str]]:
    filas = [
        [etiqueta, _texto(indicadores[clave])]
        for clave, etiqueta in _ETIQUETAS_INDICADOR
        if clave in indicadores
    ]
    filas.append(
        [
            "Dimensiones con prioridad alta",
            _lista(indicadores.get("dimensiones_prioridad_alta")),
        ]
    )
    filas.append(
        [
            "Familias de guardrail cubiertas",
            _lista(indicadores.get("familias_guardrail_cubiertas")),
        ]
    )
    return filas


def _filas_grupos(indicadores: Mapping[str, Any]) -> List[List[str]]:
    return [
        [
            _texto(grupo.get("grupo_tematico")),
            _lista(grupo.get("dimensiones_incluidas")),
            _texto(grupo.get("ausentes")),
            _texto(grupo.get("parciales")),
            _texto(grupo.get("explicitas")),
            _etiqueta_prioridad(grupo.get("prioridad_maxima")),
            _texto(bool(grupo.get("requiere_revision_humana"))),
        ]
        for grupo in indicadores.get("por_grupo", [])
    ]


def _filas_dimensiones(resultados: Sequence[Mapping[str, Any]]) -> List[List[str]]:
    return [
        [
            _texto(resultado.get("dimension_codigo")),
            _texto(resultado.get("dimension_nombre")),
            _texto(resultado.get("grupo_tematico")),
            _etiqueta_nivel(resultado.get("nivel_consolidado")),
            _cobertura_ponderada(resultado),
            _etiqueta_prioridad(resultado.get("prioridad_documental")),
            _texto(bool(resultado.get("requiere_revision_humana"))),
        ]
        for resultado in resultados
    ]


def _filas_alertas(alertas: Sequence[Mapping[str, Any]]) -> List[List[str]]:
    return [
        [
            _texto(alerta.get("dimension_codigo")),
            _texto(alerta.get("titulo")),
            _etiqueta_nivel(alerta.get("nivel_cobertura")),
            _etiqueta_prioridad(alerta.get("prioridad_documental")),
            _texto(bool(alerta.get("requiere_revision_humana"))),
        ]
        for alerta in alertas
    ]


def _filas_recomendaciones(
    recomendaciones: Sequence[Mapping[str, Any]],
) -> List[List[str]]:
    return [
        [
            _texto(recomendacion.get("dimension_codigo")),
            _texto(recomendacion.get("tipo_mejora")),
            _etiqueta_prioridad(recomendacion.get("prioridad_documental")),
            _texto(recomendacion.get("accion_sugerida")),
        ]
        for recomendacion in recomendaciones
    ]


def _descripcion_evidencia(evidencia: Mapping[str, Any]) -> str:
    """Ubica la evidencia dentro de la ERS para que el hallazgo sea rastreable."""
    partes: List[str] = []
    for clave in ("identificador_ers", "seccion_origen"):
        if evidencia.get(clave):
            partes.append(_texto(evidencia[clave]))
    inicio = evidencia.get("posicion_inicio")
    fin = evidencia.get("posicion_fin")
    if inicio is not None and fin is not None:
        partes.append(f"posiciones {inicio}-{fin}")
    if evidencia.get("observacion"):
        partes.append(_texto(evidencia["observacion"]))
    return " · ".join(partes)


def _celda_markdown(texto: str) -> str:
    """Evita que un texto de la ERS rompa la tabla que lo contiene."""
    return texto.replace("|", "\\|").replace("\n", " ").strip()


def _tabla_markdown(
    encabezados: Sequence[str],
    filas: Sequence[Sequence[str]],
) -> List[str]:
    lineas = [
        "| " + " | ".join(_celda_markdown(encabezado) for encabezado in encabezados) + " |",
        "| " + " | ".join("---" for _ in encabezados) + " |",
    ]
    lineas.extend(
        "| " + " | ".join(_celda_markdown(celda) for celda in fila) + " |"
        for fila in filas
    )
    return lineas


def _exportar_markdown(
    reporte: Mapping[str, Any],
    metadatos: Mapping[str, Any],
    fecha_generacion: datetime,
) -> str:
    indicadores = reporte.get("indicadores", {})
    resultados = reporte.get("resultados_dimension", [])
    hallazgos = reporte.get("hallazgos", [])
    alertas = reporte.get("alertas", [])
    recomendaciones = reporte.get("recomendaciones", [])
    advertencias = reporte.get("advertencias", [])

    lineas: List[str] = [
        "# Reporte de cobertura ética documental",
        "",
        f"> {AVISO_ALCANCE}",
        "",
        "## Identificación",
        "",
    ]
    lineas.extend(
        _tabla_markdown(
            ("Campo", "Valor"),
            [
                ["Documento", _texto(metadatos.get("nombre_documento"))],
                ["ID del documento", _texto(metadatos.get("documento_id"))],
                ["ID del análisis", _texto(metadatos.get("analisis_id"))],
                ["Estado", _texto(metadatos.get("estado"))],
                ["Dominio de aplicación", _dominio(metadatos)],
                ["Inicio del análisis", _texto(metadatos.get("fecha_inicio"))],
                ["Fin del análisis", _texto(metadatos.get("fecha_fin"))],
                ["Fecha de exportación", fecha_generacion.isoformat()],
                ["Lectura global", _texto(reporte.get("lectura_global"))],
            ],
        )
    )
    lineas.extend(
        [
            "",
            "## Resumen ejecutivo",
            "",
            _texto(reporte.get("resumen_ejecutivo")),
            "",
            "## Indicadores globales",
            "",
        ]
    )
    lineas.extend(_tabla_markdown(("Indicador", "Valor"), _filas_indicadores(indicadores)))

    filas_grupos = _filas_grupos(indicadores)
    if filas_grupos:
        lineas.extend(["", "## Cobertura por grupo temático", ""])
        lineas.extend(
            _tabla_markdown(
                (
                    "Grupo temático",
                    "Dimensiones",
                    "Ausentes",
                    "Parciales",
                    "Explícitas",
                    "Prioridad máxima",
                    "Revisión humana",
                ),
                filas_grupos,
            )
        )

    lineas.extend(["", "## Cobertura por dimensión", ""])
    lineas.extend(
        _tabla_markdown(
            (
                "Código",
                "Dimensión",
                "Grupo temático",
                "Nivel",
                "Cobertura ponderada",
                "Prioridad",
                "Revisión humana",
            ),
            _filas_dimensiones(resultados),
        )
    )

    for resultado in resultados:
        lineas.extend(
            [
                "",
                f"### {_texto(resultado.get('dimension_codigo'))} — "
                f"{_texto(resultado.get('dimension_nombre'))}",
                "",
                f"- **Nivel consolidado:** {_etiqueta_nivel(resultado.get('nivel_consolidado'))}",
                f"- **Cobertura ponderada:** {_cobertura_ponderada(resultado)}",
                f"- **Prioridad documental:** "
                f"{_etiqueta_prioridad(resultado.get('prioridad_documental'))}",
                f"- **Justificación:** {_texto(resultado.get('justificacion'))}",
                f"- **Brechas principales:** {_lista(resultado.get('brechas_principales'))}",
                f"- **Guardrails críticos pendientes:** "
                f"{_lista(resultado.get('guardrails_criticos_pendientes'))}",
                f"- **Revisión humana:** {_revision_humana(resultado)}",
                f"- **Hallazgos relacionados:** "
                f"{len(resultado.get('hallazgos_relacionados', []))}",
            ]
        )

    lineas.append("")
    lineas.append("## Hallazgos")
    if not hallazgos:
        lineas.extend(
            [
                "",
                "No se registraron hallazgos para los guardrails aplicados "
                "en esta ejecución.",
            ]
        )
    for hallazgo in hallazgos:
        lineas.extend(
            [
                "",
                f"### {_texto(hallazgo.get('guardrail_codigo'))} "
                f"v{_texto(hallazgo.get('guardrail_version'))} — "
                f"{_etiqueta_nivel(hallazgo.get('nivel_preliminar'))}",
                "",
                f"- **Familia:** {_texto(hallazgo.get('familia_guardrail'))}",
                f"- **Dimensiones asociadas:** "
                f"{_lista(hallazgo.get('dimensiones_asociadas'))}",
                f"- **Criterios asociados:** {_lista(hallazgo.get('criterios_asociados'))}",
                f"- **Prioridad documental:** "
                f"{_etiqueta_prioridad(hallazgo.get('prioridad_documental'))} "
                f"({_texto(hallazgo.get('justificacion_prioridad'))})",
                f"- **Peso en la cobertura ponderada:** {_texto(hallazgo.get('peso'))}",
                f"- **Justificación:** {_texto(hallazgo.get('justificacion'))}",
                f"- **Revisión humana:** {_revision_humana(hallazgo)}",
            ]
        )
        evidencias = hallazgo.get("evidencias", [])
        if not evidencias:
            lineas.append("- **Evidencias:** —")
            continue
        lineas.append("- **Evidencias:**")
        for evidencia in evidencias:
            descripcion = _descripcion_evidencia(evidencia)
            detalle = f" ({descripcion})" if descripcion else ""
            lineas.append(
                f"  - `{_texto(evidencia.get('tipo_vinculo'))}` "
                f"«{_texto(evidencia.get('texto'))}»{detalle}"
            )

    lineas.append("")
    lineas.append("## Alertas")
    if not alertas:
        lineas.extend(
            ["", "No se generaron alertas documentales en esta ejecución."]
        )
    else:
        lineas.append("")
        lineas.extend(
            _tabla_markdown(
                ("Dimensión", "Alerta", "Nivel", "Prioridad", "Revisión humana"),
                _filas_alertas(alertas),
            )
        )
        for alerta in alertas:
            lineas.extend(
                [
                    "",
                    f"### {_texto(alerta.get('dimension_codigo'))} — "
                    f"{_texto(alerta.get('titulo'))}",
                    "",
                    f"- **Descripción:** {_texto(alerta.get('descripcion'))}",
                    f"- **Brechas:** {_lista(alerta.get('brechas'))}",
                    f"- **Revisión humana:** {_revision_humana(alerta)}",
                    f"- **Hallazgos relacionados:** "
                    f"{len(alerta.get('hallazgos_relacionados', []))}",
                    f"- **Recomendaciones asociadas:** "
                    f"{len(alerta.get('recomendaciones_asociadas', []))}",
                ]
            )

    lineas.append("")
    lineas.append("## Recomendaciones")
    if not recomendaciones:
        lineas.extend(
            ["", "No se generaron recomendaciones documentales en esta ejecución."]
        )
    else:
        lineas.append("")
        lineas.extend(
            _tabla_markdown(
                ("Dimensión", "Tipo de mejora", "Prioridad", "Acción sugerida"),
                _filas_recomendaciones(recomendaciones),
            )
        )
        for recomendacion in recomendaciones:
            lineas.extend(
                [
                    "",
                    f"### {_texto(recomendacion.get('dimension_codigo'))} — "
                    f"{_texto(recomendacion.get('tipo_mejora'))}",
                    "",
                    f"- **Acción sugerida:** "
                    f"{_texto(recomendacion.get('accion_sugerida'))}",
                    f"- **Fundamento:** {_texto(recomendacion.get('fundamento'))}",
                    f"- **Prioridad documental:** "
                    f"{_etiqueta_prioridad(recomendacion.get('prioridad_documental'))}",
                    f"- **Plantilla:** "
                    f"{_texto(recomendacion.get('plantilla_version'))}",
                ]
            )

    lineas.extend(["", "## Advertencias", ""])
    if advertencias:
        lineas.extend(f"- {_texto(advertencia)}" for advertencia in advertencias)
    else:
        lineas.append("Sin advertencias registradas durante la evaluación.")

    lineas.append("")
    return "\n".join(lineas)


_CLASES_NIVEL = {
    NivelCobertura.AUSENTE.value: "nivel-ausente",
    NivelCobertura.PARCIAL.value: "nivel-parcial",
    NivelCobertura.EXPLICITO.value: "nivel-explicito",
}

_CLASES_PRIORIDAD = {
    PrioridadDocumental.BAJA.value: "prioridad-baja",
    PrioridadDocumental.MEDIA.value: "prioridad-media",
    PrioridadDocumental.ALTA.value: "prioridad-alta",
}

_ESTILOS_HTML = """
:root { color-scheme: light; }
* { box-sizing: border-box; }
body {
  margin: 0;
  padding: 2.5rem 1.5rem 4rem;
  background: #f6f7f9;
  color: #1c1f23;
  font-family: "Segoe UI", system-ui, -apple-system, "Helvetica Neue", sans-serif;
  font-size: 15px;
  line-height: 1.55;
}
main { max-width: 60rem; margin: 0 auto; }
h1 { font-size: 1.75rem; margin: 0 0 .25rem; }
h2 {
  font-size: 1.15rem;
  margin: 2.25rem 0 .75rem;
  padding-bottom: .35rem;
  border-bottom: 1px solid #d7dbe0;
}
h3 { font-size: 1rem; margin: 1.5rem 0 .5rem; }
p { margin: .5rem 0; }
.aviso {
  margin: 1.25rem 0 0;
  padding: .85rem 1rem;
  background: #fff8e6;
  border-left: 4px solid #d9a441;
  border-radius: 4px;
  font-size: .9rem;
}
.tarjeta {
  background: #ffffff;
  border: 1px solid #e2e5ea;
  border-radius: 8px;
  padding: 1rem 1.25rem;
  margin: 0 0 1rem;
}
.subtitulo { color: #5b6470; margin: 0 0 1rem; }
table { width: 100%; border-collapse: collapse; margin: .5rem 0 1rem; font-size: .9rem; }
th, td { text-align: left; padding: .5rem .65rem; border-bottom: 1px solid #e2e5ea; vertical-align: top; }
th { background: #eef1f5; font-weight: 600; }
tbody tr:nth-child(even) { background: #fafbfc; }
.etiqueta {
  display: inline-block;
  padding: .1rem .5rem;
  border-radius: 999px;
  font-size: .8rem;
  font-weight: 600;
  white-space: nowrap;
}
.nivel-ausente { background: #fbe3e3; color: #8c2020; }
.nivel-parcial { background: #fdf1d8; color: #855c10; }
.nivel-explicito { background: #e0f2e4; color: #1d6b32; }
.prioridad-alta { background: #fbe3e3; color: #8c2020; }
.prioridad-media { background: #fdf1d8; color: #855c10; }
.prioridad-baja { background: #e9edf2; color: #47505c; }
.dato { margin: .2rem 0; }
.dato span { color: #5b6470; }
.evidencia {
  margin: .35rem 0 .35rem 1rem;
  padding-left: .75rem;
  border-left: 3px solid #d7dbe0;
  font-size: .9rem;
}
.evidencia .ubicacion { display: block; color: #5b6470; font-size: .82rem; }
.vacio { color: #5b6470; font-style: italic; }
ul { margin: .35rem 0 .35rem 1.1rem; padding: 0; }
footer { margin-top: 3rem; color: #5b6470; font-size: .82rem; }
@media print {
  body { background: #ffffff; padding: 0; font-size: 11pt; }
  .tarjeta { border: none; padding: 0; }
  h2 { page-break-after: avoid; }
  h3, table, .evidencia { page-break-inside: avoid; }
}
"""


def _e(valor: Any) -> str:
    return html.escape(_texto(valor), quote=False)


def _etiqueta_html(texto: str, clase: str) -> str:
    return f'<span class="etiqueta {clase}">{html.escape(texto, quote=False)}</span>'


def _clave_de_etiqueta(valor: Any, etiquetas: Mapping[str, str]) -> str:
    texto = str(_valor_plano(valor)).casefold()
    for clave, etiqueta in etiquetas.items():
        if texto in {clave.casefold(), etiqueta.casefold()}:
            return clave
    return str(_valor_plano(valor))


def _nivel_html(valor: Any) -> str:
    clave = _clave_de_etiqueta(valor, _ETIQUETAS_NIVEL)
    return _etiqueta_html(
        _ETIQUETAS_NIVEL.get(clave, _texto(valor)),
        _CLASES_NIVEL.get(clave, ""),
    )


def _prioridad_html(valor: Any) -> str:
    clave = _clave_de_etiqueta(valor, _ETIQUETAS_PRIORIDAD)
    return _etiqueta_html(
        _ETIQUETAS_PRIORIDAD.get(clave, _texto(valor)),
        _CLASES_PRIORIDAD.get(clave, ""),
    )


def _tabla_html(
    encabezados: Sequence[str],
    filas: Sequence[Sequence[str]],
    columnas_crudas: Sequence[int] = (),
) -> str:
    """Arma una tabla; `columnas_crudas` indica las celdas que ya son HTML."""
    cabecera = "".join(f"<th>{_e(encabezado)}</th>" for encabezado in encabezados)
    cuerpo = []
    for fila in filas:
        celdas = "".join(
            f"<td>{celda if indice in columnas_crudas else _e(celda)}</td>"
            for indice, celda in enumerate(fila)
        )
        cuerpo.append(f"<tr>{celdas}</tr>")
    return (
        "<table><thead><tr>"
        + cabecera
        + "</tr></thead><tbody>"
        + "".join(cuerpo)
        + "</tbody></table>"
    )


def _dato_html(etiqueta: str, valor: str) -> str:
    return f'<p class="dato"><span>{_e(etiqueta)}:</span> {_e(valor)}</p>'


def _exportar_html(
    reporte: Mapping[str, Any],
    metadatos: Mapping[str, Any],
    fecha_generacion: datetime,
) -> str:
    indicadores = reporte.get("indicadores", {})
    resultados = reporte.get("resultados_dimension", [])
    hallazgos = reporte.get("hallazgos", [])
    alertas = reporte.get("alertas", [])
    recomendaciones = reporte.get("recomendaciones", [])
    advertencias = reporte.get("advertencias", [])
    titulo = f"Reporte de cobertura ética documental — {_texto(metadatos.get('nombre_documento'))}"

    partes: List[str] = [
        "<!doctype html>",
        '<html lang="es">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{_e(titulo)}</title>",
        f"<style>{_ESTILOS_HTML}</style>",
        "</head>",
        "<body><main>",
        "<h1>Reporte de cobertura ética documental</h1>",
        f'<p class="subtitulo">{_e(metadatos.get("nombre_documento"))}</p>',
        f'<p class="aviso">{_e(AVISO_ALCANCE)}</p>',
        "<h2>Identificación</h2>",
        '<div class="tarjeta">',
        _tabla_html(
            ("Campo", "Valor"),
            [
                ["ID del documento", _texto(metadatos.get("documento_id"))],
                ["ID del análisis", _texto(metadatos.get("analisis_id"))],
                ["Estado", _texto(metadatos.get("estado"))],
                ["Dominio de aplicación", _dominio(metadatos)],
                ["Inicio del análisis", _texto(metadatos.get("fecha_inicio"))],
                ["Fin del análisis", _texto(metadatos.get("fecha_fin"))],
                ["Fecha de exportación", fecha_generacion.isoformat()],
                ["Lectura global", _texto(reporte.get("lectura_global"))],
            ],
        ),
        "</div>",
        "<h2>Resumen ejecutivo</h2>",
        f'<div class="tarjeta"><p>{_e(reporte.get("resumen_ejecutivo"))}</p></div>',
        "<h2>Indicadores globales</h2>",
        '<div class="tarjeta">',
        _tabla_html(("Indicador", "Valor"), _filas_indicadores(indicadores)),
        "</div>",
    ]

    filas_grupos = _filas_grupos(indicadores)
    if filas_grupos:
        for fila in filas_grupos:
            fila[5] = _prioridad_html(fila[5])
        partes.extend(
            [
                "<h2>Cobertura por grupo temático</h2>",
                '<div class="tarjeta">',
                _tabla_html(
                    (
                        "Grupo temático",
                        "Dimensiones",
                        "Ausentes",
                        "Parciales",
                        "Explícitas",
                        "Prioridad máxima",
                        "Revisión humana",
                    ),
                    filas_grupos,
                    columnas_crudas=(5,),
                ),
                "</div>",
            ]
        )

    filas_dimensiones = [
        [
            _texto(resultado.get("dimension_codigo")),
            _texto(resultado.get("dimension_nombre")),
            _texto(resultado.get("grupo_tematico")),
            _nivel_html(resultado.get("nivel_consolidado")),
            _cobertura_ponderada(resultado),
            _prioridad_html(resultado.get("prioridad_documental")),
            _texto(bool(resultado.get("requiere_revision_humana"))),
        ]
        for resultado in resultados
    ]
    partes.extend(
        [
            "<h2>Cobertura por dimensión</h2>",
            '<div class="tarjeta">',
            _tabla_html(
                (
                    "Código",
                    "Dimensión",
                    "Grupo temático",
                    "Nivel",
                    "Cobertura ponderada",
                    "Prioridad",
                    "Revisión humana",
                ),
                filas_dimensiones,
                columnas_crudas=(3, 5),
            ),
            "</div>",
        ]
    )

    for resultado in resultados:
        partes.extend(
            [
                f"<h3>{_e(resultado.get('dimension_codigo'))} — "
                f"{_e(resultado.get('dimension_nombre'))} "
                f"{_nivel_html(resultado.get('nivel_consolidado'))}</h3>",
                '<div class="tarjeta">',
                _dato_html("Cobertura ponderada", _cobertura_ponderada(resultado)),
                _dato_html(
                    "Prioridad documental",
                    _etiqueta_prioridad(resultado.get("prioridad_documental")),
                ),
                _dato_html("Justificación", _texto(resultado.get("justificacion"))),
                _dato_html(
                    "Brechas principales",
                    _lista(resultado.get("brechas_principales")),
                ),
                _dato_html(
                    "Guardrails críticos pendientes",
                    _lista(resultado.get("guardrails_criticos_pendientes")),
                ),
                _dato_html("Revisión humana", _revision_humana(resultado)),
                "</div>",
            ]
        )

    partes.append("<h2>Hallazgos</h2>")
    if not hallazgos:
        partes.append(
            '<p class="vacio">No se registraron hallazgos para los guardrails '
            "aplicados en esta ejecución.</p>"
        )
    for hallazgo in hallazgos:
        partes.extend(
            [
                f"<h3>{_e(hallazgo.get('guardrail_codigo'))} "
                f"v{_e(hallazgo.get('guardrail_version'))} "
                f"{_nivel_html(hallazgo.get('nivel_preliminar'))}</h3>",
                '<div class="tarjeta">',
                _dato_html("Familia", _texto(hallazgo.get("familia_guardrail"))),
                _dato_html(
                    "Dimensiones asociadas",
                    _lista(hallazgo.get("dimensiones_asociadas")),
                ),
                _dato_html(
                    "Criterios asociados",
                    _lista(hallazgo.get("criterios_asociados")),
                ),
                _dato_html(
                    "Prioridad documental",
                    f"{_etiqueta_prioridad(hallazgo.get('prioridad_documental'))} "
                    f"({_texto(hallazgo.get('justificacion_prioridad'))})",
                ),
                _dato_html(
                    "Peso en la cobertura ponderada",
                    _texto(hallazgo.get("peso")),
                ),
                _dato_html("Justificación", _texto(hallazgo.get("justificacion"))),
                _dato_html("Revisión humana", _revision_humana(hallazgo)),
            ]
        )
        evidencias = hallazgo.get("evidencias", [])
        if evidencias:
            partes.append("<p class=\"dato\"><span>Evidencias:</span></p>")
            for evidencia in evidencias:
                descripcion = _descripcion_evidencia(evidencia)
                ubicacion = (
                    f'<span class="ubicacion">{_e(descripcion)}</span>'
                    if descripcion
                    else ""
                )
                partes.append(
                    f'<div class="evidencia">{_e(evidencia.get("tipo_vinculo"))}: '
                    f"«{_e(evidencia.get('texto'))}»{ubicacion}</div>"
                )
        else:
            partes.append('<p class="vacio">Sin evidencias asociadas.</p>')
        partes.append("</div>")

    partes.append("<h2>Alertas</h2>")
    if not alertas:
        partes.append(
            '<p class="vacio">No se generaron alertas documentales en esta '
            "ejecución.</p>"
        )
    else:
        filas_alertas = _filas_alertas(alertas)
        for fila in filas_alertas:
            fila[2] = _nivel_html(fila[2])
            fila[3] = _prioridad_html(fila[3])
        partes.extend(
            [
                '<div class="tarjeta">',
                _tabla_html(
                    ("Dimensión", "Alerta", "Nivel", "Prioridad", "Revisión humana"),
                    filas_alertas,
                    columnas_crudas=(2, 3),
                ),
                "</div>",
            ]
        )
        for alerta in alertas:
            partes.extend(
                [
                    f"<h3>{_e(alerta.get('dimension_codigo'))} — "
                    f"{_e(alerta.get('titulo'))} "
                    f"{_prioridad_html(alerta.get('prioridad_documental'))}</h3>",
                    '<div class="tarjeta">',
                    _dato_html("Descripción", _texto(alerta.get("descripcion"))),
                    _dato_html("Brechas", _lista(alerta.get("brechas"))),
                    _dato_html("Revisión humana", _revision_humana(alerta)),
                    "</div>",
                ]
            )

    partes.append("<h2>Recomendaciones</h2>")
    if not recomendaciones:
        partes.append(
            '<p class="vacio">No se generaron recomendaciones documentales en '
            "esta ejecución.</p>"
        )
    else:
        filas_recomendaciones = _filas_recomendaciones(recomendaciones)
        for fila in filas_recomendaciones:
            fila[2] = _prioridad_html(fila[2])
        partes.extend(
            [
                '<div class="tarjeta">',
                _tabla_html(
                    ("Dimensión", "Tipo de mejora", "Prioridad", "Acción sugerida"),
                    filas_recomendaciones,
                    columnas_crudas=(2,),
                ),
                "</div>",
            ]
        )
        for recomendacion in recomendaciones:
            partes.extend(
                [
                    f"<h3>{_e(recomendacion.get('dimension_codigo'))} — "
                    f"{_e(recomendacion.get('tipo_mejora'))} "
                    f"{_prioridad_html(recomendacion.get('prioridad_documental'))}"
                    "</h3>",
                    '<div class="tarjeta">',
                    _dato_html(
                        "Acción sugerida",
                        _texto(recomendacion.get("accion_sugerida")),
                    ),
                    _dato_html("Fundamento", _texto(recomendacion.get("fundamento"))),
                    _dato_html(
                        "Plantilla", _texto(recomendacion.get("plantilla_version"))
                    ),
                    "</div>",
                ]
            )

    partes.append("<h2>Advertencias</h2>")
    if advertencias:
        elementos = "".join(
            f"<li>{_e(advertencia)}</li>" for advertencia in advertencias
        )
        partes.append(f'<div class="tarjeta"><ul>{elementos}</ul></div>')
    else:
        partes.append(
            '<p class="vacio">Sin advertencias registradas durante la evaluación.</p>'
        )

    partes.extend(
        [
            "<footer>Generado por el prototipo de revisión ética temprana de ERS de IA "
            f"el {_e(fecha_generacion.isoformat())}.</footer>",
            "</main></body></html>",
        ]
    )
    return "\n".join(partes) + "\n"
