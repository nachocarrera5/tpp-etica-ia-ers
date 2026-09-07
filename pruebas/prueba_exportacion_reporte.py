from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterator, Tuple
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from etica_ia_ers.api import (
    app,
    obtener_repositorio,
    obtener_repositorio_guardrails,
)
from etica_ia_ers.dominio import (
    ContextoEvaluacionEtica,
    DecisionAplicabilidad,
    DefinicionGuardrail,
    DimensionEtica,
    EstadoGuardrail,
    EvaluacionPreliminarGuardrail,
    FamiliaGuardrail,
    NivelCobertura,
    PrioridadDocumental,
    ReferenciaEvidencia,
    TipoVinculoEvidencia,
)
from etica_ia_ers.modelo_etico_y_guardrails import RepositorioGuardrailsEnMemoria
from etica_ia_ers.persistencia_y_trazabilidad import RepositorioEnMemoria
from etica_ia_ers.resultados_y_presentacion import (
    AVISO_ALCANCE,
    FormatoExportacion,
    FormatoExportacionNoSoportadoError,
    ReporteInvalidoError,
    escribir_reporte,
    exportar_reporte,
    formatos_disponibles,
)

ANALISIS_ID = "6f1c9d4e-2a3b-4c5d-8e9f-0a1b2c3d4e5f"
DOCUMENTO_ID = "11111111-2222-3333-4444-555555555555"


