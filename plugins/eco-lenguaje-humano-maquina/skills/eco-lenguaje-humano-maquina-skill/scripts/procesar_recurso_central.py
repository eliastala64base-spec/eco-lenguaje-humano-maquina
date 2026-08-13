#!/usr/bin/env python3
"""Genera derivados centralizados por proyecto o area sin tocar los originales."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import procesar_recurso_lateral as base


SKILL_VERSION = "0.5.0-beta.1"
PROCESSING_MODE = "RECURSO_CENTRALIZADO"
OUTPUT_NAME = "80_LENGUAJE_HUMANO_MAQUINA"
CONTROL_NAME = "99_CONTROL"
PROFILE_VERSION = "central-static-v1"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def json_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def find_container(target: Path) -> Path:
    start = target if target.is_dir() else target.parent
    for candidate in (start, *start.parents):
        if (candidate / "00_PROYECTO.md").is_file() or any(candidate.glob("00_GUIA_*.md")):
            return candidate
    return start


def resolve_output(target: Path, requested: Path | None) -> Path:
    output = requested.resolve() if requested else find_container(target) / OUTPUT_NAME
    if output.name != OUTPUT_NAME:
        raise ValueError(f"El almacén derivado debe llamarse exactamente {OUTPUT_NAME}.")
    container = output.parent
    conflicts = [
        child.name
        for child in container.iterdir()
        if child.name.startswith("80_") and child.name != OUTPUT_NAME
    ] if container.is_dir() else []
    if conflicts:
        raise ValueError(f"El prefijo 80 está reservado; conflictos detectados: {conflicts}")
    return output


def processing_fingerprint(
    source_hash: str,
    configuration_hash: str,
    enrichment: dict[str, Any] | None,
) -> str:
    return json_hash(
        {
            "source_sha256": source_hash,
            "skill_version": SKILL_VERSION,
            "schema_version": base.SCHEMA_VERSION,
            "processing_mode": PROCESSING_MODE,
            "extractor_profile": PROFILE_VERSION,
            "configuration_hash": configuration_hash,
            "enrichment_hash": json_hash(enrichment) if enrichment else None,
        }
    )


def package_path(output: Path, source_hash: str, fingerprint: str) -> Path:
    return output / "RECURSOS" / source_hash[:2] / source_hash / fingerprint


def checksum_text(source: Path) -> str:
    return (
        f"# schema_name: {base.SCHEMA_NAME}\n"
        f"# schema_version: {base.SCHEMA_VERSION}\n"
        f"# artifact_type: source_integrity\n"
        f"# source_filename: {source.name}\n"
        f"# source_size_bytes: {source.stat().st_size}\n"
        f"# source_sha256: {base.sha256_file(source)}\n"
        f"{base.sha256_file(source)}  {source.name}\n"
    )


def graph_record(source: Path, relative: str, source_hash: str, fingerprint: str) -> dict[str, Any]:
    return {
        "@context": {
            "name": "https://schema.org/name",
            "contentSize": "https://schema.org/contentSize",
            "sha256": "https://schema.org/sha256",
            "sourcePath": "https://schema.org/contentUrl",
            "processingFingerprint": "urn:eco:processingFingerprint",
        },
        "@id": f"urn:sha256:{source_hash}",
        "@type": "https://schema.org/DigitalDocument",
        "name": source.name,
        "contentSize": source.stat().st_size,
        "sha256": source_hash,
        "sourcePath": relative,
        "processingFingerprint": fingerprint,
    }


def validate_package(package: Path, source: Path, fingerprint: str) -> list[dict[str, Any]]:
    jsonl = package / "recurso.jsonl"
    records = base.validate_jsonl(jsonl, source, PROCESSING_MODE)
    manifest = base.find_record(records, "manifest")
    if manifest.get("processing_fingerprint") != fingerprint:
        raise ValueError("El fingerprint del paquete no corresponde al procesamiento solicitado.")
    if (package / "lectura.md").exists():
        expected = base.render_markdown(records, base.sha256_file(jsonl))
        if (package / "lectura.md").read_text(encoding="utf-8") != expected:
            raise ValueError("La vista Markdown no deriva del JSONL validado.")
    if (package / "integridad.sha256").read_text(encoding="utf-8") != checksum_text(source):
        raise ValueError("La integridad declarada no corresponde al original.")
    json.loads((package / "relaciones.jsonld").read_text(encoding="utf-8"))
    json.loads((package / "calidad.json").read_text(encoding="utf-8"))
    return records


def publish_package(stage: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    backup = destination.with_name(destination.name + ".previous")
    if backup.exists():
        shutil.rmtree(backup)
    if destination.exists():
        os.replace(destination, backup)
    try:
        os.replace(stage, destination)
    except Exception:
        if backup.exists() and not destination.exists():
            os.replace(backup, destination)
        raise
    if backup.exists():
        shutil.rmtree(backup)


def build_package(
    item: dict[str, Any],
    container: Path,
    output: Path,
    enrichment: dict[str, Any],
    configuration_hash: str,
    forced_failure: bool = False,
) -> dict[str, Any]:
    source: Path = item["path"]
    source_hash = item["hash"]
    original_size = item["size"]
    try:
        relative = source.relative_to(container).as_posix()
    except ValueError as exc:
        raise ValueError("La fuente debe estar dentro del proyecto o área propietario de la carpeta 80.") from exc
    source_enrichment = enrichment.get(relative) if enrichment else None
    fingerprint = processing_fingerprint(source_hash, configuration_hash, source_enrichment)
    destination = package_path(output, source_hash, fingerprint)
    if destination.is_dir():
        try:
            validate_package(destination, source, fingerprint)
            return {
                "source": str(source), "source_relative_path": relative,
                "source_sha256": source_hash, "processing_fingerprint": fingerprint,
                "status": "OMITIDO_FINGERPRINT_VIGENTE", "package": str(destination),
            }
        except Exception:
            pass
    stage_parent = destination.parent
    stage_parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".lhm-central-stage-", dir=stage_parent))
    try:
        metadata = {
            "processing_fingerprint": fingerprint,
            "extractor_profile": PROFILE_VERSION,
            "configuration_hash": configuration_hash,
        }
        records = base.build_records(
            source,
            container,
            item["role"],
            item["basis"],
            [item["relation"]] if item.get("relation") else [],
            source_enrichment,
            PROCESSING_MODE,
            metadata,
        )
        jsonl = stage / "recurso.jsonl"
        base.write_jsonl(jsonl, records)
        base.validate_jsonl(jsonl, source, PROCESSING_MODE)
        if base.wants_markdown(item["role"], records):
            (stage / "lectura.md").write_text(
                base.render_markdown(records, base.sha256_file(jsonl)), encoding="utf-8"
            )
        (stage / "integridad.sha256").write_text(checksum_text(source), encoding="utf-8")
        write_json(stage / "relaciones.jsonld", graph_record(source, relative, source_hash, fingerprint))
        write_json(
            stage / "calidad.json",
            {
                "quality": base.find_record(records, "quality"),
                "warnings": [record for record in records if record["record_type"] == "warning"],
            },
        )
        if forced_failure:
            raise ValueError("Fallo de validación solicitado para prueba.")
        validate_package(stage, source, fingerprint)
        if source.stat().st_size != original_size or base.sha256_file(source) != source_hash:
            raise ValueError("El original cambió durante el procesamiento; no se publica el paquete.")
        publish_package(stage, destination)
        return {
            "source": str(source), "source_relative_path": relative,
            "source_sha256": source_hash, "processing_fingerprint": fingerprint,
            "status": "GENERADO", "package": str(destination),
        }
    finally:
        if stage.exists():
            shutil.rmtree(stage, ignore_errors=True)


def read_manifest(path: Path) -> dict[tuple[str, str, str], dict[str, Any]]:
    records: dict[tuple[str, str, str], dict[str, Any]] = {}
    if not path.is_file():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        key = (
            str(record.get("source_relative_path")),
            str(record.get("source_sha256")),
            str(record.get("processing_fingerprint")),
        )
        records[key] = record
    return records


def update_control(output: Path, results: list[dict[str, Any]]) -> None:
    control = output / CONTROL_NAME
    control.mkdir(parents=True, exist_ok=True)
    manifest_path = control / "MANIFEST.jsonl"
    records = read_manifest(manifest_path)
    now = utc_now()
    for result in results:
        if "source_relative_path" not in result:
            continue
        record = {
            "source_relative_path": result["source_relative_path"],
            "source_sha256": result["source_sha256"],
            "processing_fingerprint": result["processing_fingerprint"],
            "package": Path(result["package"]).relative_to(output).as_posix(),
            "last_seen_at": now,
            "status": result["status"],
        }
        records[(record["source_relative_path"], record["source_sha256"], record["processing_fingerprint"])] = record
    manifest_path.write_text(
        "".join(json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n" for value in sorted(records.values(), key=lambda item: (item["source_relative_path"], item["processing_fingerprint"]))),
        encoding="utf-8",
    )
    with (control / "EVENTOS.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"event": "CENTRAL_PROCESSING", "occurred_at": now, "skill_version": SKILL_VERSION, "results": len(results)}, ensure_ascii=False, separators=(",", ":")) + "\n")
    index = ["# Lenguaje Humano–Máquina", "", "Derivados centralizados; los originales conservan autoridad.", ""]
    for record in sorted(records.values(), key=lambda item: item["source_relative_path"]):
        link = f"{record['package']}/lectura.md"
        index.append(f"- [{record['source_relative_path']}]({link}) — `{record['source_sha256'][:12]}`")
    (output / "00_INDICE.md").write_text("\n".join(index) + "\n", encoding="utf-8")
    checksum_file = control / "CHECKSUMS.sha256"
    files = [path for path in sorted(output.rglob("*")) if path.is_file() and path != checksum_file]
    checksum_file.write_text("\n".join(f"{base.sha256_file(path)}  {path.relative_to(output).as_posix()}" for path in files) + "\n", encoding="utf-8")


def validate_target(target: Path, output: Path) -> None:
    if OUTPUT_NAME in target.parts:
        raise ValueError(f"{OUTPUT_NAME} no puede utilizarse como fuente.")
    if not target.exists() or target.is_symlink() or not (target.is_file() or target.is_dir()):
        raise ValueError("La ruta debe ser un archivo o carpeta ordinaria existente.")
    if output.exists() and (not output.is_dir() or output.is_symlink()):
        raise ValueError("El destino 80 existente no es una carpeta ordinaria segura.")


def prepare(
    target: Path,
    output_root: Path | None,
    configuration_hash: str,
) -> tuple[Path, Path, list[dict[str, Any]], list[dict[str, Any]]]:
    target = target.resolve()
    output = resolve_output(target, output_root)
    validate_target(target, output)
    container = output.parent
    _, descriptors = base.prepare_descriptors(target)
    plan = []
    for item in descriptors:
        source: Path = item["path"]
        relative = source.relative_to(container).as_posix()
        fingerprint = processing_fingerprint(item["hash"], configuration_hash, None)
        destination = package_path(output, item["hash"], fingerprint)
        plan.append({
            "source_relative_path": relative,
            "source_sha256": item["hash"],
            "processing_fingerprint": fingerprint,
            "planned_package": str(destination),
            "status": "OMITIR_SI_VALIDO" if destination.is_dir() else "GENERAR",
        })
    return target, output, descriptors, plan


def process(
    target: Path,
    output_root: Path | None = None,
    enrichment_path: Path | None = None,
    configuration_hash: str = "DEFAULT",
    forced_failure: bool = False,
) -> dict[str, Any]:
    target, output, descriptors, _ = prepare(target, output_root, configuration_hash)
    enrichment = base.load_enrichment(enrichment_path)
    results = [
        build_package(item, output.parent, output, enrichment, configuration_hash, forced_failure)
        for item in descriptors
        if item["role"] != "TEMPORAL_CACHE"
    ]
    output.mkdir(parents=True, exist_ok=True)
    update_control(output, results)
    return {
        "estado": "COMPLETADO", "modo": PROCESSING_MODE,
        "ruta_analizada": str(target), "destino": str(output),
        "recursos_detectados": len(descriptors), "resultados": results,
        "originales_modificados": False, "version_skill": SKILL_VERSION,
    }


def dry_run(
    target: Path,
    output_root: Path | None = None,
    configuration_hash: str = "DEFAULT",
) -> dict[str, Any]:
    target, output, descriptors, plan = prepare(target, output_root, configuration_hash)
    return {
        "estado": "APROBADO", "modo": PROCESSING_MODE,
        "ruta_analizada": str(target), "destino": str(output),
        "recursos_detectados": len(descriptors), "plan": plan,
        "originales_modificados": False, "version_skill": SKILL_VERSION,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ruta", type=Path)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--configuration-hash", default="DEFAULT")
    parser.add_argument("--ai-enrichment", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force-validation-failure", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        report = dry_run(args.ruta, args.output_root, args.configuration_hash) if args.dry_run else process(
            args.ruta, args.output_root, args.ai_enrichment, args.configuration_hash, args.force_validation_failure
        )
    except Exception as exc:
        report = {"estado": "ERROR", "modo": PROCESSING_MODE, "motivo": f"{type(exc).__name__}: {exc}", "acciones": "No se publicaron derivados incompletos."}
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
