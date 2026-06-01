from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from oss_ready.scanner import scan_repository


class ScannerTests(unittest.TestCase):
    def test_complete_small_project_scores_well(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text(
                "# Demo\n\n## Installation\n\nInstall it.\n\n## Usage\n\nRun it.\n",
                encoding="utf-8",
            )
            (root / "LICENSE").write_text("MIT\n", encoding="utf-8")
            (root / "pyproject.toml").write_text("[project]\nname = \"demo\"\n", encoding="utf-8")
            (root / ".gitignore").write_text("__pycache__/\n", encoding="utf-8")
            (root / "CONTRIBUTING.md").write_text("# Contributing\n", encoding="utf-8")
            (root / "CODE_OF_CONDUCT.md").write_text("# Code of Conduct\n", encoding="utf-8")
            (root / "tests").mkdir()
            (root / "tests" / "test_demo.py").write_text("def test_demo(): pass\n", encoding="utf-8")
            (root / ".github" / "workflows").mkdir(parents=True)
            (root / ".github" / "workflows" / "ci.yml").write_text("name: CI\n", encoding="utf-8")

            report = scan_repository(root)

            self.assertGreaterEqual(report.score, 95)
            self.assertFalse(report.markdown_issues)

    def test_missing_project_basics_lower_score(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# Demo\n", encoding="utf-8")

            report = scan_repository(root)

            failing_ids = {check.id for check in report.checks if check.status == "fail"}
            self.assertIn("license", failing_ids)
            self.assertIn("metadata", failing_ids)
            self.assertLess(report.score, 50)


if __name__ == "__main__":
    unittest.main()

