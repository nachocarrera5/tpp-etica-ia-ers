import json
from io import BytesIO

from docx import Document
from fastapi.testclient import TestClient

from etica_ia_ers.api import app
from etica_ia_ers.dominio import FormatoDocumento

client = TestClient(app)


def _crear_docx_bytes() -> bytes:
    documento = Document()
    documento.add_paragraph("Requisito de explicabilidad")
    buffer = BytesIO()
    documento.save(buffer)
    return buffer.getvalue()


def prueba_api_carga_documento_y_consulta_estado() -> None:
    contenido = _crear_docx_bytes()

    respuesta = client.post(
        "/documentos",
        files={
            "archivo": (
                "ers.docx",
                contenido,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
        data={"metadatos": json.dumps({"dominio": "crediticio"})},
    )

    assert respuesta.status_code == 201
    datos = respuesta.json()
    assert datos["status"] == "COMPLETADO"
    assert datos["formato_origen"] == FormatoDocumento.DOCX.value
    assert datos["documento_id"] is not None
    assert datos["hash_contenido"] is not None

    estado = client.get(f"/documentos/{datos['id']}/estado")
    assert estado.status_code == 200
    datos_estado = estado.json()
    assert datos_estado["status"] == "COMPLETADO"
    assert datos_estado["error"] is None


def prueba_api_rechaza_metadatos_invalidos() -> None:
    respuesta = client.post(
        "/documentos",
        files={"archivo": ("ers.txt", b"Texto de prueba", "text/plain")},
        data={"metadatos": "{"},
    )

    assert respuesta.status_code == 400


def prueba_api_rechaza_formato_no_soportado() -> None:
    respuesta = client.post(
        "/documentos",
        files={"archivo": ("ers.md", b"# No soportado", "text/markdown")},
    )

    assert respuesta.status_code == 400