def _reporte(**cambios: Any) -> Dict[str, Any]:
    """Reporte con la forma que produce `serializar_reporte_resultados`."""
    reporte: Dict[str, Any] = {
        "metadatos": {
            "analisis_id": ANALISIS_ID,
            "documento_id": DOCUMENTO_ID,
            "nombre_documento": "ERS Diagnóstico Médico.docx",
            "fecha_inicio": "2026-09-01T10:00:00+00:00",
            "fecha_fin": "2026-09-01T10:00:03+00:00",
            "estado": "EVALUADO",
        },
        "resumen_ejecutivo": "Se registraron observaciones documentales.",
        "lectura_global": "Cobertura documental inicial",
        "indicadores": {
            "total_dimensiones": 10,
            "dimensiones_ausentes": 8,
            "dimensiones_parciales": 1,
            "dimensiones_explicitas": 1,
            "porcentaje_cobertura_explicita": 10.0,
            "porcentaje_cobertura_no_ausente": 20.0,
            "total_hallazgos": 2,
            "total_alertas": 1,
            "total_recomendaciones": 1,
            "recomendaciones_alta_prioridad": 1,
            "hallazgos_con_revision_humana": 1,
            "porcentaje_revision_humana": 50.0,
            "hallazgos_prioridad_alta": 1,
            "hallazgos_prioridad_media": 1,
            "hallazgos_prioridad_baja": 0,
            "dimensiones_prioridad_alta": ["D01"],
            "guardrails_aplicados": 2,
            "guardrails_no_aplicables": 0,
            "guardrails_con_error": 0,
            "familias_guardrail_cubiertas": ["G-PRES"],
            "por_grupo": [
                {
                    "grupo_tematico": "Contexto y afectados",
                    "dimensiones_incluidas": ["D01", "D02"],
                    "ausentes": 1,
                    "parciales": 0,
                    "explicitas": 1,
                    "prioridad_maxima": "ALTA",
                    "requiere_revision_humana": True,
                }
            ],
        },
        "resultados_dimension": [
            {
                "dimension_codigo": "D01",
                "dimension_nombre": "Proposito y contexto",
                "grupo_tematico": "Contexto y afectados",
                "nivel_consolidado": "EXPLICITO",
                "valor_auxiliar": 2,
                "prioridad_documental": "ALTA",
                "justificacion": "La ERS declara el proposito del sistema.",
                "requiere_revision_humana": False,
                "motivo_revision_humana": None,
                "brechas_principales": [],
                "hallazgos_relacionados": [str(uuid4())],
            },
            {
                "dimension_codigo": "D02",
                "dimension_nombre": "Stakeholders e impacto",
                "grupo_tematico": "Contexto y afectados",
                "nivel_consolidado": "AUSENTE",
                "valor_auxiliar": 0,
                "prioridad_documental": "MEDIA",
                "justificacion": "No se identificaron stakeholders afectados.",
                "requiere_revision_humana": True,
                "motivo_revision_humana": "Confirmar la ausencia con el equipo.",
                "brechas_principales": ["Sin analisis de impacto"],
                "hallazgos_relacionados": [],
            },
        ],
        "hallazgos": [
            {
                "hallazgo_id": str(uuid4()),
                "analisis_id": ANALISIS_ID,
                "guardrail_codigo": "GR-D01-PROPOSITO",
                "guardrail_version": 1,
                "familia_guardrail": "G-PRES",
                "dimensiones_asociadas": ["D01"],
                "criterios_asociados": ["C-D01-01"],
                "nivel_preliminar": "EXPLICITO",
                "valor_auxiliar": 2,
                "prioridad_documental": "ALTA",
                "justificacion": "El fragmento declara el proposito.",
                "justificacion_prioridad": "Criticidad configurada del guardrail.",
                "requiere_revision_humana": False,
                "motivo_revision_humana": None,
                "evidencias": [
                    {
                        "fragmento_id": str(uuid4()),
                        "identificador_ers": "1.1",
                        "seccion_origen": "Introduccion",
                        "texto": "El sistema asiste al diagnostico medico.",
                        "posicion_inicio": 0,
                        "posicion_fin": 40,
                        "tipo_vinculo": "SOPORTA",
                        "relevancia": 0.8,
                        "observacion": None,
                    }
                ],
                "fecha_generacion": "2026-09-01T10:00:02+00:00",
            }
        ],
        "alertas": [
            {
                "alerta_id": str(uuid4()),
                "analisis_id": ANALISIS_ID,
                "documento_id": DOCUMENTO_ID,
                "resultado_dimension_id": str(uuid4()),
                "dimension_codigo": "D02",
                "nivel_cobertura": "AUSENTE",
                "prioridad_documental": "ALTA",
                "titulo": "Cobertura documental ausente en D02",
                "descripcion": "No se identificaron stakeholders afectados.",
                "brechas": ["Sin analisis de impacto"],
                "hallazgos_relacionados": [str(uuid4())],
                "recomendaciones_asociadas": [str(uuid4())],
                "requiere_revision_humana": True,
                "motivo_revision_humana": "Confirmar la ausencia con el equipo.",
            }
        ],
        "recomendaciones": [
            {
                "recomendacion_id": str(uuid4()),
                "analisis_id": ANALISIS_ID,
                "resultado_dimension_id": str(uuid4()),
                "dimension_codigo": "D02",
                "hallazgos_relacionados": [str(uuid4())],
                "accion_sugerida": "Documentar los stakeholders y su impacto.",
                "fundamento": "La dimension no registra evidencia documental.",
                "prioridad_documental": "ALTA",
                "tipo_mejora": "INCORPORAR",
                "plantilla_version": "1.0",
            }
        ],
        "advertencias": ["Una dimension quedo sin guardrails aplicables."],
    }
    reporte.update(cambios)
    return reporte


def prueba_exportacion_json_conserva_el_reporte_y_sella_la_salida() -> None:
    reporte = _reporte()

    exportado = exportar_reporte(reporte, FormatoExportacion.JSON)
    contenido = json.loads(exportado.contenido)

    for clave, valor in reporte.items():
        assert contenido[clave] == valor
    assert contenido["exportacion"]["formato"] == "JSON"
    assert contenido["exportacion"]["version_formato"] == 1
    assert contenido["exportacion"]["aviso_alcance"] == AVISO_ALCANCE
    assert exportado.tipo_contenido.startswith("application/json")
    assert exportado.analisis_id == ANALISIS_ID
    assert exportado.documento_id == DOCUMENTO_ID


