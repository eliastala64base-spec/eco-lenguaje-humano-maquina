# Roles operativos y familias laterales

## Roles

- `FUENTE_PRIMARIA`: valor técnico/intelectual independiente; JSONL + MD + SHA-256.
- `MANIFESTACION_ASOCIADA`: misma obra con nombre base exacto y evidencia suficiente; derivados según valor propio.
- `ARCHIVO_AUXILIAR`: soporte para interpretar una fuente; JSONL + SHA-256, MD solo si aporta lectura.
- `DERIVADO_GENERADO`: exportación/reporte; JSONL + SHA-256, MD solo si es útil; relación `GENERADO_POR` probable/confirmada.
- `RESPALDO_COPIA`: respaldo o duplicado exacto; solo SHA-256 si no aporta contenido nuevo.
- `CONTENEDOR`: inventario estático JSONL + SHA-256.
- `BASE_DATOS`: esquema controlado JSONL + MD + SHA-256, sin volcado masivo.
- `CODIGO_FUENTE`: análisis estático JSONL + MD + SHA-256.
- `EJECUTABLE_ACTIVO`: análisis estático JSONL + SHA-256, sin ejecución.
- `TEMPORAL_CACHE`: solo reporte de campaña.
- `DESCONOCIDO`: metadatos/hash y advertencia; no inventar.

## Asociación y familias técnicas

El mismo nombre base no prueba por sí solo una manifestación: requiere evidencia de contenido/estructura o procedencia. Sin ella, registrar relación `POSIBLE`. Un cambio en el nombre base crea otro recurso.

En una familia técnica con nombre base exacto, un `.edb`, `.sdb`, `.rvt`, `.qgz`, `.dwg` u otro modelo puede ser principal; XLSX/PDF/imagen pueden ser derivados, LOG/PRJ auxiliares, BAK respaldos y archivos de bloqueo temporales. Registrar el criterio y no eliminar nada.

Detectar duplicado exacto por SHA-256. Elegir determinísticamente la primera ruta Unicode como representación extraída y dar solo SHA-256 a copias exactas posteriores. Una copia renombrada sigue intacta y no se elimina.

## Extensiones mínimas

Admitir documentos/hojas/presentaciones, CAD/BIM/GIS/3D, imágenes, audio, video, ZIP/RAR/7Z/TAR/GZ/CAB/DMG/IMG/KMZ, EML/MSG, SQLite/DB/MDB/ACCDB, código/configuración y ejecutables habituales. Un formato sin extractor recibe identidad, integridad, rol, advertencia y calidad parcial; nunca datos inventados.
