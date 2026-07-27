import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUALITY_PATH = ROOT / "scripts" / "quality_records.py"


def load_quality():
    if not QUALITY_PATH.exists():
        raise AssertionError("scripts/quality_records.py is missing")
    spec = importlib.util.spec_from_file_location("quality_records", QUALITY_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def valid_record():
    return {
        "record_version": "1.0",
        "record_id": "20260727-peb-vc-4-1-demo",
        "created_at": "2026-07-27T20:00:00+08:00",
        "skill": "physics-unit-package-qc",
        "skill_version": "1.0.0",
        "project_code": "PEb-Vc-4-1",
        "official_code": "PEb-Vc-4",
        "artifact_refs": ["sha256:demo"],
        "evidence": [{"level": "A", "ref": "curriculum:PEb-Vc-4"}],
        "decision": "REVISE",
        "strengths": [{"criterion": "terminology", "note": "三份教材皆使用慣性"}],
        "findings": [
            {
                "severity": "major",
                "criterion": "scope",
                "note": "必修教材含公式推導",
                "action": "改為定性說明",
            }
        ],
        "human_decision": None,
    }


class QualityRecordTests(unittest.TestCase):
    def test_valid_record_passes(self):
        quality = load_quality()
        self.assertEqual([], quality.validate_record(valid_record()))

    def test_invalid_decision_is_rejected(self):
        quality = load_quality()
        record = valid_record()
        record["decision"] = "LOOKS_GOOD"
        errors = quality.validate_record(record)
        self.assertTrue(any("decision" in error for error in errors))

    def test_summary_keeps_strengths_and_findings(self):
        quality = load_quality()
        summary = quality.summarize_records([valid_record()])
        self.assertEqual(1, summary["records"])
        self.assertEqual(1, summary["strengths_by_criterion"]["terminology"])
        self.assertEqual(1, summary["findings_by_severity"]["major"])
        self.assertEqual(1, summary["decisions"]["REVISE"])

    def test_read_records_accepts_json_and_jsonl(self):
        quality = load_quality()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            record = valid_record()
            (root / "one.json").write_text(
                json.dumps(record, ensure_ascii=False),
                encoding="utf-8",
            )
            (root / "two.jsonl").write_text(
                json.dumps(record, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            records = quality.read_records([root])
            self.assertEqual(2, len(records))


if __name__ == "__main__":
    unittest.main()
