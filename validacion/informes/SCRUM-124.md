# SCRUM-124: Registrar falsos positivos y falsos negativos

## Objetivo

Registrar de forma trazable las discrepancias encontradas en la validacion de
D01-D10, separar errores de deteccion de diferencias de graduacion y dejar
criterios concretos para los ajustes posteriores.

La linea base corresponde al commit `20b3e5a1be313afb00e40ae1bdbcc36867fc41c0`,
con 7 documentos, 72 guardrails, 504 aplicaciones y 70 resultados de
dimension. La referencia y los resultados comparados se encuentran en
`validacion/referencia_dimensiones.csv` y
`validacion/resultados/comparacion_referencia.csv`.

## Definiciones

- **Falso positivo (FP):** la referencia indica `AUSENTE`, pero el motor
  informa `PARCIAL` o `EXPLICITO`.
- **Falso negativo (FN):** la referencia indica evidencia `PARCIAL` o
  `EXPLICITO`, pero el motor informa `AUSENTE`.
- **Diferencia de nivel:** ambos reconocen que existe evidencia, pero no
  coinciden entre `PARCIAL` y `EXPLICITO`. No se contabiliza como FP ni FN.

## Resumen

| Tipo | Casos | Documentos afectados |
|---|---:|---|
| Falso positivo | 1 | SMS-MURCIA-REAL |
| Falso negativo | 2 | RECOMENDADOR-SINTETICO, CLM-REAL |
| Subestimacion de nivel | 29 | Tres ERS sinteticas |

La deteccion global conserva 62 verdaderos positivos, 5 verdaderos negativos,
1 falso positivo y 2 falsos negativos. Esto equivale a precision de 98,41%,
exhaustividad de 96,88% y F1 de 97,64%. El acuerdo exacto de nivel es 54,29%.

## VAL-001: falso positivo D04

**Documento:** pliego del Servicio Murciano de Salud.

**Esperado:** `AUSENTE`. **Obtenido:** `PARCIAL`.

El motor vinculo "por grupos de pacientes" con
`GR-D04-DELIM-GRUPOS` y "acciones correctivas" con
`GR-D04-CTRL-MITIGACION`. El primer texto describe escalado de alertas y el
segundo soporte ante incidencias. Ninguno trata sesgos, equidad, trato desigual
o comparacion de desempeno entre subpoblaciones.

La causa es una coincidencia lexica sin contexto tematico. El ajuste debe
exigir una señal cercana de D04 antes de considerar grupos o acciones
correctivas como evidencia etica.

## VAL-002: falso negativo D07

**Documento:** ERS sintetica del sistema recomendador.

**Esperado:** `PARCIAL`. **Obtenido:** `AUSENTE`.

La ERS permite desactivar la personalizacion, asigna al adulto responsable la
revision del perfil infantil y establece revision periodica por un comite. No
constituye una supervision completa de decisiones, pero si evidencia parcial
de control humano. Los ocho guardrails D07 quedaron ausentes.

El vocabulario actual esta orientado a figuras como analista o supervisor. El
ajuste debe reconocer controles ejercidos por usuarios, tutores y comites como
evidencia parcial, sin elevarlos por si solos a `EXPLICITO`.

## VAL-003: falso negativo D06

**Documento:** marco de IA generativa de Castilla-La Mancha.

**Esperado:** `PARCIAL`. **Obtenido:** `AUSENTE`.

El pliego exige "definir guias de transparencia e interpretabilidad". Es una
exigencia generica e incompleta, pero relevante para D06. El motor no la
reconocio porque no aparece formulada como explicacion de una salida, factores
o razones.

El ajuste debe aceptar interpretabilidad como señal parcial y mantener una
exigencia mayor para `EXPLICITO`: salida identificada, destinatario, formato,
factores y utilidad verificable.

## Diferencia de calibracion

Los 29 desacuerdos restantes no son FP/FN: la referencia y el motor coinciden
en que existe evidencia, pero el motor devuelve `PARCIAL` donde la referencia
espera `EXPLICITO`. Todos corresponden a dimensiones de las ERS sinteticas
completas.

Este patron apunta a dos causas combinadas:

1. Variantes de redaccion validas no activan todas las señales explicitas.
2. La consolidacion sólo produce `EXPLICITO` cuando todos los guardrails de la
   dimension son explicitos.

La correccion debe coordinarse con SCRUM-125 y la ponderacion de SCRUM-155. No
conviene resolverla agregando sinonimos indiscriminadamente, porque aumentaria
los falsos positivos como VAL-001.

## Criterios de regresion

La siguiente corrida posterior a los ajustes debe cumplir, como minimo:

1. `SMS-MURCIA-REAL / D04` pasa de `PARCIAL` a `AUSENTE`.
2. `RECOMENDADOR-SINTETICO / D07` pasa de `AUSENTE` a `PARCIAL`.
3. `CLM-REAL / D06` pasa de `AUSENTE` a `PARCIAL`.
4. Los 67 casos cuya deteccion coincide con la referencia no regresan.
5. Las mejoras de nivel se contrastan contra los 29 casos registrados, sin
   reducir precision ni ocultar brechas reales.

## Estado

Los tres errores de deteccion y el problema de calibracion quedan registrados
en `validacion/registro_discrepancias.csv` con causa, impacto, correccion
propuesta y tarea de destino. La referencia continua pendiente de una segunda
revision humana antes de utilizarse como resultado definitivo de la tesis.
