import contextlib
import html
import io
import re
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "skills" / "poe" / "scripts"))

import poe_report  # noqa: E402

FIXTURE_TASK = REPO_ROOT / "tests" / "fixtures" / "poe" / "sample-task"
SESSION_ID = "11111111-2222-3333-4444-555555555555"


def find_call(transcript, tool_use_id):
    for step in transcript.steps:
        if step.kind == "tool_call" and step.tool_use_id == tool_use_id:
            return step
    raise AssertionError(f"no tool call {tool_use_id}")


class LoadFixtureTaskTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.task = poe_report.load_task(FIXTURE_TASK)
        cls.session = cls.task.sessions[0]
        cls.main = cls.session.main
        cls.worker = cls.session.workers[0]

    def test_task_documents_in_order(self):
        paths = [path for path, _ in self.task.documents]
        self.assertEqual(paths, ["plan.md", "status.md", "phases/01-x.md", "progress/01a-x.md"])
        self.assertEqual(self.task.slug, "sample-task")

    def test_one_session_with_one_worker(self):
        self.assertEqual(len(self.task.sessions), 1)
        self.assertEqual(self.session.session_id, SESSION_ID)
        self.assertEqual(self.main.name, SESSION_ID)
        self.assertEqual(self.main.actor, "orchestrator")
        self.assertEqual(len(self.session.workers), 1)

    def test_step_counts_and_kinds(self):
        self.assertEqual(len(self.main.steps), 13)
        self.assertEqual(len(self.worker.steps), 8)
        kinds = [step.kind for step in self.main.steps]
        self.assertEqual(
            kinds,
            ["user", "thinking", "assistant"]
            + ["tool_call", "tool_result"] * 4
            + ["system", "assistant"],
        )
        worker_kinds = [step.kind for step in self.worker.steps]
        self.assertEqual(
            worker_kinds,
            ["user", "tool_call", "tool_result", "thinking", "thinking", "narration", "thinking", "assistant"],
        )

    def test_thinking_counts_exclude_narration(self):
        # main: one thinking block with text; worker: two with text, one empty.
        self.assertEqual((self.main.thinking_recorded, self.main.thinking_blocks), (1, 1))
        self.assertEqual((self.worker.thinking_recorded, self.worker.thinking_blocks), (2, 3))

    def test_anchors_are_unique(self):
        anchors = [step.anchor for step in self.main.steps + self.worker.steps]
        self.assertEqual(len(anchors), len(set(anchors)))

    def test_each_tool_call_paired_with_its_result(self):
        for transcript in (self.main, self.worker):
            calls = [step for step in transcript.steps if step.kind == "tool_call"]
            self.assertEqual(len(calls), transcript.tool_calls)
            for call in calls:
                self.assertIsNotNone(call.result, call.tool_use_id)
                self.assertEqual(call.result.kind, "tool_result")
                self.assertEqual(call.result.tool_use_id, call.tool_use_id)
                self.assertEqual(call.result.tool_name, call.tool_name)
        self.assertEqual(self.main.tool_calls, 4)
        self.assertEqual(self.worker.tool_calls, 1)

    def test_error_flagged(self):
        result = find_call(self.main, "toolu_error_1").result
        self.assertTrue(result.is_error)
        self.assertFalse(result.is_denied)

    def test_denial_flagged(self):
        result = find_call(self.main, "toolu_denied_1").result
        self.assertTrue(result.is_denied)

    def test_accepted_results_not_flagged(self):
        for tool_use_id in ("toolu_agent_1", "toolu_read_1"):
            result = find_call(self.main, tool_use_id).result
            self.assertFalse(result.is_error)
            self.assertFalse(result.is_denied)
        self.assertEqual(self.main.errors, 2)
        self.assertEqual(self.worker.errors, 0)

    def test_text_kept_whole(self):
        result = find_call(self.main, "toolu_read_1").result
        self.assertEqual(result.text, "<script>alert(1)</script>")
        agent_result = find_call(self.main, "toolu_agent_1").result
        self.assertEqual(agent_result.text, "Worker done: sample.txt written.")
        self.assertEqual(self.main.steps[-2].text, "Stop hook ran.")

    def test_garbage_signature_stays_thinking(self):
        garbage = self.worker.steps[6]
        self.assertEqual(garbage.kind, "thinking")
        self.assertEqual(garbage.text, "Thinking with a garbage signature.")

    def test_worker_linked_by_tool_use_id(self):
        call = find_call(self.main, "toolu_agent_1")
        self.assertIs(call.worker, self.worker)
        self.assertIs(self.worker.parent_step, call)
        self.assertEqual(self.worker.name, "agent-a0000000000000001")
        self.assertEqual(self.worker.agent_type, "poe:phase-worker")
        self.assertEqual(self.worker.description, "Execute unit 01a sample")
        self.assertEqual(self.worker.actor, "Execute unit 01a sample")

    def test_unknown_type_and_malformed_line_skipped_and_counted(self):
        # mystery-record and the malformed line; internal types are not counted.
        self.assertEqual(self.main.skipped, 2)
        self.assertEqual(self.worker.skipped, 0)
        self.assertEqual(self.task.skipped, 2)

    def test_token_totals_count_each_message_id_once(self):
        # msg_main_1 appears in two records but is counted once: 6 messages.
        self.assertEqual(self.main.input_tokens, 60)
        self.assertEqual(self.main.output_tokens, 120)
        self.assertEqual(self.main.cache_read_tokens, 600)
        self.assertEqual(self.main.cache_creation_tokens, 300)
        self.assertEqual(self.worker.input_tokens, 20)
        self.assertEqual(self.worker.output_tokens, 40)
        self.assertEqual(self.worker.cache_read_tokens, 200)
        self.assertEqual(self.worker.cache_creation_tokens, 100)

    def test_models_timestamps_and_cost(self):
        self.assertEqual(self.main.models, {"fake-model-1"})
        self.assertEqual(self.worker.models, {"fake-model-2"})
        self.assertEqual(self.main.first_timestamp, "2026-01-01T10:00:00.000Z")
        self.assertEqual(self.main.last_timestamp, "2026-01-01T10:00:29.000Z")
        self.assertAlmostEqual(self.main.cost_usd, 0.1234)
        self.assertIsNone(self.worker.cost_usd)


