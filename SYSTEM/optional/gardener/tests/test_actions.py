import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gardener as g  # noqa: E402
from tests.vaultfixture import make_vault  # noqa: E402


def _commit_action_line(vault, rel_path, line, date):
    """Append one open #action line to rel_path and commit it with a fixed
    author/committer date, so git log -S can later discover a real,
    distinct created-date per line — exercising the oldest-first ordering."""
    p = vault / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        p.write_text("---\ntype: concept\ndescription: batch test.\n---\n\n# Batch\n\n## Actions\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(vault), "add", "-A"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(vault), "commit", "-q", "-m", f"add {rel_path}"], check=True, capture_output=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    env = os.environ.copy()
    env["GIT_AUTHOR_DATE"] = f"{date}T09:00:00"
    env["GIT_COMMITTER_DATE"] = f"{date}T09:00:00"
    subprocess.run(["git", "-C", str(vault), "add", "-A"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(vault), "commit", "-q", "-m", f"line for {date}"], check=True, capture_output=True, env=env)


class TestActionDating(unittest.TestCase):
    def setUp(self):
        self.vault = make_vault()

    def tearDown(self):
        shutil.rmtree(self.vault, ignore_errors=True)

    def test_open_action_without_date_gets_stamped(self):
        result = g.do_actions(self.vault)
        text = (self.vault / "05 concepts" / "example-concept.md").read_text()
        # the line that had no date should now carry a ➕ YYYY-MM-DD stamp
        self.assertRegex(text, r"- \[ \] still open, no date #action ➕ \d{4}-\d{2}-\d{2}")
        self.assertGreaterEqual(result["actions_stamped"], 1)
        self.assertIn("05 concepts/example-concept.md", result["files_changed"])

    def test_already_checked_action_untouched(self):
        before = (self.vault / "05 concepts" / "example-concept.md").read_text()
        g.do_actions(self.vault)
        after = (self.vault / "05 concepts" / "example-concept.md").read_text()
        self.assertIn("- [x] already done #action\n", after)
        self.assertIn("- [x] already done #action\n", before)

    def test_raw_never_touched(self):
        raw = self.vault / "raw" / "2026-09-01-example-capture.md"
        before = raw.read_text()
        g.do_actions(self.vault)
        self.assertEqual(raw.read_text(), before)

    def test_idempotent_second_run_no_further_changes(self):
        result1 = g.do_actions(self.vault)
        self.assertIsNotNone(result1["commit"])  # first run commits the stamp itself
        result2 = g.do_actions(self.vault)
        self.assertEqual(result2["actions_stamped"], 0)
        self.assertEqual(result2["files_changed"], [])
        self.assertIsNone(result2["commit"])

    def test_commits_when_changed(self):
        before_sha = subprocess.run(
            ["git", "-C", str(self.vault), "rev-parse", "HEAD"], capture_output=True, text=True
        ).stdout.strip()
        result = g.do_actions(self.vault)
        self.assertIsNotNone(result["commit"])
        self.assertNotEqual(result["commit"], before_sha)
        log = subprocess.run(
            ["git", "-C", str(self.vault), "log", "-1", "--format=%s"], capture_output=True, text=True
        ).stdout
        self.assertTrue(log.startswith("gardener(actions):"))


class TestActionCapOldestFirst(unittest.TestCase):
    def setUp(self):
        self.vault = make_vault()

    def tearDown(self):
        shutil.rmtree(self.vault, ignore_errors=True)

    def test_caps_at_max_stamps_and_picks_oldest_first(self):
        # 5 distinct-dated action lines across 5 files, oldest to newest
        # commit dates, asking for only the oldest 3 in one run.
        dates = ["2026-01-01", "2026-02-01", "2026-03-01", "2026-04-01", "2026-05-01"]
        for i, date in enumerate(dates):
            _commit_action_line(
                self.vault, f"02 Areas/batch-{i}.md",
                f"- [ ] task from {date} #action", date,
            )
        result = g.do_actions(self.vault, max_stamps=3)
        # +1 candidate from the vault fixture's own pre-existing unstamped
        # action (05 concepts/example-concept.md), introduced at fixture
        # creation time — newer than all 5 of these fixed-past-date lines,
        # so it never displaces them from the oldest-3 selection below.
        self.assertEqual(result["actions_stamped"], 3)
        self.assertEqual(result["candidates_total"], 6)
        self.assertEqual(result["skipped_budget"], 3)
        # the three OLDEST must be the ones stamped; the two newest left alone
        for date in dates[:3]:
            idx = dates.index(date)
            text = (self.vault / f"02 Areas/batch-{idx}.md").read_text()
            self.assertIn(f"➕ {date}", text)
        for date in dates[3:]:
            idx = dates.index(date)
            text = (self.vault / f"02 Areas/batch-{idx}.md").read_text()
            self.assertNotIn("➕", text)

    def test_default_cap_is_50(self):
        self.assertEqual(g.ACTIONS_MAX_STAMPS_PER_RUN, 50)


if __name__ == "__main__":
    unittest.main()