def prueba_exportacion_markdown_incluye_indicadores_dimensiones_y_hallazgos() -> None:
    exportado = exportar_reporte(_reporte(), FormatoExportacion.MARKDOWN)
    contenido = exportado.contenido

    assert contenido.startswith("# Reporte de cobertura ética documental")
    assert AVISO_ALCANCE in contenido
    assert "## Resumen ejecutivo" in contenido
    assert "## Indicadores globales" in contenido
    assert "## Cobertura por grupo temático" in contenido
    assert "## Cobertura por dimensión" in contenido
    assert "### D01 — Proposito y contexto" in contenido
    assert "### GR-D01-PROPOSITO v1 — Explícito" in contenido
    assert "El sistema asiste al diagnostico medico." in contenido
    assert "Sí — Confirmar la ausencia con el equipo." in contenido
    assert "Una dimension quedo sin guardrails aplicables." in contenido
    assert exportado.tipo_contenido.startswith("text/markdown")


def prueba_exportacion_markdown_neutraliza_separadores_de_tabla() -> None:
    reporte = _reporte()
    reporte["resultados_dimension"][0]["dimension_nombre"] = "Proposito | contexto"

    contenido = exportar_reporte(reporte, FormatoExportacion.MARKDOWN).contenido

    # La barra del texto no debe partir la celda de la tabla de dimensiones.
    fila = next(
        linea
        for linea in contenido.splitlines()
        if linea.startswith("| D01 |")
    )
    assert "Proposito \\| contexto" in fila
    # Seis columnas: solo los siete separadores reales quedan sin escapar.
    assert fila.replace("\\|", "").count("|") == 7


def prueba_exportacion_html_escapa_el_texto_tomado_de_la_ers() -> None:
    reporte = _reporte()
    reporte["hallazgos"][0]["evidencias"][0]["texto"] = "<script>alert('x')</script>"

    contenido = exportar_reporte(reporte, FormatoExportacion.HTML).contenido

    assert "<script>alert" not in contenido
    assert "&lt;script&gt;alert" in contenido


def prueba_exportacion_html_es_un_documento_autocontenido_e_imprimible() -> None:
    exportado = exportar_reporte(_reporte(), FormatoExportacion.HTML)
    contenido = exportado.contenido

    assert contenido.startswith("<!doctype html>")
    assert contenido.rstrip().endswith("</html>")
    assert "@media print" in contenido
    assert "<link" not in contenido and "<script" not in contenido
    assert "Reporte de cobertura ética documental" in contenido
    assert AVISO_ALCANCE in contenido
    assert exportado.tipo_contenido.startswith("text/html")


def prueba_exportacion_incluye_alertas_y_recomendaciones() -> None:
    """El reporte de SCRUM-111 no puede perderse al pasar a Markdown ni a HTML."""
    markdown = exportar_reporte(_reporte(), FormatoExportacion.MARKDOWN).contenido
    html = exportar_reporte(_reporte(), FormatoExportacion.HTML).contenido

    for contenido in (markdown, html):
        assert "Alertas" in contenido
        assert "Recomendaciones" in contenido
        assert "Cobertura documental ausente en D02" in contenido
        assert "No se identificaron stakeholders afectados." in contenido
        assert "Documentar los stakeholders y su impacto." in contenido
        assert "La dimension no registra evidencia documental." in contenido
        assert "INCORPORAR" in contenido
        # Indicadores incorporados junto con las alertas.
        assert "Alertas generadas" in contenido
        assert "Recomendaciones de prioridad alta" in contenido

    assert '<span class="etiqueta nivel-ausente">Ausente</span>' in html
    assert '<span class="etiqueta prioridad-alta">Alta</span>' in html


def prueba_exportacion_informa_reporte_sin_alertas_ni_recomendaciones() -> None:
    reporte = _reporte(alertas=[], recomendaciones=[])

    markdown = exportar_reporte(reporte, FormatoExportacion.MARKDOWN).contenido
    html = exportar_reporte(reporte, FormatoExportacion.HTML).contenido

    for contenido in (markdown, html):
        assert "No se generaron alertas documentales" in contenido
        assert "No se generaron recomendaciones documentales" in contenido


def prueba_exportacion_tolera_un_reporte_sin_alertas_ni_recomendaciones() -> None:
    """Un reporte previo a SCRUM-111 sigue exportando, sin esas secciones."""
    reporte = _reporte()
    del reporte["alertas"]
    del reporte["recomendaciones"]

    markdown = exportar_reporte(reporte, FormatoExportacion.MARKDOWN).contenido

    assert "No se generaron alertas documentales" in markdown
    assert markdown.startswith("# Reporte de cobertura ética documental")