class ThinkingBlockKindTest(unittest.TestCase):
    NARRATION_SIGNATURE = "CAQSxQYKEQgTGAI4AUIJbmFycmF0aW9u"
    THINKING_SIGNATURE = "CAQS0AUKEAgTGAI4AUIIdGhpbmtpbmc="

    def test_narration_tag(self):
        self.assertEqual(poe_report.thinking_block_kind(self.NARRATION_SIGNATURE), "narration")
        # A long signature is decoded only from its start.
        long_signature = self.NARRATION_SIGNATURE + "A" * 5000
        self.assertEqual(poe_report.thinking_block_kind(long_signature), "narration")

    def test_thinking_tag(self):
        self.assertEqual(poe_report.thinking_block_kind(self.THINKING_SIGNATURE), "thinking")
        self.assertEqual(poe_report.thinking_block_kind(self.THINKING_SIGNATURE.rstrip("=")), "thinking")

    def test_missing_or_unreadable_signature_falls_back_to_thinking(self):
        for signature in (None, "", "x", "!!!not-base64!!!", 123, ["CAQS"]):
            self.assertEqual(poe_report.thinking_block_kind(signature), "thinking", signature)


class LoadTaskWithoutLogsTest(unittest.TestCase):
    def test_task_without_logs_has_no_sessions(self):
        with tempfile.TemporaryDirectory() as temp:
            task_dir = Path(temp) / "no-logs"
            task_dir.mkdir()
            (task_dir / "plan.md").write_text("# Plan\n", encoding="utf-8")
            task = poe_report.load_task(task_dir)
        self.assertEqual(task.sessions, [])
        self.assertEqual(task.skipped, 0)
        self.assertEqual(task.documents, [("plan.md", "# Plan\n")])

    def test_missing_task_dir_raises(self):
        with self.assertRaises(FileNotFoundError):
            poe_report.load_task(FIXTURE_TASK / "does-not-exist")


def run_main(argv):
    """Run poe_report.main and return (exit code, stdout, stderr)."""
    stdout, stderr = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = poe_report.main(argv)
    return code, stdout.getvalue(), stderr.getvalue()


