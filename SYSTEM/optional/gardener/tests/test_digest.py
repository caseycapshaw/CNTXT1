import datetime as dt
import shutil
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gardener as g  # noqa: E402
from tests.vaultfixture import make_vault  # noqa: E402


class TestDigest(unittest.TestCase):
    def setUp(self):
        self.vault = make_vault()
        self.today = dt.date.today().isoformat()

    def tearDown(self):
        shutil.rmtree(self.vault, ignore_errors=True)

    def sample_run_result(self):
        return {
            "mode": "apply",
            "stages": [
                {"name": "regen", "commit": "abc1234", "ran": ["regen-all"], "skipped": [], "failed": [], "rejections": [], "llm_calls": 0},
                {
                    "name": "compile", "commit": None, "orphans_found": [], "compiled": [],
                    "skipped_budget": [], "rejections": [{"path": "raw/2026-09-01-x.md", "reason": "raw/ content modified", "stage": "compile"}],
                    "llm_calls": 1,
                },
            ],
        }

    def test_creates_note_if_absent(self):
        note = g.write_digest(self.vault, self.sample_run_result())
        self.assertTrue(note.exists())
        text = note.read_text()
        self.assertIn(g.GARDENER_DIGEST_START, text)
        self.assertIn(g.GARDENER_DIGEST_END, text)
        self.assertIn("## Gardener", text)
        self.assertIn("### regen", text)
        self.assertIn("### compile", text)
        self.assertIn("raw/2026-09-01-x.md", text)

    def test_replaces_block_idempotently(self):
        note_path = self.vault / "00 daily" / f"{self.today}.md"
        note_path.parent.mkdir(parents=True, exist_ok=True)
        note_path.write_text(
            f"# {self.today} — Daily plan\n\n## Work log\n- 09:00 — did a thing\n\n"
            f"{g.GARDENER_DIGEST_START}\n## Gardener\n\nSTALE OLD CONTENT\n{g.GARDENER_DIGEST_END}\n",
            encoding="utf-8",
        )
        g.write_digest(self.vault, self.sample_run_result())
        text = note_path.read_text()
        self.assertNotIn("STALE OLD CONTENT", text)
        self.assertIn("### regen", text)
        # hand-written section above the marker must survive untouched
        self.assertIn("## Work log\n- 09:00 — did a thing", text)
        # exactly one start/end pair
        self.assertEqual(text.count(g.GARDENER_DIGEST_START), 1)
        self.assertEqual(text.count(g.GARDENER_DIGEST_END), 1)

    def test_human_section_above_marker_preserved_on_rewrite(self):
        note_path = self.vault / "00 daily" / f"{self.today}.md"
        note_path.parent.mkdir(parents=True, exist_ok=True)
        note_path.write_text(
            f"# {self.today} — Daily plan\n\n> [!human]\n> The owner's own note text.\n",
            encoding="utf-8",
        )
        g.write_digest(self.vault, self.sample_run_result())
        text = note_path.read_text()
        self.assertIn("> [!human]\n> The owner's own note text.", text)

    def test_revert_commands_included(self):
        note = g.write_digest(self.vault, self.sample_run_result())
        text = note.read_text()
        self.assertIn("git -C", text)
        self.assertIn("revert abc1234", text)

    def test_no_stage_data_message_for_digest_only_run(self):
        note = g.write_digest(self.vault, {"mode": "apply", "stages": []})
        text = note.read_text()
        self.assertIn("No stage data", text)


if __name__ == "__main__":
    unittest.main()
