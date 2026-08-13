#!/usr/bin/env python3
"""Procesa recursos externos en modo lateral sin ejecutar contenido activo."""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import mimetypes
import os
import re
import shutil
import sqlite3
import subprocess
import tarfile
import tempfile
import wave
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from email import policy
from email.parser import BytesParser
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote
from xml.etree import ElementTree as ET

SKILL_NAME = "Lenguaje Humano‚ÄìM√°quina"
SKILL_VERSION = "0.5.0-beta.1"
SCHEMA_NAME = "lenguaje_humano_maquina"
SCHEMA_VERSION = 2
PROCESSING_MODE = "RECURSO_PORTABLE_LATERAL"
OUTPUT_80 = "80_LENGUAJE_HUMANO_MAQUINA"
MAX_TEXT_CHARS = 5_000_000
MAX_ARCHIVE_MEMBERS = 100_000
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

DOCUMENTS = {".pdf", ".docx", ".doc", ".docm", ".rtf", ".odt", ".txt", ".md", ".epub"}
SPREADSHEETS = {".xlsx", ".xls", ".xlsm", ".xlsb", ".csv", ".ods"}
PRESENTATIONS = {".pptx", ".ppt", ".pptm", ".odp"}
IMAGES = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp", ".heic", ".gif"}
AUDIO = {".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg", ".wma"}
VIDEO = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".mpeg", ".mpg", ".m4v"}
TECHNICAL = {
    ".dwg", ".dxf", ".dwt", ".dwf", ".dwfx", ".dgn", ".rvt", ".rfa", ".ifc",
    ".nwd", ".nwc", ".edb", ".sdb", ".f2k", ".e2k", ".qgz", ".qgs", ".shp",
    ".geojson", ".kml", ".kmz", ".las", ".laz", ".stl", ".obj", ".fbx", ".3ds",
}
ARCHIVES = {".zip", ".rar", ".7z", ".tar", ".gz", ".tgz", ".bz2", ".xz", ".cab", ".dmg", ".img", ".kmz"}
EMAILS = {".eml", ".msg"}
DATABASES = {".sqlite", ".sqlite3", ".db", ".accdb", ".mdb"}
CODE = {
    ".py", ".pyi", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".java", ".c",
    ".h", ".cpp", ".hpp", ".cs", ".go", ".rs", ".rb", ".php", ".swift", ".kt",
    ".kts", ".scala", ".sql", ".r", ".m", ".vue", ".svelte", ".html", ".css",
    ".scss", ".json", ".json5", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".xml",
}
ACTIVE = {".exe", ".dll", ".msi", ".sys", ".bat", ".cmd", ".ps1", ".sh", ".vbs", ".jar", ".wasm", ".com", ".scr"}
BACKUPS = {".bak", ".backup", ".old", ".orig", ".bk"}
AUXILIARY = {".log", ".xsd", ".properties", ".prj", ".cpg", ".dbf", ".shx", ".sld", ".aux"}
TEMPORARY = {".tmp", ".temp", ".cache", ".lock", ".lck", ".swp", ".part", ".crdownload", ".autosave"}
ALL_KNOWN = DOCUMENTS | SPREADSHEETS | PRESENTATIONS | IMAGES | AUDIO | VIDEO | TECHNICAL | ARCHIVES | EMAILS | DATABASES | CODE | ACTIVE | BACKUPS | AUXILIARY
TECHNICAL_PRIMARY = {".edb", ".sdb", ".f2k", ".e2k", ".rvt", ".nwd", ".qgz", ".qgs", ".shp", ".dwg", ".dgn", ".ifc"}
GENERATED_CANDIDATES = {".xlsx", ".xls", ".xlsm", ".xlsb", ".csv", ".ods", ".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff"}

ORDER = {
    "manifest": 1, "source_metadata": 2, "integrity": 3, "file_role": 4,
    "format_information": 5, "structure": 6, "page": 6, "section": 6, "heading": 6,
    "table": 6, "sheet": 6, "slide": 6, "layer": 6, "archive_member": 6, "database_table": 6,
    "database_field": 6, "content": 7, "paragraph": 7, "cell": 7, "subtitle": 7,
    "transcript_segment": 7, "email_message": 7, "comment": 7, "technical_data": 8,
    "formula": 8, "chart": 8, "image": 8, "drawing": 8, "block": 8, "entity": 9,
    "bim_element": 9, "gis_feature": 9, "audio_segment": 9, "video_segment": 9,
    "attachment": 9, "database_relation": 10, "code_file": 9, "code_symbol": 9,
    "dependency": 10, "relation": 10, "summary": 11, "keywords": 12,
    "rights_observed": 13, "security": 14, "comparison_features": 15, "quality": 16,
    "warning": 17, "warnings": 17, "end": 18,
}
UNIVERSAL = {
    "manifest", "source_metadata", "integrity", "file_role", "format_information",
    "summary", "keywords", "quality", "warnings", "end",
}
REQUIRED_BY_TYPE = {
    "manifest": {"schema_name", "schema_version", "source_filename", "source_relative_path", "generated_at", "generated_by", "processing_mode"},
    "source_metadata": {"source_filename", "source_relative_path", "source_size_bytes", "source_modified_at"},
    "integrity": {"algorithm", "source_sha256", "source_size_bytes"},
    "file_role": {"role", "basis", "classification_is_final"},
    "format_information": {"declared_extension", "declared_format", "detected_format"},
    "summary": {
        "text", "short_description", "brief_description", "long_description",
        "synonyms", "generation_method",
    },
    "keywords": {"values", "classification_is_final"},
    "quality": {"extraction_confidence", "extraction_status", "deterministic_extraction", "ai_enrichment_applied", "ai_passes"},
    "warning": {"code", "description", "severity"},
    "warnings": {"codes", "count"},
    "end": {"status", "source_sha256"},
}
ALLOWED_ROLES = {
    "FUENTE_PRIMARIA", "MANIFESTACION_ASOCIADA", "ARCHIVO_AUXILIAR", "DERIVADO_GENERADO",
    "RESPALDO_COPIA", "CONTENEDOR", "BASE_DATOS", "CODIGO_FUENTE", "EJECUTABLE_ACTIVO",
    "TEMPORAL_CACHE", "DESCONOCIDO",
}
STOPWORDS = {
    "para", "como", "desde", "hasta", "entre", "sobre", "este", "esta", "estos", "estas",
    "that", "this", "with", "from", "into", "documento", "archivo", "file", "the", "and", "una",
    "uno", "unos", "unas", "del", "las", "los", "por", "con", "sin", "que", "sus", "de", "la",
    "el", "en", "un", "y", "o", "a",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, bytes):
        return value.hex()
    if isinstance(value, (list, tuple, set)):
        return [json_safe(item) for item in value]
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    return str(value)


