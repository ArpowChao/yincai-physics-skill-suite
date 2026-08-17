import csv
import tempfile
import unittest
from pathlib import Path

from scripts.check_ecdict_terms import (
    ECDICT_LICENSE,
    ECDICT_REVISION,
    build_report,
)


class EcdictTermCheckTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.transcript = self.root / "transcript.txt"
        self.transcript.write_text(
            "用 Whisper 解釋 algorithm 與 long-time，並保留 PepTSh、3M3SH、"
            "S-Cys-Gly-3M3SH。",
            encoding="utf-8",
        )
        self.original_text = self.transcript.read_text(encoding="utf-8")

        self.ecdict = self.root / "ecdict.csv"
        with self.ecdict.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "word",
                    "phonetic",
                    "translation",
                    "pos",
                    "exchange",
                ],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "word": "whisper",
                    "phonetic": "'wispə",
                    "translation": "低语",
                    "pos": "v:100/n:1",
                    "exchange": "d:whispered",
                }
            )
            writer.writerow(
                {
                    "word": "algorithm",
                    "phonetic": "'ælgəriðəm",
                    "translation": "算法",
                    "pos": "n:100",
                    "exchange": "s:algorithms",
                }
            )
            writer.writerow(
                {
                    "word": "long time",
                    "phonetic": "",
                    "translation": "很长时间",
                    "pos": "",
                    "exchange": "",
                }
            )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_report_classifies_candidates_without_replacing_source(self):
        report = build_report(self.transcript, self.ecdict)
        by_token = {item["token"]: item for item in report["candidates"]}

        self.assertEqual(by_token["algorithm"]["match"], "exact")
        self.assertEqual(by_token["Whisper"]["match"], "case-variant")
        self.assertEqual(by_token["long-time"]["match"], "normalized")
        self.assertEqual(by_token["PepTSh"]["match"], "not-found")
        self.assertEqual(by_token["3M3SH"]["match"], "not-found")
        self.assertEqual(by_token["S-Cys-Gly-3M3SH"]["match"], "not-found")
        self.assertTrue(all(not item["auto_replace"] for item in by_token.values()))
        self.assertEqual(self.transcript.read_text(encoding="utf-8"), self.original_text)

    def test_report_records_pinned_source_and_license(self):
        report = build_report(self.transcript, self.ecdict)

        self.assertTrue(report["candidate_only"])
        self.assertTrue(report["source_unchanged"])
        self.assertEqual(report["ecdict"]["revision"], ECDICT_REVISION)
        self.assertEqual(report["ecdict"]["license"], ECDICT_LICENSE)

    def test_csv_requires_word_column(self):
        invalid_csv = self.root / "invalid.csv"
        invalid_csv.write_text("term,translation\nalgorithm,算法\n", encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "word"):
            build_report(self.transcript, invalid_csv)


if __name__ == "__main__":
    unittest.main()
