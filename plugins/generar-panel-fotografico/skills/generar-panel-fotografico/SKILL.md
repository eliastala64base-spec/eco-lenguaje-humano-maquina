---
name: generar-panel-fotografico
description: Prepara paneles fotográficos trazables y revisables desde un catálogo JSONL y fotografías existentes, sin depender de una ruta o proyecto concreto. Usar cuando Codex deba seleccionar evidencias por códigos o relaciones, crear un paquete HTML A4 de hasta seis fotos por página, conservar SHA-256, generar panel.json, manifiesto y checksums, o preparar una salida para revisión humana e integración posterior a ECOSISTEMA.
---

# Generar panel fotográfico

Versión técnica inicial: `v0.1.0-alpha.1`.

## Principios

- Tratar fotografías, catálogo, matriz y plantilla como fuentes de solo lectura.
- Usar SHA-256 como identidad técnica; nunca inferir identidad desde la ruta.
- Recibir todas las rutas mediante parámetros. No codificar `OBRA_INNOVA`, letras de unidad ni nombres de cliente en el programa.
- Generar derivados en una carpeta nueva; no sobrescribir paquetes existentes.
- La IA propone la selección. La emisión y aprobación son decisiones humanas.
- No afirmar conformidad, liberación, aprobación ni ubicación no sustentada.

## Inicio obligatorio

1. Leer reglas del proyecto y control de configuración aplicables.
2. Identificar el catálogo JSONL canónico, la raíz de fotografías y los códigos solicitados.
3. Leer [references/contrato-panel.md](references/contrato-panel.md).
4. Leer [references/adaptacion-catalogos.md](references/adaptacion-catalogos.md) si el catálogo no usa el perfil nativo.
5. Ejecutar primero en simulación.

## Ejecutar

```text
python scripts/generar_panel.py \
  --project-root RUTA_FOTOS \
  --catalog RUTA_CATALOGO_JSONL \
  --output-root RUTA_BORRADORES \
  --panel-id PANEL_ID \
  --code CODIGO \
  --limit 6 \
  --dry-run
```

Si la simulación no reporta errores, repetir sin `--dry-run`. Se pueden repetir `--code` y completar encabezados con `--project-name`, `--client`, `--component`, `--area` y `--title`.

## Selección

1. Aceptar registros cuyo código aparezca en clasificación primaria, clasificaciones adicionales, códigos explícitos, índices o relaciones contextuales.
2. Exigir que el archivo exista y que su hash coincida con el catálogo.
3. Ordenar por fecha efectiva y nombre controlado.
4. Limitar la salida al número solicitado; el valor inicial recomendado es seis.
5. Registrar candidatos no elegidos y advertencias sin ocultarlos.

Para losas, no asignar `L01`, `L02` o `L03` solo por fecha o correlativo. Una descripción sin número de losa permanece ambigua y requiere revisión humana.

## Salida

Cada ejecución crea un paquete nuevo con `panel.json`, `panel.html`, `manifest.json`, `checksums.sha256` y `media/`. Las imágenes son copias derivadas byte a byte; las fuentes permanecen intactas.

## Cierre

1. Validar JSON y checksums.
2. Confirmar `source_files_modified: false`.
3. Revisar visualmente el HTML antes de convertirlo a PDF.
4. Mantener estado `BORRADOR` o `EN_REVISION` hasta aprobación humana.
5. Registrar versión del generador, catálogo, códigos, entradas, salidas y hashes para ECOSISTEMA.

## Límites de `v0.1.0-alpha.1`

- Genera HTML y paquete trazable; la conversión PDF y la escritura directa sobre formatos Excel quedan para una versión posterior.
- No clasifica fotografías nuevas ni actualiza el catálogo.
- No publica, libera, firma ni aprueba paneles.
