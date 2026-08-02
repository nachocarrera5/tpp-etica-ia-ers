import json
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

import pytest

from etica_ia_ers.dominio import (
    AccionTrazabilidad,
    DocumentoERS,
    EstadoAnalisis,
    FormatoDocumento,
    TextoNormalizado,
)
from etica_ia_ers.entrada_documental import cargar_documento
from etica_ia_ers.persistencia_y_trazabilidad import (
    AlmacenamientoCorruptoError,
    DocumentoNoEncontradoError,
    DocumentoYaRegistradoError,
    ErrorAlmacenamiento,
    RepositorioEnArchivos,
    RepositorioEnMemoria,
    TextoNormalizadoInvalidoError,
)
from etica_ia_ers.procesamiento_textual_y_nlp import NormalizadorDeTexto

FECHA_BASE = datetime(2026, 7, 20, 10, 30, tzinfo=timezone.utc)


def _documento(
    nombre: str = "ers.txt",
    contenido: str = "El sistema deberá explicar sus decisiones.",
    metadatos: Optional[Dict[str, Any]] = None,
    fecha_carga: Optional[datetime] = None,
    formato: FormatoDocumento = FormatoDocumento.TXT,
) -> DocumentoERS:
    return DocumentoERS(
        id=uuid4(),
        nombre_original=nombre,
        formato_origen=formato,
        contenido_extraido=contenido,
        hash_contenido=sha256(contenido.encode("utf-8")).hexdigest(),
        fecha_carga=fecha_carga or FECHA_BASE,
        metadatos=dict(metadatos or {}),
    )


@pytest.fixture(params=["memoria", "archivos"])
def repositorio(request: pytest.FixtureRequest, tmp_path: Path):
    if request.param == "memoria":
        return RepositorioEnMemoria()
    return RepositorioEnArchivos(tmp_path / "almacenamiento")


@pytest.fixture
def repositorio_en_archivos(tmp_path: Path) -> RepositorioEnArchivos:
    return RepositorioEnArchivos(tmp_path / "almacenamiento")


def prueba_guardar_registra_el_documento_en_estado_cargado(repositorio) -> None:
    documento = _documento()

    registro = repositorio.guardar(documento)

    assert registro.id == documento.id
    assert registro.estado is EstadoAnalisis.CARGADO
    assert registro.fecha_actualizacion.tzinfo is timezone.utc


def prueba_obtener_conserva_todos_los_campos(repositorio) -> None:
    documento = _documento(
        nombre="ers-crediticio.pdf",
        contenido="Sección 3.2 — sesgos\nEl modelo deberá auditarse.\n",
        metadatos={"dominio": "crediticio", "revisores": ["ana", "luis"]},
        formato=FormatoDocumento.PDF,
    )
    repositorio.guardar(documento)

    recuperado = repositorio.obtener(documento.id).documento

    assert recuperado == documento


def prueba_obtener_documento_inexistente(repositorio) -> None:
    with pytest.raises(DocumentoNoEncontradoError):
        repositorio.obtener(uuid4())


def prueba_rechaza_guardar_dos_veces_el_mismo_documento(repositorio) -> None:
    documento = _documento()
    repositorio.guardar(documento)

    with pytest.raises(DocumentoYaRegistradoError):
        repositorio.guardar(documento)


def prueba_admite_dos_cargas_del_mismo_archivo(repositorio) -> None:
    primero = _documento(contenido="Mismo contenido")
    segundo = _documento(contenido="Mismo contenido")

    repositorio.guardar(primero)
    repositorio.guardar(segundo)

    assert primero.hash_contenido == segundo.hash_contenido
    assert {resumen.id for resumen in repositorio.listar()} == {primero.id, segundo.id}


def prueba_listar_ordena_por_fecha_de_carga(repositorio) -> None:
    reciente = _documento(nombre="segunda.txt", fecha_carga=FECHA_BASE + timedelta(hours=1))
    antiguo = _documento(nombre="primera.txt", fecha_carga=FECHA_BASE)
    repositorio.guardar(reciente)
    repositorio.guardar(antiguo)

    resumenes = repositorio.listar()

    assert [resumen.nombre_original for resumen in resumenes] == [
        "primera.txt",
        "segunda.txt",
    ]


def prueba_listar_sin_documentos(repositorio) -> None:
    assert repositorio.listar() == []


