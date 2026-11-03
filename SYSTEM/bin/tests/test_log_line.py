"""One log writer: log-line appends on the writer host or to a per-host sidecar; fold_log folds
sidecars into SYSTEM/log.md on the writer (SYSTEM/SCHEMA.md § One log writer).
Run: python3 -m unittest discover -s SYSTEM/bin/tests"""
import datetime as dt
import importlib.machinery
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

BIN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BIN))
spec = importlib.util.spec_from_loader("log_line", importlib.machinery.SourceFileLoader("log_line", str(BIN / "log-line")))
LL = importlib.util.module_from_spec(spec)
spec.loader.exec_module(LL)
import fold_log as F  # noqa: E402

TODAY = dt.date(2026, 11, 3)
HEADER = "# Log — knowledge base updates\n\nChronological record.\n\n"


def vault():
    v = Path(tempfile.mkdtemp(prefix="logv-"))
    (v / "SYSTEM/log").mkdir(parents=True)
    (v / "SYSTEM/log.md").write_text(HEADER + "- 2026-11-01 — writer line one\n")
    (v / "SYSTEM/writer-host.conf").write_text("# comment\nhost=writer-box\n")
    return v


class LogLine(unittest.TestCase):
    def test_writer_host_appends_to_log_md_with_prefix(self):
        v = vault()
        p = LL.write(v, "did a thing", host="writer-box", today=TODAY)
        self.assertEqual(p, v / "SYSTEM/log.md")
        self.assertTrue((v / "SYSTEM/log.md").read_text().endswith("- 2026-11-01 — writer line one\n- 2026-11-03 — did a thing\n"))

    def test_other_host_writes_its_own_monthly_sidecar(self):
        v = vault()
        p = LL.write(v, "did a thing", host="laptop", today=TODAY)
        self.assertEqual(p, v / "SYSTEM/log.d/2026-11.laptop.md")
        self.assertEqual(p.read_text(), "- 2026-11-03 — did a thing\n")
        self.assertNotIn("did a thing", (v / "SYSTEM/log.md").read_text())

    def test_existing_prefix_kept_and_newlines_flattened(self):
        v = vault()
        LL.write(v, "- 2026-11-02 — already\ndated", host="laptop", today=TODAY)
        self.assertEqual((v / "SYSTEM/log.d/2026-11.laptop.md").read_text(), "- 2026-11-02 — already dated\n")

    def test_log_md_missing_trailing_newline_is_repaired(self):
        v = vault()
        (v / "SYSTEM/log.md").write_text(HEADER + "- 2026-11-01 — no newline")
        LL.write(v, "next", host="writer-box", today=TODAY)
        self.assertIn("- 2026-11-01 — no newline\n- 2026-11-03 — next\n", (v / "SYSTEM/log.md").read_text())

    def test_writer_host_read_from_conf(self):
        self.assertEqual(LL.writer_host(vault()), "writer-box")

    def test_no_conf_means_single_machine_every_host_writes_log_md(self):
        v = vault()
        (v / "SYSTEM/writer-host.conf").unlink()
        self.assertIsNone(LL.writer_host(v))
        p = LL.write(v, "solo", host="laptop", today=TODAY)
        self.assertEqual(p, v / "SYSTEM/log.md")
        self.assertFalse((v / "SYSTEM/log.d").exists())

    def test_empty_text_refused(self):
        with self.assertRaises(ValueError):
            LL.write(vault(), "   ", host="laptop", today=TODAY)


class Fold(unittest.TestCase):
    def setUp(self):
        self.v = vault()
        (self.v / "SYSTEM/log.d").mkdir()

    def side(self, name, text):
        (self.v / "SYSTEM/log.d" / name).write_text(text)

    def test_new_sidecar_lines_are_appended_once(self):
        self.side("2026-11.laptop.md", "- 2026-11-02 — laptop a\n- 2026-11-03 — laptop b\n")
        r = F.fold(self.v, today=TODAY)
        self.assertEqual(r["added"], 2)
        log = (self.v / "SYSTEM/log.md").read_text()
        self.assertTrue(log.endswith("- 2026-11-01 — writer line one\n- 2026-11-02 — laptop a\n- 2026-11-03 — laptop b\n"))
        self.assertEqual(F.fold(self.v, today=TODAY)["added"], 0)          # idempotent
        self.assertEqual((self.v / "SYSTEM/log.md").read_text(), log)

    def test_sidecar_is_never_edited(self):
        self.side("2026-11.laptop.md", "- 2026-11-02 — laptop a\n")
        before = (self.v / "SYSTEM/log.d/2026-11.laptop.md").read_text()
        F.fold(self.v, today=TODAY)
        self.assertEqual((self.v / "SYSTEM/log.d/2026-11.laptop.md").read_text(), before)

    def test_line_already_rotated_into_the_archive_is_not_readded(self):
        (self.v / "SYSTEM/log/2026-10.md").write_text("# Log — 2026-10\n\n- 2026-10-31 — old laptop line\n")
        self.side("2026-10.laptop.md", "- 2026-10-31 — old laptop line\n")
        self.assertEqual(F.fold(self.v, today=TODAY)["added"], 0)

    def test_previous_month_sidecar_removed_once_fully_archived(self):
        (self.v / "SYSTEM/log/2026-10.md").write_text("- 2026-10-31 — old laptop line\n")
        self.side("2026-10.laptop.md", "- 2026-10-31 — old laptop line\n")
        self.side("2026-11.laptop.md", "- 2026-11-02 — current\n")
        r = F.fold(self.v, today=TODAY)
        self.assertEqual(r["removed"], ["2026-10.laptop.md"])
        self.assertTrue((self.v / "SYSTEM/log.d/2026-11.laptop.md").exists())

    def test_previous_month_sidecar_kept_while_lines_are_still_in_log_md(self):
        # folded but not yet rotated: rotate_log.sh moves it to the archive later; keep the sidecar till then
        self.side("2026-10.laptop.md", "- 2026-10-31 — late laptop line\n")
        r = F.fold(self.v, today=TODAY)
        self.assertEqual(r["added"], 1)
        self.assertEqual(r["removed"], [])

    def test_malformed_lines_are_skipped_and_reported(self):
        self.side("2026-11.laptop.md", "stray text\n- 2026-11-02 — fine\n\n")
        r = F.fold(self.v, today=TODAY)
        self.assertEqual((r["added"], r["skipped"]), (1, ["2026-11.laptop.md: stray text"]))

    def test_no_sidecar_dir_is_a_no_op(self):
        (self.v / "SYSTEM/log.d").rmdir()
        self.assertEqual(F.fold(self.v, today=TODAY), {"added": 0, "removed": [], "skipped": []})


if __name__ == "__main__":
    unittest.main()
