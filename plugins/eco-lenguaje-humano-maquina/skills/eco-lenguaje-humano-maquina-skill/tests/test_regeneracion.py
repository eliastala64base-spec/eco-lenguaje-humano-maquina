import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pypdf import PdfWriter

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("lhm", ROOT / "scripts" / "convertir_lenguaje_humano_maquina.py")
lhm = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(lhm)


def checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_blank_pdf(path: Path) -> None:
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    with path.open("wb") as stream:
        writer.write(stream)


class Regeneracion80Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "documento"
        self.root.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def test_direct_80_is_replaced_not_merged(self):
        (self.root / "MATRIZ.xlsx").write_text("A,B\n1,2\n", encoding="utf-8")
        old = self.root / lhm.OUTPUT_NAME
        old.mkdir()
        (old / "obsoleto.txt").write_text("viejo", encoding="utf-8")
        result = lhm.generate(self.root)
        self.assertEqual(result["resultado"], "REGENERADO")
        self.assertFalse((old / "obsoleto.txt").exists())
        self.assertTrue((old / "MATRIZ" / "00_DOCUMENTO.md").is_file())

    def test_nested_80_blocks_without_partial_output(self):
        child = self.root / "RE-P-01"
        (child / lhm.OUTPUT_NAME).mkdir(parents=True)
        (child / lhm.OUTPUT_NAME / "existente.txt").write_text("no tocar", encoding="utf-8")
        report = lhm.generate(self.root)
        self.assertEqual(report["estado"], "BLOQUEADO")
        self.assertFalse((self.root / lhm.OUTPUT_NAME).exists())
        self.assertTrue((child / lhm.OUTPUT_NAME / "existente.txt").exists())

    def test_nested_80_also_preserves_existing_direct_80(self):
        direct = self.root / lhm.OUTPUT_NAME
        direct.mkdir()
        (direct / "vigente.txt").write_text("conservar", encoding="utf-8")
        child = self.root / "RE-P-01" / lhm.OUTPUT_NAME
        child.mkdir(parents=True)
        report = lhm.generate(self.root)
        self.assertEqual(report["estado"], "BLOQUEADO")
        self.assertEqual((direct / "vigente.txt").read_text(encoding="utf-8"), "conservar")
        self.assertTrue(child.is_dir())

    def test_execution_inside_80_blocks(self):
        nested = self.root / lhm.OUTPUT_NAME
        nested.mkdir()
        self.assertEqual(lhm.prevalidate(nested)["estado"], "BLOQUEADO")
        self.assertEqual(
            lhm.prevalidate(nested)["caso_aplicable"],
            "BLOQUEO_RUTA_DENTRO_DE_80_LENGUAJE_HUMANO_MAQUINA",
        )

    def test_direct_destination_file_is_blocked(self):
        destination = self.root / lhm.OUTPUT_NAME
        destination.write_text("no reemplazar", encoding="utf-8")
        report = lhm.generate(self.root)
        self.assertEqual(report["estado"], "BLOQUEADO")
        self.assertTrue(report["conflicto_en_destino_directo"])
        self.assertEqual(destination.read_text(encoding="utf-8"), "no reemplazar")

    def test_direct_destination_symlink_is_blocked(self):
        target = self.root / "destino_externo"
        target.mkdir()
        destination = self.root / lhm.OUTPUT_NAME
        try:
            destination.symlink_to(target, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"El entorno no permite crear symlinks: {exc}")
        report = lhm.generate(self.root)
        self.assertEqual(report["estado"], "BLOQUEADO")
        self.assertTrue(report["conflicto_en_destino_directo"])
        self.assertTrue(destination.is_symlink())

    def test_case_02_direct_document_has_80_at_same_level_as_revisions(self):
        logical = self.root / "RE-GPCC-CC-P-XX"
        (logical / "Rev.B").mkdir(parents=True)
        (logical / "Rev.00").mkdir()
        source = logical / "Rev.00" / "PROCEDIMIENTO.pdf"
        write_blank_pdf(source)
        result = lhm.generate(logical)
        self.assertEqual(result["resultado"], "REGENERADO")
        self.assertEqual(result["caso_aplicable"], "CASO_02_DOCUMENTO_LOGICO_CONTROLADO")
        self.assertTrue((logical / lhm.OUTPUT_NAME / "PROCEDIMIENTO").is_dir())
        self.assertFalse((self.root / lhm.OUTPUT_NAME).exists())

    def test_case_01_container_is_reported_explicitly(self):
        (self.root / "INFORME.csv").write_text("a\n1\n", encoding="utf-8")
        report = lhm.prevalidate(self.root)
        self.assertEqual(report["caso_aplicable"], "CASO_01_AREA_O_CARPETA_CONTENEDORA")

    def test_mode_auto_uses_ecosistema_markers_and_rejects_ambiguity(self):
        independent = Path(self.temp.name) / "02_PROYECTOS_INDEPENDIENTES" / "recurso"
        dependent = Path(self.temp.name) / "03_PROYECTOS_DEPENDIENTES" / "documento"
        independent.mkdir(parents=True)
        dependent.mkdir(parents=True)
        self.assertEqual(lhm.detect_execution_mode(independent, "AUTO"), lhm.MODE_CENTRAL)
        self.assertEqual(lhm.detect_execution_mode(dependent, "AUTO"), lhm.MODE_CENTRAL)
        with self.assertRaisesRegex(ValueError, "Modo ambiguo"):
            lhm.detect_execution_mode(self.root, "AUTO")

    def test_exact_basename_and_priority_are_separate_per_revision(self):
        revision = self.root / "Rev.00"
        revision.mkdir()
        (revision / "MATRIZ.csv").write_text("a,b\n1,2\n", encoding="utf-8")
        write_blank_pdf(revision / "MATRIZ.pdf")
        write_blank_pdf(revision / "MATRIZ_FINAL.pdf")
        lhm.generate(self.root)
        sources = json.loads((self.root / lhm.OUTPUT_NAME / "MATRIZ" / "99_CONTROL" / "fuentes_asociadas.json").read_text())
        self.assertEqual(next(x for x in sources if x["nombre_archivo"] == "MATRIZ.csv")["rol"], "principal")
        self.assertTrue((self.root / lhm.OUTPUT_NAME / "MATRIZ_FINAL").is_dir())

    def test_full_precedence_and_revision_traceability(self):
        rev_b = self.root / "Rev.B"
        rev_00 = self.root / "Rev.00"
        rev_b.mkdir()
        rev_00.mkdir()
        for extension in (".csv", ".docx", ".pdf", ".dwg", ".png"):
            (rev_00 / f"ORDEN{extension}").write_text("dato", encoding="utf-8")
        write_blank_pdf(rev_00 / "ORDEN.pdf")
        (rev_b / "ORDEN.csv").write_text("b\n", encoding="utf-8")
        lhm.generate(self.root)
        resource = json.loads((self.root / lhm.OUTPUT_NAME / "ORDEN" / "02_RECURSO_CANONICO.json").read_text())
        self.assertEqual(resource["control_revision"]["por_revision"]["00"], "ORDEN.csv")
        self.assertEqual(resource["control_revision"]["por_revision"]["B"], "ORDEN.csv")
        sources = resource["fuentes"]
        self.assertEqual(next(x for x in sources if x["nombre_archivo"] == "ORDEN.csv" and x["revision_detectada"] == "00")["rol"], "principal")
        self.assertEqual([lhm.PRIORITY[x] for x in ("EXCEL", "WORD", "PDF", "CAD_EDITABLE", "IMAGEN")], [0, 1, 2, 3, 4])

    def test_metadata_only_cad_is_readable_and_can_be_principal(self):
        source = self.root / "PLANO.dwg"
        source.write_bytes(b"DWG verificable por bytes")
        lhm.generate(self.root)
        resource = json.loads(
            (self.root / lhm.OUTPUT_NAME / "PLANO" / "02_RECURSO_CANONICO.json").read_text()
        )
        record = resource["fuentes"][0]
        self.assertNotIn("_texto_extraido", record)
        self.assertEqual(record["rol"], "principal")
        self.assertEqual(record["familia_documental"], "CAD_EDITABLE")
        self.assertFalse(record["errores_de_lectura"])
        self.assertTrue(record["advertencias_de_lectura"])

    def test_validation_checks_all_json_and_checksums(self):
        (self.root / "A.csv").write_text("x\n1\n", encoding="utf-8")
        lhm.generate(self.root)
        output = self.root / lhm.OUTPUT_NAME
        lhm.validate_output(output, 1)
        resource = output / "A" / "02_RECURSO_CANONICO.json"
        resource.write_text("{json inválido", encoding="utf-8")
        with self.assertRaises(json.JSONDecodeError):
            lhm.validate_output(output, 1)

    def test_checksum_tampering_is_detected(self):
        (self.root / "A.csv").write_text("x\n1\n", encoding="utf-8")
        lhm.generate(self.root)
        output = self.root / lhm.OUTPUT_NAME
        document = output / "A" / "00_DOCUMENTO.md"
        document.write_text(document.read_text(encoding="utf-8") + "alterado\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Checksum no coincide"):
            lhm.validate_output(output, 1)

    def test_publication_failure_restores_previous_direct_output(self):
        destination = self.root / lhm.OUTPUT_NAME
        destination.mkdir()
        sentinel = destination / "anterior.txt"
        sentinel.write_text("conservar", encoding="utf-8")
        staging = Path(self.temp.name) / "staging" / lhm.OUTPUT_NAME
        staging.mkdir(parents=True)
        (staging / "nuevo.txt").write_text("nuevo", encoding="utf-8")
        real_replace = lhm.os.replace

        def fail_new_publication(source, target):
            if Path(source) == staging and Path(target) == destination:
                raise OSError("fallo simulado")
            return real_replace(source, target)

        with mock.patch.object(lhm.os, "replace", side_effect=fail_new_publication):
            with self.assertRaisesRegex(OSError, "fallo simulado"):
                lhm.publish_output(staging, destination)
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "conservar")
        self.assertFalse((destination / "nuevo.txt").exists())

    def test_sanitized_name_collision_does_not_replace_previous_output(self):
        (self.root / "A-B.csv").write_text("x\n1\n", encoding="utf-8")
        (self.root / "A_B.csv").write_text("x\n2\n", encoding="utf-8")
        old = self.root / lhm.OUTPUT_NAME
        old.mkdir()
        sentinel = old / "anterior.txt"
        sentinel.write_text("conservar", encoding="utf-8")
        real_safe_name = lhm.safe_name
        with mock.patch.object(
            lhm,
            "safe_name",
            side_effect=lambda value: "COLLISION" if value in {"A-B", "A_B"} else real_safe_name(value),
        ):
            with self.assertRaisesRegex(ValueError, "misma ruta derivada"):
                lhm.generate(self.root)
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "conservar")

    def test_validation_failure_keeps_previous_direct_output_and_original(self):
        source = self.root / "A.csv"
        source.write_text("x\n1\n", encoding="utf-8")
        source_hash = checksum(source)
        old = self.root / lhm.OUTPUT_NAME
        old.mkdir()
        sentinel = old / "mantener.txt"
        sentinel.write_text("anterior", encoding="utf-8")
        with self.assertRaises(ValueError):
            lhm.generate(self.root, forced_failure=True)
        self.assertEqual(checksum(source), source_hash)
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "anterior")


if __name__ == "__main__":
    unittest.main()