def prueba_resumen_expone_el_estado_sin_el_contenido(repositorio) -> None:
    documento = _documento(metadatos={"dominio": "medico"})
    repositorio.guardar(documento)

    resumen = repositorio.listar()[0]

    assert resumen.id == documento.id
    assert resumen.nombre_original == documento.nombre_original
    assert resumen.formato_origen is documento.formato_origen
    assert resumen.hash_contenido == documento.hash_contenido
    assert resumen.fecha_carga == documento.fecha_carga
    assert resumen.estado is EstadoAnalisis.CARGADO
    assert resumen.metadatos == {"dominio": "medico"}
    assert not hasattr(resumen, "contenido_extraido")


def prueba_buscar_por_hash_devuelve_la_carga_mas_antigua(repositorio) -> None:
    reciente = _documento(
        nombre="copia.txt",
        contenido="Contenido repetido",
        fecha_carga=FECHA_BASE + timedelta(days=1),
    )
    original = _documento(
        nombre="original.txt",
        contenido="Contenido repetido",
        fecha_carga=FECHA_BASE,
    )
    repositorio.guardar(reciente)
    repositorio.guardar(original)

    encontrado = repositorio.buscar_por_hash(original.hash_contenido)

    assert encontrado is not None
    assert encontrado.id == original.id


def prueba_buscar_por_hash_sin_coincidencias(repositorio) -> None:
    repositorio.guardar(_documento())

    assert repositorio.buscar_por_hash("0" * 64) is None


def prueba_actualizar_estado(repositorio) -> None:
    registro = repositorio.guardar(_documento())

    resumen = repositorio.actualizar_estado(registro.id, EstadoAnalisis.NORMALIZADO)

    assert resumen.estado is EstadoAnalisis.NORMALIZADO
    assert resumen.fecha_actualizacion >= registro.fecha_actualizacion
    assert repositorio.obtener(registro.id).estado is EstadoAnalisis.NORMALIZADO
    assert repositorio.listar()[0].estado is EstadoAnalisis.NORMALIZADO


def prueba_actualizar_estado_no_altera_el_documento(repositorio) -> None:
    documento = _documento(metadatos={"dominio": "recomendador"})
    repositorio.guardar(documento)

    repositorio.actualizar_estado(documento.id, EstadoAnalisis.EVALUADO)

    assert repositorio.obtener(documento.id).documento == documento


def prueba_actualizar_estado_de_documento_inexistente(repositorio) -> None:
    with pytest.raises(DocumentoNoEncontradoError):
        repositorio.actualizar_estado(uuid4(), EstadoAnalisis.ERROR)


def _texto_normalizado(documento: DocumentoERS) -> TextoNormalizado:
    return TextoNormalizado(
        original=documento.contenido_extraido,
        normalizado=documento.contenido_extraido.upper(),
        pasos_aplicados=["normalizar_unicode", "colapsar_espacios"],
    )


def prueba_guardar_texto_normalizado_deja_el_documento_normalizado(repositorio) -> None:
    documento = _documento()
    repositorio.guardar(documento)

    resumen = repositorio.guardar_texto_normalizado(
        documento.id, _texto_normalizado(documento)
    )

    assert resumen.estado is EstadoAnalisis.NORMALIZADO
    assert repositorio.obtener(documento.id).estado is EstadoAnalisis.NORMALIZADO
    assert repositorio.listar()[0].estado is EstadoAnalisis.NORMALIZADO


def prueba_obtener_texto_normalizado(repositorio) -> None:
    documento = _documento()
    repositorio.guardar(documento)
    texto_normalizado = _texto_normalizado(documento)
    repositorio.guardar_texto_normalizado(documento.id, texto_normalizado)

    assert repositorio.obtener_texto_normalizado(documento.id) == texto_normalizado


def prueba_sin_normalizacion_todavia(repositorio) -> None:
    documento = _documento()
    repositorio.guardar(documento)

    assert repositorio.obtener_texto_normalizado(documento.id) is None


def prueba_normalizacion_de_documento_inexistente(repositorio) -> None:
    documento = _documento()

    with pytest.raises(DocumentoNoEncontradoError):
        repositorio.guardar_texto_normalizado(
            documento.id, _texto_normalizado(documento)
        )
    with pytest.raises(DocumentoNoEncontradoError):
        repositorio.obtener_texto_normalizado(documento.id)


