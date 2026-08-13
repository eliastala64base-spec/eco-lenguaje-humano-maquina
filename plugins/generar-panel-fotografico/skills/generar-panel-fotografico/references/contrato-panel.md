Exit code: 0
Wall time: 0.3 seconds
Output:
# Contrato del panel

## Entradas

- raÃ­z de fotografÃ­as;
- catÃ¡logo JSONL, un registro por foto;
- uno o mÃ¡s cÃ³digos de selecciÃ³n;
- identificador de panel;
- metadatos de encabezado opcionales.

## Campos nativos del catÃ¡logo

- `sha256` o `foto_id`;
- `nombre_actual`, `nombre_controlado` o `ruta_relativa`;
- `fecha.fecha_efectiva`;
- `guia_humana.descripcion_manual`;
- `clasificacion.clasificaciones[].codigo`;
- `clasificacion.codigos_explicitos`;
- `clasificacion.indices_consulta`;
- `clasificacion.relaciones_contextuales`.

## Estados

- paquete generado: `BORRADOR`;
- publicaciÃ³n: `RESTRINGIDO`;
- aprobaciÃ³n: `PENDIENTE_REVISION_HUMANA`;
- preservaciÃ³n: no asignar automÃ¡ticamente.

## Trazabilidad mÃ­nima

Registrar generador y versiÃ³n, catÃ¡logo y hash, cÃ³digos solicitados, fotos candidatas, fotos seleccionadas, nombre fuente, nombre derivado, SHA-256, fecha efectiva, descripciÃ³n y advertencias.

## RegeneraciÃ³n

Una modificaciÃ³n de entradas genera un `PANEL_ID` nuevo o una nueva ejecuciÃ³n identificable. No mezclar residuos de dos ejecuciones ni sustituir silenciosamente un paquete anterior.


