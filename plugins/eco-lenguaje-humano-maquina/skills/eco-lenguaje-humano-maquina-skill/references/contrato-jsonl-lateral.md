# Contrato JSONL lateral

## Orden lógico

```text
01 manifest
02 source_metadata
03 integrity
04 file_role
05 format_information
06 structure y registros estructurales
07 content y fragmentos
08 technical_data
09 entities
10 relations
11 summary
12 keywords
13 rights_observed
14 security
15 comparison_features
16 quality
17 warning / warnings
18 end
```

Cada línea es un objeto JSON independiente con `record_type`. Exigir exactamente una línea de cada universal: `manifest`, `source_metadata`, `integrity`, `file_role`, `format_information`, `summary`, `keywords`, `quality`, `warnings` y `end`. `warnings` agrega códigos y puede tener cero; `warning` solo aparece por cada limitación real. No crear registros condicionales vacíos.

`manifest` usa `schema_name: lenguaje_humano_maquina`, `schema_version: 2` y `processing_mode: RECURSO_PORTABLE_LATERAL`. `integrity` contiene SHA-256 y tamaño. `file_role` aclara que el rol no es clasificación final. `security` confirma que no se ejecutó contenido. `end` repite el hash y estado.

## Rutas universales para Python

Usar siempre las mismas claves, sin depender del formato original. Tratar como rutas canónicas:

| Dato lógico | Selector JSONL canónico |
|---|---|
| Nombre | `record_type == "source_metadata"` → `source_filename` |
| Ruta relativa | `record_type == "source_metadata"` → `source_relative_path` |
| Extensión | `record_type == "source_metadata"` → `source_extension` |
| Tamaño | `record_type == "source_metadata"` → `source_size_bytes` |
| Modificación | `record_type == "source_metadata"` → `source_modified_at` |
| SHA-256 | `record_type == "integrity"` → `source_sha256` |
| Formato detectado | `record_type == "format_information"` → `detected_format` |
| Descripción corta | `record_type == "summary"` → `short_description` |
| Descripción breve | `record_type == "summary"` → `brief_description` |
| Descripción larga | `record_type == "summary"` → `long_description` |
| Sinónimos | `record_type == "summary"` → `synonyms` |
| Palabras clave | `record_type == "keywords"` → `values` |

Mantener estas rutas en PDF, Word, Excel, CAD/BIM/GIS, imagen, audio, video, correo, base, código, contenedor y binario. Los registros específicos agregan detalle, pero nunca desplazan las rutas universales. `integrity.source_size_bytes` y `comparison_features.source_size_bytes` son copias de control: deben coincidir con `source_metadata.source_size_bytes`; no son la ruta primaria de consulta.

El registro `summary` debe incluir siempre `short_description`, `brief_description`, `long_description`, `synonyms`, `generation_method` y el alias compatible `text`, cuyo valor debe ser idéntico a `brief_description`. El registro `keywords.values` continúa separado para búsquedas e índices. No inventar sinónimos: usar una lista vacía cuando no estén sustentados.

`comparison_features` conserva, con `null` si no existe evidencia: hash, tamaño, fechas, formato, páginas, hojas/nombres, tablas, fórmulas, imágenes, capas, entidades, longitud textual, título normalizado, hash de texto normalizado, firma estructural y firma de metadatos. No calcular porcentaje definitivo ni fusionar recursos.

Validar todas las líneas antes del Markdown. El Markdown debe poder regenerarse byte por byte desde el JSONL y registrar su hash JSONL. No introducir contenido adicional. Si el volumen supera límites técnicos, dividir solo mediante fragmentos documentados dentro del mismo JSONL; no crear JSON paralelos por defecto.

## Enriquecimiento IA de campaña

Cuando exista IA, realizar una sola pasada y guardar temporalmente —fuera de la carpeta fuente— un objeto indexado por ruta relativa:

```json
{
  "subcarpeta/archivo.ext": {
    "short_description": "Frase nominal sustentada.",
    "brief_description": "Descripción breve sustentada.",
    "long_description": "Descripción amplia sustentada en el contenido extraído.",
    "synonyms": ["término equivalente"],
    "keywords": ["término"],
    "entities": [{"name": "Entidad", "entity_type": "TIPO", "evidence": "página/celda/segmento"}],
    "relations": [{"relation_type": "RELACIONADO_CON", "target_filename": "otro.ext", "evidence": "página/celda/segmento", "status": "OBSERVADA"}]
  }
}
```

Pasarlo con `--ai-enrichment`. Aceptar `summary` únicamente como alias heredado de `brief_description`. Rechazar entidades o relaciones sin evidencia. Sustentar descripciones, sinónimos y palabras clave en contenido extraído y redactar secretos aparentes. El archivo temporal no forma parte de la salida lateral y debe retirarse al terminar. Si no hay enriquecimiento, conservar las tres descripciones deterministas, sinónimos vacíos, palabras clave deterministas y `IA_NO_APLICADA`.
