# Contrato de salida

## Contenido

1. Autoridad y terminología
2. Salida controlada
3. Salida lateral
4. Publicación segura

## Autoridad y terminología

“Carpeta 80”, “la 80” y “directorio 80” significan exclusivamente `80_LENGUAJE_HUMANO_MAQUINA`. Usar siempre el nombre completo en rutas y reportes. Los originales son autoridad; toda salida es derivada y regenerable.

## Salida controlada

`REVISION_CONTROLADA_80` genera una sola `80_LENGUAJE_HUMANO_MAQUINA` en el destino directo de la ruta entregada. Cada unidad contiene `00_DOCUMENTO.md`, `01_VISTA_DOCUMENTO.html`, `02_RECURSO_CANONICO.json`, `03_RELACIONES_GRAPHITI.jsonld`, `04_MEDIA_DERIVADA/` y `90_CONTROL_DOCUMENTO/`. Mantener el índice y control técnico general vigente.

Una `80_LENGUAJE_HUMANO_MAQUINA` directa puede regenerarse. Una interna no esperada bloquea. Nunca usar una `80_LENGUAJE_HUMANO_MAQUINA` como fuente.

## Salida lateral

`RECURSO_UNICO_LATERAL` no crea `80_LENGUAJE_HUMANO_MAQUINA` ni subcarpetas. Para `archivo.ext` administrar solo:

```text
archivo.ext.jsonl
archivo.ext.md
archivo.ext.sha256
```

El rol decide el subconjunto. No crear `.txt`, `.csv`, `.sqlite`, `.metadata.json`, `.structure.json`, varios JSONL ni archivos vacíos. Un original que ya sea JSON conserva su nombre; sus derivados empiezan por `original.json.`.

Usar un contrato de etiquetas común en los tres derivados. El JSONL es canónico; Markdown y SHA-256 repiten identidad e integridad para revisión cruzada:

| Dato | JSONL | Frontmatter Markdown | Comentario `.sha256` |
|---|---|---|---|
| Esquema | `manifest.schema_version` | `schema_version` | `# schema_version:` |
| Nombre | `source_metadata.source_filename` | `source_filename` | `# source_filename:` |
| Tamaño | `source_metadata.source_size_bytes` | `source_size_bytes` | `# source_size_bytes:` |
| Hash | `integrity.source_sha256` | `source_sha256` | `# source_sha256:` |

El `.sha256` debe usar el mismo `schema_name`, declarar `artifact_type: integrity` y terminar con la línea estándar `<hash><dos espacios><nombre>` para conservar compatibilidad con verificadores comunes. Las líneas anteriores empiezan por `#`, contienen etiquetas estables y no alteran la verificación. Todo valor repetido debe coincidir exactamente con el original y con el JSONL.

## Publicación segura

Construir en zona temporal hermana, validar y publicar atómicamente. En modo controlado sustituir la carpeta derivada completa. En modo lateral sustituir únicamente los tres nombres administrados correspondientes al original y retirar un Markdown obsoleto si el rol vigente ya no lo autoriza. No tocar otros archivos. Ante fallo, restaurar todos los derivados anteriores y conservar los originales.
