---
name: eco-lenguaje-humano-maquina-skill
description: Transforma carpetas documentales autorizadas y recursos externos en derivados humanos y de máquina trazables, regenerables y seguros. Use when the user asks to extraer, normalizar, preparar para Obsidian, comparar duplicados o crear lenguaje humano–máquina para documentos propios con revisiones en 80_LENGUAJE_HUMANO_MAQUINA o para recursos únicos/externos con JSONL, Markdown y SHA-256 laterales; admite documentos, hojas, presentaciones, CAD/BIM/GIS, imágenes, audio, video, correo, bases, código, contenedores y binarios mediante inspección estática.
---

# Lenguaje Humano–Máquina

Versión técnica vigente: `v0.4.1`.

## Propósito y límite

Transformar fuentes autorizadas sin modificar, mover, renombrar, borrar ni sustituir originales. Terminar con:

```text
ORIGINAL INTACTO
+ REPRESENTACIÓN ESTRUCTURADA PARA MÁQUINA
+ REPRESENTACIÓN RESUMIDA PARA PERSONA
+ HUELLA DE INTEGRIDAD
```

Preparar para consulta, Obsidian, automatización, comparación e incorporación futura a ECOSISTEMA. No decidir clasificación final, carpeta/proyecto/acceso, publicación, venta, OAIS definitivo, `Rev.00`, eliminación/fusión, base de datos, embeddings ni Graphiti operativo.

Interpretar “carpeta 80”, “la 80” o “directorio 80” exclusivamente como `80_LENGUAJE_HUMANO_MAQUINA`. Usar siempre el nombre completo en rutas, reportes y decisiones.

Antes de operar, leer las reglas aplicables desde la ruta hasta la raíz y las referencias:

- `references/modos-ejecucion.md`: selección del modo y topologías.
- `references/contrato-salida.md`: salidas y publicación segura.
- `references/seleccion-revision.md`: revisión, asociación y prelación del modo controlado.
- `references/contrato-jsonl-lateral.md`: jerarquía y contrato del modo lateral.
- `references/roles-y-formatos.md`: roles, familias y profundidad segura.
- `references/modelo-normalizacion.md`: autoridad, Obsidian, IA y etapas posteriores.
- `references/perfiles-formato.md`: capacidades y limitaciones por formato.

## Elegir obligatoriamente un modo

```yaml
execution_modes:
  - REVISION_CONTROLADA_80
  - RECURSO_UNICO_LATERAL
```

No inferir autoría por formato, nombre ni ausencia de revisiones. Usar el modo declarado por el usuario. `AUTO` solo es válido cuando una ruta ancestral llamada exactamente `02_PROYECTOS_INDEPENDIENTES` determina `RECURSO_UNICO_LATERAL`, una llamada `03_PROYECTOS_DEPENDIENTES` determina `REVISION_CONTROLADA_80`, o existen revisiones `Rev.*` hijas directas que determinan el modo controlado. Si no hay evidencia inequívoca, detener y pedir/indicar `--mode`.

Ejecutar primero:

```text
python scripts/convertir_lenguaje_humano_maquina.py RUTA --mode MODO --dry-run
```

Informar la prevalidación. Continuar solo con estado `APROBADO`.

## Modo `REVISION_CONTROLADA_80`

Aplicar a documentos propios/controlados y entregables con `Rev.A`, `Rev.B`, `Rev.00`, `Rev.01`, etc. Conservar íntegramente el comportamiento compatible de `v0.3.1`:

1. Usar el orden `topología → prevalidación → revisión → nombre base exacto → fuente principal → extracción`.
2. Elegir la revisión numérica más alta; si no existe numérica, la alfabética más alta. Registrar todas sin mezclar emisiones.
3. Asociar manifestaciones solo si el nombre base completo sin extensión coincide exactamente y pertenecen al mismo contexto de revisión.
4. Elegir por revisión: `Excel → Word → PDF → CAD editable → imagen`. Mantener las demás como asociadas.
5. Generar únicamente `80_LENGUAJE_HUMANO_MAQUINA` en el destino directo definido por la topología.

Prevalidar antes de escribir:

- Bloquear si la ruta es `80_LENGUAJE_HUMANO_MAQUINA` o está dentro de ella.
- Permitir regenerar una `80_LENGUAJE_HUMANO_MAQUINA` exactamente en el destino directo: construir temporalmente, validar y sustituir por completo sin mezclar residuos.
- Bloquear si existe otra `80_LENGUAJE_HUMANO_MAQUINA` en subcarpetas del ámbito.
- Bloquear archivos, enlaces simbólicos o colisiones en el destino.
- Mantener la salida anterior si falla generación, validación o publicación; restaurarla si falla el intercambio.

Usar `CASO_01_AREA_O_CARPETA_CONTENEDORA` cuando el destino es `RUTA/80_LENGUAJE_HUMANO_MAQUINA`. Usar `CASO_02_DOCUMENTO_LOGICO_CONTROLADO` cuando la ruta entregada contiene `Rev.*` como hijas: la salida queda dentro de ese documento lógico, al nivel de `Rev.*`.

## Modo `RECURSO_UNICO_LATERAL`

