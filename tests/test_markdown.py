from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from oss_ready.markdown import check_markdown, slugify_heading


class MarkdownTests(unittest.TestCase):
    def test_slugify_heading_matches_common_markdown_anchors(self) -> None:
        self.assertEqual(slugify_heading("Usage: `oss-ready`"), "usage-oss-ready")

    def test_broken_local_link_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("[missing](docs/missing.md)\n", encoding="utf-8")

            issues = check_markdown(root)

            self.assertEqual(len(issues), 1)
            self.assertEqual(issues[0].severity, "fail")
            self.assertIn("does not exist", issues[0].message)

    def test_heading_anchor_is_validated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# Guide\n\n[ok](#guide)\n[bad](#missing)\n", encoding="utf-8")

            issues = check_markdown(root)

            self.assertEqual(len(issues), 1)
            self.assertIn("anchor", issues[0].message)

    def test_image_alt_text_and_code_language_warnings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("![](image.png)\n\n```\nprint('hi')\n```\n", encoding="utf-8")
            (root / "image.png").write_bytes(b"fake")

            issues = check_markdown(root)

            messages = {issue.message for issue in issues}
            self.assertIn("image is missing alt text", messages)
            self.assertIn("fenced code block has no language", messages)


if __name__ == "__main__":
    unittest.main()

