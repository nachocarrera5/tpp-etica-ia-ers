const ERS_DEMO = `ERS - Asistente para priorización de turnos médicos

1. Propósito y alcance
El sistema asistirá al personal de admisión en la priorización de solicitudes de turnos. Su propósito es reducir demoras sin reemplazar el criterio clínico. No deberá utilizarse para emitir diagnósticos ni rechazar atención de urgencia.

2. Actores y personas afectadas
El personal de admisión cargará la solicitud. Los pacientes recibirán información sobre el uso del sistema. Un profesional de salud revisará las recomendaciones de prioridad antes de confirmarlas.

3. Datos
El sistema utilizará edad, especialidad solicitada, síntomas declarados y disponibilidad de turnos. Los datos se usarán sólo para priorizar la solicitud y se conservarán durante 12 meses. El acceso quedará restringido al personal autorizado.

4. Trato justo
El equipo evaluará diferencias de resultados por edad, género y zona geográfica. Cuando una diferencia supere el 5 %, se realizará una revisión y se ajustará el modelo.

5. Transparencia y explicación
La interfaz informará al paciente que una herramienta de IA intervino en la priorización. Para cada recomendación mostrará los factores principales y sus límites en lenguaje comprensible.

6. Supervisión humana
El profesional podrá modificar o rechazar la recomendación. Toda intervención quedará registrada con fecha, motivo y responsable. Ante síntomas de urgencia, el sistema derivará el caso para revisión inmediata.

7. Seguridad, auditoría e impacto
El servicio deberá alcanzar 99,5 % de disponibilidad mensual. Se monitorearán errores, latencia e incidentes; existirá un procedimiento de contingencia. El responsable funcional revisará trimestralmente los registros y atenderá reclamos. Antes del despliegue se evaluarán accesibilidad, autonomía de pacientes e impacto ambiental.`;