def prueba_exportacion_informa_reporte_sin_hallazgos() -> None:
    reporte = _reporte(hallazgos=[], advertencias=[])

    markdown = exportar_reporte(reporte, FormatoExportacion.MARKDOWN).contenido
    html = exportar_reporte(reporte, FormatoExportacion.HTML).contenido

    assert "No se registraron hallazgos" in markdown
    assert "Sin advertencias registradas" in markdown
    assert "No se registraron hallazgos" in html
    assert "Sin advertencias registradas" in html


@pytest.mark.parametrize(
    "alias, esperado",
    [
        ("json", FormatoExportacion.JSON),
        ("JSON", FormatoExportacion.JSON),
        ("md", FormatoExportacion.MARKDOWN),
        (".md", FormatoExportacion.MARKDOWN),
        ("Markdown", FormatoExportacion.MARKDOWN),
        (" html ", FormatoExportacion.HTML),
        ("htm", FormatoExportacion.HTML),
    ],
)
def prueba_formato_se_resuelve_por_alias(
    alias: str,
    esperado: FormatoExportacion,
) -> None:
    assert FormatoExportacion.desde_texto(alias) is esperado
    assert exportar_reporte(_reporte(), alias).formato is esperado


def prueba_formato_desconocido_lista_los_disponibles() -> None:
    with pytest.raises(FormatoExportacionNoSoportadoError) as error:
        FormatoExportacion.desde_texto("pdf")

    mensaje = str(error.value)
    for alias in formatos_disponibles():
        assert alias in mensaje


@pytest.mark.parametrize(
    "reporte_incompleto",
    [
        {},
        {"metadatos": {"analisis_id": ANALISIS_ID}},
    ],
)
def prueba_reporte_incompleto_se_rechaza(reporte_incompleto: Dict[str, Any]) -> None:
    with pytest.raises(ReporteInvalidoError):
        exportar_reporte(reporte_incompleto, FormatoExportacion.JSON)


def prueba_reporte_con_metadatos_incompletos_se_rechaza() -> None:
    reporte = _reporte()
    del reporte["metadatos"]["nombre_documento"]

    with pytest.raises(ReporteInvalidoError) as error:
        exportar_reporte(reporte, FormatoExportacion.MARKDOWN)

    assert "nombre_documento" in str(error.value)


@pytest.mark.parametrize(
    "nombre_documento, esperado",
    [
        ("ERS Diagnóstico Médico.docx", "reporte-etico-ers-diagnostico-medico"),
        ("../../etc/passwd.txt", "reporte-etico-passwd"),
        ("   ", "reporte-etico-ers"),
        ("ers:crediticio*v2.txt", "reporte-etico-ers-crediticio-v2"),
    ],
)
def prueba_nombre_de_archivo_es_seguro(
    nombre_documento: str,
    esperado: str,
) -> None:
    reporte = _reporte()
    reporte["metadatos"]["nombre_documento"] = nombre_documento

    nombre = exportar_reporte(reporte, FormatoExportacion.JSON).nombre_archivo

    sufijo = UUID(ANALISIS_ID).hex[:8]
    assert nombre == f"{esperado}-{sufijo}.json"
    assert Path(nombre).name == nombre


@pytest.mark.parametrize(
    "formato, extension",
    [
        (FormatoExportacion.JSON, ".json"),
        (FormatoExportacion.MARKDOWN, ".md"),
        (FormatoExportacion.HTML, ".html"),
    ],
)
def prueba_escribir_reporte_guarda_el_archivo_completo(
    tmp_path: Path,
    formato: FormatoExportacion,
    extension: str,
) -> None:
    exportado = exportar_reporte(_reporte(), formato)

    ruta = escribir_reporte(exportado, tmp_path / "salida")

    assert ruta.name.endswith(extension)
    assert ruta.read_text(encoding="utf-8") == exportado.contenido
    # La escritura atomica no debe dejar residuos junto al archivo final.
    assert sorted(p.name for p in ruta.parent.iterdir()) == [ruta.name]


