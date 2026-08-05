# Perfiles de formato

## Contenido

1. Documentos y hojas
2. Medios
3. Modelos técnicos
4. Contenedores, correo, bases y código
5. Seguridad y limitaciones

## Documentos y hojas

- PDF: metadatos, páginas y texto; marcar OCR cuando no haya texto extraíble.
- Word/ODF/RTF: propiedades, encabezados, secciones, párrafos, tablas, vínculos, comentarios, cambios y objetos cuando el extractor lo permita. No aceptar cambios.
- Excel/ODS/CSV: libro, hojas, visibilidad, rangos, celdas, fórmulas/valores, tablas, gráficos, nombres, vínculos, validaciones, conexiones y macros detectadas. No ejecutar macros y no crear archivos por hoja.
- Presentaciones: orden, diapositivas, títulos, texto, notas, tablas, imágenes, objetos y vínculos.

## Medios

- Imagen: dimensiones, orientación, EXIF, GPS advertido, OCR/descripción visual solo con herramienta o IA verificable.
- Audio/video: códec, duración, canales/pistas, resolución/FPS, capítulos y segmentos cuando estén disponibles. Transcribir una vez; si no, `NO_EXTRAIDO`.

## Modelos técnicos

CAD, BIM, GIS, ETABS, SAP2000 y 3D: extraer solo propiedades, unidades, capas, bloques, familias, entidades, parámetros, coordenadas, referencias, niveles, vistas, sistema/extent y dependencias que el lector verifique. Si no puede representar geometría, registrar `GEOMETRIA_NO_REPRESENTADA`. Para formatos propietarios sin lector, no inventar conteos ni contenido.

## Contenedores, correo, bases y código

- Contenedores: inventariar rutas, tamaños, fechas, cifrado y riesgo sin extraer ni ejecutar miembros.
- EML/MSG: encabezados, cuerpo, adjuntos y relaciones; advertir privacidad.
- Bases: abrir en solo lectura, extraer motor, tablas, campos, relaciones, índices/vistas/triggers detectados y conteos; no volcar masivamente datos personales.
- Código/configuración: análisis estático de lenguaje, archivos, símbolos, dependencias, entradas/salidas y secretos aparentes; nunca ejecutar.
- Ejecutables/sistema: identidad, firma, formato, propiedades y dependencias estáticas; nunca ejecutar, instalar ni cargar.

## Seguridad y limitaciones

No confundir “sin extractor estructurado” con “ilegible”. Conservar metadatos/hash y registrar la limitación. No ejecutar macros, vínculos, consultas activas, scripts ni binarios. No abrir miembros peligrosos. No reproducir secretos aparentes en Markdown. Cada limitación debe ser explícita y afectar la confianza de extracción.
