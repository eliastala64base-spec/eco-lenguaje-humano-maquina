# Regeneración y fingerprint

## Identidades separadas

- `resource_id`: identifica el recurso lógico cuando exista en el catálogo.
- `file_id`: identifica una manifestación concreta.
- `source_sha256`: identifica exactamente los bytes del original.
- `processing_fingerprint`: identifica las condiciones usadas para generar los derivados.

No usar SHA-256 como única identidad del documento lógico.

## Fingerprint mínimo

Calcularlo de forma determinista con:

```text
source_sha256
+ skill_version
+ schema_version
+ extractor_profile
+ configuration_hash
+ model_version
+ prompt_version
+ enrichment_hash
```

Usar `null` o un valor canónico cuando una capa no intervenga. No omitir silenciosamente un componente que pueda cambiar el resultado.

## Decisiones

| Condición | Acción |
|---|---|
| SHA y fingerprint iguales | Validar el paquete existente y omitir reprocesamiento |
| SHA igual y ruta diferente | Registrar una nueva observación de ubicación; reutilizar el paquete |
| SHA diferente | Crear una nueva manifestación y conservar la anterior |
| SHA igual y fingerprint diferente | Crear derivados nuevos sin releer más de lo necesario |
| Paquete inválido o incompleto | Regenerar en zona temporal y sustituir solo tras validar |
| Fuente ausente | Marcar ausencia; no borrar paquete ni respaldo automáticamente |

Registrar cada ejecución u omisión en `99_CONTROL/EVENTOS.jsonl`. Mantener las observaciones de ruta en `99_CONTROL/MANIFEST.jsonl`.