def prueba_rechaza_normalizacion_de_otro_documento(repositorio) -> None:
    documento = _documento(contenido="Texto de la ERS almacenada")
    repositorio.guardar(documento)
    ajena = TextoNormalizado(
        original="Texto de otra ERS",
        normalizado="texto de otra ers",
        pasos_aplicados=["colapsar_espacios"],
    )

    with pytest.raises(TextoNormalizadoInvalidoError):
        repositorio.guardar_texto_normalizado(documento.id, ajena)

    assert repositorio.obtener_texto_normalizado(documento.id) is None
    assert repositorio.obtener(documento.id).estado is EstadoAnalisis.CARGADO


def prueba_renormalizar_reemplaza_la_normalizacion_anterior(repositorio) -> None:
    documento = _documento()
    repositorio.guardar(documento)
    repositorio.guardar_texto_normalizado(documento.id, _texto_normalizado(documento))
    segunda = TextoNormalizado(
        original=documento.contenido_extraido,
        normalizado=documento.contenido_extraido.lower(),
        pasos_aplicados=["colapsar_espacios"],
    )

    repositorio.guardar_texto_normalizado(documento.id, segunda)

    assert repositorio.obtener_texto_normalizado(documento.id) == segunda


def prueba_trazabilidad_registra_la_normalizacion(repositorio) -> None:
    documento = _documento()
    repositorio.guardar(documento)
    repositorio.guardar_texto_normalizado(documento.id, _texto_normalizado(documento))

    evento = repositorio.trazabilidad.eventos(documento.id)[-1]

    assert evento.accion is AccionTrazabilidad.NORMALIZACION
    assert evento.detalle["estado_anterior"] == "CARGADO"
    assert evento.detalle["estado_nuevo"] == "NORMALIZADO"
    assert evento.detalle["pasos_aplicados"] == [
        "normalizar_unicode",
        "colapsar_espacios",
    ]


def prueba_almacena_la_normalizacion_producida_por_el_normalizador(repositorio) -> None:
    documento = cargar_documento(
        "ers.txt",
        "1) El sistema  deberá  \r\n auditar sus decisiones.\r\n".encode("utf-8"),
    )
    repositorio.guardar(documento)

    texto_normalizado = NormalizadorDeTexto().normalizar(documento.contenido_extraido)
    repositorio.guardar_texto_normalizado(documento.id, texto_normalizado)

    assert repositorio.obtener_texto_normalizado(documento.id) == texto_normalizado


def prueba_eliminar_borra_tambien_la_normalizacion(repositorio) -> None:
    documento = _documento()
    repositorio.guardar(documento)
    repositorio.guardar_texto_normalizado(documento.id, _texto_normalizado(documento))
    repositorio.eliminar(documento.id)

    repositorio.guardar(documento)

    assert repositorio.obtener_texto_normalizado(documento.id) is None


def prueba_eliminar_documento(repositorio) -> None:
    documento = _documento()
    repositorio.guardar(documento)

    repositorio.eliminar(documento.id)

    assert repositorio.listar() == []
    with pytest.raises(DocumentoNoEncontradoError):
        repositorio.obtener(documento.id)


def prueba_eliminar_documento_inexistente(repositorio) -> None:
    with pytest.raises(DocumentoNoEncontradoError):
        repositorio.eliminar(uuid4())


def prueba_trazabilidad_registra_el_ciclo_de_vida(repositorio) -> None:
    documento = _documento()
    repositorio.guardar(documento)
    repositorio.actualizar_estado(documento.id, EstadoAnalisis.NORMALIZADO)
    repositorio.eliminar(documento.id)

    eventos = repositorio.trazabilidad.eventos(documento.id)

    assert [evento.accion for evento in eventos] == [
        AccionTrazabilidad.CARGA,
        AccionTrazabilidad.CAMBIO_ESTADO,
        AccionTrazabilidad.ELIMINACION,
    ]
    assert eventos[0].detalle["hash_contenido"] == documento.hash_contenido
    assert eventos[1].detalle == {
        "estado_anterior": "CARGADO",
        "estado_nuevo": "NORMALIZADO",
    }
    assert all(evento.fecha.tzinfo is timezone.utc for evento in eventos)


def prueba_trazabilidad_filtra_por_documento(repositorio) -> None:
    primero = _documento(nombre="primera.txt")
    segundo = _documento(nombre="segunda.txt")
    repositorio.guardar(primero)
    repositorio.guardar(segundo)

    assert len(repositorio.trazabilidad.eventos()) == 2
    assert len(repositorio.trazabilidad.eventos(primero.id)) == 1


