# Phase 02: HTML rendering and command-line entry

Depends on: unit 01a verified.

## Unit 02a: render `report.html`

**Goal.** Add the **Render** part of plan §1 to `skills/poe/scripts/poe_report.py`, plus `main()`, so `python3 poe_report.py poe/<task-slug>` writes `poe/<task-slug>/report.html` and prints its path.

**Inputs to read.**

- `poe/poe-report-dashboard/plan.md` (Approach §1 "Render", Acceptance criteria)
- `poe/poe-report-dashboard/progress/01a-parser.md` (the interface actually built, and the usage rule)
- `skills/poe/scripts/poe_report.py`, `tests/test_poe_report.py`, `tests/fixtures/poe/sample-task/`

**Files it may change.** `skills/poe/scripts/poe_report.py` (add rendering and `main`; change the loader only to fix a bug, noted in the progress notes), `tests/test_poe_report.py` (add tests). Not the fixture, unless a test needs data it lacks (note why).

**What to build** (all from the plan):

- One HTML string, inline CSS, no JavaScript, no external URLs. Light/dark via `prefers-color-scheme`.
- Sidebar of anchor links: overview, errors, documents, each session with workers indented.
- Overview cards: slug, date generated, `status.md` as written (preformatted), sessions, workers, tool calls, errors, tokens, cost, duration, skipped records.
- Errors section: every errored or denied tool result with tool name, one-line excerpt, link to the step anchor.
- Documents: each in a `<details>` with `<pre>`.
- Session timelines, ordered by first timestamp, then each worker: one row per step with a coloured left border by kind, timestamp, content. Tool input/output in monospace `<details>` with the first few lines visible in the summary. Error rows red. Thinking collapsed. Worker sections start with type, description, model(s), totals, and a link back to the starting step; the `Agent` call links forward to the worker section.
- Every piece of log or document text through `html.escape`. Never truncate; collapse instead.
- No `logs/` or no transcripts: render documents and say no transcripts were found.
- `main`: exit 0 and print the path on success; non-zero with a message if the task dir does not exist or the file cannot be written.

Keep it plain: small functions, f-strings or simple string building, no template engine.

**Tests to add.** `<script>alert(1)</script>` from the fixture appears only escaped; no `src="http` / `href="http` in the output; a dir without `logs/` still writes a report containing the "no transcripts" message; `main` on a missing dir exits non-zero; error rows link to existing anchors.

**Non-goals.** No JavaScript, search, charts, JSON export, Markdown rendering, SKILL.md/README edits.

**Verification.**

```sh
cd /Users/sbandyopadhyay/projects/SCRIPTS/custom_claude_plugins/poe
python3 -m unittest discover tests -v
python3 skills/poe/scripts/poe_report.py tests/fixtures/poe/sample-task   # writes into the fixture dir: delete that report.html afterwards, do not commit it
grep -nE '(src|href)="https?:' tests/fixtures/poe/sample-task/report.html; echo "external refs: $?"
```

**Completion criteria.** Tests pass (observed). The fixture report contains every section above (checked by grep or by the tests). No leftover generated `report.html` in the fixture dir.

**Progress notes:** `poe/poe-report-dashboard/progress/02a-render.md`
