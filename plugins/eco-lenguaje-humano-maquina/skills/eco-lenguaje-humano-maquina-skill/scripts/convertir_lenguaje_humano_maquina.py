#!/usr/bin/env python3
"""Genera derivados humanos y de máquina sin tocar las fuentes originales."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import tempfile
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

SKILL_NAME = "Lenguaje Humano–Máquina"
SKILL_VERSION = "0.5.0-beta.1"
OUTPUT_NAME = "80_LENGUAJE_HUMANO_MAQUINA"
MODE_CONTROLLED = "DOCUMENTO_CONTROLADO"
MODE_CENTRAL = "RECURSO_CENTRALIZADO"
MODE_LATERAL = "RECURSO_PORTABLE_LATERAL"
MODE_CONTROLLED_LEGACY = "REVISION_CONTROLADA_80"
MODE_LATERAL_LEGACY = "RECURSO_UNICO_LATERAL"
REV_RE = re.compile(r"^rev(?:ision)?[._ -]*(?P<v>[A-Z]|\d{1,3})$", re.I)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

FAMILIES = {
    "EXCEL": {".xlsx", ".xls", ".xlsm", ".xlsb", ".csv", ".ods"},
    "WORD": {".docx", ".doc", ".docm", ".rtf", ".odt"},
    "PDF": {".pdf"},
    "CAD_EDITABLE": {".dwg", ".dxf", ".dwt", ".dgn"},
    "IMAGEN": {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp", ".heic"},
}
PRIORITY = {family: index for index, family in enumerate(FAMILIES)}
SUPPORTED = set().union(*FAMILIES.values())
SOURCE_FIELDS = {
    "ruta_relativa",
    "nombre_base_exacto",
    "nombre_archivo",
    "extension",
    "familia_documental",
    "rol",
    "revision_detectada",
    "fecha_lectura",
    "hash",
    "criterio_de_seleccion",
    "errores_de_lectura",
    "advertencias_de_lectura",
}
UNIT_FILES = (
    "00_DOCUMENTO.md",
    "01_VISTA_DOCUMENTO.html",
    "02_RECURSO_CANONICO.json",
    "03_RELACIONES_GRAPHITI.jsonld",
    "99_CONTROL/manifiesto.json",
    "99_CONTROL/fuentes_asociadas.json",
    "99_CONTROL/calidad_extraccion.json",
    "99_CONTROL/checksums.sha256",
)
RESERVED_TOP_LEVEL = {"99_control"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def family(extension: str) -> str | None:
    return next((name for name, values in FAMILIES.items() if extension in values), None)


def revision_of(path: Path, root: Path) -> str:
    for parent in (path.parent, *path.parents):
        if parent == root.parent:
            break
        match = REV_RE.fullmatch(parent.name)
        if match:
            value = match.group("v").upper()
            return value.zfill(2) if value.isdigit() else value
        if parent == root:
            break
    return "SIN_REVISION_DECLARADA"


def revision_rank(value: str) -> tuple[int, int]:
    if value == "SIN_REVISION_DECLARADA":
        return (0, 0)
    if value.isdigit():
        return (2, int(value))
    return (1, ord(value))


def relative_scope(path: Path, root: Path) -> str:
    """Contexto lógico: ruta sin carpetas Rev.*, para evitar mezclar homónimos."""
    parts = []
    for item in path.parent.relative_to(root).parts:
        if not REV_RE.fullmatch(item):
            parts.append(item)
    return "/".join(parts) or "__RAIZ__"


def safe_name(value: str) -> str:
    result = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", value).strip(" .")
    return result or "SIN_NOMBRE"


def is_inside_output(path: Path) -> bool:
    return any(part == OUTPUT_NAME for part in path.parts)


def direct_output(root: Path) -> Path:
    return root / OUTPUT_NAME


def detect_execution_mode(path: Path, requested: str) -> str:
    """Resolver el modo sin inferir autoría a partir del formato o del nombre del archivo."""
    requested = {
        MODE_CONTROLLED_LEGACY: MODE_CONTROLLED,
        MODE_LATERAL_LEGACY: MODE_LATERAL,
    }.get(requested, requested)
    if requested != "AUTO":
        return requested
    if path.is_dir() and any(
        child.is_dir() and not child.is_symlink() and REV_RE.fullmatch(child.name)
        for child in path.iterdir()
    ):
        return MODE_CONTROLLED
    ancestors = {part.casefold() for part in path.resolve().parts}
    if {"02_proyectos_independientes", "03_proyectos_dependientes"}.intersection(ancestors):
        return MODE_CENTRAL
    raise ValueError(
        "Modo ambiguo: indique --mode DOCUMENTO_CONTROLADO, "
        "--mode RECURSO_CENTRALIZADO o --mode RECURSO_PORTABLE_LATERAL. "
        "La ausencia de revisiones no demuestra que un recurso sea externo."
    )


def applicable_case(root: Path) -> str:
    direct_revisions = any(
        child.is_dir() and not child.is_symlink() and REV_RE.fullmatch(child.name)
        for child in root.iterdir()
    )
    return (
        "CASO_02_DOCUMENTO_LOGICO_CONTROLADO"
        if direct_revisions
        else "CASO_01_AREA_O_CARPETA_CONTENEDORA"
    )


def prevalidate(root: Path) -> dict[str, Any]:
    expected = direct_output(root)
    inside = is_inside_output(root)
    expected_exists = expected.exists() or expected.is_symlink()
    direct_exists = expected.is_dir() and not expected.is_symlink()
    destination_conflict = expected_exists and not direct_exists
    nested = []
    if root.is_dir() and not inside:
        nested = sorted(
            str(path) for path in root.rglob(OUTPUT_NAME)
            if (path.is_dir() or path.is_symlink()) and path != expected
        )
    sources = [
        path for path in root.rglob("*")
        if path.is_file() and not is_inside_output(path) and path.suffix.lower() in SUPPORTED
    ] if root.is_dir() and not inside else []
    revisions = sorted({revision_of(path, root) for path in sources}, key=revision_rank)
    units = sorted({f"{relative_scope(path, root)}::{path.stem}" for path in sources})
    blocked_reason = None
    if inside:
        blocked_reason = "Una carpeta derivada 80_LENGUAJE_HUMANO_MAQUINA no puede ser fuente de esta misma skill."
    elif nested:
        blocked_reason = ("La ruta contiene una carpeta 80_LENGUAJE_HUMANO_MAQUINA dentro de una subcarpeta. "
                          "La skill no puede trabajar sobre una estructura que ya contiene derivados 80 en niveles internos.")
    elif destination_conflict:
        blocked_reason = ("El destino directo esperado 80_LENGUAJE_HUMANO_MAQUINA existe, pero no es una carpeta "
                          "ordinaria segura. No se reemplazan archivos, enlaces simbólicos ni otros objetos.")
    return {
        "etapa": "PREVALIDACION_DE_RUTA",
        "estado": "BLOQUEADO" if blocked_reason else "APROBADO",
        "ruta_analizada": str(root),
        "caso_aplicable": (
            "BLOQUEO_RUTA_DENTRO_DE_80_LENGUAJE_HUMANO_MAQUINA"
            if inside
            else applicable_case(root)
        ),
        "skill": SKILL_NAME,
        "version_skill": SKILL_VERSION,
        "nombre_carpeta_derivada": OUTPUT_NAME,
        "destino_directo_esperado": str(expected),
        "carpeta_80_lenguaje_humano_maquina_directa_existente": direct_exists,
        "conflicto_en_destino_directo": destination_conflict,
        "carpetas_80_lenguaje_humano_maquina_en_subcarpetas": nested,
        "fuentes_detectadas": [str(path.relative_to(root)) for path in sources],
        "revisiones_detectadas": revisions,
        "unidades_documentales_detectadas": units,
        "motivo_de_bloqueo": blocked_reason,
        "acciones_autorizadas": (["Generar temporalmente", "Validar",
                                  "Reemplazar íntegramente la carpeta 80_LENGUAJE_HUMANO_MAQUINA directa"]
                                 if not blocked_reason else ["Ninguna. No se modificaron fuentes, derivados ni controles."]),
    }


def source_record(path: Path, root: Path) -> dict[str, Any]:
    extension = path.suffix.lower()
    return {
        "ruta_relativa": path.relative_to(root).as_posix(),
        "nombre_base_exacto": path.stem,
        "nombre_archivo": path.name,
        "extension": extension,
        "familia_documental": family(extension),
        "rol": "asociada",
        "revision_detectada": revision_of(path, root),
        "fecha_lectura": utc_now(),
        "hash": sha256_file(path),
        "criterio_de_seleccion": None,
        "errores_de_lectura": [],
        "advertencias_de_lectura": [],
    }


def public_source_record(record: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in record.items() if not key.startswith("_")}


def collect_units(root: Path) -> dict[tuple[str, str], list[Path]]:
    units: dict[tuple[str, str], list[Path]] = defaultdict(list)
    for path in sorted(root.rglob("*")):
        if path.is_file() and not is_inside_output(path) and path.suffix.lower() in SUPPORTED:
            units[(relative_scope(path, root), path.stem)].append(path)
    return units


def extract_text(path: Path) -> tuple[str, str | None, str | None]:
    """Devuelve texto, error real y advertencia de extracción, sin inventar contenido."""
    extension = path.suffix.lower()
    try:
        if extension == ".pdf":
            from pypdf import PdfReader
            text = "\n\f\n".join((page.extract_text() or "") for page in PdfReader(path).pages)
            warning = None if text.strip() else "PDF sin texto extraíble; puede requerir OCR verificado."
            return text, None, warning
        if extension in {".xlsx", ".xlsm"}:
            import openpyxl
            book = openpyxl.load_workbook(path, read_only=True, data_only=False, keep_vba=extension == ".xlsm")
            rows = []
            for sheet in book.worksheets:
                for row in sheet.iter_rows(values_only=False):
                    for cell in row:
                        if cell.value is not None:
                            rows.append(f"{sheet.title}!{cell.coordinate}: {cell.value}")
            book.close()
            return "\n".join(rows), None, None
        if extension == ".csv":
            return path.read_text(encoding="utf-8", errors="replace"), None, None
        if extension in {".docx", ".docm"}:
            with zipfile.ZipFile(path) as archive:
                xml = archive.read("word/document.xml")
            tree = ET.fromstring(xml)
            return "\n".join(node.text or "" for node in tree.iter() if node.tag.endswith("}t")), None, None
        with path.open("rb") as stream:
            stream.read(64)
        return "", None, (
            "Extracción estructurada no disponible para esta variante; "
            "el archivo se verificó por lectura binaria, metadatos y hash."
        )
    except Exception as exc:  # continua con la siguiente fuente legible
        return "", f"{type(exc).__name__}: {exc}", None


def select_sources(paths: list[Path], root: Path) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], list[str]]:
    records = [source_record(path, root) for path in paths]
    by_revision: dict[str, list[tuple[Path, dict[str, Any]]]] = defaultdict(list)
    for path, record in zip(paths, records):
        by_revision[record["revision_detectada"]].append((path, record))
    selected: dict[str, dict[str, Any]] = {}
    warnings = []
    for revision, items in by_revision.items():
        ordered = sorted(items, key=lambda item: (PRIORITY[item[1]["familia_documental"]], item[1]["nombre_archivo"]))
        if len(ordered) > 1 and PRIORITY[ordered[0][1]["familia_documental"]] == PRIORITY[ordered[1][1]["familia_documental"]]:
            warnings.append(f"Ambigüedad en Rev.{revision}: empate de familia; se aplicó orden Unicode.")
        for path, record in ordered:
            text, error, warning = extract_text(path)
            record["_texto_extraido"] = text
            if error:
                record["errores_de_lectura"].append(error)
            if warning:
                record["advertencias_de_lectura"].append(warning)
            if revision not in selected and not error:
                record["rol"] = "principal"
                record["criterio_de_seleccion"] = f"PRELACION_{record['familia_documental']}"
                selected[revision] = record
            else:
                record["criterio_de_seleccion"] = ("ASOCIADA_MISMO_NOMBRE_BASE_Y_REVISION" if not error else "NO_LEIBLE_CONTINUAR_SIGUIENTE")
        if revision not in selected:
            warnings.append(f"Rev.{revision}: ninguna fuente pudo leerse; se conservaron errores de lectura.")
    return records, selected, warnings


def canonical_revision(selected: dict[str, dict[str, Any]]) -> str:
    return max(selected or {"SIN_REVISION_DECLARADA": {}}, key=revision_rank)


def output_relative_for(scope: str, base: str, all_units: dict[tuple[str, str], list[Path]]) -> Path:
    same_base = [item for item in all_units if item[1] == base]
    if len(same_base) == 1:
        return Path(safe_name(base))
    scope_parts = [safe_name(part) for part in scope.split("/") if part]
    return Path(*scope_parts, safe_name(base))


def plan_output_paths(all_units: dict[tuple[str, str], list[Path]]) -> dict[tuple[str, str], Path]:
    planned: dict[tuple[str, str], Path] = {}
    occupied: dict[str, tuple[str, str]] = {}
    for key in all_units:
        relative = output_relative_for(*key, all_units)
        if relative.parts and relative.parts[0].casefold() in RESERVED_TOP_LEVEL:
            raise ValueError(
                f"Colisión con nombre técnico reservado: {relative.as_posix()}. "
                "No se reemplazará 80_LENGUAJE_HUMANO_MAQUINA."
            )
        collision_key = relative.as_posix().casefold()
        if collision_key in occupied:
            other = occupied[collision_key]
            raise ValueError(
                "Dos unidades producirían la misma ruta derivada después de sanear sus nombres: "
                f"{other!r} y {key!r}. No se reemplazará 80_LENGUAJE_HUMANO_MAQUINA."
            )
        occupied[collision_key] = key
        planned[key] = relative
    return planned


def build_document(unit_dir: Path, scope: str, base: str, records: list[dict[str, Any]], selected: dict[str, dict[str, Any]], warnings: list[str]) -> None:
    revision = canonical_revision(selected)
    primary = selected.get(revision)
    media = unit_dir / "04_MEDIA_DERIVADA"
    control = unit_dir / "99_CONTROL"
    media.mkdir(parents=True)
    control.mkdir(parents=True)
    source_warnings = [
        f"{record['nombre_archivo']}: {warning}"
        for record in records
        for warning in record["advertencias_de_lectura"]
    ]
    quality = {"errores_criticos": [], "advertencias": [*warnings, *source_warnings], "revision_canonica": revision,
               "fuentes_principales_por_revision": {key: value["nombre_archivo"] for key, value in selected.items()},
               "fuentes_legibles": len(selected), "fuentes_total": len(records)}
    public_records = [pu���G����ƭy�["hash"],
            "eco:rutaRelativa": record["ruta_relativa"],
            "eco:nombreArchivo": record["nombre_archivo"],
            "eco:revisionDetectada": record["revision_detectada"],
            "eco:rol": record["rol"],
        }
        for record in public_records
    ]
    graph = {
        "@context": {
            "eco": "https://ecosistema.local/vocab/",
            "prov": "http://www.w3.org/ns/prov#",
        },
        "@graph": [
            {
                "@id": f"urn:eco:unidad:{hashlib.sha256((scope+'|'+base).encode()).hexdigest()}",
                "@type": "eco:UnidadDocumental",
                "eco:nombreBaseExacto": base,
                "eco:revisionCanonica": revision,
                "prov:wasDerivedFrom": [node["@id"] for node in source_nodes],
            },
            *source_nodes,
        ],
    }
    write_json(unit_dir / "03_RELACIONES_GRAPHITI.jsonld", graph)
    write_json(control / "fuentes_asociadas.json", public_records)
    write_json(control / "calidad_extraccion.json", quality)
    manifest = {"nombre_base_exacto": base, "contexto_logico": scope, "generado_en": utc_now(), "fuentes": public_records,
                "derivados": [str(path.relative_to(unit_dir)) for path in sorted(unit_dir.rglob("*")) if path.is_file()], "originales_modificados": False}
    write_json(control / "manifiesto.json", manifest)
    checks = [path for path in sorted(unit_dir.rglob("*")) if path.is_file() and path.name != "checksums.sha256"]
    (control / "checksums.sha256").write_text("\n".join(f"{sha256_file(path)}  {path.relative_to(unit_dir).as_posix()}" for path in checks) + "\n", encoding="utf-8")


def validate_checksums(unit_dir: Path) -> None:
    checksum_file = unit_dir / "99_CONTROL" / "checksums.sha256"
    declared: dict[str, str] = {}
    for line in checksum_file.read_text(encoding="utf-8").splitlines():
        digest, separator, relative = line.partition("  ")
        if not separator or not SHA256_RE.fullmatch(digest) or not relative:
            raise ValueError(f"Línea de checksum inválida en {checksum_file}: {line!r}")
        if relative in declared:
            raise ValueError(f"Ruta duplicada en {checksum_file}: {relative}")
        declared[relative] = digest
    expected = {
        path.relative_to(unit_dir).as_posix()
        for path in unit_dir.rglob("*")
        if path.is_file() and path != checksum_file
    }
    if set(declared) != expected:
        raise ValueError(f"Inventario de checksums incompleto o excedente en {unit_dir}")
    for relative, digest in declared.items():
        if sha256_file(unit_dir / relative) != digest:
            raise ValueError(f"Checksum no coincide: {unit_dir / relative}")


def validate_traceability(unit_dir: Path) -> list[dict[str, Any]]:
    resource = json.loads((unit_dir / "02_RECURSO_CANONICO.json").read_text(encoding="utf-8"))
    if resource.get("schema_version") != 3:
        raise ValueError(f"schema_version inválida en {unit_dir}")
    required_resource = {"identidad", "control_revision", "fuentes", "contenido", "procesamiento", "calidad"}
    if not required_resource.issubset(resource):
        raise ValueError(f"Recurso canónico incompleto en {unit_dir}")
    records = json.loads(
        (unit_dir / "99_CONTROL" / "fuentes_asociadas.json").read_text(encoding="utf-8")
    )
    if not records or records != resource["fuentes"]:
        raise ValueError(f"Trazabilidad de fuentes incompleta o inconsistente en {unit_dir}")
    for record in records:
        missing = SOURCE_FIELDS.difference(record)
        if missing:
            raise ValueError(f"Campos de fuente ausentes en {unit_dir}: {sorted(missing)}")
        extra = set(record).difference(SOURCE_FIELDS)
        if extra:
            raise ValueError(f"Campos de fuente no previstos en {unit_dir}: {sorted(extra)}")
        if not SHA256_RE.fullmatch(record["hash"]):
            raise ValueError(f"Hash de fuente inválido en {unit_dir}: {record['nombre_archivo']}")
        relative = Path(record["ruta_relativa"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"Ruta relativa insegura en {unit_dir}: {record['ruta_relativa']}")
    graph = json.loads((unit_dir / "03_RELACIONES_GRAPHITI.jsonld").read_text(encoding="utf-8"))
    if not isinstance(graph.get("@graph"), list) or not graph["@graph"]:
        raise ValueError(f"JSON-LD sin grafo verificable en {unit_dir}")
    manifest = json.loads(
        (unit_dir / "99_CONTROL" / "manifiesto.json").read_text(encoding="utf-8")
    )
    if manifest.get("originales_modificados") is not False or manifest.get("fuentes") != records:
        raise ValueError(f"Manifiesto inconsistente en {unit_dir}")
    quality = json.loads(
        (unit_dir / "99_CONTROL" / "calidad_extraccion.json").read_text(encoding="utf-8")
    )
    if quality != resource["calidad"]:
        raise ValueError(f"Control de calidad inconsistente en {unit_dir}")
    processing = resource["procesamiento"]
    if (
        processing.get("skill") != SKILL_NAME
        or processing.get("version") != SKILL_VERSION
        or processing.get("originales_modificados") is not False
    ):
        raise ValueError(f"Metadatos de procesamiento inconsistentes en {unit_dir}")
    return records


def validate_output(temp: Path, expected_units: int, forced_failure: bool = False) -> None:
    if forced_failure:
        raise ValueError("Fallo de validación solicitado para prueba.")
    units = [path for path in temp.rglob("00_DOCUMENTO.md")]
    if len(units) != expected_units:
        raise ValueError("Estructura incompleta: no existe un documento por cada unidad.")
    for path in [*temp.rglob("*.json"), *temp.rglob("*.jsonld")]:
        json.loads(path.read_text(encoding="utf-8"))
    prevalidation = json.loads((temp / "00_PREVALIDACION_DE_RUTA.json").read_text(encoding="utf-8"))
    if prevalidation.get("estado") != "APROBADO":
        raise ValueError("La salida contiene una prevalidación no aprobada.")
    inventory = json.loads(
        (temp / "99_CONTROL" / "inventario_archivos.json").read_text(encoding="utf-8")
    )
    events = (temp / "99_CONTROL" / "eventos.jsonl").read_text(encoding="utf-8").splitlines()
    if not events:
        raise ValueError("El registro de eventos está vacío.")
    for event in events:
        json.loads(event)
    traced_records = []
    for unit in units:
        base = unit.parent
        for directory in ("04_MEDIA_DERIVADA", "99_CONTROL"):
            if not (base / directory).is_dir():
                raise ValueError(f"Falta el directorio {directory} en {base}")
        for item in UNIT_FILES[1:]:
            if not (base / item).is_file():
                raise ValueError(f"Falta {item} en {base}")
        traced_records.extend(validate_traceability(base))
        validate_checksums(base)
    sort_key = lambda record: (
        record["ruta_relativa"],
        record["revision_detectada"],
        record["nombre_archivo"],
    )
    if sorted(inventory, key=sort_key) != sorted(traced_records, key=sort_key):
        raise ValueError("El inventario técnico no coincide con las fuentes de las unidades documentales.")


def unique_sibling_path(parent: Path, prefix: str) -> Path:
    reserved = Path(tempfile.mkdtemp(prefix=prefix, dir=parent))
    reserved.rmdir()
    return reserved


def publish_output(temp_output: Path, destination: Path) -> list[str]:
    if destination.is_symlink() or (destination.exists() and not destination.is_dir()):
        raise ValueError(
            "El destino 80_LENGUAJE_HUMANO_MAQUINA dejó de ser una carpeta ordinaria segura."
        )
    backup = unique_sibling_path(destination.parent, f".{OUTPUT_NAME}.backup-")
    previous_moved = False
    if destination.exists():
        os.replace(destination, backup)
        previous_moved = True
    try:
        os.replace(temp_output, destination)
    except Exception as publish_error:
        if previous_moved and backup.exists() and not destination.exists():
            try:
                os.replace(backup, destination)
            except Exception as restore_error:
                raise RuntimeError(
                    "Falló la publicación y también la restauración automática de "
                    "80_LENGUAJE_HUMANO_MAQUINA; la salida anterior permanece en "
                    f"{backup}"
                ) from restore_error
        raise publish_error
    warnings = []
    if backup.exists():
        try:
            shutil.rmtree(backup)
        except OSError as exc:
            warnings.append(f"No se pudo retirar la copia temporal anterior {backup}: {exc}")
    return warnings


def generate(root: Path, forced_failure: bool = False) -> dict[str, Any]:
    report = prevalidate(root)
    if report["estado"] == "BLOQUEADO":
        return report
    units = collect_units(root)
    planned_paths = plan_output_paths(units)
    original_hashes = {
        str(path.relative_to(root)): (path.stat().st_size, sha256_file(path))
        for paths in units.values()
        for path in paths
    }
    parent = root.parent
    temp = Path(tempfile.mkdtemp(prefix=f".{OUTPUT_NAME}.tmp-", dir=parent))
    temp_output = temp / OUTPUT_NAME
    temp_output.mkdir()
    try:
        write_json(temp_output / "00_PREVALIDACION_DE_RUTA.json", report)
        index = ["# Índice general", "", "Derivado regenerable; las fuentes originales conservan autoridad.", ""]
        inventory = []
        for (scope, base), paths in units.items():
            records, selected, warnings = select_sources(paths, root)
            unit_dir = temp_output / planned_paths[(scope, base)]
            unit_dir.mkdir(parents=True)
            build_document(unit_dir, scope, base, records, selected, warnings)
            index.append(f"- [{base}]({unit_dir.relative_to(temp_output).as_posix()}/00_DOCUMENTO.md) — `{scope}`")
            inventory.extend(public_source_record(record) for record in records)
        (temp_output / "00_INDICE_GENERAL.md").write_text("\n".join(index) + "\n", encoding="utf-8")
        technical = temp_output / "99_CONTROL"
        technical.mkdir()
        write_json(technical / "inventario_archivos.json", inventory)
        (technical / "eventos.jsonl").write_text(
            json.dumps(
                {
                    "evento": "GENERACION_COMPLETA",
                    "fecha": utc_now(),
                    "unidades": len(units),
                    "skill": SKILL_NAME,
                    "version": SKILL_VERSION,
                },
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        validate_output(temp_output, len(units), forced_failure)
        final_report = prevalidate(root)
        if final_report["estado"] != "APROBADO":
            raise ValueError(
                "La PREVALIDACION_DE_RUTA cambió durante la generación; no se reemplazará "
                "80_LENGUAJE_HUMANO_MAQUINA."
            )
        if {
            str(path.relative_to(root)): (path.stat().st_size, sha256_file(path))
            for paths in collect_units(root).values()
            for path in paths
        } != original_hashes:
            raise ValueError("Se detectó modificación de una fuente; no se reemplazará la salida.")
        destination = direct_output(root)
        publication_warnings = publish_output(temp_output, destination)
        report.update(
            {
                "resultado": "REGENERADO",
                "unidades_generadas": len(units),
                "originales_modificados": False,
                "version_skill": SKILL_VERSION,
                "advertencias_publicacion": publication_warnings,
            }
        )
        return report
    finally:
        if temp.exists():
            shutil.rmtree(temp, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ruta", type=Path)
    parser.add_argument(
        "--mode",
        choices=(
            "AUTO", MODE_CONTROLLED, MODE_CENTRAL, MODE_LATERAL,
            MODE_CONTROLLED_LEGACY, MODE_LATERAL_LEGACY,
        ),
        default="AUTO",
        help=(
            "AUTO solo usa marcadores inequívocos de ECOSISTEMA o revisiones directas; "
            "en los demás casos el modo debe indicarse."
        ),
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--configuration-hash", default="DEFAULT")
    parser.add_argument("--ai-enrichment", type=Path)
    parser.add_argument("--force-validation-failure", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        target = args.ruta.resolve()
        mode = detect_execution_mode(target, args.mode)
        if mode == MODE_LATERAL:
            from procesar_recurso_lateral import dry_run as lateral_dry_run
            from procesar_recurso_lateral import process as lateral_process

            report = (
                lateral_dry_run(target)
                if args.dry_run
                else lateral_process(target, args.ai_enrichment, args.force_validation_failure)
            )
        elif mode == MODE_CENTRAL:
            from procesar_recurso_central import dry_run as central_dry_run
            from procesar_recurso_central import process as central_process

            report = (
                central_dry_run(target, args.output_root, args.configuration_hash)
                if args.dry_run
                else central_process(
                    target,
                    args.output_root,
                    args.ai_enrichment,
                    args.configuration_hash,
                    args.force_validation_failure,
                )
            )
        else:
            if not target.is_dir():
                raise NotADirectoryError(target)
            if args.ai_enrichment:
                raise ValueError("--ai-enrichment solo corresponde a recursos centralizados o portables.")
            report = prevalidate(target) if args.dry_run else generate(target, args.force_validation_failure)
            report["modo"] = MODE_CONTROLLED
    except Exception as exc:
        report = {
            "estado": "ERROR",
            "ruta_analizada": str(args.ruta.resolve()),
            "nombre_carpeta_derivada": OUTPUT_NAME,
            "version_skill": SKILL_VERSION,
            "motivo": f"{type(exc).__name__}: {exc}",
            "acciones_ejecutadas": (
                "No se publicó una nueva carpeta 80_LENGUAJE_HUMANO_MAQUINA; "
                "las fuentes originales permanecen sin modificación."
            ),
        }
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 2 if report["estado"] == "BLOQUEADO" else 0


if __name__ == "__main__":
    raise SystemExit(main())