def prueba_trazabilidad_en_memoria_no_expone_su_estado_interno() -> None:
    repositorio = RepositorioEnMemoria()
    documento = _documento()
    repositorio.guardar(documento)

    eventos = repositorio.trazabilidad.eventos(documento.id)
    eventos[0].detalle["estado"] = "ALTERADO"

    evento_guardado = repositorio.trazabilidad.eventos(documento.id)[0]
    assert evento_guardado.detalle["estado"] == EstadoAnalisis.CARGADO.value


def prueba_metadatos_almacenados_no_se_comparten_con_el_llamador(repositorio) -> None:
    metadatos = {"dominio": "crediticio"}
    documento = _documento(metadatos=metadatos)
    repositorio.guardar(documento)

    documento.metadatos["dominio"] = "modificado"
    metadatos["dominio"] = "modificado"

    assert repositorio.obtener(documento.id).documento.metadatos == {
        "dominio": "crediticio"
    }


def prueba_almacena_documento_cargado_desde_bytes(repositorio) -> None:
    documento = cargar_documento(
        "ers.txt",
        "El sistema deberá registrar cada decisión.".encode("utf-8"),
        {"dominio": "crediticio"},
    )
    repositorio.guardar(documento)

    assert repositorio.obtener(documento.id).documento == documento


def prueba_persiste_entre_instancias(tmp_path: Path) -> None:
    directorio = tmp_path / "almacenamiento"
    documento = _documento(metadatos={"dominio": "medico"})
    RepositorioEnArchivos(directorio).guardar(documento)

    repositorio = RepositorioEnArchivos(directorio)

    assert repositorio.obtener(documento.id).documento == documento
    assert [evento.accion for evento in repositorio.trazabilidad.eventos()] == [
        AccionTrazabilidad.CARGA
    ]


def prueba_estructura_de_archivos_es_inspeccionable(
    repositorio_en_archivos: RepositorioEnArchivos,
) -> None:
    documento = _documento(contenido="Requisito de transparencia")
    repositorio_en_archivos.guardar(documento)

    carpeta = repositorio_en_archivos.directorio_base / "documentos" / str(documento.id)
    datos = json.loads((carpeta / "documento.json").read_text(encoding="utf-8"))

    assert (carpeta / "contenido.txt").read_text(encoding="utf-8") == (
        "Requisito de transparencia"
    )
    assert datos["id"] == str(documento.id)
    assert datos["estado"] == "CARGADO"
    assert datos["version_formato"] == 1


def prueba_normalizacion_queda_en_archivos_aparte(
    repositorio_en_archivos: RepositorioEnArchivos,
) -> None:
    documento = _documento(contenido="Requisito  de   transparencia")
    repositorio_en_archivos.guardar(documento)
    texto_normalizado = _texto_normalizado(documento)
    repositorio_en_archivos.guardar_texto_normalizado(documento.id, texto_normalizado)

    carpeta = repositorio_en_archivos.directorio_base / "documentos" / str(documento.id)
    datos = json.loads((carpeta / "normalizacion.json").read_text(encoding="utf-8"))

    assert (carpeta / "contenido.txt").read_text(encoding="utf-8") == (
        documento.contenido_extraido
    )
    assert (carpeta / "texto_normalizado.txt").read_text(encoding="utf-8") == (
        texto_normalizado.normalizado
    )
    assert datos["pasos_aplicados"] == texto_normalizado.pasos_aplicados
    assert datos["version_formato"] == 1


def prueba_normalizacion_persiste_entre_instancias(tmp_path: Path) -> None:
    directorio = tmp_path / "almacenamiento"
    documento = _documento()
    texto_normalizado = _texto_normalizado(documento)
    primera = RepositorioEnArchivos(directorio)
    primera.guardar(documento)
    primera.guardar_texto_normalizado(documento.id, texto_normalizado)

    repositorio = RepositorioEnArchivos(directorio)

    assert repositorio.obtener_texto_normalizado(documento.id) == texto_normalizado
    assert repositorio.obtener(documento.id).estado is EstadoAnalisis.NORMALIZADO


def prueba_normalizacion_ilegible(
    repositorio_en_archivos: RepositorioEnArchivos,
) -> None:
    documento = _documento()
    repositorio_en_archivos.guardar(documento)
    repositorio_en_archivos.guardar_texto_normalizado(
        documento.id, _texto_normalizado(documento)
    )
    carpeta = repositorio_en_archivos.directorio_base / "documentos" / str(documento.id)
    (carpeta / "normalizacion.json").write_text("{ esto no es json", encoding="utf-8")

    with pytest.raises(AlmacenamientoCorruptoError):
        repositorio_en_archivos.obtener_texto_normalizado(documento.id)


