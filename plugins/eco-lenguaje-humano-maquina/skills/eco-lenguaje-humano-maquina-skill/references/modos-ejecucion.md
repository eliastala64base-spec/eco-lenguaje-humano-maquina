# Modos de ejecución

## Selección

Usar:

- `DOCUMENTO_CONTROLADO` para una unidad documental con revisiones `Rev.*`.
- `RECURSO_CENTRALIZADO` para recursos de un proyecto o área que deben mantener limpias sus carpetas fuente.
- `RECURSO_PORTABLE_LATERAL` solo para entregar los derivados junto al original por portabilidad expresa.

Aceptar `REVISION_CONTROLADA_80` y `RECURSO_UNICO_LATERAL` como alias heredados, sin usarlos en registros nuevos.

`AUTO` solo acepta:

- Revisiones `Rev.*` hijas directas → `DOCUMENTO_CONTROLADO`.
- Ancestro exacto `02_PROYECTOS_INDEPENDIENTES` o `03_PROYECTOS_DEPENDIENTES` → `RECURSO_CENTRALIZADO`.

Fuera de esos casos exigir modo explícito.

## Flujos

Controlado: topología → prevalidación → revisiones → fuentes → extracción → validación → única carpeta `80_LENGUAJE_HUMANO_MAQUINA`.

Centralizado: proyecto/área → inventario → SHA-256 → fingerprint → extracción necesaria → paquete por hash/fingerprint → actualización de `99_CONTROL`.

Portable: archivo → inspección → SHA-256 → JSONL → Markdown derivado → publicación lateral atómica.

No ejecutar un modo sobre derivados de otro. Omitir cualquier árbol `80_LENGUAJE_HUMANO_MAQUINA` durante el inventario.
