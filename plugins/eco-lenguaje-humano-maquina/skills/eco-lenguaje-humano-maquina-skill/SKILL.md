---
name: eco-lenguaje-humano-maquina-skill
description: Transformar fuentes documentales autorizadas en representaciones humanas y de máquina trazables sin modificar originales. Usar al extraer, normalizar, preparar para Obsidian, generar JSONL/Markdown/JSON-LD, verificar SHA-256, comparar duplicados o actualizar derivados de documentos controlados y recursos de proyectos personales, independientes o dependientes. Centralizar por defecto los derivados en 80_LENGUAJE_HUMANO_MAQUINA y usar salidas laterales solo cuando el usuario solicite un paquete portable.
---

# Lenguaje Humano–Máquina

Versión técnica: `v0.5.0-beta.1`.

## Propósito

Conservar cada original intacto y producir representaciones regenerables para personas, Obsidian, Python, IA y grafos. No decidir clasificación final, permisos, publicación, venta, licencia, `Rev.00`, línea base, OAIS definitivo ni eliminación.

Interpretar «carpeta 80» exclusivamente como `80_LENGUAJE_HUMANO_MAQUINA`. Reservar `99_CONTROL` para controles. No crear otra carpeta iniciada por `80_` o `99_` con significado diferente.

## Inicio obligatorio

1. Leer las reglas desde la ruta objetivo hasta la raíz.
2. Leer `references/modos-ejecucion.md`, `references/contrato-salida.md`, `references/numeracion-reservada.md` y `references/regeneracion-fingerprint.md`.
3. Leer las referencias de revisión y formato cuando correspondan.
4. Identificar el proyecto o área propietario y sus permisos.
5. Ejecutar primero con `--dry-run`.
6. No mover, renombrar, sobrescribir, eliminar ni ejecutar originales o contenido activo.

## Seleccionar un modo

```yaml
execution_modes:
  - DOCUMENTO_CONTROLADO
  - RECURSO_CENTRALIZADO
  - RECURSO_PORTABLE_LATERAL
```

### `DOCUMENTO_CONTROLADO`

Usar cuando la unidad tiene revisiones `Rev.A`, `Rev.B`, `Rev.00`, `Rev.01`, etc. Seleccionar la emisión aplicable conforme a `references/seleccion-revision.md` y generar una sola `80_LENGUAJE_HUMANO_MAQUINA` en el documento lógico o contenedor indicado.

### `RECURSO_CENTRALIZADO`

Usar por defecto dentro de proyectos personales, independientes y dependientes. Mantener limpios los directorios fuente y generar los derivados en la única carpeta `80_LENGUAJE_HUMANO_MAQUINA` del proyecto o área propietaria.

Organizar cada manifestación por SHA-256 y fingerprint de procesamiento. Si ambos siguen vigentes, no extraer nuevamente. Si cambia el original, crear una nueva manifestación. Si cambia la skill, esquema, extractor, configuración, prompt, modelo o enriquecimiento, generar un fingerprint nuevo sin sustituir paquetes anteriores.

### `RECURSO_PORTABLE_LATERAL`

Usar únicamente cuando el usuario solicite portabilidad junto al original o cuando no exista un proyecto/área propietario. Crear `archivo.ext.jsonl`, `archivo.ext.md` cuando aporte lectura humana y `archivo.ext.sha256`. No usar este modo como predeterminado dentro de ECOSISTEMA.

Aceptar `REVISION_CONTROLADA_80` y `RECURSO_UNICO_LATERAL` solo como alias de compatibilidad; informar siempre el nombre canónico actual.

`AUTO` debe elegir `DOCUMENTO_CONTROLADO` si existen revisiones directas y `RECURSO_CENTRALIZADO` dentro de proyectos independientes o dependientes. Detenerse si la evidencia es ambigua.

## Ejecutar

```text
python scripts/convertir_lenguaje_humano_maquina.py RUTA --mode RECURSO_CENTRALIZADO --dry-run
python scripts/convertir_lenguaje_humano_maquina.py RUTA --mode RECURSO_CENTRALIZADO
```

Opciones principales:

```text
--output-root RUTA/80_LENGUAJE_HUMANO_MAQUINA
--configuration-hash HASH_CONFIGURACION
--ai-enrichment ARCHIVO_JSON
```

Exigir que `--output-root` termine exactamente en `80_LENGUAJE_HUMANO_MAQUINA`.

## Reglas de extracción

- Calcular SHA-256 antes y después del procesamiento.
- Extraer estáticamente; no ejecutar macros, scripts, binarios, instaladores, consultas ni miembros activos.
- Generar JSONL canónico antes del Markdown.
- Generar Markdown únicamente desde el JSONL validado.
- Generar JSON-LD como exportación portable, no como grafo operativo único.
- Registrar calidad, advertencias, procedencia, formato, rol y limitaciones.
- No resumir en lugar de extraer; agregar el resumen como capa adicional.
- Registrar `NO_EXTRAIDO`, `EXTRACCION_PARCIAL`, `ARCHIVO_PROTEGIDO`, `CONTENIDO_ACTIVO_NO_EJECUTADO` u otra limitación verificable.

## Publicación segura

1. Construir en una zona temporal hermana.
2. Validar estructura, JSON/JSONL/JSON-LD, hashes y correspondencia con la fuente.
3. Confirmar que el original conserva tamaño y SHA-256.
4. Publicar atómicamente solo los derivados administrados.
5. Restaurar la salida anterior ante fallo.
6. Mantener paquetes anteriores cuando cambie el fingerprint.
7. Actualizar `99_CONTROL/MANIFEST.jsonl`, `EVENTOS.jsonl` y `CHECKSUMS.sha256` en modo central.

## Validación

Ejecutar la suite completa, la validación de la skill y una prueba representativa de cada modo. No declarar éxito sin confirmar `originales_modificados: false` y sin comprobar que solo existen los prefijos altos reservados.

## Límites

- Mantener el original como autoridad.
- No mezclar derivados entre proyectos, áreas o niveles de acceso.
- No utilizar una carpeta `80_LENGUAJE_HUMANO_MAQUINA` como fuente.
- No crear SQLite por archivo ni dentro de la carpeta 80; usar un catálogo operativo externo y reconstruible.
- No editar cachés instaladas como si fueran la fuente canónica.
