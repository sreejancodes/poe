import contextlib
import io
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "skills" / "poe" / "scripts"))

import poe_results  # noqa: E402

FIXTURE_SESSION = REPO_ROOT / "tests" / "fixtures" / "results"


def run_main(argv):
    """Run poe_results.main and return (exit code, stdout, stderr)."""
    stdout, stderr = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = poe_results.main(argv)
    return code, stdout.getvalue(), stderr.getvalue()


def keys(analyses):
    return [analysis.key for analysis in analyses]


def analysis_block(page_html, anchor):
    """The page HTML from an analysis's opening tag onwards."""
    return page_html[page_html.index(f'id="{anchor}"'):]


class ArrangeFixtureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = poe_results.build_page(FIXTURE_SESSION)
        cls.tasks = {task.slug: task for task in cls.page.tasks}

    def test_one_section_per_task_without_docs_or_trash(self):
        self.assertEqual([task.slug for task in self.page.tasks], ["clustering", "rna-qc"])

    def test_follows_chain_nests_analyses(self):
        rna_qc = self.tasks["rna-qc"]
        self.assertEqual(keys(rna_qc.roots), ["rna-qc/01"])
        first = rna_qc.roots[0]
        self.assertEqual(keys(first.children), ["rna-qc/02", "manual-3"])
        self.assertEqual(keys(first.children[0].children), ["rna-qc/03"])

    def test_bare_number_follows_from(self):
        clustering = self.tasks["clustering"]
        self.assertEqual(keys(clustering.roots[0].children), ["clustering/02"])

    def test_manual_entry_with_follows_nests_under_that_analysis(self):
        manual = self.tasks["rna-qc"].roots[0].children[1]
        self.assertEqual(manual.question, "Quick look at mito fraction")
        self.assertIsNone(manual.slug)

    def test_manual_entry_placed_by_notebook_directory(self):
        self.assertEqual(keys(self.tasks["clustering"].roots), ["clustering/01", "manual-5"])

    def test_manual_entry_without_context_goes_to_untracked(self):
        self.assertEqual(keys(self.page.untracked), ["manual-6"])
        self.assertEqual(self.page.untracked[0].files, ["scripts/sizes.py"])

    def test_last_log_entry_is_latest(self):
        self.assertEqual(self.page.latest.key, "rna-qc/03")
        self.assertTrue(self.page.latest.is_latest)

    def test_record_fields(self):
        first = self.tasks["rna-qc"].roots[0]
        self.assertEqual(first.status, "done")
        self.assertEqual(first.question, "How many counts per cell?")
        self.assertEqual(first.interpretation, "Depth is typical for this protocol.")
        self.assertEqual(first.notebook, "notebooks/rna-qc/qc.ipynb")
        self.assertEqual(first.figures, ["notebooks/rna-qc/figures/counts.png"])
        self.assertEqual(first.files, ["notebooks/rna-qc/tables/counts.csv"])
        self.assertEqual(first.record, "poe/rna-qc/analysis/01-counts.md")

    def test_malformed_record_and_log_entry_counted(self):
        self.assertEqual(self.page.skipped, 2)
        self.assertEqual(self.page.record_count, 5)
        self.assertEqual(self.page.entry_count, 8)


class ExtractPathsTest(unittest.TestCase):
    def test_plain_backtick_and_markdown_link(self):
        text = "Figure: a/plot.png, `b/table.csv` and [umap](c/umap.svg); notebook n.ipynb#01: QC."
        self.assertEqual(
            poe_results.extract_paths(text), ["c/umap.svg", "b/table.csv", "a/plot.png", "n.ipynb"]
        )

    def test_numbers_and_words_are_not_paths(self):
        self.assertEqual(poe_results.extract_paths("r = 0.85, e.g. p.adj below 0.05"), [])


class RenderFixtureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(temp.cleanup)
        cls.session_dir = Path(temp.name) / "session"
        shutil.copytree(FIXTURE_SESSION, cls.session_dir)
        cls.code, cls.stdout, _ = run_main([str(cls.session_dir)])
        cls.page_path = cls.session_dir / "poe" / "docs" / "all_analysis.html"
        cls.html = cls.page_path.read_text(encoding="utf-8")

    def test_prints_path_and_exits_zero(self):
        self.assertEqual(self.code, 0)
        self.assertEqual(self.stdout.strip(), str(self.page_path))

    def test_task_sections(self):
        self.assertIn('<section id="task-rna-qc">', self.html)
        self.assertIn('<section id="task-clustering">', self.html)
        self.assertNotIn("Trashed analysis", self.html)

    def test_nested_thread(self):
        first = analysis_block(self.html, "analysis-rna-qc-01")
        children = first[first.index('<div class="children">'):]
        self.assertIn('id="analysis-rna-qc-02"', children)
        self.assertIn('id="manual-3"', children)

    def test_inline_image_for_existing_figure(self):
        self.assertIn('<img src="../../notebooks/rna-qc/figures/counts.png"', self.html)

    def test_missing_figure_marked(self):
        self.assertIn(
            '<a class="missing" href="../../notebooks/rna-qc/figures/umap.png">'
            "notebooks/rna-qc/figures/umap.png (missing)</a>",
            self.html,
        )
        self.assertNotIn('<img src="../../notebooks/rna-qc/figures/umap.png"', self.html)

    def test_manual_entry_placed_by_notebook_in_task_section(self):
        clustering = self.html[self.html.index('id="task-clustering"'):self.html.index('id="task-rna-qc"')]
        self.assertIn("Tried resolution 0.5", clustering)

    def test_untracked_work_section(self):
        untracked = self.html[self.html.index('<section id="untracked-work">'):]
        self.assertIn("Checked raw file sizes", untracked)
        self.assertNotIn("Tried resolution 0.5", untracked)

    def test_latest_marked_and_linked_from_top(self):
        self.assertIn('<p>Latest: <a href="#analysis-rna-qc-03">', self.html)
        self.assertIn('class="analysis dimmed latest" id="analysis-rna-qc-03"', self.html)
        self.assertEqual(self.html.count('<span class="badge latest">'), 1)

    def test_failed_and_abandoned_dimmed(self):
        self.assertIn('class="analysis dimmed" id="analysis-clustering-02"', self.html)
        self.assertIn('class="analysis" id="analysis-rna-qc-01"', self.html)

    def test_skipped_count_in_footer(self):
        footer = self.html[self.html.index("<footer>"):]
        self.assertIn("Skipped 2 malformed entries.", footer)

    def test_caveats_and_later_paragraphs_omitted(self):
        self.assertNotIn("Not shown.", self.html)
        self.assertNotIn("Second paragraph", self.html)

    def test_no_script_and_light_dark(self):
        self.assertNotIn("<script", self.html)
        self.assertIn("prefers-color-scheme: dark", self.html)

    def test_rerun_is_byte_identical(self):
        first = self.page_path.read_bytes()
        code, _, _ = run_main([str(self.session_dir)])
        self.assertEqual(code, 0)
        self.assertEqual(self.page_path.read_bytes(), first)


class MainTest(unittest.TestCase):
    def test_empty_dir_writes_empty_state_page(self):
        with tempfile.TemporaryDirectory() as temp:
            code, stdout, _ = run_main([temp])
            page_path = Path(temp) / "poe" / "docs" / "all_analysis.html"
            self.assertEqual(code, 0)
            self.assertEqual(stdout.strip(), str(page_path))
            page = page_path.read_text(encoding="utf-8")
        self.assertIn("No analyses yet", page)
        self.assertIn("Skipped 0 malformed entries.", page)

    def test_missing_dir_exits_non_zero(self):
        code, stdout, stderr = run_main([str(FIXTURE_SESSION / "does-not-exist")])
        self.assertNotEqual(code, 0)
        self.assertEqual(stdout, "")
        self.assertIn("not found", stderr)


if __name__ == "__main__":
    unittest.main()
