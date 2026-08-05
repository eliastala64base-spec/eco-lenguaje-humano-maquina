# Revisiones, asociación y prelación controlada

Reconocer `Rev.A`…`Rev.Z` como internas y `Rev.00`…`Rev.999` como emitidas. Para representación vigente, seleccionar la numérica más alta; si no existe numérica, la alfabética más alta. Registrar cada revisión por separado y nunca mezclar su contenido.

Una unidad documental controlada existe solo para un `nombre_base_exacto` dentro del mismo contexto de revisión. La extensión es lo único que se omite. `MATRIZ_CALIDAD.xlsx` y `MATRIZ_CALIDAD.pdf` se asocian; `MATRIZ_CALIDAD_FINAL.pdf` es otra unidad. No quitar `FINAL`, `EDITABLE`, `COPIA`, `V2`, `REV00` ni `APROBADO`.

Seleccionar por revisión:

```text
Excel → Word → PDF → CAD editable → imagen
```

Excel: `.xlsx .xls .xlsm .xlsb .csv .ods`; Word: `.docx .doc .docm .rtf .odt`; PDF: `.pdf`; CAD editable: `.dwg .dxf .dwt .dgn`; imagen: `.jpg .jpeg .png .tif .tiff .bmp .webp .heic`.

Dentro de una familia, ordenar por nombre completo Unicode y registrar empate. Si la primera fuente tiene un error real de lectura, probar la siguiente. Una limitación de extractor no equivale a ilegibilidad. Las fuentes no principales siguen asociadas y no se eliminan.
