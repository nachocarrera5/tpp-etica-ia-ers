import json
from io import BytesIO
from typing import Iterator, Tuple
from uuid import UUID, uuid4

import pytest
from docx import Document
from fastapi.testclient import TestClient

from etica_ia_ers.api import app, obtener_repositorio
from etica_ia_ers.dominio import EstadoAnalisis, FormatoDocumento
from etica_ia_ers.persistencia_y_trazabilidad import (
    RepositorioEnArchivos,
    RepositorioEnMemoria,
)


@pytest.fixture
def entorno_api() -> Iterator[Tuple[TestClient, RepositorioEnMemoria]]:
    repositorio = RepositorioEnMemoria()
    app.dependency_overrides[obtener_repositorio] = lambda: repositorio
    try:
        with TestClient(app) as cliente:
            yield cliente, repositorio
    finally:
        app.dependency_overrides.clear()


def _crear_docx_bytes() -> bytes:
    documento = Document()
    documento.add_paragraph("Requisito de explicabilidad")
    buffer = BytesIO()
    documento.save(buffer)
    return buffer.getvalue()


def prueba_api_carga_normaliza_almacena_y_consulta_estado(entorno_api) -> None:
    cliente, repositorio = entorno_api

    respuesta = cliente.post(
        "/documentos",
        files={
            "archivo": (
                "ers.docx",
                _crear_docx_bytes(),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
        data={"metadatos": json.dumps({"dominio": "crediticio"})},
    )

    assert respuesta.status_code == 201
    datos = respuesta.json()
    assert datos["id"] == datos["documento_id"]
    assert datos["estado"] == EstadoAnalisis.NORMALIZADO.value
    assert datos["formato_origen"] == FormatoDocumento.DOCX.value
    assert datos["hash_contenido"] is not None

    documento_id = datos["documento_id"]
    registro = repositorio.obtener(UUID(documento_id))
    normalizacion = repositorio.obtener_texto_normalizado(UUID(documento_id))
    assert registro.estado is EstadoAnalisis.NORMALIZADO
    assert registro.documento.metadatos == {"dominio": "crediticio"}
    assert normalizacion is not None
    assert normalizacion.original == registro.documento.contenido_extraido

    estado = cliente.get(f"/documentos/{documento_id}/estado")
    assert estado.status_code == 200
    assert estado.json()["estado"] == EstadoAnalisis.NORMALIZADO.value


def prueba_api_rechaza_metadatos_invalidos_sin_almacenar(entorno_api) -> None:
    cliente, repositorio = entorno_api

    respuesta = cliente.post(
        "/documentos",
        files={"archivo": ("ers.txt", b"Texto de prueba", "text/plain")},
        data={"metadatos": "{"},
    )

    assert respuesta.status_code == 400
    assert repositorio.listar() == []


def prueba_api_rechaza_formato_no_soportado_sin_almacenar(entorno_api) -> None:
    cliente, repositorio = entorno_api

    respuesta = cliente.post(
        "/documentos",
        files={"archivo": ("ers.md", b"# No soportado", "text/markdown")},
    )

    assert respuesta.status_code == 400
    assert repositorio.listar() == []


def prueba_api_informa_documento_no_encontrado(entorno_api) -> None:
    cliente, _ = entorno_api

    respuesta = cliente.get(f"/documentos/{uuid4()}/estado")

    assert respuesta.status_code == 404
    assert respuesta.json()["detail"] == "Documento no encontrado."


def prueba_api_sirve_interfaz_y_estado_de_salud(entorno_api) -> None:
    cliente, _ = entorno_api

    interfaz = cliente.get("/")
    estilos = cliente.get("/recursos/estilos.css")
    aplicacion = cliente.get("/recursos/aplicacion.js")
    salud = cliente.get("/salud")

    assert interfaz.status_code == 200
    assert "Revisión ética de ERS" in interfaz.text
    assert 'id="descargar-reporte"' in interfaz.text
    assert 'id="formato-exportacion"' in interfaz.text
    assert 'href="/recursos/estilos.css?v=4"' in interfaz.text
    assert 'src="/recursos/aplicacion.js?v=4"' in interfaz.text
    assert 'id="alternar-panel"' in interfaz.text
    assert 'id="buscar-hallazgos"' in interfaz.text
    assert "E10" not in interfaz.text
    assert estilos.status_code == 200
    assert "--acento" in estilos.text
    assert "body.modo-publico .panel-documentos" not in estilos.text
    assert aplicacion.status_code == 200
    assert "renderizarResultado" in aplicacion.text
    assert "descargarReporte" in aplicacion.text
    assert "Sin almacenamiento" not in aplicacion.text
    assert "resultadosTemporales" in aplicacion.text
    assert salud.json() == {"estado": "disponible", "version": "0.1.0"}


def prueba_api_analiza_sin_persistir_documento(entorno_api) -> None:
    cliente, repositorio = entorno_api

    respuesta = cliente.post(
        "/analisis",
        files={
            "archivo": (
                "ers-publica.txt",
                b"El sistema permitira al operador revisar cada decision.",
                "text/plain",
            )
        },
        data={"metadatos": json.dumps({"dominio": "otro"})},
    )

    assert respuesta.status_code == 200
    resultado = respuesta.json()
    assert resultado["metadatos"]["nombre_documento"] == "ers-publica.txt"
    assert len(resultado["resultados_dimension"]) == 10
    assert resultado["indicadores"]["guardrails_aplicados"] == 72
    assert repositorio.listar() == []


def prueba_api_modo_publico_oculta_operaciones_persistentes(
    entorno_api,
    monkeypatch,
) -> None:
    cliente, _ = entorno_api
    monkeypatch.setenv("MODO_PUBLICO", "true")
    configuracion = cliente.get("/configuracion-publica")

    assert configuracion.status_code == 200
    assert configuracion.json()["modo_publico"] is True
    assert configuracion.json()["persistencia_habilitada"] is False
    assert cliente.get("/documentos").status_code == 404
    assert cliente.post(
        "/documentos",
        files={"archivo": ("ers.txt", b"Un requisito", "text/plain")},
    ).status_code == 404


def prueba_api_modo_publico_no_inicializa_almacenamiento(monkeypatch) -> None:
    monkeypatch.setenv("MODO_PUBLICO", "true")
    obtener_repositorio.cache_clear()

    def fallar_si_se_inicializa():
        raise AssertionError("No debe inicializarse almacenamiento en modo público")

    monkeypatch.setattr(
        "etica_ia_ers.api.RepositorioEnArchivos",
        fallar_si_se_inicializa,
    )
    try:
        with TestClient(app) as cliente:
            respuesta = cliente.get("/documentos")
    finally:
        obtener_repositorio.cache_clear()

    assert respuesta.status_code == 404


def prueba_api_rechaza_archivo_que_supera_el_limite(
    entorno_api,
    monkeypatch,
) -> None:
    cliente, _ = entorno_api
    monkeypatch.setenv("MAX_TAMANO_ARCHIVO_MB", "0.01")

    respuesta = cliente.post(
        "/analisis",
        files={"archivo": ("ers.txt", b"a" * 11_000, "text/plain")},
    )

    assert respuesta.status_code == 413
    assert "0.01 MB" in respuesta.json()["detail"]


def prueba_api_lista_y_elimina_documentos(entorno_api) -> None:
    cliente, repositorio = entorno_api
    primera = cliente.post(
        "/documentos",
        files={"archivo": ("primera.txt", b"Primer requisito", "text/plain")},
    )
    segunda = cliente.post(
        "/documentos",
        files={"archivo": ("segunda.txt", b"Segundo requisito", "text/plain")},
    )

    respuesta_lista = cliente.get("/documentos")

    assert primera.status_code == 201
    assert segunda.status_code == 201
    assert respuesta_lista.status_code == 200
    assert [item["nombre_original"] for item in respuesta_lista.json()] == [
        "segunda.txt",
        "primera.txt",
    ]

    documento_id = primera.json()["documento_id"]
    respuesta_eliminacion = cliente.delete(f"/documentos/{documento_id}")

    assert respuesta_eliminacion.status_code == 204
    assert len(repositorio.listar()) == 1
    assert cliente.delete(f"/documentos/{documento_id}").status_code == 404


def prueba_api_conserva_documento_y_normalizacion_tras_reabrir_repositorio(
    tmp_path,
) -> None:
    repositorio = RepositorioEnArchivos(tmp_path)
    app.dependency_overrides[obtener_repositorio] = lambda: repositorio
    try:
        with TestClient(app) as cliente:
            respuesta = cliente.post(
                "/documentos",
                files={"archivo": ("ers.txt", b"Requisito verificable", "text/plain")},
            )
    finally:
        app.dependency_overrides.clear()

    assert respuesta.status_code == 201
    documento_id = UUID(respuesta.json()["documento_id"])

    repositorio_reabierto = RepositorioEnArchivos(tmp_path)
    registro = repositorio_reabierto.obtener(documento_id)
    normalizacion = repositorio_reabierto.obtener_texto_normalizado(documento_id)
    assert registro.estado is EstadoAnalisis.NORMALIZADO
    assert normalizacion is not None
    assert normalizacion.normalizado == "Requisito verificable"
