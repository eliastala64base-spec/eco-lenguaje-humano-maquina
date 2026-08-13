Exit code: 0
Wall time: 0.3 seconds
Output:
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import html
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

VERSION = "0.1.0-alpha.1"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_jsonl(path: Path) -> list[dict]:
    records = []
    for number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"La lÃ­nea {number} no contiene un objeto JSON")
        records.append(value)
    return records


def codes_for(record: dict) -> set[str]:
    classification = record.get("clasificacion") or {}
    values: set[str] = set()
    for item in classification.get("clasificaciones") or []:
        if isinstance(item, dict) and item.get("codigo"):
            values.add(str(item["codigo"]).upper())
    for key in ("codigos_explicitos", "indices_consulta"):
        for value in classification.get(key) or []:
            if isinstance(value, str):
                values.add(value.upper())
    for item in classification.get("relaciones_contextuales") or []:
        if isinstance(item, str):
            values.add(item.upper())
        elif isinstance(item, dict):
            for key in ("codigo", "related_code", "code"):
                if item.get(key):
                    values.add(str(item[key]).upper())
    return values


def record_path(project_root: Path, record: dict) -> Path:
    value = record.get("ruta_relativa") or record.get("nombre_actual") or record.get("nombre_controlado")
    if not value:
        raise ValueError("Registro sin ruta o nombre de fotografÃ­a")
    candidate = (project_root / str(value)).resolve()
    candidate.relative_to(project_root.resolve())
    return candidate


def description_for(record: dict) -> str:
    guide = record.get("guia_humana") or {}
    text = guide.get("descripcion_manual") or record.get("descripcion_aprobada") or record.get("descripcion_propuesta")
    return str(text or "DescripciÃ³n pendiente de revisiÃ³n humana").strip()


def effective_date(record: dict) -> str:
    date = record.get("fecha") or {}
    return str(date.get("fecha_efectiva") or record.get("fecha_efectiva") or "99999999")


def render_html(panel: dict) -> str:
    cards = []
    for item in panel["photos"]:
        cards.append(
            '<figure class="photo">'
            f'<img src="{html.escape(item["media_path"])}" alt="{html.escape(item["description"])}">'
            f'<figcaption>{html.escape(item["description"])}<small>{html.escape(item["controlled_name"])}</small></figcaption>'
            '</figure>'
        )
    return f'''<!doctype html>
<html lang="es"><head><meta charset="utf-8"><title>{html.escape(panel["title"])}</title>
<style>
@page {{ size: A4 portrait; margin: 12mm; }}
* {{ box-sizing: border-box; }} body {{ margin: 0; font-family: Arial, sans-serif; color: #111; }}
.page {{ width: 186mm; min-height: 273mm; margin: auto; display: grid; grid-template-rows: auto 1fr auto; gap: 4mm; }}
header {{ border: 1px solid #222; display: grid; grid-template-columns: 32mm 1fr; }}
header strong {{ background: #edf3f6; padding: 2mm; border-right: 1px solid #222; }} header span {{ padding: 2mm; }}
.meta {{ display: grid; grid-template-columns: 1fr 1fr; border: 1px solid #222; border-top: 0; font-size: 9pt; }}
.meta div {{ padding: 1.5mm 2mm; border-right: 1px solid #ccc; }}
.photos {{ display: grid; grid-template-columns: 1fr 1fr; grid-template-rows: repeat(3, 1fr); gap: 3mm; }}
.photo {{ margin: 0; border: 1px solid #333; display: grid; grid-template-rows: 1fr auto; min-height: 72mm; overflow: hidden; }}
.photo img {{ width: 100%; height: 100%; object-fit: contain; min-height: 58mm; background: #f5f5f5; }}
figcaption {{ border-top: 1px solid #333; padding: 1.5mm 2mm; font-size: 8.5pt; min-height: 12mm; }}
figcaption small {{ display: block; color: #555; margin-top: 1mm; font-size: 7pt; }}
footer {{ border: 1px solid #222; padding: 2mm; font-size: 8pt; display: flex; justify-content: space-between; }}
</style></head><body><main class="page">
<section><header><strong>Panel fotogrÃ¡fico</strong><span>{html.escape(panel["title"])}</span></header>
<div class="meta"><div><b>Proyecto:</b> {html.escape(panel["project_name"])}</div><div><b>Cliente:</b> {html.escape(panel["client"])}</div>
<div><b>Componente:</b> {html.escape(panel["component"])}</div><div><b>Ãrea:</b> {html.escape(panel["area"])}</div></div></section>
<section class="photos">{''.join(cards)}</section>
<footer><span>{html.escape(panel["panel_id"])}</span><span>BORRADOR Â· revisiÃ³n humana pendiente</span></footer>
</main></body></html>'''


