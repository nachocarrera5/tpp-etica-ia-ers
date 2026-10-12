# Validacion del Sprint 11

Este directorio contiene la validacion funcional preliminar del catalogo de
guardrails sobre el corpus de siete ERS utilizado por el equipo. La version
evaluada queda identificada en cada corrida mediante el commit Git.

## Alcance

- `SCRUM-120`: dimensiones D01-D02.
- `SCRUM-121`: dimensiones D03-D04.
- `SCRUM-122`: dimensiones D05-D07.
- `SCRUM-123`: dimensiones D08-D10.

La validacion mide dos aspectos diferentes:

1. **Nivel de dimension**: compara `AUSENTE`, `PARCIAL` o `EXPLICITO` contra
   una referencia preparada mediante lectura documental.
2. **Deteccion de cobertura**: compara si existe o no evidencia, agrupando
   `PARCIAL` y `EXPLICITO` como evidencia presente. Esto permite distinguir
   una omision completa de una diferencia de graduacion.

Los resultados no prueban cumplimiento etico ni calidad del sistema real.
Evalúan si el prototipo encuentra evidencia documental compatible con su
rubrica. La referencia incluida es una primera anotacion asistida y debe ser
revisada por, al menos, una segunda persona antes de utilizar las metricas como
resultado definitivo de la tesis.

## Corpus

`corpus.csv` identifica los siete documentos, su origen y su naturaleza. Los
PDF no se versionan en este repositorio de desarrollo: el ejecutor los busca en
un directorio indicado por linea de comandos.

## Ejecucion

Desde la raiz del proyecto, con las dependencias instaladas:

```bash
python validacion/ejecutar_validacion.py \
  --corpus "/ruta/a/ERS de prueba" \
  --referencia validacion/referencia_dimensiones.csv \
  --salida /tmp/validacion-sprint-11
```

La corrida genera:

- `resultados_guardrails.csv`: salida de los 72 guardrails por documento;
- `resultados_dimensiones.csv`: consolidacion D01-D10;
- `comparacion_referencia.csv`: comparacion con la referencia esperada;
- `resumen_metricas.csv`: acuerdo y metricas por tarea;
- `evidencias.json`: evidencias vinculadas para auditoria;
- `informe.md`: resumen legible de la corrida.

## Criterio de referencia

La referencia se registra en `referencia_dimensiones.csv`. Cada fila incluye
una justificacion breve y un estado de revision. Las decisiones se toman sobre
el contenido completo del documento, no sobre las palabras detectadas por el
motor. Para cerrar formalmente las cuatro tareas, una segunda persona debe
confirmar o corregir las filas con estado `PENDIENTE_SEGUNDA_REVISION`.

Los defectos encontrados durante esta medicion se registran en el informe, sin
modificar reglas ni umbrales. Esos cambios corresponden a la tarea posterior
de ajuste del modelo, para evitar medir una version que cambia durante la
validacion.

## Registro de discrepancias

`registro_discrepancias.csv` contiene los falsos positivos, falsos negativos y
problemas de calibracion confirmados en SCRUM-124. El informe detallado se
encuentra en `informes/SCRUM-124.md`. Los errores de deteccion se mantienen
separados de los desacuerdos `PARCIAL/EXPLICITO` para no inflar artificialmente
las metricas de precision y exhaustividad.

## Calidad documental

SCRUM-152 evalua cobertura etica, ambiguedad, verificabilidad y evidencia con
`evaluar_calidad_documental.py`. Los resultados reproducibles se versionan en
`resultados_calidad/` y su interpretacion se documenta en
`informes/SCRUM-152.md`.

```bash
python validacion/evaluar_calidad_documental.py \
  --corpus "/ruta/a/ERS de prueba" \
  --salida validacion/resultados_calidad
```

## Ponderacion de guardrails

SCRUM-155 reconsolida la linea base de `resultados/` con la rubrica ponderada
y compara varios umbrales contra la referencia. No necesita los PDF del
corpus. La interpretacion se documenta en `informes/SCRUM-155.md`.

```bash
python validacion/evaluar_ponderacion.py
```
