# ECO Lenguaje Humano–Máquina

Plugin distribuible de la skill `eco-lenguaje-humano-maquina-skill`, versión `0.5.0-beta.1`.

Convierte fuentes autorizadas en representaciones trazables para personas y máquinas sin modificar los originales.

## Modos

- `DOCUMENTO_CONTROLADO`: documentos propios con revisiones `Rev.*`.
- `RECURSO_CENTRALIZADO`: modo predeterminado de proyectos y áreas; conserva todos los derivados en `80_LENGUAJE_HUMANO_MAQUINA`.
- `RECURSO_PORTABLE_LATERAL`: excepción solicitada para llevar JSONL, Markdown y SHA-256 junto al original.

Los alias `REVISION_CONTROLADA_80` y `RECURSO_UNICO_LATERAL` se aceptan temporalmente por compatibilidad.

## Principios

- `80_LENGUAJE_HUMANO_MAQUINA` y `99_CONTROL` son nombres reservados.
- SHA-256 identifica los bytes del original.
- El fingerprint incorpora versión de skill, esquema, extractor, configuración y enriquecimiento.
- Un SHA y fingerprint vigentes evitan reprocesamiento.
- Un cambio de fuente o procesamiento genera un paquete nuevo y conserva el anterior.
- JSONL es canónico; Markdown y JSON-LD son vistas derivadas.
- SQLite no se crea por archivo ni dentro de la carpeta 80.

## Ejecución

```text
python plugins/eco-lenguaje-humano-maquina/skills/eco-lenguaje-humano-maquina-skill/scripts/convertir_lenguaje_humano_maquina.py RUTA --mode RECURSO_CENTRALIZADO --dry-run
```

Después de revisar el plan:

```text
python plugins/eco-lenguaje-humano-maquina/skills/eco-lenguaje-humano-maquina-skill/scripts/convertir_lenguaje_humano_maquina.py RUTA --mode RECURSO_CENTRALIZADO
```

La skill, scripts, referencias, esquemas y pruebas viven dentro del plugin. El repositorio no almacena originales ni derivados procesados de usuarios.