def iso_timestamp(value: float | None) -> str | None:
    return datetime.fromtimestamp(value, timezone.utc).replace(microsecond=0).isoformat() if value is not None else None


def warning(code: str, description: str, severity: str = "MEDIO") -> dict[str, Any]:
    return {"record_type": "warning", "code": code, "description": description, "severity": severity}


def is_temporary(path: Path) -> bool:
    return (
        path.suffix.lower() in TEMPORARY
        or path.name.startswith("~$")
        or path.name in {".DS_Store", "Thumbs.db"}
        or path.name.endswith("~")
    )


def is_attached_derivative(path: Path) -> bool:
    if path.name.endswith(".sha256"):
        return True
    for suffix in (".jsonl", ".sha256", ".md"):
        if path.name.endswith(suffix):
            original = path.with_name(path.name[: -len(suffix)])
            if original.is_file():
                return True
    try:
        if path.name.endswith(".jsonl"):
            with path.open("r", encoding="utf-8") as stream:
                first_line = stream.readline()
            manifest = json.loads(first_line)
            return manifest.get("record_type") == "manifest" and manifest.get("schema_name") == "lenguaje_humano_maquina"
        if path.name.endswith(".md"):
            head = path.read_text(encoding="utf-8", errors="replace")[:4096]
            return (
                (
                    head.startswith(f"---\nschema_name: {SCHEMA_NAME}\n")
                    and f"\nschema_version: {SCHEMA_VERSION}\n" in head
                )
                or head.startswith("---\nschema_version: 1\n")
            ) and (
                "\njsonl_sha256: " in head
                and "\nfile_role: " in head
            )
    except (OSError, UnicodeError, json.JSONDecodeError):
        return False
    return False


def iter_sources(target: Path) -> list[Path]:
    if target.is_file():
        return [] if is_attached_derivative(target) else [target]
    sources: list[Path] = []
    for path in sorted(target.rglob("*")):
        if OUTPUT_80 in path.parts:
            continue
        if path.is_file() and not path.is_symlink() and not is_attached_derivative(path):
            sources.append(path)
    return sources


def detect_format(path: Path) -> dict[str, Any]:
    extension = path.suffix.lower()
    head = path.read_bytes()[:32]
    detected = None
    if head.startswith(b"%PDF-"):
        detected = "PDF"
    elif head.startswith(b"PK\x03\x04"):
        detected = "ZIP_OOXML_OR_CONTAINER"
    elif head.startswith(b"SQLite format 3\x00"):
        detected = "SQLITE3"
    elif head.startswith(b"MZ"):
        detected = "PE_EXECUTABLE"
    elif head.startswith(b"\x7fELF"):
        detected = "ELF_BINARY"
    elif head.startswith(b"\x89PNG\r\n\x1a\n"):
        detected = "PNG"
    elif head.startswith(b"\xff\xd8\xff"):
        detected = "JPEG"
    elif head[:4] in {b"II*\x00", b"MM\x00*"}:
        detected = "TIFF"
    elif head.startswith(b"GIF8"):
        detected = "GIF"
    elif head.startswith(b"RIFF") and head[8:12] == b"WAVE":
        detected = "WAV"
    elif head.startswith(b"RIFF") and head[8:12] == b"WEBP":
        detected = "WEBP"
    elif head.startswith(b"Rar!\x1a\x07"):
        detected = "RAR"
    elif head.startswith(b"7z\xbc\xaf\x27\x1c"):
        detected = "7Z"
    mime, _ = mimetypes.guess_type(path.name)
    return {
        "declared_extension": extension,
        "declared_format": extension[1:].upper() if extension else "SIN_EXTENSION",
        "detected_format": detected or (mime.upper() if mime else "NO_DETERMINADO"),
        "mime_type": mime,
        "signature_match": bool(detected),
    }


def base_metadata(path: Path, root: Path) -> dict[str, Any]:
    stat = path.stat()
    created = getattr(stat, "st_birthtime", None)
    return {
        "record_type": "source_metadata",
        "source_filename": path.name,
        "source_extension": path.suffix.lower(),
        "source_relative_path": path.relative_to(root).as_posix() if root.is_dir() else path.name,
        "source_size_bytes": stat.st_size,
        "source_created_at": iso_timestamp(created),
        "source_modified_at": iso_timestamp(stat.st_mtime),
        "filesystem_ctime": iso_timestamp(stat.st_ctime),
        "language": None,
        "author_detected": None,
        "organization_detected": None,
        "creator_application": None,
        "modifier_application": None,
        "metadata_confidence": "VERIFICADO_SISTEMA_ARCHIVOS",
    }


def metadata_value(metadata: dict[str, Any], *names: str) -> Any:
    folded = {str(key).casefold(): value for key, value in metadata.items()}
    return next((folded[name.casefold()] for name in names if folded.get(name.casefold()) not in (None, "")), None)


def preliminary_role(path: Path) -> tuple[str, str]:
    ext = path.suffix.lower()
    if is_temporary(path):
        return "TEMPORAL_CACHE", "PATRON_TEMPORAL_DETERMINISTA"
    if ext in BACKUPS:
        return "RESPALDO_COPIA", "EXTENSION_DE_RESPALDO"
    if ext in ACTIVE:
        return "EJECUTABLE_ACTIVO", "EXTENSION_DE_CONTENIDO_ACTIVO"
    if ext in ARCHIVES:
        return "CONTENEDOR", "FORMATO_CONTENEDOR"
    if ext in DATABASES:
        return "BASE_DATOS", "FORMATO_BASE_DE_DATOS"
    if ext in CODE:
        return "CODIGO_FUENTE", "FORMATO_CODIGO_O_CONFIGURACION"
    if ext in AUXILIARY:
        return "ARCHIVO_AUXILIAR", "FORMATO_AUXILIAR"
    return "FUENTE_PRIMARIA", "VALOR_TECNICO_O_INTELECTUAL_INDEPENDIENTE"


