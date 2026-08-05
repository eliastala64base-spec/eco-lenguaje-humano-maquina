# Lenguaje Humano–Máquina

Repositorio distribuible de la skill `eco-lenguaje-humano-maquina-skill`, versión `0.4.1`, empaquetada como plugin de ChatGPT y Codex.

## Contenido

- `.agents/plugins/marketplace.json`: catálogo del repositorio.
- `plugins/eco-lenguaje-humano-maquina/.codex-plugin/plugin.json`: manifiesto instalable.
- `plugins/eco-lenguaje-humano-maquina/skills/eco-lenguaje-humano-maquina-skill/`: skill completa, incluidos scripts, referencias, esquemas y pruebas.

## Publicar en GitHub

1. Crear un repositorio privado vacío en GitHub.
2. Subir el contenido de esta carpeta a la raíz del repositorio.
3. Usar la rama `main`.
4. No agregar documentos originales, credenciales, archivos procesados ni derivados de proyectos.

## Agregar el catálogo en Codex

Desde una sesión con acceso al repositorio:

```text
codex plugin marketplace add USUARIO/REPOSITORIO --ref main
```

Después, abrir **Plugins**, seleccionar el catálogo **ecosistema-virtual** e instalar **Lenguaje Humano–Máquina**. Iniciar un chat nuevo y seleccionar la skill con `@` en ChatGPT Work o con `$` en Codex.

## Uso inicial recomendado

```text
Usa Lenguaje Humano–Máquina.

Ruta objetivo: [RUTA]
Modo: RECURSO_UNICO_LATERAL

Ejecuta primero la prevalidación en seco. Continúa únicamente si el estado es APROBADO. No modifiques, muevas ni renombres los originales.
```

Para documentación propia con revisiones, sustituir el modo por `REVISION_CONTROLADA_80`.