def prueba_escribir_reporte_reemplaza_la_version_anterior(tmp_path: Path) -> None:
    primero = exportar_reporte(_reporte(), FormatoExportacion.MARKDOWN)
    segundo = exportar_reporte(
        _reporte(lectura_global="Cobertura documental desarrollada"),
        FormatoExportacion.MARKDOWN,
    )

    ruta = escribir_reporte(primero, tmp_path)
    assert escribir_reporte(segundo, tmp_path) == ruta

    contenido = ruta.read_text(encoding="utf-8")
    assert "Cobertura documental desarrollada" in contenido
    assert "Cobertura documental inicial" not in contenido


class GuardrailSintetico:
    """Guardrail de prueba: siempre EXPLICITO sobre el primer fragmento."""

    def __init__(self, codigo: str, dimension: DimensionEtica) -> None:
        self.definicion = DefinicionGuardrail(
            codigo=codigo,
            nombre=f"Guardrail sintetico {codigo}",
            version=1,
            estado=EstadoGuardrail.ACTIVA,
            familia=FamiliaGuardrail.PRESENCIA,
            dimensiones=(dimension,),
            descripcion="Guardrail usado por las pruebas de exportacion.",
            prioridad_base=PrioridadDocumental.MEDIA,
        )

    def decidir_aplicabilidad(
        self, contexto: ContextoEvaluacionEtica
    ) -> DecisionAplicabilidad:
        return DecisionAplicabilidad(aplica=True, motivo="Aplica siempre en la prueba.")

    def evaluar(
        self, contexto: ContextoEvaluacionEtica
    ) -> EvaluacionPreliminarGuardrail:
        fragmento = contexto.resultado_nlp.fragmentos_clasificados[0].fragmento
        return EvaluacionPreliminarGuardrail(
            nivel=NivelCobertura.EXPLICITO,
            justificacion="Evidencia sintetica encontrada en el primer fragmento.",
            prioridad=PrioridadDocumental.MEDIA,
            justificacion_prioridad="Prioridad fija de la prueba.",
            evidencias=(
                ReferenciaEvidencia(
                    fragmento_id=fragmento.id,
                    tipo_vinculo=TipoVinculoEvidencia.SOPORTA,
                ),
            ),
        )


@pytest.fixture
def entorno_api() -> Iterator[Tuple[TestClient, RepositorioEnMemoria]]:
    repositorio = RepositorioEnMemoria()
    app.dependency_overrides[obtener_repositorio] = lambda: repositorio
    app.dependency_overrides[obtener_repositorio_guardrails] = (
        lambda: RepositorioGuardrailsEnMemoria(
            (GuardrailSintetico("GR-PRUEBA-EXPORT-01", DimensionEtica.D01),)
        )
    )
    try:
        with TestClient(app) as cliente:
            yield cliente, repositorio
    finally:
        app.dependency_overrides.clear()


def _cargar_documento(cliente: TestClient) -> UUID:
    respuesta = cliente.post(
        "/documentos",
        files={
            "archivo": (
                "ers_credito.txt",
                b"1.1. El sistema debera registrar cada decision automatizada.",
                "text/plain",
            )
        },
    )
    assert respuesta.status_code == 201
    return UUID(respuesta.json()["documento_id"])


def prueba_api_exporta_json_por_defecto(entorno_api) -> None:
    cliente, _ = entorno_api
    documento_id = _cargar_documento(cliente)

    respuesta = cliente.get(f"/documentos/{documento_id}/reporte")

    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"].startswith("application/json")
    disposicion = respuesta.headers["content-disposition"]
    assert disposicion.startswith('attachment; filename="reporte-etico-ers-credito-')
    assert disposicion.endswith('.json"')

    contenido = respuesta.json()
    assert contenido["metadatos"]["documento_id"] == str(documento_id)
    assert contenido["exportacion"]["formato"] == "JSON"
    assert len(contenido["resultados_dimension"]) == 10


