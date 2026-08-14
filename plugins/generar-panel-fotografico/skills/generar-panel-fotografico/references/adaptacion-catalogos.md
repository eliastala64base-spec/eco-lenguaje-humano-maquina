# Adaptación de catálogos

La ubicación de archivos nunca forma parte del contrato lógico. Adaptar nombres de campos antes de ejecutar si otro proyecto usa un esquema distinto.

Mapeo mínimo:

| Concepto | Campo requerido |
|---|---|
| Identidad | SHA-256 |
| Ruta | ruta relativa desde la raíz fotográfica |
| Clasificación | lista de códigos consultables |
| Descripción | texto humano confirmado o propuesta marcada |
| Fecha | fecha efectiva y fuente de fecha |
| Revisión | estado de revisión humana |

No usar semejanza de nombres como sustituto del hash. No convertir una relación contextual en clasificación primaria sin confirmación.

