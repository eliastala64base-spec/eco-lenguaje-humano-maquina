Exit code: 0
Wall time: 0.3 seconds
Output:
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "generar_panel.py"


class GenerarPanelTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.photos = self.root / "photos"
        self.output = self.root / "output"
        self.photos.mkdir()
        photo = self.photos / "CTM-RF-OCI-VAR-PAN-20260813-0001.jpg"
        photo.write_bytes(b"evidencia-fotografica-prueba")
        digest = hashlib.sha256(photo.read_bytes()).hexdigest()
        record = {
            "ruta_relativa": photo.name,
            "sha256": digest,
            "fecha": {"fecha_efectiva": "2026-08-13"},
            "clasificacion": {"clasificaciones": [{"codigo": "OCI-VAR-PAN"}]},
            "guia_humana": {"descripcion_manual": "InstalaciÃ³n de panel de junta"},
        }
        self.catalog = self.root / "catalogo.jsonl"
        self.catalog.write_text(json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def run_cli(self, *extra):
        command = [
            sys.executable,
            str(SCRIPT),
            "--project-root", str(self.photos),
            "--catalog", str(self.catalog),
            "--output-root", str(self.output),
            "--panel-id", "PF-PRUEBA-001",
            "--code", "OCI-VAR-PAN",
            *extra,
        ]
        return subprocess.run(command, text=True, capture_output=True, encoding="utf-8")

    def test_dry_run_does_not_create_output(self):
        result = self.run_cli("--dry-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.output / "PF-PRUEBA-001").exists())
        self.assertTrue(json.loads(result.stdout)["source_files_modified"] is False)

    def test_generation_is_traceable_and_refuses_overwrite(self):
        first = self.run_cli()
        self.assertEqual(first.returncode, 0, first.stderr)
        package = self.output / "PF-PRUEBA-001"
        panel = json.loads((package / "panel.json").read_text(encoding="utf-8"))
        self.assertEqual(panel["state"], "BORRADOR")
        self.assertEqual(panel["photos"][0]["matched_codes"], ["OCI-VAR-PAN"])
        self.assertTrue((package / "checksums.sha256").is_file())
        second = self.run_cli()
        self.assertNotEqual(second.returncode, 0)
        self.assertIn("El paquete ya existe", second.stderr)


if __name__ == "__main__":
    unittest.main()