def main() -> int:
    parser = argparse.ArgumentParser(description="Genera un paquete HTML de panel fotogrÃ¡fico trazable")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--panel-id", required=True)
    parser.add_argument("--code", action="append", required=True)
    parser.add_argument("--limit", type=int, default=6)
    parser.add_argument("--project-name", default="PENDIENTE")
    parser.add_argument("--client", default="PENDIENTE")
    parser.add_argument("--component", default="PENDIENTE")
    parser.add_argument("--area", default="PENDIENTE")
    parser.add_argument("--title", default="Registro fotogrÃ¡fico")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    catalog = Path(args.catalog).resolve()
    output = Path(args.output_root).resolve() / args.panel_id
    requested = {value.upper() for value in args.code}
    if args.limit < 1 or args.limit > 6:
        raise ValueError("--limit debe estar entre 1 y 6 para v0.1.0-alpha.1")
    if output.exists():
        raise FileExistsError(f"El paquete ya existe: {output}")

    candidates = []
    failures = []
    for record in load_jsonl(catalog):
        if not (codes_for(record) & requested):
            continue
        try:
            source = record_path(root, record)
            if not source.is_file():
                raise FileNotFoundError(str(source))
            expected = str(record.get("sha256") or record.get("foto_id") or "").lower()
            actual = sha256(source)
            if expected and actual != expected:
                raise ValueError("SHA-256 no coincide")
            candidates.append((effective_date(record), source.name.casefold(), record, source, actual))
        except Exception as error:
            failures.append({"record": record.get("nombre_actual"), "error": str(error)})
    candidates.sort(key=lambda item: (item[0], item[1]))
    selected = candidates[: args.limit]
    report = {
        "mode": "DRY_RUN" if args.dry_run else "GENERATE",
        "generator_version": VERSION,
        "panel_id": args.panel_id,
        "requested_codes": sorted(requested),
        "candidate_count": len(candidates),
        "selected_count": len(selected),
        "failures": failures,
        "selected": [item[3].name for item in selected],
        "source_files_modified": False,
    }
    if failures or not selected:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1
    if args.dry_run:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    media = output / "media"
    media.mkdir(parents=True)
    photos = []
    for index, (_, _, record, source, digest) in enumerate(selected, 1):
        target = media / source.name
        shutil.copy2(source, target)
        if sha256(target) != digest or sha256(source) != digest:
            raise RuntimeError(f"FallÃ³ la verificaciÃ³n de copia: {source.name}")
        photos.append({
            "order": index,
            "source_path": str(source),
            "controlled_name": source.name,
            "sha256": digest,
            "media_path": f"media/{source.name}",
            "effective_date": effective_date(record),
            "description": description_for(record),
            "matched_codes": sorted(codes_for(record) & requested),
        })
    panel = {
        "schema_version": 1,
        "generator": {"component": "generar-panel-fotografico", "version": VERSION},
        "panel_id": args.panel_id,
        "state": "BORRADOR",
        "publication_state": "RESTRINGIDO",
        "approval_state": "PENDIENTE_REVISION_HUMANA",
        "title": args.title,
        "project_name": args.project_name,
        "client": args.client,
        "component": args.component,
        "area": args.area,
        "requested_codes": sorted(requested),
        "catalog": {"path": str(catalog), "sha256": sha256(catalog)},
        "photos": photos,
        "source_files_modified": False,
    }
    (output / "panel.json").write_text(json.dumps(panel, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "panel.html").write_text(render_html(panel), encoding="utf-8")
    manifest_files = []
    for path in sorted(p for p in output.rglob("*") if p.is_file()):
        manifest_files.append({"path": path.relative_to(output).as_posix(), "bytes": path.stat().st_size, "sha256": sha256(path)})
    manifest = {"schema_version": 1, "generated_at": datetime.now(timezone.utc).isoformat(), "panel_id": args.panel_id, "generator_version": VERSION, "files": manifest_files}
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    checksum_paths = sorted(p for p in output.rglob("*") if p.is_file() and p.name != "checksums.sha256")
    (output / "checksums.sha256").write_text("".join(f"{sha256(p)}  {p.relative_to(output).as_posix()}\n" for p in checksum_paths), encoding="utf-8")
    report["output"] = str(output)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