def quote_sql_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def extract_pdf(path: Path) -> tuple[list[dict[str, Any]], str, dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    from pypdf import PdfReader
    reader = PdfReader(path)
    records: list[dict[str, Any]] = []
    texts = []
    for index, page in enumerate(reader.pages, 1):
        text = page.extract_text() or ""
        texts.append(text)
        records.append({"record_type": "page", "page_number": index, "text": text})
    metadata = {str(k).lstrip("/"): json_safe(v) for k, v in (reader.metadata or {}).items()}
    warnings = []
    full_text = "\n\f\n".join(texts)
    if not full_text.strip():
        warnings.append(warning("NO_EXTRAIDO", "El PDF no contiene texto extra√≠ble; puede requerir OCR verificado."))
    metrics = {"page_count": len(reader.pages), "text_length": len(full_text)}
    return records, full_text, metrics, warnings, metadata


def extract_docx(path: Path) -> tuple[list[dict[str, Any]], str, dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    from docx import Document
    document = Document(path)
    records: list[dict[str, Any]] = []
    texts = []
    heading_count = 0
    for index, paragraph in enumerate(document.paragraphs, 1):
        text = paragraph.text
        if not text:
            continue
        texts.append(text)
        record_type = "heading" if paragraph.style and paragraph.style.name.startswith("Heading") else "paragraph"
        heading_count += int(record_type == "heading")
        records.append({"record_type": record_type, "paragraph_number": index, "text": text, "style": paragraph.style.name if paragraph.style else None})
    for table_index, table in enumerate(document.tables, 1):
        rows = [[cell.text for cell in row.cells] for row in table.rows]
        records.append({"record_type": "table", "table_number": table_index, "rows": rows})
        texts.extend(" | ".join(row) for row in rows)
    core = document.core_properties
    metadata = {
        "title": core.title or None, "author": core.author or None, "subject": core.subject or None,
        "keywords": core.keywords or None, "comments": core.comments or None,
        "created": json_safe(core.created), "modified": json_safe(core.modified),
    }
    warnings = []
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        if "word/comments.xml" in names:
            warnings.append(warning("COMENTARIOS_DETECTADOS", "Se detectaron comentarios; su contexto puede requerir revisi√≥n manual.", "BAJO"))
        document_xml = archive.read("word/document.xml")
        if b"<w:ins" in document_xml or b"<w:del" in document_xml:
            warnings.append(warning("CONTROL_CAMBIOS_DETECTADO", "Se detect√≥ control de cambios; no fue aceptado ni rechazado."))
        if any(name.startswith("word/embeddings/") for name in names):
            warnings.append(w◊é˘⁄⁄$z{-ÆÈ‹j◊ùW7G'V7GW&Fñ6ñˆÊ¬WáG&:÷&∆RFRf˜&÷FWFW&÷ñÊó7F‚"ê–¢∆ñÊW2ÊWáFVÊBÖ≤""¬"22FF˜2L:ñ6Êñ6˜2&V∆WfÁFW2"¬""¬b"“F÷;Û¢∂÷WFFF≤w6˜W&6U˜6ó¶Uˆ'óFW2u◊÷'óFW2"¬b"“4Ñ”#Sc¢∂ñÁFVw&óGï≤w6˜W&6U˜6Ü#Sbu◊÷"¬""¬"226ñÏ;6Êñ÷˜2"¬"%“ê–¢∆ñÊW2ÊWáFVÊBÜb"“∑f«VW“"f˜"f«VRñ‚7V÷÷'íÊvWBÇ'7ñÊˆÁñ◊2"¬µ“íê–¢ñbÊ˜B7V÷÷'íÊvWBÇ'7ñÊˆÁñ◊2"ì†–¢∆ñÊW2ÊVÊBÇ"“6ñ‚6ñÏ;6Êñ÷˜27W7FVÁFF˜2‚"ê–¢∆ñÊW2ÊWáFVÊBÖ≤""¬"22∆'&26∆fR"¬"%“ê–¢∆ñÊW2ÊWáFVÊBÜb"“∑f«VW“"f˜"f«VRñ‚∂Wóv˜&G2ÊvWBÇ'f«VW2"¬µ“íê–¢ñbÊ˜B∂Wóv˜&G2ÊvWBÇ'f«VW2"ì†–¢∆ñÊW2ÊVÊBÇ"“6ñ‚∆'&26∆fRfW&ñfñ6&∆W2‚"ê–¢∆ñÊW2ÊWáFVÊBÖ≤""¬"22&V∆6ñˆÊW2ˆ'6W'fF2"¬"%“ê–¢ñb&V∆FñˆÁ3†–¢∆ñÊW2ÊWáFVÊBÜb"“∂óFV“ÊvWBÇw&V∆FñˆÂ˜GóRró”¢∂óFV“ÊvWBÇwF&vWEˆfñ∆VÊ÷Rró“á∂óFV“ÊvWBÇw7FGW2r¬tÙ%4U%dDró“í"f˜"óFV“ñ‚&V∆FñˆÁ2ê–¢V«6S†–¢∆ñÊW2ÊVÊBÇ"“ÊÚ6R6ˆÊfó&÷&ˆ‚&V∆6ñˆÊW2WFˆ‹:Fñ62‚"ê–¢∆ñÊW2ÊWáFVÊBÖ≤""¬"22∆ñ÷óF6ñˆÊW2FRWáG&66ú;6‚"¬"%“ê–¢ñbv&ÊñÊw3†–¢∆ñÊW2ÊWáFVÊBÜb"“∂óFV’≤v6ˆFRu◊÷¢∂óFV’≤vFW67&óFñˆ‚u◊“"f˜"óFV“ñ‚v&ÊñÊw2ê–¢V«6S†–¢∆ñÊW2ÊVÊBÇ"“6ñ‚∆ñ÷óF6ñˆÊW2&Vvó7G&F2‚"ê–¢∆ñÊW2ÊWáFVÊBÖ∞–¢""¬"226∆ñFB"¬""¬b"“6ˆ&W'GW&¢∑V∆óGï≤vWáG&7FñˆÂ˜7FGW2u◊÷"¿–¢b"“6ˆÊfñÁ¶¢∑V∆óGï≤vWáG&7FñˆÂˆ6ˆÊfñFVÊ6Ru◊÷"¬b"“GfW'FVÊ6ñ3¢∂∆V‚áv&ÊñÊw2ó÷"¿–¢b"“&Wfó6ú;6‚áV÷Ê¢≤u$T4Ù‘T‰DDrñbV∆óGï≤váV÷Â˜&WfñWu˜&V6ˆ÷÷VÊFVBu“V«6Rtı4îÙ‰¬w÷"¿–¢""¬"22,;7Üñ÷WF"¬""¿–¢$V¬&V7W'6ÚW7L:&W&FÚ&V‚&ˆ6W6Ú˜7FW&ñ˜"FR6∆6ñfñ66ú;6‚RñÊ6˜'˜&6ú;6‚T4ı4ï5DT‘‚W7FRFW&ófFÚÊÚFV6ñFR7RFW7FñÊÚFVfñÊóFófÚ‚"¬""¿–¢“ê–¢&WGW&‚%∆‚"Ê¶ˆñ‚Ü∆ñÊW2ê–†–†–¶FVb6Ü#Se˜FWáBá6˜W&6S¢FÇí”‚7G#†–¢6˜W&6UˆÜ6Ç“6Ü#Seˆfñ∆Rá6˜W&6Rê–¢&WGW&‚%∆‚"Ê¶ˆñ‚Ö∞–¢b"266ÜV÷ˆÊ÷S¢µ44ÑT‘Ù‰‘W“"¿–¢b"266ÜV÷˜fW'6ñˆ„¢µ44ÑT‘ıdU%4îÙÁ“"¿–¢"2'Fñf7E˜GóS¢ñÁFVw&óGí"¿–¢b"26˜W&6Uˆfñ∆VÊ÷S¢∂ß6ˆ‚ÊGV◊2á6˜W&6RÊÊ÷R¬VÁ7W&Uˆ66ñì‘f«6Ró“"¿–¢b"26˜W&6U˜6ó¶Uˆ'óFW3¢∑6˜W&6RÁ7FBÇíÁ7E˜6ó¶W“"¿–¢b"26˜W&6U˜6Ü#Sc¢∑6˜W&6UˆÜ6á“"¿–¢b'∑6˜W&6UˆÜ6á“∑6˜W&6RÊÊ÷W“"¿–¢""¿–¢“ê–†–†–¶FVbvÁG5ˆ÷&∂F˜v‚á&ˆ∆S¢7G"¬&V6˜&G3¢∆ó7E∂Fñ7E∑7G"¬Áï’“í”‚&ˆˆ√†–¢ñb&ˆ∆Rñ‚≤$eTTÂDUı$î‘$î"¬$‘‰îdU5D4îÙÂÙ4Ù4îD"¬$$4UÙDDı2"¬$4ÙDîtıÙeTTÂDR'”†–¢&WGW&‚G'VP–¢ñb&ˆ∆Rñ‚≤$$4ÑïdıÙUÑîƒî""¬$DU$ïdDıÙtT‰U$DÚ'”†–¢6ˆ◊&ó6ˆ‚“fñÊE˜&V6˜&Bá&V6˜&G2¬&6ˆ◊&ó6ˆÂˆfVGW&W2"ê–¢&WGW&‚&ˆˆ¬Ü6ˆ◊&ó6ˆ‚ÊvWBÇ'FWáEˆ∆VÊwFÇ"íê–¢&WGW&‚f«6P–†–†–¶FVb˜WGWE˜Fá2á6˜W&6S¢FÇí”‚Fñ7E∑7G"¬FÖ”†–¢&WGW&‚∞–¢&ß6ˆÊ¬#¢6˜W&6RÁvóFÖˆÊ÷Rá6˜W&6RÊÊ÷R≤"Êß6ˆÊ¬"í¿–¢&÷&∂F˜v‚#¢6˜W&6RÁvóFÖˆÊ÷Rá6˜W&6RÊÊ÷R≤"Ê÷B"í¿–¢'6Ü#Sb#¢6˜W&6RÁvóFÖˆÊ÷Rá6˜W&6RÊÊ÷R≤"Á6Ü#Sb"í¿–¢––†–†–¶FVbf∆ñFFUˆ'VÊF∆Rá7FvS¢FÇ¬6˜W&6S¢FÇ¬ñÊ6«VFUˆß6ˆÊ√¢&ˆˆ¬¬ñÊ6«VFUˆ÷&∂F˜v„¢&ˆˆ¬í”‚ÊˆÊS†–¢Fá2“˜WGWE˜Fá2á6˜W&6Rê–¢7FvVEˆß6ˆÊ¬“7FvRÚFá5≤&ß6ˆÊ¬%“ÊÊ÷P–¢7FvVEˆ÷B“7FvRÚFá5≤&÷&∂F˜v‚%“ÊÊ÷P–¢7FvVE˜6Ü“7FvRÚFá5≤'6Ü#Sb%“ÊÊ÷P–¢ñbÊ˜B7FvVE˜6ÜÊó5ˆfñ∆RÇí˜"7FvVE˜6ÜÁ&VE˜FWáBÜVÊ6ˆFñÊs“'WFb”Ç"í“6Ü#Se˜FWáBá6˜W&6Rì†–¢&ó6Rf«VTW'&˜"Ç$&6ÜófÚ4Ñ”#SbñÁl:∆ñFÚÚÊÚ6˜'&W7ˆÊFR¬˜&ñvñÊ¬‚"ê–¢ñbñÊ6«VFUˆß6ˆÊ√†–¢&V6˜&G2“f∆ñFFUˆß6ˆÊ¬á7FvVEˆß6ˆÊ¬¬6˜W&6Rê–¢ñbñÊ6«VFUˆ÷&∂F˜v„†–¢WáV7FVB“&VÊFW%ˆ÷&∂F˜v‚á&V6˜&G2¬6Ü#Seˆfñ∆Rá7FvVEˆß6ˆÊ¬íê–¢ñb7FvVEˆ÷BÁ&VE˜FWáBÜVÊ6ˆFñÊs“'WFb”Ç"í“WáV7FVC†–¢&ó6Rf«VTW'&˜"Ç$V¬÷&∂F˜v‚ÊÚgVRvVÊW&FÚWÜ6«W6óf÷VÁFRFW6FRV¬•4Ù‰¬f∆ñFFÚ‚"ê–¢V∆ñb7FvVEˆ÷BÊWÜó7G2Çì†–¢&ó6Rf«VTW'&˜"Ç%6RvVÊW,;2÷&∂F˜v‚ÊÚWF˜&ó¶FÚ&W7FR&ˆ¬‚"ê–¢V«6S†–¢ñb7FvVEˆß6ˆÊ¬ÊWÜó7G2Çí˜"7FvVEˆ÷BÊWÜó7G2Çì†–¢&ó6Rf«VTW'&˜"Ç$V¬&ˆ¬6ˆ∆ÚWF˜&ó¶4Ñ”#Sb‚"ê–†–†–¶FVbV&∆ó6Öˆ'VÊF∆Rá7FvS¢FÇ¬6˜W&6S¢FÇ¬FW6ó&VC¢6WE∑7G%“í”‚ÊˆÊS†–¢Fá2“˜WGWE˜Fá2á6˜W&6Rê–¢÷ÊvVB“∂∂Wì¢f«VRf˜"∂Wí¬f«VRñ‚Fá2ÊóFV◊2Çó––¢f˜"FW7FñÊFñˆ‚ñ‚÷ÊvVBÁf«VW2Çì†–¢ñbFW7FñÊFñˆ‚Êó5˜7ñ÷∆ñÊ≤Çí˜"ÜFW7FñÊFñˆ‚ÊWÜó7G2ÇíÊBÊ˜BFW7FñÊFñˆ‚Êó5ˆfñ∆RÇíì†–¢&ó6Rf«VTW'&˜"Üb$6ˆ∆ó6ú;6‚ñÁ6VwW&V‚FW&ófFÚ∆FW&√¢∂FW7FñÊFñˆÁ“"ê–¢&6∑W“FÇáFV◊fñ∆RÊ÷∂GFV◊á&VfóÉ÷b"Á∑6˜W&6RÊÊ÷W“Ê∆Ü“÷&6∑W“"¬Fó#◊6˜W&6RÁ&VÁBíê–¢÷˜fVEˆˆ∆C¢∆ó7E∑GW∆UµFÇ¬FÖ’““µ––¢V&∆ó6ÜVC¢∆ó7EµFÖ““µ––¢∂VWˆ&6∑W“f«6P–¢G'ì†–¢f˜"∂Wí¬FW7FñÊFñˆ‚ñ‚÷ÊvVBÊóFV◊2Çì†–¢ñbFW7FñÊFñˆ‚ÊWÜó7G2Çì†–¢ˆ∆B“&6∑WÚFW7FñÊFñˆ‚ÊÊ÷P–¢˜2Á&W∆6RÜFW7FñÊFñˆ‚¬ˆ∆Bê–¢÷˜fVEˆˆ∆BÊVÊBÇÜˆ∆B¬FW7FñÊFñˆ‚íê–¢f˜"∂Wíñ‚Ç&ß6ˆÊ¬"¬&÷&∂F˜v‚"¬'6Ü#Sb"ì†–¢ñb∂WíÊ˜Bñ‚FW6ó&VC†–¢6ˆÁFñÁVP–¢7FvVB“7FvRÚFá5∂∂Wï“ÊÊ÷P–¢˜2Á&W∆6Rá7FvVB¬Fá5∂∂Wï“ê–¢V&∆ó6ÜVBÊVÊBáFá5∂∂Wï“ê–¢WÜ6WBWÜ6WFñˆ‚2V&∆ó6ÖˆW'&˜#†–¢f˜"FW7FñÊFñˆ‚ñ‚V&∆ó6ÜVC†–¢ñbFW7FñÊFñˆ‚ÊWÜó7G2Çì†–¢FW7FñÊFñˆ‚ÁVÊ∆ñÊ≤Çê–¢&W7F˜&UˆW'&˜'2“µ––¢f˜"ˆ∆B¬FW7FñÊFñˆ‚ñ‚&WfW'6VBÜ÷˜fVEˆˆ∆Bì†–¢ñbˆ∆BÊWÜó7G2Çì†–¢G'ì†–¢˜2Á&W∆6RÜˆ∆B¬FW7FñÊFñˆ‚ê–¢WÜ6WBWÜ6WFñˆ‚2&W7F˜&UˆW'&˜#†–¢&W7F˜&UˆW'&˜'2ÊVÊBÜb'∂FW7FñÊFñˆÁ”¢∑&W7F˜&UˆW'&˜'“"ê–¢ñb&W7F˜&UˆW'&˜'3†–¢∂VWˆ&6∑W“G'VP–¢&ó6R'VÁFñ÷TW'&˜"Ä–¢$f∆Ã;2∆V&∆ñ66ú;6‚∆FW&¬í∆&W7FW&6ú;6‚ÊÚgVR6ˆ◊∆WF≤ –¢b&∆˜2FW&ófF˜2&V7WW&&∆W2W&÷ÊV6V‚V‚∂&6∑W”¢≤s≤rÊ¶ˆñ‚á&W7F˜&UˆW'&˜'2ó“ –¢íg&ˆ“V&∆ó6ÖˆW'&˜ –¢&ó6RV&∆ó6ÖˆW'&˜ –¢fñÊ∆«ì†–¢ñbÊ˜B∂VWˆ&6∑W†–¢6áWFñ¬Á&◊G&VRÜ&6∑W¬ñvÊ˜&UˆW'&˜'3’G'VRê–†–†–¶FVb∆ˆEˆVÁ&ñ6Ü÷VÁBáFÉ¢FÇ¬ÊˆÊRí”‚Fñ7E∑7G"¬Áï”†–¢ñbFÇó2ÊˆÊS†–¢&WGW&‚∑––¢f«VR“ß6ˆ‚Ê∆ˆG2áFÇÁ&VE˜FWáBÜVÊ6ˆFñÊs“'WFb”Ç"íê–¢ñbÊ˜Bó6ñÁ7FÊ6Ráf«VR¬Fñ7Bì†–¢&ó6Rf«VTW'&˜"Ç$V¬VÁ&óVV6ñ÷ñVÁFÚîFV&R6W"V‚ˆ&¶WFÚ˜"'WF&V∆Fóf‚"ê–¢&WGW&‚f«VP–†–†–¶FVb&W&UˆFW67&óF˜'2áF&vWC¢FÇí”‚GW∆UµFÇ¬∆ó7E∂Fñ7E∑7G"¬Áï’’”†–¢&ˆ˜B“F&vWBñbF&vWBÊó5ˆFó"ÇíV«6RF&vWBÁ&VÁ@–¢FW67&óF˜'2“µ––¢f˜"FÇñ‚óFW%˜6˜W&6W2áF&vWBì†–¢&ˆ∆R¬&6ó2“&V∆ñ÷ñÊ'ï˜&ˆ∆RáFÇê–¢FñvW7B“6Ü#Seˆfñ∆RáFÇê–¢FW67&óF˜'2ÊVÊBá≤'FÇ#¢FÇ¬&Ü6Ç#¢FñvW7B¬'6ó¶R#¢FÇÁ7FBÇíÁ7E˜6ó¶R¬'&ˆ∆R#¢&ˆ∆R¬&&6ó2#¢&6ó2¬'7FV“#¢FÇÁ7FV“¬&WáFVÁ6ñˆ‚#¢FÇÁ7VffóÇÊ∆˜vW"Çó“ê–¢'ïˆÜ6É¢Fñ7E∑7G"¬∆ó7E∂Fñ7E∑7G"¬Áï’’““FVfV«FFñ7BÜ∆ó7Bê–¢f˜"óFV“ñ‚FW67&óF˜'3†–¢'ïˆÜ6Ö∂óFV’≤&Ü6Ç%’“ÊVÊBÜóFV“ê–¢f˜"óFV◊2ñ‚'ïˆÜ6ÇÁf«VW2Çì†–¢ñb∆V‚ÜóFV◊2í‚†–¢f˜"GW∆ñ6FRñ‚6˜'FVBÜóFV◊2¬∂Wì÷∆÷&FóFV”¢óFV’≤'FÇ%“Á&V∆FófU˜FÚá&ˆ˜BíÊ5˜˜6óÇÇíï≥•”†–¢GW∆ñ6FU≤'&ˆ∆R%““%$U5ƒDıÙ4ıî –¢GW∆ñ6FU≤&&6ó2%““$EUƒî4DıÙUÑ5Dıı4Ñ#Sb –¢'ï˜7FV”¢Fñ7E∑GW∆UµFÇ¬7G%“¬∆ó7E∂Fñ7E∑7G"¬Áï’’““FVfV«FFñ7BÜ∆ó7Bê–¢f˜"óFV“ñ‚FW67&óF˜'3†–¢'ï˜7FV’≤ÜóFV’≤'FÇ%“Á&VÁB¬óFV’≤'7FV“%“ï“ÊVÊBÜóFV“ê–¢f˜"óFV◊2ñ‚'ï˜7FV“Áf«VW2Çì†–¢FV6ÜÊñ6¬“ÊWáBÇÜóFV“f˜"óFV“ñ‚óFV◊2ñbóFV’≤&WáFVÁ6ñˆ‚%“ñ‚DT4Ñ‰î4≈ı$î‘%íÊBóFV’≤'&ˆ∆R%“”“$eTTÂDUı$î‘$î"í¬ÊˆÊRê–¢ñbFV6ÜÊñ6√†–¢f˜"óFV“ñ‚óFV◊3†–¢ñbóFV“ó2Ê˜BFV6ÜÊñ6¬ÊBóFV’≤&WáFVÁ6ñˆ‚%“ñ‚tT‰U$DTEÙ4‰DîDDU2ÊBóFV’≤'&ˆ∆R%“”“$eTTÂDUı$î‘$î#†–¢óFV’≤'&ˆ∆R%““$DU$ïdDıÙtT‰U$DÚ –¢óFV’≤&&6ó2%““b$‘ï4‘ıÙ‰Ù‘%$UÙ$4UıTU˜∑FV6ÜÊñ6≈≤wFÇu“ÊÊ÷W“ –¢óFV’≤'&V∆Fñˆ‚%““≤'&V∆FñˆÂ˜GóR#¢$tT‰U$Dııı""¬'F&vWEˆfñ∆VÊ÷R#¢FV6ÜÊñ6≈≤'FÇ%“ÊÊ÷R¬'7FGW2#¢%$Ù$$ƒR'––¢V∆ñbóFV’≤'&ˆ∆R%“”“$$4ÑïdıÙUÑîƒî"#†–¢óFV’≤'&V∆Fñˆ‚%““≤'&V∆FñˆÂ˜GóR#¢$DUT‰DUÙDR"¬'F&vWEˆfñ∆VÊ÷R#¢FV6ÜÊñ6≈≤'FÇ%“ÊÊ÷R¬'7FGW2#¢%$Ù$$ƒR'––¢V∆ñbóFV’≤'&ˆ∆R%“”“%$U5ƒDıÙ4ıî#†–¢óFV’≤'&V∆Fñˆ‚%““≤'&V∆FñˆÂ˜GóR#¢%$U5ƒDıÙDR"¬'F&vWEˆfñ∆VÊ÷R#¢FV6ÜÊñ6≈≤'FÇ%“ÊÊ÷R¬'7FGW2#¢%$Ù$$ƒR'––¢V«6S†–¢6ÊFñFFW2“6˜'FVBÄ–¢ÜóFV“f˜"óFV“ñ‚óFV◊2ñbóFV’≤'&ˆ∆R%“”“$eTTÂDUı$î‘$î"í¿–¢∂Wì÷∆÷&FóFV”¢óFV’≤'FÇ%“ÊÊ÷R¿–¢ê–¢ñb∆V‚Ü6ÊFñFFW2í‚†–¢FWáEˆÜ6ÜW3¢Fñ7E∑7G"¬∆ó7E∂Fñ7E∑7G"¬Áï’’““FVfV«FFñ7BÜ∆ó7Bê–¢f˜"óFV“ñ‚6ÊFñFFW3†–¢Ú¬FWáE˜f«VR¬Ú¬Ú¬Ú“FWFW&÷ñÊó7Fñ5ˆWáG&7BÜóFV’≤'FÇ%“¬óFV’≤'&ˆ∆R%“ê–¢Ê˜&÷∆ó¶VB“Ê˜&÷∆ó¶VE˜FWáBáFWáE˜f«VRê–¢ñbÊ˜&÷∆ó¶VC†–¢FWáEˆÜ6ÜW5∂Ü6Ü∆ñ"Á6Ü#SbÜÊ˜&÷∆ó¶VBÊVÊ6ˆFRÇííÊÜWÜFñvW7BÇï“ÊVÊBÜóFV“ê–¢76ˆ6ñFVEˆñG3¢6WE∂ñÁE““6WBÇê–¢f˜"÷F6ÜñÊrñ‚FWáEˆÜ6ÜW2Áf«VW2Çì†–¢ñb∆V‚Ü÷F6ÜñÊrí¬#†–¢6ˆÁFñÁVP–¢6ÊˆÊñ6¬“÷F6ÜñÊu≥––¢f˜"óFV“ñ‚÷F6ÜñÊu≥•”†–¢óFV’≤'&ˆ∆R%““$‘‰îdU5D4îÙÂÙ4Ù4îD –¢óFV’≤&&6ó2%““$‰Ù‘%$UÙ$4UÙUÑ5DııïÙÑ4ÖıDUÖDıÙ‰ı$‘ƒï§DıÙ4Ùî‰4îDTÂDR –¢óFV’≤'&V∆Fñˆ‚%““∞–¢'&V∆FñˆÂ˜GóR#¢$‘‰îdU5D4îÙÂÙDR"¬'F&vWEˆfñ∆VÊ÷R#¢6ÊˆÊñ6≈≤'FÇ%“ÊÊ÷R¿–¢'7FGW2#¢$4Ù‰dï$‘D"¬&WfñFVÊ6R#¢$‰ı$‘ƒï§TEıDUÖEÙÑ4ÖÙ‘D4Ç"¿–¢––¢76ˆ6ñFVEˆñG2ÊFBÜñBÜóFV“íê–¢6ÊˆÊñ6¬“6ÊFñFFW5≥––¢f˜"óFV“ñ‚6ÊFñFFW5≥•”†–¢ñbñBÜóFV“íÊ˜Bñ‚76ˆ6ñFVEˆñG3†–¢óFV’≤'&V∆Fñˆ‚%““∞–¢'&V∆FñˆÂ˜GóR#¢%$Tƒ4îÙ‰DıÙ4Ù‚"¬'F&vWEˆfñ∆VÊ÷R#¢6ÊˆÊñ6≈≤'FÇ%“ÊÊ÷R¿–¢'7FGW2#¢%ı4î$ƒR"¬&WfñFVÊ6R#¢$‰Ù‘%$UÙ$4UÙUÑ5Dıı4îÂÙUdîDT‰4îÙDUÙ4ÙÂDT‰îDıı5Tddî4îTÂDR"¿–¢––¢&WGW&‚&ˆ˜B¬FW67&óF˜'0–†–†–¶FVb&ˆ6W75ˆˆÊRÜóFV”¢Fñ7E∑7G"¬Áï“¬&ˆ˜C¢FÇ¬VÁ&ñ6Ü÷VÁC¢Fñ7E∑7G"¬Áï“¬f˜&6VEˆfñ«W&S¢&ˆˆ¬“f«6Rí”‚Fñ7E∑7G"¬Áï”†–¢6˜W&6S¢FÇ“óFV’≤'FÇ%––¢˜&ñvñÊ≈ˆÜ6Ç“óFV’≤&Ü6Ç%––¢&ˆ∆R“óFV’≤'&ˆ∆R%––¢ñb&ˆ∆R”“%DT’ı$≈Ù44ÑR#†–¢&WGW&‚≤'6˜W&6R#¢7G"á6˜W&6Rí¬'&ˆ∆R#¢&ˆ∆R¬'7FGW2#¢$DUDT5DDıı4îÂÙDU$ïdDı2'––¢ñÊ6«VFUˆß6ˆÊ¬“&ˆ∆R“%$U5ƒDıÙ4ıî –¢7FvR“FÇáFV◊fñ∆RÊ÷∂GFV◊á&VfóÉ÷b"Á∑6˜W&6RÊÊ÷W“Ê∆Ü“◊7FvR“"¬Fó#◊6˜W&6RÁ&VÁBíê–¢G'ì†–¢Fá2“˜WGWE˜Fá2á6˜W&6Rê–¢FW6ó&VB“≤'6Ü#Sb'––¢á7FvRÚFá5≤'6Ü#Sb%“ÊÊ÷RíÁw&óFU˜FWáBá6Ü#Se˜FWáBá6˜W&6Rí¬VÊ6ˆFñÊs“'WFb”Ç"ê–¢ñÊ6«VFUˆ÷B“f«6P–¢ñbñÊ6«VFUˆß6ˆÊ√†–¢&V∆FófR“6˜W&6RÁ&V∆FófU˜FÚá&ˆ˜BíÊ5˜˜6óÇÇíñb&ˆ˜BÊó5ˆFó"ÇíV«6R6˜W&6RÊÊ÷P–¢&V6˜&G2“'Vñ∆E˜&V6˜&G2á6˜W&6R¬&ˆ˜B¬&ˆ∆R¬óFV’≤&&6ó2%“¬∂óFV’≤'&V∆Fñˆ‚%’“ñbóFV“ÊvWBÇ'&V∆Fñˆ‚"íV«6Rµ“¬VÁ&ñ6Ü÷VÁBÊvWBá&V∆FófRíê–¢7FvVEˆß6ˆÊ¬“7FvRÚFá5≤&ß6ˆÊ¬%“ÊÊ÷P–¢w&óFUˆß6ˆÊ¬á7FvVEˆß6ˆÊ¬¬&V6˜&G2ê–¢f∆ñFFUˆß6ˆÊ¬á7FvVEˆß6ˆÊ¬¬6˜W&6Rê–¢FW6ó&VBÊFBÇ&ß6ˆÊ¬"ê–¢ñÊ6«VFUˆ÷B“vÁG5ˆ÷&∂F˜v‚á&ˆ∆R¬&V6˜&G2ê–¢ñbñÊ6«VFUˆ÷C†–¢á7FvRÚFá5≤&÷&∂F˜v‚%“ÊÊ÷RíÁw&óFU˜FWáBá&VÊFW%ˆ÷&∂F˜v‚á&V6˜&G2¬6Ü#Seˆfñ∆Rá7FvVEˆß6ˆÊ¬íí¬VÊ6ˆFñÊs“'WFb”Ç"ê–¢FW6ó&VBÊFBÇ&÷&∂F˜v‚"ê–¢ñbf˜&6VEˆfñ«W&S†–¢&ó6Rf«VTW'&˜"Ç$f∆∆ÚFRf∆ñF6ú;6‚6ˆ∆ñ6óFFÚ&'VV&‚"ê–¢f∆ñFFUˆ'VÊF∆Rá7FvR¬6˜W&6R¬ñÊ6«VFUˆß6ˆÊ¬¬ñÊ6«VFUˆ÷Bê–¢ñb6˜W&6RÁ7FBÇíÁ7E˜6ó¶R“óFV’≤'6ó¶R%“˜"6Ü#Seˆfñ∆Rá6˜W&6Rí“˜&ñvñÊ≈ˆÜ6É†–¢&ó6Rf«VTW'&˜"Ç$V¬˜&ñvñÊ¬6÷&ú;2GW&ÁFRV¬&ˆ6W6÷ñVÁFÛ≤ÊÚ6RV&∆ñ6‚FW&ófF˜2‚"ê–¢V&∆ó6Öˆ'VÊF∆Rá7FvR¬6˜W&6R¬FW6ó&VBê–¢&WGW&‚≤'6˜W&6R#¢7G"á6˜W&6Rí¬'&ˆ∆R#¢&ˆ∆R¬'7FGW2#¢$tT‰U$DÚ"¬&˜WGWG2#¢∑7G"Ü˜WGWE˜Fá2á6˜W&6Rï∂∂Wï“íf˜"∂Wíñ‚6˜'FVBÜFW6ó&VBï“¬&˜&ñvñÊ≈ˆ÷ˆFñfñVB#¢f«6W––¢fñÊ∆«ì†–¢6áWFñ¬Á&◊G&VRá7FvR¬ñvÊ˜&UˆW'&˜'3’G'VRê–†–†–¶FVb&ˆ6W72áF&vWC¢FÇ¬VÁ&ñ6Ü÷VÁE˜FÉ¢FÇ¬ÊˆÊR“ÊˆÊR¬f˜&6VEˆfñ«W&S¢&ˆˆ¬“f«6Rí”‚Fñ7E∑7G"¬Áï”†–¢F&vWB“F&vWBÁ&W6ˆ«fRÇê–¢ñbıUEUEÛÉñ‚F&vWBÁ'G3†–¢&WGW&‚≤&W7FFÚ#¢$$ƒıTTDÚ"¬&÷ˆFÚ#¢$Ù4U54î‰uÙ‘ÙDR¬&÷˜FófÚ#¢b'¥ıUEUEÛÉ“ÊÚVVFR6W"gVVÁFR‚"¬&66ñˆÊW5ˆV¶V7WFF2#¢$ÊñÊwVÊ‚'––¢ñbÊ˜BF&vWBÊWÜó7G2Çí˜"F&vWBÊó5˜7ñ÷∆ñÊ≤Çí˜"Ê˜BáF&vWBÊó5ˆfñ∆RÇí˜"F&vWBÊó5ˆFó"Çíì†–¢&ó6Rf«VTW'&˜"Ç$∆'WFFV&R6W"V‚&6ÜófÚÚ6'WF˜&FñÊ&ñWÜó7FVÁFR‚"ê–¢&ˆ˜B¬FW67&óF˜'2“&W&UˆFW67&óF˜'2áF&vWBê–¢VÁ&ñ6Ü÷VÁB“∆ˆEˆVÁ&ñ6Ü÷VÁBÜVÁ&ñ6Ü÷VÁE˜FÇê–¢&W7V«G2“µ––¢f˜"óFV“ñ‚FW67&óF˜'3†–¢&W7V«G2ÊVÊBá&ˆ6W75ˆˆÊRÜóFV“¬&ˆ˜B¬VÁ&ñ6Ü÷VÁB¬f˜&6VEˆfñ«W&Ríê–¢&WGW&‚∞–¢&W7FFÚ#¢$4Ù’ƒUDDÚ"¬&÷ˆFÚ#¢$Ù4U54î‰uÙ‘ÙDR¬''WFˆÊ∆ó¶F#¢7G"áF&vWBí¿–¢'&V7W'6˜5ˆFWFV7FF˜2#¢∆V‚ÜFW67&óF˜'2í¬'&W7V«FF˜2#¢&W7V«G2¿–¢&˜&ñvñÊ∆W5ˆ÷ˆFñfñ6F˜2#¢f«6R¬'fW'6ñˆÂ˜6∂ñ∆¬#¢4¥îƒ≈ıdU%4îÙ‚¿–¢&Ê˜F#¢$ÊÚ6R6∆6ñfñ6&ˆ‚¬÷˜fñW&ˆ‚¬&VÊˆ÷'&&ˆ‚¬gW6ñˆÊ&ˆ‚ÊíV∆ñ÷ñÊ&ˆ‚˜&ñvñÊ∆W2‚"¿–¢––†–†–¶FVbG'ï˜'V‚áF&vWC¢FÇí”‚Fñ7E∑7G"¬Áï”†–¢F&vWB“F&vWBÁ&W6ˆ«fRÇê–¢ñbıUEUEÛÉñ‚F&vWBÁ'G3†–¢&WGW&‚≤&W7FFÚ#¢$$ƒıTTDÚ"¬&÷ˆFÚ#¢$Ù4U54î‰uÙ‘ÙDR¬&÷˜FófÚ#¢b'¥ıUEUEÛÉ“ÊÚVVFR6W"gVVÁFR‚'––¢&ˆ˜B¬FW67&óF˜'2“&W&UˆFW67&óF˜'2áF&vWBê–¢&WGW&‚∞–¢&W7FFÚ#¢$$Ù$DÚ"¬&÷ˆFÚ#¢$Ù4U54î‰uÙ‘ÙDR¬''WFˆÊ∆ó¶F#¢7G"áF&vWBí¿–¢'&V7W'6˜2#¢∞–¢≤''WF˜&V∆Fóf#¢óFV’≤'FÇ%“Á&V∆FófU˜FÚá&ˆ˜BíÊ5˜˜6óÇÇíñb&ˆ˜BÊó5ˆFó"ÇíV«6RóFV’≤'FÇ%“ÊÊ÷R¬'&ˆ∆R#¢óFV’≤'&ˆ∆R%“¬&&6ó2#¢óFV’≤&&6ó2%◊––¢f˜"óFV“ñ‚FW67&óF˜'0–¢“¿–¢&FW7FñÊÚ#¢$DU$ïdDı5ÙƒDU$ƒU5Ù•TÂDıÙÙ4DÙı$îtî‰¬"¿–¢––†–†–¶FVb÷ñ‚Çí”‚ñÁC†–¢'6W"“&w'6R‰&wV÷VÁE'6W"ÜFW67&óFñˆ„’ıˆFˆ5ıÚê–¢'6W"ÊFEˆ&wV÷VÁBÇ''WF"¬GóS’FÇê–¢'6W"ÊFEˆ&wV÷VÁBÇ"“÷G'í◊'V‚"¬7Fñˆ„“'7F˜&U˜G'VR"ê–¢'6W"ÊFEˆ&wV÷VÁBÇ"“÷í÷VÁ&ñ6Ü÷VÁB"¬GóS’FÇê–¢'6W"ÊFEˆ&wV÷VÁBÇ"“÷f˜&6R◊f∆ñFFñˆ‚÷fñ«W&R"¬7Fñˆ„“'7F˜&U˜G'VR"¬ÜV«÷&w'6RÂ5U$U52ê–¢&w2“'6W"Á'6Uˆ&w2Çê–¢G'ì†–¢&W˜'B“G'ï˜'V‚Ü&w2Á'WFíñb&w2ÊG'ï˜'V‚V«6R&ˆ6W72Ü&w2Á'WF¬&w2ÊïˆVÁ&ñ6Ü÷VÁB¬&w2Êf˜&6U˜f∆ñFFñˆÂˆfñ«W&Rê–¢WÜ6WBWÜ6WFñˆ‚2WÜ3†–¢&W˜'B“≤&W7FFÚ#¢$U%$ı""¬&÷ˆFÚ#¢$Ù4U54î‰uÙ‘ÙDR¬&÷˜FófÚ#¢b'∑GóRÜWÜ2íÂıˆÊ÷Uı˜”¢∂WÜ7“"¬&66ñˆÊW2#¢$ÊÚ6RV&∆ñ6&ˆ‚FW&ófF˜2ñÊ6ˆ◊∆WF˜2‚'––¢&ñÁBÜß6ˆ‚ÊGV◊2á&W˜'B¬VÁ7W&Uˆ66ñì‘f«6R¬ñÊFVÁC”"íê–¢&WGW&‚–¢&ñÁBÜß6ˆ‚ÊGV◊2á&W˜'B¬VÁ7W&Uˆ66ñì‘f«6R¬ñÊFVÁC”"íê–¢&WGW&‚"ñb&W˜'E≤&W7FFÚ%“”“$$ƒıTTDÚ"V«6R –†–†–¶ñbıˆÊ÷UıÚ”“%ıˆ÷ñÂıÚ#†–¢&ó6R7ó7FV‘WÜóBÜ÷ñ‚Çíê–