def section(report, section_id):
    """The HTML of the <section> with the given id (sections are not nested)."""
    start = report.index(f'<section id="{section_id}"')
    return report[start:report.index("</section>", start)]


def step_html(report, anchor):
    """The HTML of one rendered step, up to the start of the next one."""
    start = report.index(f'id="{anchor}"')
    start = report.rindex("<div", 0, start)
    end = report.find('<div class="step ', start + 1)
    return report[start:end if end != -1 else len(report)]


class RenderFixtureReportTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.task = poe_report.load_task(FIXTURE_TASK)
        cls.report = poe_report.render_report(cls.task, generated="2026-01-02 00:00 UTC")
        cls.ids = set(re.findall(r'id="([^"]+)"', cls.report))

    def test_script_string_appears_only_escaped(self):
        self.assertNotIn("<script", self.report)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", self.report)

    def test_script_string_in_thinking_escaped(self):
        self.assertIn("&lt;script&gt;alert(2)&lt;/script&gt;", self.report)
        self.assertNotIn("<script>alert(2)", self.report)

    def test_thinking_text_visible_not_collapsed(self):
        step = self.task.sessions[0].workers[0].steps[3]
        html_of_step = step_html(self.report, step.anchor)
        self.assertIn('<span class="kind">thinking</span>', html_of_step)
        self.assertIn("<pre>Summary: the file was written.", html_of_step)
        self.assertNotIn("<details", html_of_step)

    def test_long_thinking_text_shows_first_lines(self):
        text = "\n".join(f"thought {n}" for n in range(30))
        step = poe_report.Step(index=1, timestamp=None, kind="thinking", text=text, anchor="step-x-1")
        rendered = poe_report.render_step(step)
        # The first lines are in the <summary>, which shows while collapsed.
        summary = re.search(r"<summary>(.*?)</summary>", rendered, re.S).group(1)
        self.assertIn("thought 0\nthought 1", summary)
        self.assertNotIn("thought 29", summary)
        self.assertIn("thought 29", rendered)

    def test_narration_labelled(self):
        step = self.task.sessions[0].workers[0].steps[5]
        html_of_step = step_html(self.report, step.anchor)
        self.assertIn('class="step kind-narration"', html_of_step)
        self.assertIn('<span class="kind">narration</span>', html_of_step)
        self.assertIn("Wrote sample.txt, so I&#x27;m reporting back.", html_of_step)
        self.assertIn(".kind-narration", self.report)

    def test_empty_thinking_message(self):
        step = self.task.sessions[0].workers[0].steps[4]
        html_of_step = step_html(self.report, step.anchor)
        self.assertIn("(thinking text not recorded; see README: Thinking text in the report)", html_of_step)

    def test_thinking_recorded_counts(self):
        overview = section(self.report, "overview")
        self.assertIn('<div class="label">Thinking</div><div class="value">thinking recorded: 3 of 4 blocks</div>',
                      overview)
        worker_section = self.report[self.report.index('id="transcript-agent-a0000000000000001"'):]
        self.assertIn("thinking recorded: 2 of 3 blocks", worker_section)
        self.assertIn("orchestrator only: models: fake-model-1 · tool calls 4 · errors 2 · "
                      "thinking recorded: 1 of 1 blocks", self.report)
        self.assertIn("session (orchestrator and workers): models: fake-model-1, fake-model-2 · "
                      "tool calls 5 · errors 2 · thinking recorded: 3 of 4 blocks", self.report)

    def test_no_external_urls_and_no_javascript(self):
        self.assertIsNone(re.search(r'(src|href)="https?:', self.report))
        self.assertNotIn("<script", self.report)
        self.assertNotIn("<link", self.report)

    def test_all_sections_present(self):
        for section_id in ("overview", "errors", "documents", f"transcript-{SESSION_ID}",
                           "transcript-agent-a0000000000000001"):
            self.assertIn(section_id, self.ids)
        self.assertIn("<nav>", self.report)
        self.assertIn("prefers-color-scheme: dark", self.report)
        for path, _ in self.task.documents:
            self.assertIn(f'<summary class="mono">{path}</summary>', self.report)

    def test_overview_cards(self):
        overview = section(self.report, "overview")
        for label, value in [("Task", "sample-task"), ("Sessions", "1"), ("Workers", "1"),
                             ("Tool calls", "5"), ("Errors", "2"), ("Tokens", "1,440"),
                             ("Cost", "$0.1234"), ("Duration", "29s"), ("Skipped records", "2")]:
            self.assertIn(f'<div class="label">{label}</div><div class="value">{value}</div>', overview)
        self.assertIn("| 01 | 01a | done |", overview)

    def test_error_rows_link_to_existing_anchors(self):
        errors = section(self.report, "errors")
        links = re.findall(r'href="#([^"]+)"', errors)
        self.assertEqual(len(links), 2)
        for anchor in links:
            self.assertIn(anchor, self.ids)
        self.assertIn(find_call(self.task.sessions[0].main, "toolu_error_1").result.anchor, links)
        self.assertIn("denied", errors)

    def test_every_internal_link_resolves(self):
        for anchor in re.findall(r'href="#([^"]+)"', self.report):
            self.assertIn(anchor, self.ids)

    def test_agent_call_and_worker_link_both_ways(self):
        call = find_call(self.task.sessions[0].main, "toolu_agent_1")
        self.assertIn('href="#transcript-agent-a0000000000000001"', self.report)
        worker_section = self.report[self.report.index('id="transcript-agent-a0000000000000001"'):]
        self.assertIn(f'href="#{call.anchor}"', worker_section)
        self.assertIn("poe:phase-worker", worker_section)

    def test_error_rows_marked(self):
        result = find_call(self.task.sessions[0].main, "toolu_error_1").result
        self.assertIn(f'class="step kind-tool_result error" id="{result.anchor}"', self.report)


