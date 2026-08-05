# Modos de ejecución

## Selección

Usar `REVISION_CONTROLADA_80` para documentación propia/controlada. Usar `RECURSO_UNICO_LATERAL` para materiales externos, de terceros o ediciones únicas. La decisión describe procedencia/control, no formato.

`AUTO` solo acepta:

- Ancestro exacto `02_PROYECTOS_INDEPENDIENTES` → lateral.
- Ancestro exacto `03_PROYECTOS_DEPENDIENTES` → controlado.
- Carpetas `Rev.*` hijas directas → controlado.

Fuera de esos casos exigir modo explícito. No usar la ausencia de revisión como prueba de que un recurso es externo.

## Flujos

Controlado: topología → prevalidación de `80_LENGUAJE_HUMANO_MAQUINA` → revisiones → unidades exactas → prelación → extracción → validación → publicación completa.

Lateral: inventario seguro → roles → hash/duplicados exactos → extracción estática → JSONL → validación → Markdown desde JSONL → verificación de hash → publicación junto a cada original.

Los modos nunca se ejecutan uno sobre los derivados del otro. En lateral, omitir árboles `80_LENGUAJE_HUMANO_MAQUINA`; en controlado, bloquear una ubicación interna no esperada.