def prueba_texto_normalizado_faltante(
    repositorio_en_archivos: RepositorioEnArchivos,
) -> None:
    documento = _documento()
    repositorio_en_archivos.guardar(documento)
    repositorio_en_archivos.guardar_texto_normalizado(
        documento.id, _texto_normalizado(documento)
    )
    carpeta = repositorio_en_archivos.directorio_base / "documentos" / str(documento.id)
    (carpeta / "texto_normalizado.txt").unlink()

    with pytest.raises(AlmacenamientoCorruptoError):
        repositorio_en_archivos.obtener_texto_normalizado(documento.id)


def prueba_bitacora_se_escribe_como_json_lines(
    repositorio_en_archivos: RepositorioEnArchivos,
) -> None:
    documento = _documento()
    repositorio_en_archivos.guardar(documento)
    repositorio_en_archivos.actualizar_estado(documento.id, EstadoAnalisis.EVALUADO)

    bitacora = repositorio_en_archivos.directorio_base / "trazabilidad.jsonl"
    lineas = bitacora.read_text(encoding="utf-8").splitlines()

    assert len(lineas) == 2
    assert [json.loads(linea)["accion"] for linea in lineas] == [
        "CARGA",
        "CAMBIO_ESTADO",
    ]
    assert UUID(json.loads(lineas[0])["id_documento"]) == documento.id


def prueba_conserva_el_texto_extraido_sin_alterarlo(
    repositorio_en_archivos: RepositorioEnArchivos,
) -> None:
    contenido = "Línea 1\r\nLínea 2\n\n  sangría\ttabulación\n"
    documento = _documento(contenido=contenido)
    repositorio_en_archivos.guardar(documento)

    assert repositorio_en_archivos.obtener(documento.id).documento.contenido_extraido == (
        contenido
    )


def prueba_rechaza_metadatos_no_serializables(
    repositorio_en_archivos: RepositorioEnArchivos,
) -> None:
    documento = _documento(metadatos={"revisor": object()})

    with pytest.raises(ErrorAlmacenamiento):
        repositorio_en_archivos.guardar(documento)

    carpeta = repositorio_en_archivos.directorio_base / "documentos" / str(documento.id)
    assert not carpeta.exists()


def prueba_registro_ilegible(repositorio_en_archivos: RepositorioEnArchivos) -> None:
    documento = _documento()
    repositorio_en_archivos.guardar(documento)
    carpeta = repositorio_en_archivos.directorio_base / "documentos" / str(documento.id)
    (carpeta / "documento.json").write_text("{ esto no es json", encoding="utf-8")

    with pytest.raises(AlmacenamientoCorruptoError):
        repositorio_en_archivos.obtener(documento.id)


def prueba_version_de_formato_desconocida(
    repositorio_en_archivos: RepositorioEnArchivos,
) -> None:
    documento = _documento()
    repositorio_en_archivos.guardar(documento)
    ruta = (
        repositorio_en_archivos.directorio_base
        / "documentos"
        / str(documento.id)
        / "documento.json"
    )
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    datos["version_formato"] = 99
    ruta.write_text(json.dumps(datos), encoding="utf-8")

    with pytest.raises(AlmacenamientoCorruptoError):
        repositorio_en_archivos.obtener(documento.id)


def prueba_contenido_extraido_faltante(
    repositorio_en_archivos: RepositorioEnArchivos,
) -> None:
    documento = _documento()
    repositorio_en_archivos.guardar(documento)
    carpeta = repositorio_en_archivos.directorio_base / "documentos" / str(documento.id)
    (carpeta / "contenido.txt").unlink()

    with pytest.raises(AlmacenamientoCorruptoError):
        repositorio_en_archivos.obtener(documento.id)


def prueba_bitacora_ilegible(repositorio_en_archivos: RepositorioEnArchivos) -> None:
    repositorio_en_archivos.guardar(_documento())
    bitacora = repositorio_en_archivos.directorio_base / "trazabilidad.jsonl"
    bitacora.write_text("evento sin formato\n", encoding="utf-8")

    with pytest.raises(AlmacenamientoCorruptoError):
        repositorio_en_archivos.trazabilidad.eventos()


def prueba_crea_el_directorio_de_almacenamiento(tmp_path: Path) -> None:
    directorio = tmp_path / "nuevo" / "almacenamiento"

    RepositorioEnArchivos(directorio)

    assert (directorio / "documentos").is_dir()
