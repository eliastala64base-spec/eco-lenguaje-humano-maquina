# Contrato del panel

## Entradas

- raíz de fotografías;
- catálogo JSONL, un registro por foto;
- uno o más códigos de selección;
- identificador de panel;
- metadatos de encabezado opcionales.

## Campos nativos del catálogo

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
- publicación: `RESTRINGIDO`;
- aprobación: `PENDIENTE_REVISION_HUMANA`;
- preservación: no asignar automáticamente.

## Trazabilidad mínima

Registrar generador y versión, catálogo y hash, códigos solicitados, fotos candidatas, fotos seleccionadas, nombre fuente, nombre derivado, SHA-256, fecha efectiva, descripción y advertencias.

## Regeneración

Una modificación de entradas genera un `PANEL_ID` nuevo o una nueva ejecución identificable. No mezclar residuos de dos ejecuciones ni sustituir silenciosamente un paquete anterior.