Aplicar a recursos externos, de terceros o ediciones únicas. No crear `80_LENGUAJE_HUMANO_MAQUINA`, subcarpetas por archivo, TXT, CSV, SQLite ni JSON separados. No procesar una `80_LENGUAJE_HUMANO_MAQUINA` como fuente. Al recorrer una carpeta, omitir cualquier árbol `80_LENGUAJE_HUMANO_MAQUINA`; bloquear si la ruta entregada está dentro de uno.

Para una fuente primaria crear junto al original:

```text
NOMBRE_COMPLETO_ORIGINAL.ext
NOMBRE_COMPLETO_ORIGINAL.ext.jsonl
NOMBRE_COMPLETO_ORIGINAL.ext.md
NOMBRE_COMPLETO_ORIGINAL.ext.sha256
```

Usar el nombre completo, incluida la extensión, como prefijo. Para `configuracion.json`, crear `configuracion.json.jsonl`, `configuracion.json.md` y `configuracion.json.sha256`.

Asignar antes un rol operativo no definitivo: `FUENTE_PRIMARIA`, `MANIFESTACION_ASOCIADA`, `ARCHIVO_AUXILIAR`, `DERIVADO_GENERADO`, `RESPALDO_COPIA`, `CONTENEDOR`, `BASE_DATOS`, `CODIGO_FUENTE`, `EJECUTABLE_ACTIVO`, `TEMPORAL_CACHE` o `DESCONOCIDO`. Aplicar:

- Fuente primaria: JSONL + Markdown + SHA-256.
- Auxiliar o derivado: JSONL + SHA-256; Markdown solo con contenido humano útil.
- Respaldo/copia exacta: SHA-256; no repetir extracción.
- Temporal/caché: ningún derivado; incluir solo en el reporte de campaña.
- Ejecutable/activo: JSONL estático + SHA-256; nunca ejecutar ni generar explicación basada en ejecución.
- Contenedor: JSONL con inventario + SHA-256; no extraer/ejecutar miembros.

No asociar por similitud. Para manifestaciones, exigir nombre base exacto y evidencia suficiente; si solo coincide el nombre, registrar relación posible, no fusionar. Para familias técnicas, distinguir principal, exportaciones, auxiliares, respaldos y temporales con evidencia y estado de relación.

## Flujo lateral obligatorio

```text
original → inspección solo lectura → SHA-256 → formato real → rol
→ extracción determinista → una intervención IA opcional por archivo/campaña
→ un JSONL → validación → Markdown desde JSONL → SHA-256 final
→ verificación del original → publicación lateral atómica → reporte
```

Python obtiene hechos objetivos, detecta contenido activo sin ejecutarlo, valida cada línea JSONL, genera el Markdown desde el JSONL validado, escribe SHA-256 y compara el hash original antes/después. La IA solo comprende, redacta descripciones corta/breve/larga, propone sinónimos, palabras clave, entidades y relaciones, y genera la vista humana; no sustituye hechos deterministas. Cuando esté disponible, consolidar su única intervención en un archivo temporal de enriquecimiento por campaña y pasarlo con `--ai-enrichment`; si no está disponible, registrar `IA_NO_APLICADA`, sin inventar.

Conservar rutas universales independientes del formato: `source_metadata.source_size_bytes` para tamaño, `integrity.source_sha256` para hash, `summary.short_description|brief_description|long_description|synonyms` para descripciones y sinónimos, y `keywords.values` para palabras clave. Repetir nombre, tamaño y hash con las mismas etiquetas en el frontmatter Markdown y como comentarios `# clave:` del `.sha256`; validar que coincidan. Consultar el mapeo completo en `references/contrato-jsonl-lateral.md`.

El JSONL es la fuente canónica extraída; el Markdown es una vista breve regenerada únicamente desde él; el original conserva autoridad sobre bits, formato, geometría, fórmulas, macros, capas, audio, video, código y comportamiento. Registrar toda limitación con códigos explícitos como `NO_EXTRAIDO`, `ARCHIVO_PROTEGIDO`, `MACRO_NO_EJECUTADA`, `GEOMETRIA_NO_REPRESENTADA`, `CONTENIDO_ACTIVO_NO_EJECUTADO`, `FORMATO_NO_SOPORTADO_COMPLETAMENTE`, `METADATO_NO_CONFIABLE` o `EXTRACCION_PARCIAL`.

## Validación y cierre

En ambos modos:

1. No ejecutar macros, scripts, binarios, instaladores ni miembros activos.
2. Comparar tamaño/hash de cada original antes y después.
3. No publicar salida parcial o vacía.
4. Validar JSON/JSON-LD o cada línea JSONL, estructura, hashes, trazabilidad y correspondencia con la fuente.
5. Generar Markdown después de validar la representación canónica y solo con datos presentes en ella.
6. Publicar mediante zona temporal y reemplazo atómico de derivados administrados; restaurar derivados anteriores ante fallo.
7. Reportar modo, versión, roles, advertencias, limitaciones y confirmar expresamente `originales_modificados: false`.

Ejecutar la suite completa y `quick_validate.py` después de modificar la skill. No declarar éxito sin pruebas de ambos modos.
