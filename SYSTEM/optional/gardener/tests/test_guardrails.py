import shutil
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gardener as g  # noqa: E402
from tests.vaultfixture import make_vault  # noqa: E402


def commit_all(vault, message="wip"):
    subprocess.run(["git", "-C", str(vault), "add", "-A"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(vault), "commit", "-q", "-m", message], check=True, capture_output=True)


class TestGuardrailDecisionFunction(unittest.TestCase):
    """Pure guardrail_reject_reason() cases — no filesystem/git involved."""

    def test_new_file_under_raw_rejected(self):
        reason = g.guardrail_reject_reason("raw/2026-09-28-new.md", "??", None, "new content")
        self.assertIsNotNone(reason)
        self.assertIn("raw/", reason)

    def test_modified_raw_content_rejected(self):
        reason = g.guardrail_reject_reason("raw/2026-09-01-x.md", "M", "old text\n", "edited text\n")
        self.assertIsNotNone(reason)

    def test_unchanged_raw_content_ok(self):
        reason = g.guardrail_reject_reason("raw/2026-09-01-x.md", "", "same\n", "same\n")
        self.assertIsNone(reason)

    def test_forbidden_decisions_md_rejected(self):
        reason = g.guardrail_reject_reason("SYSTEM/decisions.md", "M", "a", "b")
        self.assertIsNotNone(reason)

    def test_forbidden_claude_dir_rejected(self):
        reason = g.guardrail_reject_reason(".claude/agents/compile.md", "M", "a", "b")
        self.assertIsNotNone(reason)

    def test_forbidden_journal_log_rejected(self):
        reason = g.guardrail_reject_reason("Agents/life-coach/journal-log.md", "M", "a", "b")
        self.assertIsNotNone(reason)

    def test_forbidden_system_journal_rejected(self):
        reason = g.guardrail_reject_reason("SYSTEM/Journal.md", "M", "a", "b")
        self.assertIsNotNone(reason)

    def test_deletion_rejected(self):
        reason = g.guardrail_reject_reason("05 concepts/foo.md", "D", "content", None)
        self.assertIsNotNone(reason)
        self.assertIn("delete", reason)

    def test_human_callout_altered_rejected(self):
        old = "text\n\n> [!human]\n> exact words\n\nmore\n"
        new = "text\n\n> [!human]\n> DIFFERENT words\n\nmore\n"
        reason = g.guardrail_reject_reason("05 concepts/foo.md", "M", old, new)
        self.assertIsNotNone(reason)
        self.assertIn("human", reason)

    def test_human_callout_preserved_elsewhere_edited_ok(self):
        old = "text\n\n> [!human]\n> exact words\n\nmore\n"
        new = "different intro\n\n> [!human]\n> exact words\n\nmore, plus a new sentence\n"
        reason = g.guardrail_reject_reason("05 concepts/foo.md", "M", old, new)
        self.assertIsNone(reason)

    def test_checked_action_changed_rejected(self):
        old = "- [x] done thing #action\n- [ ] open thing #action\n"
        new = "- [x] done thing EDITED #action\n- [ ] open thing #action\n"
        reason = g.guardrail_reject_reason("05 concepts/foo.md", "M", old, new)
        self.assertIsNotNone(reason)

    def test_checked_action_unchanged_ok(self):
        old = "- [x] done thing #action\n- [ ] open thing #action\n"
        new = "- [x] done thing #action\n- [ ] open thing #action ➕ 2026-09-28\n"
        reason = g.guardrail_reject_reason("05 concepts/foo.md", "M", old, new)
        self.assertIsNone(reason)

    def test_ordinary_edit_ok(self):
        old = "# Concept\n\nold fact.\n"
        new = "# Concept\n\nupdated fact.\n"
        reason = g.guardrail_reject_reason("05 concepts/foo.md", "M", old, new)
        self.assertIsNone(reason)

    def test_raw_index_md_allowlisted_new_file_ok(self):
        reason = g.guardrail_reject_reason("raw/index.md", "??", None, "# raw index\n")
        self.assertIsNone(reason)

    def test_raw_index_md_allowlisted_content_change_ok(self):
        reason = g.guardrail_reject_reason("raw/index.md", "M", "old index\n", "new index\n")
        self.assertIsNone(reason)

    def test_raw_index_md_deletion_still_rejected(self):
        reason = g.guardrail_reject_reason("raw/index.md", "D", "content", None)
        self.assertIsNotNone(reason)

    def test_other_raw_path_not_covered_by_allowlist(self):
        # raw/health/index.md is NOT the allow-listed raw/index.md — still protected.
        reason = g.guardrail_reject_reason("raw/health/index.md", "M", "old\n", "new\n")
        self.assertIsNotNone(reason)


