Exit code: 0
Wall time: 0.3 seconds
Output:
---
name: generar-panel-fotografico
description: Prepara paneles fotogrÃ¡ficos trazables y revisables desde un catÃ¡logo JSONL y fotografÃ­as existentes, sin depender de una ruta o proyecto concreto. Usar cuando Codex deba seleccionar evidencias por cÃ³digos o relaciones, crear un paquete HTML A4 de hasta seis fotos por pÃ¡gina, conservar SHA-256, generar panel.json, manifiesto y checksums, o preparar una salida para revisiÃ³n humana e integraciÃ³n posterior a ECOSISTEMA.
---

# Generar panel fotogrÃ¡fico

VersiÃ³n tÃ©cnica inicial: `v0.1.0-alpha.1`.

## Principios

- Tratar fotografÃ­as, catÃ¡logo, matriz y plantilla como fuentes de solo lectura.
- Usar SHA-256 como identidad tÃ©cnica; nunca inferir identidad desde la ruta.
- Recibir todas las rutas mediante parÃ¡metros. No codificar `OBRA_INNOVA`, letras de unidad ni nombres de cliente en el programa.
- Generar derivados en una carpeta nueva; no sobrescribir paquetes existentes.
- La IA propone la selecciÃ³n. La emisiÃ³n y aprobaciÃ³n son decisiones humanas.
- No afirmar conformidad, liberaciÃ³n, aprobaciÃ³n ni ubicaciÃ³n no sustentada.

## Inicio obligatorio

1. Leer reglas del proyecto y control de configuraciÃ³n aplicables.
2. Identificar el catÃ¡logo JSONL canÃ³nico, la raÃ­z de fotografÃ­as y los cÃ³digos solicitados.
3. Leer [references/contrato-panel.md](references/contrato-panel.md).
4. Leer [references/adaptacion-catalogos.md](references/adaptacion-catalogos.md) si el catÃ¡logo no usa el perfil nativo.
5. Ejecutar primero en simulaciÃ³n.

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

Si la simulaciÃ³n no reporta errores, repetir sin `--dry-run`. Se pueden repetir `--code` y completar encabezados con `--project-name`, `--client`, `--component`, `--area` y `--title`.

## SelecciÃ³n

1. Aceptar registros cuyo cÃ³digo aparezca en clasificaciÃ³n primaria, clasificaciones adicionales, cÃ³digos explÃ­citos, Ã­ndices o relaciones contextuales.
2. Exigir que el archivo exista y que su hash coincida con el catÃ¡logo.
3. Ordenar por fecha efectiva y nombre controlado.
4. Limitar la salida al nÃºmero solicitado; el valor inicial recomendado es seis.
5. Registrar candidatos no elegidos y advertencias sin ocultarlos.

Para losas, no asignar `L01`, `L02` o `L03` solo por fecha o correlativo. Una descripciÃ³n sin nÃºmero de losa permanece ambigua y requiere revisiÃ³n humana.

## Salida

Cada ejecuciÃ³n crea un paquete nuevo con `panel.json`, `panel.html`, `manifest.json`, `checksums.sha256` y `media/`. Las imÃ¡genes son copias derivadas byte a byte; las fuentes permanecen intactas.

## Cierre

1. Validar JSON y checksums.
2. Confirmar `source_files_modified: false`.
3. Revisar visualmente el HTML antes de convertirlo a PDF.
4. Mantener estado `BORRADOR` o `EN_REVISION` hasta aprobaciÃ³n humana.
5. Registrar versiÃ³n del generador, catÃ¡logo, cÃ³digos, entradas, salidas y hashes para ECOSISTEMA.

## LÃ­mites de `v0.1.0-alpha.1`

- Genera HTML y paquete trazable; la conversiÃ³n PDF y la escritura directa sobre formatos Excel quedan para una versiÃ³n posterior.
- No clasifica fotografÃ­as nuevas ni actualiza el catÃ¡logo.
- No publica, libera, firma ni aprueba paneles.

