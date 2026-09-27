# SCRUM-122: Validar D05-D07

## Objetivo

Validar transparencia (D05), explicabilidad (D06) y supervision humana (D07)
con la misma referencia y corpus utilizados por las otras tareas.

## Resultado

| Metrica | Valor |
|---|---:|
| Casos documento-dimension | 21 |
| Acuerdo exacto de nivel | 52,38% |
| Precision de deteccion | 100,00% |
| Exhaustividad de deteccion | 88,89% |
| F1 de deteccion | 94,12% |
| Falsos positivos | 0 |
| Falsos negativos | 2 |

## Diferencias observadas

- El recomendador sintetico quedo `AUSENTE` en D07. El documento permite al
  usuario desactivar la personalizacion, al adulto responsable revisar el
  perfil infantil y a un comite revisar incidentes; estas son señales de
  control humano parciales que el vocabulario actual no reconoce.
- El marco de IA generativa de Castilla-La Mancha quedo `AUSENTE` en D06. El
  requisito de definir guias de transparencia e interpretabilidad es evidencia
  parcial, aunque todavia no especifica explicaciones por salida, destinatario
  o formato.
- Las dimensiones D05-D07 de los documentos sinteticos completos se degradan
  a `PARCIAL`, igual que en las otras familias.

Para el ajuste posterior conviene reconocer controles ejercidos por usuarios
y responsables, y expresiones de interpretabilidad documental, manteniendo
una exigencia mayor para alcanzar `EXPLICITO`.

## Cierre

La precision es alta y no se observaron falsos positivos, pero faltan dos
formas validas de evidencia parcial. Es la familia con menor exhaustividad del
Sprint 11 y debe priorizarse en SCRUM-125.
