# Contrato de salida

## Autoridad

`80_LENGUAJE_HUMANO_MAQUINA` es el único nombre permitido para el prefijo `80`. Los originales conservan autoridad y toda salida es derivada y regenerable.

## Documento controlado

`DOCUMENTO_CONTROLADO` genera una única carpeta directa:

```text
80_LENGUAJE_HUMANO_MAQUINA/
├── 00_INDICE_GENERAL.md
├── UNIDAD_DOCUMENTAL/
│   ├── 00_DOCUMENTO.md
│   ├── 01_VISTA_DOCUMENTO.html
│   ├── 02_RECURSO_CANONICO.json
│   ├── 03_RELACIONES_GRAPHITI.jsonld
│   ├── 04_MEDIA_DERIVADA/
│   └── 99_CONTROL/
└── 99_CONTROL/
```

No crear `90_CONTROL_DOCUMENTO` ni `90_CONTROL_TECNICO`.

## Recurso centralizado

`RECURSO_CENTRALIZADO` genera:

```text
80_LENGUAJE_HUMANO_MAQUINA/
├── 00_INDICE.md
├── RECURSOS/
│   └── HASH_PREFIJO/SHA256/FINGERPRINT/
│       ├── recurso.jsonl
│       ├── lectura.md
│       ├── relaciones.jsonld
│       ├── calidad.json
│       └── integridad.sha256
└── 99_CONTROL/
    ├── MANIFEST.jsonl
    ├── EVENTOS.jsonl
    └── CHECKSUMS.sha256
```

No crear derivados junto al original. Separar físicamente las carpetas 80 de proyectos o áreas con permisos diferentes.

## Recurso portable

`RECURSO_PORTABLE_LATERAL` administra, según el rol:

```text
archivo.ext.jsonl
archivo.ext.md
archivo.ext.sha256
```

No crear `.txt`, `.csv`, `.sqlite`, varios JSONL ni archivos vacíos como derivados auxiliares.

## Publicación segura

Construir en zona temporal, validar y publicar atómicamente. Sustituir únicamente derivados administrados. Mantener la salida anterior ante fallo y confirmar que el SHA-256 del original no cambió.