class TestEnforceGuardrailsIntegration(unittest.TestCase):
    """End-to-end: dirty a real fixture vault, run enforce_guardrails, verify
    the offending change is reverted and everything else survives."""

    def setUp(self):
        self.vault = make_vault()

    def tearDown(self):
        shutil.rmtree(self.vault, ignore_errors=True)

    def test_raw_edit_reverted(self):
        raw = self.vault / "raw" / "2026-09-01-example-capture.md"
        original = raw.read_text()
        raw.write_text(original + "\nan LLM added this line\n")
        rejected = g.enforce_guardrails(self.vault, "test")
        self.assertEqual(raw.read_text(), original)
        self.assertTrue(any("raw/2026-09-01-example-capture.md" in r["path"] for r in rejected))

    def test_new_raw_file_removed(self):
        new_raw = self.vault / "raw" / "2026-09-28-new-capture.md"
        new_raw.write_text("new capture\n")
        rejected = g.enforce_guardrails(self.vault, "test")
        self.assertFalse(new_raw.exists())
        self.assertTrue(any("2026-09-28-new-capture.md" in r["path"] for r in rejected))

    def test_decisions_md_edit_reverted(self):
        f = self.vault / "SYSTEM" / "decisions.md"
        original = f.read_text()
        f.write_text(original + "\n- a sneaky new ruling\n")
        rejected = g.enforce_guardrails(self.vault, "test")
        self.assertEqual(f.read_text(), original)
        self.assertTrue(any(r["path"] == "SYSTEM/decisions.md" for r in rejected))

    def test_file_deletion_restored(self):
        f = self.vault / "05 concepts" / "example-concept.md"
        original = f.read_text()
        f.unlink()
        rejected = g.enforce_guardrails(self.vault, "test")
        self.assertTrue(f.exists())
        self.assertEqual(f.read_text(), original)
        self.assertTrue(any("example-concept.md" in r["path"] for r in rejected))

    def test_human_callout_edit_reverted(self):
        f = self.vault / "05 concepts" / "example-concept.md"
        original = f.read_text()
        edited = original.replace("This is The owner's own note, verbatim. Do not touch it.", "REWRITTEN BY LLM")
        f.write_text(edited)
        rejected = g.enforce_guardrails(self.vault, "test")
        self.assertEqual(f.read_text(), original)
        self.assertTrue(any("example-concept.md" in r["path"] for r in rejected))

    def test_checked_action_edit_reverted(self):
        f = self.vault / "05 concepts" / "example-concept.md"
        original = f.read_text()
        edited = original.replace("- [x] already done #action", "- [x] already done DIFFERENTLY #action")
        f.write_text(edited)
        rejected = g.enforce_guardrails(self.vault, "test")
        self.assertEqual(f.read_text(), original)
        self.assertTrue(any("example-concept.md" in r["path"] for r in rejected))

    def test_legitimate_edit_survives(self):
        f = self.vault / "05 concepts" / "example-concept.md"
        original = f.read_text()
        edited = original + "\n\nA new, legitimate paragraph of compiled fact.\n"
        f.write_text(edited)
        rejected = g.enforce_guardrails(self.vault, "test")
        self.assertEqual(f.read_text(), edited)
        self.assertEqual(rejected, [])

    def test_new_ordinary_file_survives(self):
        new_concept = self.vault / "05 concepts" / "brand-new-concept.md"
        new_concept.write_text("---\ntype: concept\ndescription: new.\n---\n\n# Brand New\n")
        rejected = g.enforce_guardrails(self.vault, "test")
        self.assertTrue(new_concept.exists())
        self.assertEqual(rejected, [])

    def test_claude_dir_edit_reverted(self):
        claude_dir = self.vault / ".claude" / "agents"
        claude_dir.mkdir(parents=True, exist_ok=True)
        f = claude_dir / "compile.md"
        f.write_text("role file\n")
        commit_all(self.vault, "add fake .claude file")
        f.write_text("role file EDITED\n")
        rejected = g.enforce_guardrails(self.vault, "test")
        self.assertEqual(f.read_text(), "role file\n")
        self.assertTrue(any(".claude/" in r["path"] for r in rejected))

    def test_raw_index_md_regen_survives_guardrails(self):
        # Simulates the regen stage's build_directory_indexes.py writing
        # raw/index.md — the one carved-out exception to raw/'s append-only rule.
        idx = self.vault / "raw" / "index.md"
        idx.write_text("# raw/ directory index\n\n- [[2026-09-01-example-capture]]\n", encoding="utf-8")
        rejected = g.enforce_guardrails(self.vault, "test")
        self.assertTrue(idx.exists())
        self.assertEqual(rejected, [])

    def test_git_mv_rename_not_treated_as_deletion(self):
        # Simulates the inbox stage's intended `git mv` relocation of a root
        # item into raw/ — a rename must NOT trip the raw/ "new file" guard
        # (old path disappears, new path appears; git records it as R, not
        # D+??). This exercises the git_status_entries rename collapsing.
        item = self.vault / "some-dropped-file.md"
        item.write_text("dropped content\n")
        commit_all(self.vault, "add a root item")
        target = self.vault / "03 Projects" / "some-dropped-file.md"
        subprocess.run(
            ["git", "-C", str(self.vault), "mv", "some-dropped-file.md", "03 Projects/some-dropped-file.md"],
            check=True, capture_output=True,
        )
        rejected = g.enforce_guardrails(self.vault, "test")
        self.assertTrue(target.exists())
        self.assertEqual(rejected, [])


if __name__ == "__main__":
    unittest.main()
