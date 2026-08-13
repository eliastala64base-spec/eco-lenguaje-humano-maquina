import hashlib
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

import procesar_recurso_central as central  # noqa: E402


class RecursoCentralTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.project = Path(self.temp.name) / "PROYECTO_PRUEBA"
        self.project.mkdir()
        (self.project / "00_PROYECTO.md").write_text("# Proyecto\n", encoding="utf-8")
        self.sources = self.project / "01_FUENTES"
        self.sources.mkdir()
        self.source = self.sources / "Manual.txt"
        self.source.write_text("Contenido tecnico de prueba.\n", encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_centraliza_sin_crear_derivados_laterales(self):
        before = hashlib.sha256(self.source.read_bytes()).hexdigest()
        report = central.process(self.sources)
        self.assertEqual(report["estado"], "COMPLETADO")
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(), before)
        self.assertFalse(self.source.with_name(self.source.name + ".jsonl").exists())
        self.assertFalse(self.source.with_name(self.source.name + ".md").exists())
        self.assertFalse(self.source.with_name(self.source.name + ".sha256").exists())
        output = self.project / central.OUTPUT_NAME
        self.assertTrue((output / "00_INDICE.md").is_file())
        self.assertTrue((output / central.CONTROL_NAME / "MANIFEST.jsonl").is_file())
        package = Path(report["resultados"][0]["package"])
        self.assertTrue((package / "recurso.jsonl").is_file())
        self.assertTrue((package / "lectura.md").is_file())
        self.assertTrue((package / "relaciones.jsonld").is_file())
        self.assertTrue((package / "calidad.json").is_file())

    def test_repite_sin_reprocesar_si_fingerprint_sigue_vigente(self):
        first = central.process(self.sources)
        second = central.process(self.sources)
        self.assertEqual(first["resultados"][0]["status"], "GENERADO")
        self.assertEqual(second["resultados"][0]["status"], "OMITIDO_FINGERPRINT_VIGENTE")
        self.assertEqual(first["resultados"][0]["package"], second["resultados"][0]["package"])

    def test_cambio_configuracion_genera_nuevo_fingerprint_sin_tocar_original(self):
        before = hashlib.sha256(self.source.read_bytes()).hexdigest()
        first = central.process(self.sources, configuration_hash="CONFIG-A")
        second = central.process(self.sources, configuration_hash="CONFIG-B")
        self.assertNotEqual(
            first["resultados"][0]["processing_fingerprint"],
            second["resultados"][0]["processing_fingerprint"],
        )
        self.assertTrue(Path(first["resultados"][0]["package"]).is_dir())
        self.assertTrue(Path(second["resultados"][0]["package"]).is_dir())
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(), before)

    def test_prefijos_altos_quedan_reservados(self):
        central.process(self.sources)
        high = [
            path.name
            for path in self.project.rglob("*")
            if path.is_dir() and path.name[:2].isdigit() and int(path.name[:2]) >= 50
        ]
        self.assertEqual(sorted(set(high)), ["80_LENGUAJE_HUMANO_MAQUINA", "99_CONTROL"])

    def test_output_root_debe_usar_nombre_reservado(self):
        with self.assertRaisesRegex(ValueError, "exactamente"):
            central.dry_run(self.sources, self.project / "80_OTRO_USO")

    def test_fallo_no_publica_paquete_incompleto(self):
        with self.assertRaisesRegex(ValueError, "Fallo de validación"):
            central.process(self.sources, forced_failure=True)
        output = self.project / central.OUTPUT_NAME
        self.assertFalse(any(output.rglob("recurso.jsonl")))


if __name__ == "__main__":
    unittest.main()