const estado = {
  archivo: null,
  documentos: [],
  documentoActivo: null,
  resultado: null,
  resultadosTemporales: new Map(),
  dimensionActiva: "D01",
  documentoAEliminar: null,
  panelVisible: localStorage.getItem("panel-documentos-visible") !== "false",
  filtroHallazgos: {
    texto: "",
    dimension: "TODAS",
    nivel: "TODOS",
  },
  configuracion: {
    modo_publico: false,
    persistencia_habilitada: true,
    tamano_maximo_mb: 10,
  },
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

const vistas = {
  carga: $("#vista-carga"),
  proceso: $("#vista-proceso"),
  resultados: $("#vista-resultados"),
  error: $("#vista-error"),
};

function icono(id, clase = "") {
  return `<svg class="${clase}" aria-hidden="true"><use href="#i-${id}"></use></svg>`;
}

function escapar(valor) {
  return String(valor ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function resaltarTexto(texto, fragmentos = []) {
  const rangos = fragmentos
    .map((fragmento) => {
      const inicio = texto.indexOf(fragmento);
      return inicio >= 0 ? [inicio, inicio + fragmento.length] : null;
    })
    .filter(Boolean)
    .sort((a, b) => a[0] - b[0]);

  const combinados = [];
  rangos.forEach(([inicio, fin]) => {
    const ultimo = combinados.at(-1);
    if (ultimo && inicio <= ultimo[1]) ultimo[1] = Math.max(ultimo[1], fin);
    else combinados.push([inicio, fin]);
  });

  if (!combinados.length) return escapar(texto);
  let posicion = 0;
  const partes = [];
  combinados.forEach(([inicio, fin]) => {
    partes.push(escapar(texto.slice(posicion, inicio)));
    partes.push(`<mark>${escapar(texto.slice(inicio, fin))}</mark>`);
    posicion = fin;
  });
  partes.push(escapar(texto.slice(posicion)));
  return partes.join("");
}

function mostrarVista(nombre) {
  Object.entries(vistas).forEach(([clave, elemento]) => {
    elemento.hidden = clave !== nombre;
  });
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function aplicarVisibilidadPanel() {
  const aplicacion = $(".aplicacion");
  const panel = $("#panel-documentos");
  const boton = $("#alternar-panel");
  aplicacion.classList.toggle("panel-oculto", !estado.panelVisible);
  panel.setAttribute("aria-hidden", String(!estado.panelVisible));
  boton.setAttribute("aria-expanded", String(estado.panelVisible));
  boton.setAttribute(
    "aria-label",
    estado.panelVisible ? "Ocultar espacio de trabajo" : "Mostrar espacio de trabajo",
  );
  boton.title = boton.getAttribute("aria-label");
}

function alternarPanel() {
  estado.panelVisible = !estado.panelVisible;
  localStorage.setItem("panel-documentos-visible", String(estado.panelVisible));
  aplicarVisibilidadPanel();
}

function fechaLegible(fecha) {
  return new Intl.DateTimeFormat("es-AR", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(fecha));
}

function detalleError(datos, fallback) {
  if (!datos) return fallback;
  if (typeof datos.detail === "string") return datos.detail;
  if (datos.detail?.mensaje) return datos.detail.mensaje;
  return fallback;
}

async function solicitar(ruta, opciones = {}) {
  const respuesta = await fetch(ruta, opciones);
  if (!respuesta.ok) {
    let datos = null;
    try { datos = await respuesta.json(); } catch (_) { /* respuesta sin JSON */ }
    throw new Error(detalleError(datos, `La operación falló (${respuesta.status}).`));
  }
  if (respuesta.status === 204) return null;
  return respuesta.json();
}

async function cargarHistorial() {
  if (estado.configuracion.modo_publico) return;
  try {
    estado.documentos = await solicitar("/documentos");
    renderizarHistorial();
  } catch (_) {
    $("#lista-documentos").innerHTML = '<p class="vacio-documentos">No se pudo cargar el historial.</p>';
  }
}

function renderizarHistorial() {
  const contenedor = $("#lista-documentos");
  if (!estado.documentos.length) {
    contenedor.innerHTML = '<p class="vacio-documentos">Todavía no hay documentos cargados.</p>';
    return;
  }
  contenedor.innerHTML = estado.documentos.map((documento) => `
    <div class="documento-item ${documento.documento_id === estado.documentoActivo ? "activo" : ""}">
      <button class="documento-abrir" type="button" data-documento="${documento.documento_id}">
        <strong title="${escapar(documento.nombre_original)}">${escapar(documento.nombre_original)}</strong>
        <small>${escapar(documento.formato_origen)} · ${fechaLegible(documento.fecha_carga)}</small>
      </button>
      <button class="eliminar-item" type="button" data-eliminar="${documento.documento_id}" title="Eliminar documento" aria-label="Eliminar ${escapar(documento.nombre_original)}">${icono("trash")}</button>
    </div>
  `).join("");
}

function registrarResultadoTemporal(archivo, resultado) {
  const documentoId = resultado.metadatos.documento_id;
  const extension = archivo.name.split(".").pop()?.toUpperCase() || "ERS";
  estado.documentos = estado.documentos.filter(
    (documento) => documento.documento_id !== documentoId,
  );
  estado.documentos.unshift({
    documento_id: documentoId,
    nombre_original: resultado.metadatos.nombre_documento || archivo.name,
    formato_origen: extension,
    fecha_carga: resultado.metadatos.fecha_inicio || new Date().toISOString(),
  });
  estado.resultadosTemporales.set(documentoId, resultado);
  renderizarHistorial();
}

function seleccionarArchivo(archivo) {
  estado.archivo = archivo;
  if (!archivo) {
    $("#nombre-archivo").textContent = "Arrastrá o seleccioná una ERS";
    const limite = estado.configuracion.modo_publico
      ? ` · máximo ${estado.configuracion.tamano_maximo_mb} MB`
      : "";
    $("#detalle-archivo").textContent = `TXT, PDF con texto o DOCX${limite}`;
    return;
  }
  const limite = estado.configuracion.tamano_maximo_mb * 1024 * 1024;
  if (archivo.size > limite) {
    estado.archivo = null;
    $("#archivo").value = "";
    notificar(`El archivo supera el máximo de ${estado.configuracion.tamano_maximo_mb} MB.`);
    return;
  }
  $("#nombre-archivo").textContent = archivo.name;
  $("#detalle-archivo").textContent = `${(archivo.size / 1024).toFixed(1)} KB · listo para analizar`;
}

function activarPaso(paso, titulo, detalle) {
  const pasos = ["carga", "nlp", "evaluacion", "salida"];
  const indice = pasos.indexOf(paso);
  $$(".pasos-proceso li").forEach((elemento, posicion) => {
    elemento.classList.toggle("activo", posicion === indice);
  });
  $$(".proceso-grafico span").forEach((elemento, posicion) => {
    elemento.classList.toggle("completo", posicion < indice);
    elemento.classList.toggle("activo", posicion === indice);
  });
  $("#titulo-proceso").textContent = titulo;
  $("#detalle-proceso").textContent = detalle;
}

async function analizarDocumento(evento) {
  evento.preventDefault();
  const archivo = estado.archivo || $("#archivo").files[0];
  if (!archivo) {
    notificar("Seleccioná un archivo TXT, PDF o DOCX.");
    return;
  }

  mostrarVista("proceso");
  activarPaso("carga", "Preparando la ERS", "Extrayendo y normalizando el contenido.");

  const metadatos = {};
  if ($("#dominio").value === "otro" && $("#dominio-otro").value.trim()) {
    metadatos.dominio = $("#dominio-otro").value.trim();
  } else if ($("#dominio").value) {
    metadatos.dominio = $("#dominio").value;
  }
  if ($("#identificador").value.trim()) metadatos.identificador = $("#identificador").value.trim();
  const formulario = new FormData();
  formulario.append("archivo", archivo);
  formulario.append("metadatos", JSON.stringify(metadatos));

  try {
    if (estado.configuracion.modo_publico) {
      activarPaso("evaluacion", "Analizando la ERS", "Procesando el texto y aplicando 72 guardrails D01-D10 sin almacenar el documento.");
      estado.resultado = await solicitar("/analisis", { method: "POST", body: formulario });
      estado.documentoActivo = estado.resultado.metadatos.documento_id;
      registrarResultadoTemporal(archivo, estado.resultado);
    } else {
      const carga = await solicitar("/documentos", { method: "POST", body: formulario });
      estado.documentoActivo = carga.documento_id;
      activarPaso("nlp", "Leyendo requisitos", "Segmentando el texto e identificando actores, acciones y condiciones.");
      await pausaVisual();
      activarPaso("evaluacion", "Aplicando el catálogo ético", "Contrastando evidencia documental con 72 guardrails D01-D10.");
      estado.resultado = await solicitar(`/documentos/${carga.documento_id}/resultados`);
    }
    activarPaso("salida", "Organizando resultados", "Preparando alertas, evidencias y recomendaciones trazables.");
    await pausaVisual(220);
    renderizarResultado();
    if (!estado.configuracion.modo_publico) await cargarHistorial();
    mostrarVista("resultados");
  } catch (error) {
    mostrarError(error.message);
  }
}

function pausaVisual(duracion = 120) {
  return new Promise((resolver) => window.setTimeout(resolver, duracion));
}

async function abrirDocumento(documentoId) {
  estado.documentoActivo = documentoId;
  renderizarHistorial();
  if (estado.configuracion.modo_publico) {
    const resultado = estado.resultadosTemporales.get(documentoId);
    if (!resultado) {
      notificar("El análisis ya no está disponible en esta sesión.");
      return;
    }
    estado.resultado = resultado;
    renderizarResultado();
    mostrarVista("resultados");
    return;
  }
  mostrarVista("proceso");
  activarPaso("evaluacion", "Reevaluando el documento", "Aplicando la versión activa del catálogo de guardrails.");
  try {
    estado.resultado = await solicitar(`/documentos/${documentoId}/resultados`);
    renderizarResultado();
    await cargarHistorial();
    mostrarVista("resultados");
  } catch (error) {
    mostrarError(error.message);
  }
}

function renderizarResultado() {
  const resultado = estado.resultado;
  const { indicadores, metadatos } = resultado;
  const parciales = resultado.hallazgos.filter((item) => item.nivel_preliminar === "PARCIAL").length;
  const explicitos = resultado.hallazgos.filter((item) => item.nivel_preliminar === "EXPLICITO").length;
  $("#titulo-documento").textContent = metadatos.nombre_documento;
  $("#resumen-ejecutivo").textContent = resultado.resumen_ejecutivo;
  $("#lectura-global").textContent = resultado.lectura_global;
  $("#fecha-analisis").textContent = `Evaluado ${fechaLegible(metadatos.fecha_fin)}`;
  $("#indicadores").innerHTML = `
    <div class="indicador"><span>Cobertura no ausente</span><strong>${indicadores.porcentaje_cobertura_no_ausente.toFixed(2)}%</strong><div class="barra-indicador"><span style="width:${indicadores.porcentaje_cobertura_no_ausente}%"></span></div><small>Sobre dimensiones evaluadas</small></div>
    <div class="indicador"><span>Guardrails con evidencia</span><strong>${parciales + explicitos}</strong><small>${explicitos} explícitos · ${parciales} parciales</small></div>
    <div class="indicador"><span>Alertas</span><strong>${indicadores.total_alertas}</strong><small>${indicadores.recomendaciones_alta_prioridad} de prioridad alta</small></div>
    <div class="indicador"><span>Guardrails</span><strong>${indicadores.guardrails_aplicados}</strong><small>${indicadores.guardrails_no_aplicables} no aplicables · ${indicadores.guardrails_con_error} errores</small></div>
  `;

  $("#mapa-dimensiones").innerHTML = resultado.resultados_dimension.map((dimension) => celdaDimension(dimension)).join("");
  renderizarMatrizGuardrails();
  $("#resumen-alertas").innerHTML = resultado.alertas.length
    ? resultado.alertas.map((alerta) => filaAlerta(alerta)).join("")
    : '<p class="sin-resultados">No se generaron alertas para las dimensiones evaluadas.</p>';
  $("#navegacion-dimensiones").innerHTML = resultado.resultados_dimension.map((dimension) => navDimension(dimension)).join("");
  estado.filtroHallazgos = { texto: "", dimension: "TODAS", nivel: "TODOS" };
  $("#buscar-hallazgos").value = "";
  $("#filtrar-dimension").value = "TODAS";
  $$('[data-filtro-nivel]').forEach((boton) => {
    boton.classList.toggle("activo", boton.dataset.filtroNivel === "TODOS");
  });
  renderizarHallazgos();
  estado.dimensionActiva = resultado.resultados_dimension[0]?.dimension_codigo || "D01";
  renderizarDetalleDimension(estado.dimensionActiva);

  const advertencias = $("#advertencias");
  advertencias.hidden = !resultado.advertencias.length;
  advertencias.innerHTML = resultado.advertencias.map((texto) => `<p>${escapar(texto)}</p>`).join("");
  cambiarPestana("resumen");
}

function nivelDe(dimension) {
  return dimension.nivel_consolidado || "NO_EVALUADA";
}

function etiquetaNivel(nivel) {
  return nivel === "NO_EVALUADA" ? "No evaluada" : nivel.toLowerCase();
}

function celdaDimension(dimension) {
  const nivel = nivelDe(dimension);
  const resumen = resumenHallazgos(dimension);
  return `<button class="dimension-celda ${nivel}" data-dimension="${dimension.dimension_codigo}" type="button">
    <span class="codigo">${dimension.dimension_codigo}</span>
    <span class="nombre">${escapar(dimension.dimension_nombre)}</span>
    <span class="composicion">${resumen.explicitos} explícitos · ${resumen.parciales} parciales</span>
    <span class="nivel">${etiquetaNivel(nivel)}</span>
  </button>`;
}

function resumenHallazgos(dimension) {
  const relacionados = estado.resultado.hallazgos.filter((item) => dimension.hallazgos_relacionados.includes(item.hallazgo_id));
  return {
    explicitos: relacionados.filter((item) => item.nivel_preliminar === "EXPLICITO").length,
    parciales: relacionados.filter((item) => item.nivel_preliminar === "PARCIAL").length,
  };
}

function filaAlerta(alerta) {
  return `<button class="alerta-fila" data-dimension="${alerta.dimension_codigo}" type="button">
    <span class="alerta-codigo">${alerta.dimension_codigo}</span>
    <div><strong>${escapar(alerta.titulo)}</strong><p>${escapar(alerta.descripcion)}</p></div>
    <span class="prioridad ${alerta.prioridad_documental}">${escapar(alerta.prioridad_documental)}</span>
    ${icono("arrow")}
  </button>`;
}

function navDimension(dimension) {
  const nivel = nivelDe(dimension);
  return `<button class="nav-dimension ${dimension.dimension_codigo === estado.dimensionActiva ? "activa" : ""}" data-dimension="${dimension.dimension_codigo}" type="button">
    <strong>${dimension.dimension_codigo}</strong><span>${escapar(dimension.dimension_nombre)}</span><i class="punto-nivel ${nivel}"></i>
  </button>`;
}

function renderizarDetalleDimension(codigo) {
  estado.dimensionActiva = codigo;
  const dimension = estado.resultado.resultados_dimension.find((item) => item.dimension_codigo === codigo);
  const nivel = nivelDe(dimension);
  const recomendacion = estado.resultado.recomendaciones.find((item) => item.dimension_codigo === codigo);
  const hallazgos = estado.resultado.hallazgos.filter((item) => dimension.hallazgos_relacionados.includes(item.hallazgo_id));
  $$(".nav-dimension").forEach((item) => item.classList.toggle("activa", item.dataset.dimension === codigo));

  $("#detalle-dimension").innerHTML = `
    <div class="detalle-encabezado">
      <div><span class="sobrelinea">${escapar(dimension.grupo_tematico)}</span><h2>${dimension.dimension_codigo} · ${escapar(dimension.dimension_nombre)}</h2><p>${escapar(dimension.justificacion)}</p></div>
      <span class="etiqueta-nivel ${nivel}">${etiquetaNivel(nivel)}</span>
    </div>
    <div class="bloque-detalle">
      <h3>Brechas principales</h3>
      ${dimension.brechas_principales.length ? `<ul class="brechas">${dimension.brechas_principales.map((brecha) => `<li>${escapar(brecha)}</li>`).join("")}</ul>` : '<p class="sin-resultados">No se registraron brechas para esta dimensión.</p>'}
    </div>
    ${recomendacion ? `<div class="bloque-detalle"><h3>Recomendación documental</h3><div class="recomendacion"><strong>${escapar(recomendacion.tipo_mejora.replaceAll("_", " "))}</strong><p>${escapar(recomendacion.accion_sugerida)}</p></div></div>` : ""}
    <div class="bloque-detalle">
      <h3>Guardrails evaluados</h3>
      <p class="ayuda-bloque">Cada guardrail representa una comprobación documental concreta dentro de esta dimensión.</p>
      <div class="guardrails-dimension">${guardrailsDe(hallazgos)}</div>
    </div>
    <div class="bloque-detalle">
      <h3>Evidencia vinculada</h3>
      ${evidenciasDe(hallazgos)}
    </div>
  `;
}

function guardrailsDe(hallazgos) {
  return hallazgos.map((hallazgo) => `
    <details class="guardrail-dimension ${hallazgo.nivel_preliminar}">
      <summary>
        <span class="estado-guardrail"></span>
        <span><strong>${escapar(hallazgo.guardrail_nombre || hallazgo.guardrail_codigo)}</strong><small>${escapar(hallazgo.guardrail_codigo)} · ${hallazgo.evidencias.length} evidencia${hallazgo.evidencias.length === 1 ? "" : "s"}</small></span>
        <span class="etiqueta-nivel ${hallazgo.nivel_preliminar}">${etiquetaNivel(hallazgo.nivel_preliminar)}</span>
        ${icono("chevron")}
      </summary>
      <div class="guardrail-contenido">
        <p><strong>Qué busca</strong>${escapar(hallazgo.guardrail_descripcion || "Comprobar evidencia documental asociada a este criterio.")}</p>
        <p><strong>Resultado</strong>${escapar(hallazgo.justificacion)}</p>
        <small>Criterios: ${hallazgo.criterios_asociados.map(escapar).join(", ")}</small>
      </div>
    </details>
  `).join("");
}

function evidenciasDe(hallazgos) {
  const evidencias = hallazgos.flatMap((hallazgo) => hallazgo.evidencias.map((evidencia) => ({
    ...evidencia,
    guardrail: hallazgo.guardrail_codigo,
    guardrailNombre: hallazgo.guardrail_nombre || hallazgo.guardrail_codigo,
  })));
  if (!evidencias.length) return '<p class="sin-resultados">No se encontró evidencia positiva vinculada.</p>';
  return evidencias.map((evidencia) => `<div class="evidencia"><blockquote>“${resaltarTexto(evidencia.texto, evidencia.fragmentos_clave)}”</blockquote><small><strong>${escapar(evidencia.guardrailNombre)}</strong><span>${escapar(evidencia.guardrail)}${evidencia.seccion_origen ? ` · ${escapar(evidencia.seccion_origen)}` : ""}</span></small></div>`).join("");
}

function tarjetaHallazgo(hallazgo) {
  return `<details class="hallazgo ${hallazgo.nivel_preliminar}">
    <summary>
      <span class="estado-guardrail"></span>
      <span class="hallazgo-identidad"><strong>${escapar(hallazgo.guardrail_nombre || hallazgo.guardrail_codigo)}</strong><small>${escapar(hallazgo.guardrail_codigo)} · versión ${hallazgo.guardrail_version}</small></span>
      <span class="hallazgo-resumen">${hallazgo.evidencias.length} evidencia${hallazgo.evidencias.length === 1 ? "" : "s"} · ${hallazgo.dimensiones_asociadas.join(", ")}</span>
      <span class="etiqueta-nivel ${hallazgo.nivel_preliminar}">${etiquetaNivel(hallazgo.nivel_preliminar)}</span>
      ${icono("chevron")}
    </summary>
    <div class="hallazgo-contenido">
      <div class="hallazgo-explicacion"><p><strong>Qué busca este guardrail</strong>${escapar(hallazgo.guardrail_descripcion || "Comprobar evidencia documental asociada a este criterio.")}</p><p><strong>Qué se detectó</strong>${escapar(hallazgo.justificacion)}</p></div>
      <div class="hallazgo-meta"><span>Familia ${escapar(hallazgo.familia_guardrail)}</span><span>Prioridad ${escapar(hallazgo.prioridad_documental)}</span><span>Criterios ${hallazgo.criterios_asociados.map(escapar).join(", ")}</span></div>
      ${hallazgo.evidencias.length ? `<div class="hallazgo-evidencias-detalle"><h4>Evidencia vinculada</h4>${evidenciasDe([hallazgo])}</div>` : ""}
    </div>
  </details>`;
}

function renderizarHallazgos() {
  const filtro = estado.filtroHallazgos;
  const texto = filtro.texto.trim().toLocaleLowerCase("es");
  const hallazgos = estado.resultado.hallazgos.filter((hallazgo) => {
    const coincideDimension = filtro.dimension === "TODAS"
      || hallazgo.dimensiones_asociadas.includes(filtro.dimension);
    const coincideNivel = filtro.nivel === "TODOS"
      || (filtro.nivel === "EVIDENCIA" && hallazgo.evidencias.length > 0)
      || (filtro.nivel === "BRECHAS" && hallazgo.nivel_preliminar !== "EXPLICITO");
    const contenido = [
      hallazgo.guardrail_codigo,
      hallazgo.guardrail_nombre,
      hallazgo.guardrail_descripcion,
      hallazgo.justificacion,
      ...hallazgo.criterios_asociados,
    ].join(" ").toLocaleLowerCase("es");
    return coincideDimension && coincideNivel && (!texto || contenido.includes(texto));
  });

  $("#cantidad-hallazgos").textContent = `${hallazgos.length} de ${estado.resultado.hallazgos.length}`;
  $("#lista-hallazgos").innerHTML = hallazgos.length
    ? hallazgos.map(tarjetaHallazgo).join("")
    : '<p class="sin-resultados">No hay hallazgos que coincidan con estos filtros.</p>';
}

function cambiarPestana(nombre) {
  $$(".pestana").forEach((boton) => boton.classList.toggle("activa", boton.dataset.vista === nombre));
  ["resumen", "matriz", "dimensiones", "hallazgos"].forEach((panel) => {
    $(`#panel-${panel}`).hidden = panel !== nombre;
  });
}

function letraNivel(nivel) {
  return { AUSENTE: "A", PARCIAL: "P", EXPLICITO: "E" }[nivel] || "·";
}

function renderizarMatrizGuardrails() {
  const resultado = estado.resultado;
  const dimensiones = resultado.resultados_dimension;

  const codigosGuardrail = [];
  const vistos = new Set();
  dimensiones.forEach((dimension) => {
    resultado.hallazgos
      .filter((hallazgo) => hallazgo.dimensiones_asociadas.includes(dimension.dimension_codigo))
      .sort((a, b) => a.guardrail_codigo.localeCompare(b.guardrail_codigo))
      .forEach((hallazgo) => {
        if (!vistos.has(hallazgo.guardrail_codigo)) {
          vistos.add(hallazgo.guardrail_codigo);
          codigosGuardrail.push(hallazgo.guardrail_codigo);
        }
      });
  });

  const maximoColumnas = Math.max(...dimensiones.map((dimension) =>
    resultado.hallazgos.filter((hallazgo) => hallazgo.dimensiones_asociadas.includes(dimension.dimension_codigo)).length,
  ), 1);

  const encabezados = Array.from({ length: maximoColumnas }, (_, indice) => `<th scope="col">G${indice + 1}</th>`).join("");

  const filas = dimensiones.map((dimension) => {
    const hallazgosDimension = resultado.hallazgos
      .filter((hallazgo) => hallazgo.dimensiones_asociadas.includes(dimension.dimension_codigo))
      .sort((a, b) => a.guardrail_codigo.localeCompare(b.guardrail_codigo));
    const celdas = Array.from({ length: maximoColumnas }, (_, indice) => {
      const hallazgo = hallazgosDimension[indice];
      if (!hallazgo) return '<td class="celda-matriz vacia" aria-hidden="true"></td>';
      const nivel = hallazgo.nivel_preliminar;
      return `<td class="celda-matriz">
        <button type="button" class="celda-matriz-boton ${nivel}" data-hallazgo="${hallazgo.hallazgo_id}"
          title="${escapar(hallazgo.guardrail_codigo)} · ${escapar(etiquetaNivel(nivel))}"
          aria-label="${escapar(dimension.dimension_codigo)}, ${escapar(hallazgo.guardrail_codigo)}, ${escapar(etiquetaNivel(nivel))}">
          ${letraNivel(nivel)}
        </button>
      </td>`;
    }).join("");
    return `<tr>
      <th scope="row" class="fila-dimension" title="${escapar(dimension.dimension_nombre)}">
        <strong>${dimension.dimension_codigo}</strong><span>${escapar(dimension.dimension_nombre)}</span>
      </th>
      ${celdas}
    </tr>`;
  }).join("");

  $("#matriz-guardrails").innerHTML = `
    <table class="matriz-tabla">
      <thead><tr><th scope="col" class="esquina-matriz">Dimensión</th>${encabezados}</tr></thead>
      <tbody>${filas}</tbody>
    </table>
  `;
}

function abrirCeldaMatriz(hallazgoId) {
  const hallazgo = estado.resultado.hallazgos.find((item) => item.hallazgo_id === hallazgoId);
  if (!hallazgo) return;
  const dimensionCodigo = hallazgo.dimensiones_asociadas[0];
  const dimension = estado.resultado.resultados_dimension.find((item) => item.dimension_codigo === dimensionCodigo);

  $("#celda-dimension-codigo").textContent = dimension
    ? `${dimension.dimension_codigo} · ${dimension.dimension_nombre}`
    : dimensionCodigo;
  $("#celda-guardrail-nombre").textContent = hallazgo.guardrail_nombre || hallazgo.guardrail_codigo;
  const etiqueta = $("#celda-etiqueta-nivel");
  etiqueta.textContent = etiquetaNivel(hallazgo.nivel_preliminar);
  etiqueta.className = `etiqueta-nivel ${hallazgo.nivel_preliminar}`;

  $("#celda-contenido").innerHTML = `
    <p><strong>Qué busca</strong>${escapar(hallazgo.guardrail_descripcion || "Comprobar evidencia documental asociada a este criterio.")}</p>
    <p><strong>Resultado</strong>${escapar(hallazgo.justificacion)}</p>
    <div class="hallazgo-evidencias-detalle">
      <h4>Evidencia vinculada</h4>
      ${evidenciasDe([hallazgo])}
    </div>
  `;

  $("#celda-ver-dimension").onclick = () => {
    $("#dialogo-celda").close();
    irADimension(dimensionCodigo);
  };
  $("#dialogo-celda").showModal();
}

function irADimension(codigo) {
  cambiarPestana("dimensiones");
  renderizarDetalleDimension(codigo);
  $("#panel-dimensiones").scrollIntoView({ behavior: "smooth", block: "start" });
}

function nuevaCarga() {
  estado.archivo = null;
  estado.documentoActivo = null;
  estado.resultado = null;
  $("#formulario-carga").reset();
  seleccionarArchivo(null);
  actualizarCampoDominioOtro();
  renderizarHistorial();
  mostrarVista("carga");
}

function mostrarError(mensaje) {
  $("#mensaje-error").textContent = mensaje;
  mostrarVista("error");
}

function notificar(mensaje) {
  const elemento = $("#notificacion");
  elemento.textContent = mensaje;
  elemento.hidden = false;
  window.clearTimeout(notificar.temporizador);
  notificar.temporizador = window.setTimeout(() => { elemento.hidden = true; }, 3200);
}

async function descargarReporte() {
  if (!estado.resultado) return;
  const boton = $("#descargar-reporte");
  const formato = $("#formato-exportacion").value;
  boton.disabled = true;
  try {
    const respuesta = await fetch(`/reporte?formato=${encodeURIComponent(formato)}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(estado.resultado),
    });
    if (!respuesta.ok) {
      let datos = null;
      try { datos = await respuesta.json(); } catch (_) { /* respuesta sin JSON */ }
      throw new Error(detalleError(datos, `No se pudo exportar el reporte (${respuesta.status}).`));
    }

    const disposicion = respuesta.headers.get("Content-Disposition") || "";
    const nombre = disposicion.match(/filename="([^"]+)"/)?.[1] || `reporte-etico.${formato}`;
    const url = URL.createObjectURL(await respuesta.blob());
    const enlace = document.createElement("a");
    enlace.href = url;
    enlace.download = nombre;
    document.body.appendChild(enlace);
    enlace.click();
    enlace.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 0);
    notificar(`Reporte ${formato.toUpperCase()} descargado.`);
  } catch (error) {
    notificar(error.message);
  } finally {
    boton.disabled = false;
  }
}

async function configurarAplicacion() {
  try {
    estado.configuracion = await solicitar("/configuracion-publica");
  } catch (_) {
    notificar("No se pudo consultar la configuración del servicio.");
  }

  if (estado.configuracion.modo_publico) {
    $("#aviso-privacidad").hidden = false;
    $("#detalle-archivo").textContent = `TXT, PDF con texto o DOCX · máximo ${estado.configuracion.tamano_maximo_mb} MB`;
    renderizarHistorial();
  } else {
    await cargarHistorial();
  }
}

function prepararEliminacion(documentoId) {
  const documento = estado.documentos.find((item) => item.documento_id === documentoId);
  estado.documentoAEliminar = documentoId;
  $("#texto-eliminar").textContent = estado.configuracion.modo_publico
    ? `Se quitará ${documento?.nombre_original || "el documento"} de esta sesión.`
    : `Se eliminará ${documento?.nombre_original || "el documento"} y su registro local.`;
  $("#dialogo-eliminar").showModal();
}

async function confirmarEliminacion() {
  if (!estado.documentoAEliminar) return;
  const documentoId = estado.documentoAEliminar;
  estado.documentoAEliminar = null;
  try {
    if (estado.configuracion.modo_publico) {
      estado.documentos = estado.documentos.filter(
        (documento) => documento.documento_id !== documentoId,
      );
      estado.resultadosTemporales.delete(documentoId);
      if (estado.documentoActivo === documentoId) nuevaCarga();
      else renderizarHistorial();
      notificar("Análisis quitado de la sesión.");
      return;
    }
    await solicitar(`/documentos/${documentoId}`, { method: "DELETE" });
    if (estado.documentoActivo === documentoId) nuevaCarga();
    await cargarHistorial();
    notificar("Documento eliminado.");
  } catch (error) {
    notificar(error.message);
  }
}

$("#archivo").addEventListener("change", (evento) => seleccionarArchivo(evento.target.files[0]));
$("#alternar-panel").addEventListener("click", alternarPanel);
$("#formulario-carga").addEventListener("submit", analizarDocumento);
$("#nuevo-documento").addEventListener("click", nuevaCarga);
$("#volver-carga").addEventListener("click", nuevaCarga);
$("#reintentar").addEventListener("click", nuevaCarga);
$("#usar-ejemplo").addEventListener("click", () => {
  const archivo = new File([ERS_DEMO], "ers-demo-turnos-medicos.txt", { type: "text/plain" });
  seleccionarArchivo(archivo);
  $("#dominio").value = "salud";
  actualizarCampoDominioOtro();
  $("#identificador").value = "DEMO-ERS-01";
  notificar("ERS de demostración preparada.");
});

function actualizarCampoDominioOtro() {
  const esOtro = $("#dominio").value === "otro";
  $("#campo-dominio-otro").hidden = !esOtro;
  if (!esOtro) $("#dominio-otro").value = "";
}

$("#dominio").addEventListener("change", actualizarCampoDominioOtro);

const zona = $("#zona-archivo");
["dragenter", "dragover"].forEach((evento) => zona.addEventListener(evento, (e) => { e.preventDefault(); zona.classList.add("arrastrando"); }));
["dragleave", "drop"].forEach((evento) => zona.addEventListener(evento, (e) => { e.preventDefault(); zona.classList.remove("arrastrando"); }));
zona.addEventListener("drop", (evento) => seleccionarArchivo(evento.dataTransfer.files[0]));

$("#lista-documentos").addEventListener("click", (evento) => {
  const eliminar = evento.target.closest("[data-eliminar]");
  if (eliminar) { evento.stopPropagation(); prepararEliminacion(eliminar.dataset.eliminar); return; }
  const documento = evento.target.closest("[data-documento]");
  if (documento) abrirDocumento(documento.dataset.documento);
});
$("#vista-resultados").addEventListener("click", (evento) => {
  const pestana = evento.target.closest("[data-vista]");
  if (pestana) cambiarPestana(pestana.dataset.vista);
  const dimension = evento.target.closest("[data-dimension]");
  if (dimension) irADimension(dimension.dataset.dimension);
  const celda = evento.target.closest("[data-hallazgo]");
  if (celda) abrirCeldaMatriz(celda.dataset.hallazgo);
});
$("#confirmar-eliminar").addEventListener("click", confirmarEliminacion);
$("#descargar-reporte").addEventListener("click", descargarReporte);
$("#buscar-hallazgos").addEventListener("input", (evento) => {
  estado.filtroHallazgos.texto = evento.target.value;
  renderizarHallazgos();
});
$("#filtrar-dimension").addEventListener("change", (evento) => {
  estado.filtroHallazgos.dimension = evento.target.value;
  renderizarHallazgos();
});
$(".filtros-nivel").addEventListener("click", (evento) => {
  const boton = evento.target.closest("[data-filtro-nivel]");
  if (!boton) return;
  estado.filtroHallazgos.nivel = boton.dataset.filtroNivel;
  $$('[data-filtro-nivel]').forEach((item) => item.classList.toggle("activo", item === boton));
  renderizarHallazgos();
});

aplicarVisibilidadPanel();
configurarAplicacion();
