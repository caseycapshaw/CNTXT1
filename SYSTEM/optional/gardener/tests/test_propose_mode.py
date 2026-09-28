import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gardener as g  # noqa: E402
from tests.vaultfixture import make_vault  # noqa: E402

FAKE_CLAUDE = str(Path(__file__).resolve().parent / "fake_claude.py")


def head(vault):
    return subprocess.run(["git", "-C", str(vault), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()


def current_branch(vault):
    return subprocess.run(
        ["git", "-C", str(vault), "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True
    ).stdout.strip()


class IsolatedRunTestCase(unittest.TestCase):
    """Base: gives every test its own vault AND its own worktree dir, so
    parallel test runs never collide on GARDENER_WT."""

    def setUp(self):
        self.vault = make_vault()
        self.wt = Path(self.vault.parent) / f"{self.vault.name}-wt"
        self._old_env = dict(os.environ)
        os.environ["GARDENER_WT"] = str(self.wt)
        self.orig_branch = current_branch(self.vault)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._old_env)
        shutil.rmtree(self.vault, ignore_errors=True)
        shutil.rmtree(self.wt, ignore_errors=True)


class TestLiveVaultNeverCheckedOut(IsolatedRunTestCase):
    """The whole point of the redesign: the live vault's OWN working
    directory/branch must never be touched by stage work or guardrail
    reverts — only the isolated worktree is (git worktree add doesn't
    change the main checkout's branch)."""

    def test_propose_leaves_live_vault_on_same_branch(self):
        g.run(self.vault, mode="propose", stage_arg="actions", max_llm_calls=0)
        self.assertEqual(current_branch(self.vault), self.orig_branch)

    def test_apply_leaves_live_vault_on_same_branch(self):
        g.run(self.vault, mode="apply", stage_arg="actions", max_llm_calls=0)
        self.assertEqual(current_branch(self.vault), self.orig_branch)

    def test_propose_creates_review_branch_not_merged(self):
        result = g.run(self.vault, mode="propose", stage_arg="actions", max_llm_calls=0)
        self.assertTrue(result["branch"].startswith("gardener/proposal-"))
        branches = subprocess.run(["git", "-C", str(self.vault), "branch"], capture_output=True, text=True).stdout
        self.assertIn(result["branch"], branches)
        self.assertFalse(result["merge"]["merged"])

    def test_apply_merges_and_deletes_transient_branch(self):
        original_head = head(self.vault)
        result = g.run(self.vault, mode="apply", stage_arg="actions", max_llm_calls=0)
        self.assertTrue(result["merge"]["merged"])
        self.assertNotEqual(head(self.vault), original_head)
        branches = subprocess.run(["git", "-C", str(self.vault), "branch"], capture_output=True, text=True).stdout
        self.assertNotIn(result["branch"], branches)  # merged transient branch is cleaned up

    def test_worktree_removed_after_run(self):
        g.run(self.vault, mode="apply", stage_arg="actions", max_llm_calls=0)
        self.assertFalse(self.wt.exists())

    def test_rerun_propose_same_day_reuses_branch(self):
        result1 = g.run(self.vault, mode="propose", stage_arg="actions", max_llm_calls=0)
        result2 = g.run(self.vault, mode="propose", stage_arg="actions", max_llm_calls=0)
        self.assertEqual(result1["branch"], result2["branch"])


class TestCheckpointing(IsolatedRunTestCase):
    def test_pending_human_edit_checkpointed_before_isolation(self):
        # Simulate Syncthing/Obsidian Sync delivering an edit into the live
        # vault, uncommitted, before gardener ever runs.
        f = self.vault / "05 concepts" / "example-concept.md"
        f.write_text(f.read_text() + "\n\nA sentence the owner typed on their phone.\n")
        self.assertTrue(g.has_diff(self.vault))
        result = g.run(self.vault, mode="apply", stage_arg="actions", max_llm_calls=0)
        self.assertIsNotNone(result["pre_checkpoint"])
        # the human's sentence must still be present after the run
        self.assertIn("A sentence the owner typed on their phone.", f.read_text())
        # and the checkpoint commit must be attributed to the human, not the
        # service account gardener otherwise commits as
        author = subprocess.run(
            ["git", "-C", str(self.vault), "log", "-1", "--format=%an <%ae>", result["pre_checkpoint"]],
            capture_output=True, text=True,
        ).stdout.strip()
        # default = the vault's own git identity (vaultfixture sets it)
        self.assertEqual(author, "Gardener Test <test@example.com>")
        self.assertEqual(g.checkpoint_author(self.vault), "Gardener Test <test@example.com>")

    def test_checkpoint_author_env_override_and_fallback(self):
        import os
        old = os.environ.get("GARDENER_CHECKPOINT_AUTHOR")
        try:
            os.environ["GARDENER_CHECKPOINT_AUTHOR"] = "Someone <s@example.com>"
            self.assertEqual(g.checkpoint_author(self.vault), "Someone <s@example.com>")
            del os.environ["GARDENER_CHECKPOINT_AUTHOR"]
            self.assertEqual(g.checkpoint_author(None), g.FALLBACK_CHECKPOINT_AUTHOR)
        finally:
            if old is None:
                os.environ.pop("GARDENER_CHECKPOINT_AUTHOR", None)
            else:
                os.environ["GARDENER_CHECKPOINT_AUTHOR"] = old

    def test_clean_vault_no_checkpoint_commit(self):
        result = g.run(self.vault, mode="apply", stage_arg="actions", max_llm_calls=0)
        self.assertIsNone(result["pre_checkpoint"])


class TestHumanEditArrivingMidRun(IsolatedRunTestCase):
    """The scenario the whole redesign exists for: a human edit lands in the
    live vault WHILE gardener is off doing stage work in the isolated
    worktree. It must survive — never reverted, never silently dropped."""

    def test_human_edit_mid_run_preserved_through_merge(self):
        # Manually drive the same sequence run() uses, injecting a human
        # edit to the live vault between "isolate" and "merge back".
        g.checkpoint(self.vault, "pre-gardener")
        wt, branch, start_commit = g.setup_worktree(self.vault, "apply")
        try:
            budget = g.Budget(0)
            stage_result = g.do_actions(wt)
            self.assertIsNotNone(stage_result["commit"])  # gardener made real progress in the worktree

            # NOW a human edit arrives in the LIVE vault, mid-run — touching
            # a DIFFERENT file than anything the actions stage touched, so
            # the merge is conflict-free (the conflicting-edit case is its
            # own test below).
            human_file = self.vault / "SYSTEM" / "log.md"
            original = human_file.read_text()
            human_file.write_text(original + "- Mid-run human edit, must survive.\n")

            merge_result = g.merge_back(self.vault, branch)
        finally:
            g.teardown_worktree(self.vault, wt)

        self.assertTrue(merge_result["merged"])
        self.assertIsNotNone(merge_result["pre_merge_checkpoint"])
        final_text = human_file.read_text()
        self.assertIn("Mid-run human edit, must survive.", final_text)
        # AND the gardener stage's own work must also be present post-merge
        # (both sides of the 3-way merge landed).
        stamped_file = (self.vault / stage_result["files_changed"][0]) if stage_result["files_changed"] else None
        if stamped_file:
            self.assertRegex(stamped_file.read_text(), r"➕ \d{4}-\d{2}-\d{2}")


class TestMergeConflictAbortsCleanly(IsolatedRunTestCase):
    def test_conflicting_edit_aborts_merge_and_leaves_branch(self):
        target = self.vault / "05 concepts" / "example-concept.md"
        pre_run_text = target.read_text()

        g.checkpoint(self.vault, "pre-gardener")
        wt, branch, start_commit = g.setup_worktree(self.vault, "apply")
        try:
            # Simulate a gardener stage editing a specific line in the worktree...
            wt_file = wt / "05 concepts" / "example-concept.md"
            wt_text = wt_file.read_text()
            wt_file.write_text(wt_text.replace(
                "This is The owner's own note, verbatim. Do not touch it.",
                "This is The owner's own note, verbatim. Do not touch it. [gardener addendum]",
            ))
            subprocess.run(["git", "-C", str(wt), "add", "-A"], check=True, capture_output=True)
            subprocess.run(["git", "-C", str(wt), "commit", "-q", "-m", "gardener(test): conflicting edit"], check=True, capture_output=True)

            # ...while a human edits the SAME line differently in the live vault.
            target.write_text(pre_run_text.replace(
                "This is The owner's own note, verbatim. Do not touch it.",
                "This is The owner's own note, verbatim. Do not touch it. [human edit]",
            ))

            merge_result = g.merge_back(self.vault, branch)
        finally:
            g.teardown_worktree(self.vault, wt)

        self.assertFalse(merge_result["merged"])
        self.assertTrue(merge_result["conflict"])
        self.assertEqual(merge_result["branch"], branch)

        # Live vault must be back to a clean, mergeable state — no conflict
        # markers, no half-applied merge, and the human's own edit (captured
        # by the pre-merge checkpoint) must still be there.
        status = subprocess.run(["git", "-C", str(self.vault), "status", "--porcelain"], capture_output=True, text=True).stdout
        self.assertEqual(status.strip(), "")
        final_text = target.read_text()
        self.assertNotIn("<<<<<<<", final_text)
        self.assertIn("[human edit]", final_text)

        # The gardener branch itself must still exist, untouched, for review.
        branches = subprocess.run(["git", "-C", str(self.vault), "branch"], capture_output=True, text=True).stdout
        self.assertIn(branch, branches)


class TestClaudeInvocationMocked(unittest.TestCase):
    def setUp(self):
        self.vault = make_vault()
        self._old_env = dict(os.environ)
        os.chmod(FAKE_CLAUDE, 0o755)
        os.environ["GARDENER_CLAUDE_CMD"] = FAKE_CLAUDE

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._old_env)
        shutil.rmtree(self.vault, ignore_errors=True)

    def test_compile_stage_calls_fake_claude_and_commits_legit_write(self):
        os.environ["FAKE_CLAUDE_ACTION"] = "write_file"
        os.environ["FAKE_CLAUDE_WRITE_PATH"] = "05 concepts/example-capture-compiled.md"
        os.environ["FAKE_CLAUDE_WRITE_TEXT"] = "---\ntype: concept\ndescription: compiled.\n---\n\n# Compiled\n"
        budget = g.Budget(5)
        result = g.do_compile(self.vault, budget)
        self.assertGreaterEqual(len(result["orphans_found"]), 1)
        self.assertGreaterEqual(result["llm_calls"], 1)
        self.assertTrue((self.vault / "05 concepts" / "example-capture-compiled.md").exists())
        self.assertEqual(result["rejections"], [])

    def test_compile_stage_rejects_llm_that_touches_raw(self):
        os.environ["FAKE_CLAUDE_ACTION"] = "touch_raw"
        budget = g.Budget(5)
        result = g.do_compile(self.vault, budget)
        self.assertFalse((self.vault / "raw" / "2026-09-28-llm-violation.md").exists())
        self.assertTrue(len(result["rejections"]) >= 1)

    def test_llm_budget_caps_calls(self):
        os.environ["FAKE_CLAUDE_ACTION"] = "noop"
        for i in range(3):
            (self.vault / "raw" / f"2026-09-0{i+2}-extra-{i}.md").write_text(f"extra capture {i}\n", encoding="utf-8")
        budget = g.Budget(1)
        result = g.do_compile(self.vault, budget)
        self.assertEqual(budget.used, 1)
        self.assertTrue(budget.exhausted())
        self.assertGreaterEqual(len(result["skipped_budget"]), 1)


if __name__ == "__main__":
    unittest.main()