@pytest.mark.parametrize(
    "formato, tipo_contenido, extension",
    [
        ("md", "text/markdown", ".md"),
        ("markdown", "text/markdown", ".md"),
        ("html", "text/html", ".html"),
        ("JSON", "application/json", ".json"),
    ],
)
def prueba_api_exporta_cada_formato_como_archivo_descargable(
    entorno_api,
    formato: str,
    tipo_contenido: str,
    extension: str,
) -> None:
    cliente, _ = entorno_api
    documento_id = _cargar_documento(cliente)

    respuesta = cliente.get(
        f"/documentos/{documento_id}/reporte", params={"formato": formato}
    )

    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"].startswith(tipo_contenido)
    assert respuesta.headers["content-disposition"].endswith(f'{extension}"')
    assert respuesta.text.strip()


def prueba_api_rechaza_un_formato_no_soportado(entorno_api) -> None:
    cliente, _ = entorno_api
    documento_id = _cargar_documento(cliente)

    respuesta = cliente.get(
        f"/documentos/{documento_id}/reporte", params={"formato": "pdf"}
    )

    assert respuesta.status_code == 400
    assert "pdf" in respuesta.json()["detail"]


def prueba_api_valida_el_formato_antes_de_evaluar(entorno_api) -> None:
    cliente, _ = entorno_api

    # Aun sin documento que evaluar, el formato invalido se rechaza primero:
    # un pedido mal formado no cuesta una corrida de NLP y motor.
    respuesta = cliente.get(
        f"/documentos/{uuid4()}/reporte", params={"formato": "docx"}
    )

    assert respuesta.status_code == 400


def prueba_api_informa_documento_no_encontrado_al_exportar(entorno_api) -> None:
    cliente, _ = entorno_api

    respuesta = cliente.get(f"/documentos/{uuid4()}/reporte")

    assert respuesta.status_code == 404
    assert respuesta.json()["detail"] == "Documento no encontrado."


def prueba_api_exporta_el_mismo_reporte_que_devuelve_resultados(entorno_api) -> None:
    cliente, _ = entorno_api
    documento_id = _cargar_documento(cliente)

    resultados = cliente.get(f"/documentos/{documento_id}/resultados").json()
    exportado = cliente.get(f"/documentos/{documento_id}/reporte").json()

    # Cada llamada es una ejecucion nueva: cambian los identificadores, no la
    # estructura ni los indicadores del reporte.
    assert exportado["indicadores"] == resultados["indicadores"]
    assert exportado["lectura_global"] == resultados["lectura_global"]
    assert exportado["resumen_ejecutivo"] == resultados["resumen_ejecutivo"]
    assert len(exportado["hallazgos"]) == len(resultados["hallazgos"])
    assert [r["dimension_codigo"] for r in exportado["resultados_dimension"]] == [
        r["dimension_codigo"] for r in resultados["resultados_dimension"]
    ]
    assert set(resultados) <= set(exportado)


@pytest.mark.parametrize(
    "formato, tipo_contenido, extension",
    [
        ("json", "application/json", ".json"),
        ("md", "text/markdown", ".md"),
        ("html", "text/html", ".html"),
    ],
)
def prueba_api_publica_exporta_resultado_sin_persistencia(
    entorno_api,
    monkeypatch,
    formato: str,
    tipo_contenido: str,
    extension: str,
) -> None:
    cliente, repositorio = entorno_api
    monkeypatch.setenv("MODO_PUBLICO", "true")
    analisis = cliente.post(
        "/analisis",
        files={
            "archivo": (
                "ers_publica.txt",
                b"El sistema debera registrar cada decision automatizada.",
                "text/plain",
            )
        },
    )

    respuesta = cliente.post(
        "/reporte",
        params={"formato": formato},
        json=analisis.json(),
    )

    assert analisis.status_code == 200
    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"].startswith(tipo_contenido)
    assert respuesta.headers["content-disposition"].endswith(f'{extension}"')
    assert respuesta.text.strip()
    assert repositorio.listar() == []


def prueba_api_publica_rechaza_reporte_incompleto(entorno_api) -> None:
    cliente, _ = entorno_api

    respuesta = cliente.post(
        "/reporte",
        params={"formato": "html"},
        json={"metadatos": {"documento_id": str(uuid4())}},
    )

    assert respuesta.status_code == 422