class CollapsibleTextTest(unittest.TestCase):
    def shown_text(self, rendered):
        """Rejoin the preview and the collapsed rest as a reader would see them."""
        preview = re.search(r'<span class="mono preview">(.*?)</span>', rendered, re.S).group(1)
        rest = re.search(r"<pre>(.*?)</pre>", rendered, re.S).group(1)
        return html.unescape(preview), html.unescape(rest)

    def test_short_text_is_not_collapsed(self):
        self.assertEqual(poe_report.collapsible_text("a\nb", 3), "<pre>a\nb</pre>")

    def test_long_text_collapsed_but_whole(self):
        text = "\n".join(f"line {n}" for n in range(10))
        preview, rest = self.shown_text(poe_report.collapsible_text(text, 3))
        self.assertEqual(preview + "\n" + rest, text)

    def test_long_single_line_collapsed_but_whole(self):
        text = "x" * 5000 + "\nlast"
        preview, rest = self.shown_text(poe_report.collapsible_text(text, 3))
        self.assertEqual(preview + rest, text)


class MainTest(unittest.TestCase):
    def test_writes_report_and_prints_path(self):
        with tempfile.TemporaryDirectory() as temp:
            task_dir = Path(temp) / "no-logs"
            task_dir.mkdir()
            (task_dir / "plan.md").write_text("# Plan\n", encoding="utf-8")
            code, stdout, _ = run_main([str(task_dir)])
            report_path = task_dir / "report.html"
            self.assertEqual(code, 0)
            self.assertEqual(stdout.strip(), str(report_path))
            report = report_path.read_text(encoding="utf-8")
        self.assertIn("No transcripts were found", report)
        self.assertIn("# Plan", report)

    def test_missing_dir_exits_non_zero(self):
        code, stdout, stderr = run_main([str(FIXTURE_TASK / "does-not-exist")])
        self.assertNotEqual(code, 0)
        self.assertEqual(stdout, "")
        self.assertIn("not found", stderr)

    def test_unwritable_report_exits_non_zero(self):
        with tempfile.TemporaryDirectory() as temp:
            task_dir = Path(temp) / "task"
            (task_dir / "report.html").mkdir(parents=True)  # a directory cannot be written as a file
            code, _, stderr = run_main([str(task_dir)])
        self.assertNotEqual(code, 0)
        self.assertIn("could not write", stderr)


if __name__ == "__main__":
    unittest.main()
