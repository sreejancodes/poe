# Plan: Inspect-style `report.html` for a poe task

## Objective

Turn what poe saves for a task in `poe/<task-slug>/` (plan, status, phase briefs, progress notes, summary, and the copied Claude Code transcripts in `logs/`) into one self-contained `poe/<task-slug>/report.html`. The page, styled after the Inspect AI log viewer, lets a person follow, step by step, what the orchestrator and each worker did: prompts, replies, tool calls and their results, errors, and token and cost totals.

The page has two later uses, which shape it now but are not built here:

- **Stacktrace:** when a run goes wrong, errored and denied tool calls can be found quickly and traced back to the step that caused them.
- **LLM-as-judge input:** all content is plain, server-rendered HTML text (no data hidden in JavaScript), so a model can be given the file as is.

## Scope

In scope:

- `skills/poe/scripts/poe_report.py` (new): a Python 3 script using only the standard library. `python3 poe_report.py poe/<task-slug>` reads that task directory and writes `poe/<task-slug>/report.html`.
- `tests/test_poe_report.py` and `tests/fixtures/` (new): `unittest` tests against a small, hand-written transcript fixture.
- `skills/poe/SKILL.md`:
  - a new `report [plan-path]` mode that (re)builds the report;
  - an automatic report build at the end of `execute` and `resume`, right after the log copy;
  - `report.html` added to the Files layout.
- `README.md`: the `report` mode, `report.html` in the layout, how to run the script by hand, and gitignore advice.

Out of scope:

- The LLM-as-judge itself, scoring, and any JSON or other machine-readable export.
- Converting to Inspect AI's `.eval` log format, or depending on `inspect-ai` or any other pip package. "Inspect style" means the look and layout, not the tool.
- A live server, auto-refresh, search boxes, charts, or comparing several tasks.
- Changing how logs are copied. The report works with whatever is in `logs/`.
- Rendering Markdown to HTML. The task's `.md` files are shown as preformatted text.
- The older draft at `plans/poe-report-dashboard/plan.md` (written before output moved to `poe/`). This file replaces it; it is left untouched for the user to delete.

## Assumptions

- The layout is the one in the current `SKILL.md`: `poe/<slug>/{plan.md, status.md, summary.md, phases/*.md, progress/*.md, logs/<session-id>/<session-id>.jsonl, logs/<session-id>/subagents/agent-<id>.jsonl, agent-<id>.meta.json}`. Any of these may be missing, and there may be several sessions (one per `plan`, `split`, `execute`, `resume` run).
- The Claude Code transcript format is not documented and changes between versions. Checked on this machine (Claude Code 2.1.326) against existing transcripts:
  - Each line is a JSON record with a `type`. The records that matter are `user` and `assistant` (with `message.content` blocks `text`, `thinking`, `tool_use`, `tool_result`), `system`, and `cost-state` (`totalCostUSD`, `totalDuration`, `modelUsage`). Other types (`attachment`, `api-request`, `api-request-blob`, `mode`, `session-owner`, `atis-latch`, `last-prompt`, `ai-title`, `permission-mode`, `tools-used`, `file-history-*`, `queue-operation`, ...) are internal and skipped.
  - `assistant` records carry `timestamp`, `message.model`, and `message.usage` (input, output, cache read and cache creation tokens).
  - `user` records holding a `tool_result` block may carry `toolUseResult` and `permissionDecision` (`decision`, `source`). The block itself may have `is_error: true`.
  - A worker's `agent-<id>.meta.json` holds `agentType`, `description` and `toolUseId`. `toolUseId` matches the `id` of the `Agent` `tool_use` block in the main transcript, which is how a worker is linked to the step that started it.
- A tool result counts as an error when `is_error` is true, or as denied when `permissionDecision.decision` is present and not `accept`. Both are read defensively.
- Records are shown in file order (the order Claude Code appended them). The `parentUuid` tree is not reconstructed.
- `python3` (3.9 or later) is available wherever poe runs. This machine has 3.12.
- Skills substitute `${CLAUDE_SKILL_DIR}`, so `SKILL.md` can call the bundled script by its path. **To be confirmed during implementation** against the skills documentation; otherwise use `${CLAUDE_PLUGIN_ROOT}/skills/poe/scripts/poe_report.py`.

## Approach

### 1. The script, `skills/poe/scripts/poe_report.py`

One file of small functions, in three steps.

**Load.** Read the task's `.md` files as text. For each `logs/<session-id>/` folder, parse the main `.jsonl` and each `subagents/agent-*.jsonl` with its `.meta.json`. A line that is not valid JSON, or a record without the expected fields, is counted and skipped; it never stops the script.

**Build a simple timeline per transcript.** Turn the useful records into a flat list of steps, each with: time, actor (orchestrator or worker name), kind, and text. The kinds are:

- user prompt
- assistant text
- thinking (collapsed)
- tool call (tool name and its input)
- tool result (output; marked as an error or denial as above)
- system or hook message

Each tool call is paired with its result by `tool_use_id`. An `Agent` tool call links to the worker's own timeline. Per transcript, and in total, the script adds up tokens, the number of tool calls and errors, the model or models, the duration (first to last timestamp), and the cost from the last `cost-state` record when present.

**Render.** Write one HTML file with inline CSS and no external resources, so it opens offline and can be attached or emailed as a single file. The layout follows Inspect's viewer:

- **Sidebar:** anchor links to the overview, the errors list, the task documents, and each session, with its workers indented under it.
- **Overview cards:** the task slug, the date generated, the status table from `status.md` as written, the number of sessions and workers, tool calls, errors, tokens, cost, duration, and the number of skipped records.
- **Errors:** every errored or denied tool call across all transcripts, each with its tool name, a one-line excerpt, and a link to the step. This is the stacktrace view.
- **Task documents:** `plan.md`, `status.md`, `summary.md`, phase briefs and progress notes, each in a collapsible `<details>` block of preformatted text.
- **Session timelines:** one section per session, ordered by first timestamp, then one per worker. Each step is a row with a coloured left border by kind, a timestamp, and its content. Tool inputs and outputs are in monospace inside `<details>`, with the first few lines visible. Error rows are red. A worker section starts with its type, description, model and totals, and links back to the step that started it.
- Light and dark colours through `prefers-color-scheme`. `<details>` handles collapsing, so the page needs no JavaScript.

All text from the logs goes through `html.escape`, because transcripts contain arbitrary file contents and command output. Content is never truncated in the HTML. Long blocks are collapsed, not cut, so the file stays complete for a stacktrace or a judge.

If `logs/` is missing or empty, the report still renders the documents and says that no transcripts were found.

The script prints the path of the written report and exits 0. It exits non-zero only if the task directory does not exist or the report cannot be written.

### 2. Skill changes, `skills/poe/SKILL.md`

- Operating modes gain `report [plan-path]`: copy the logs (as in the Logs section), then run `python3 "${CLAUDE_SKILL_DIR}/scripts/poe_report.py" poe/<slug>` and give the user the path of the report.
- Execute mode step 9 and `resume`: after writing `summary.md` and copying the logs, build the report the same way. A failure is reported in the reply but never blocks the task, the same rule as for log copies.
- Files layout: add `report.html   step-by-step report built from the files above and logs/`.

### 3. README

Add the `report` mode to the usage list, `report.html` to the layout, the manual command `python3 <plugin>/skills/poe/scripts/poe_report.py poe/<slug>`, and a note that `report.html` contains the full transcripts, so it belongs in `.gitignore` alongside `logs/`.

## Acceptance criteria

- `python3 -m unittest discover tests` passes. The tests cover:
  - parsing the fixture: the expected number of steps, tool calls paired with their results, an error flagged, and a worker linked by `toolUseId`;
  - skipping unknown record types and malformed lines without crashing;
  - HTML escaping: a `<script>` string in a tool result appears escaped in the output;
  - a task directory without `logs/` still produces a report.
- Running the script on real transcripts (a poe session from this project, including one with workers, copied into a scratch `poe/<slug>/logs/`) writes a `report.html` that opens in a browser and shows:
  - all sessions and their workers;
  - every tool call, in order, with its result;
  - every `is_error` tool result, listed in the Errors section;
  - token totals that match a separate sum over `message.usage` in the same files.
- The report opens with no network access (no external URLs in the file).
- `SKILL.md` documents the `report` mode and the automatic build. `README.md` matches it. `claude plugin validate .` still passes.
- `/poe:poe report <slug>` run with `claude --plugin-dir .` in a scratch directory produces `poe/<slug>/report.html`.

## Risks

- **Transcript format changes.** The parser relies on undocumented fields. Mitigation: read fields defensively, skip what is unknown, and show the count of skipped records in the overview, so silent loss is visible.
- **Missing logs.** A log copy can fail (for example, refused under a restrictive permission mode). Mitigation: the report degrades to documents only and says why.
- **Permission prompts.** Running `python3` on a script outside the working directory may need approval in restrictive modes. Mitigation: the same "report and carry on" rule as for logs. The README gives the manual command.
- **Sensitive data.** The report contains everything in the transcripts, including file contents and command output. Mitigation: gitignore advice. Nothing is uploaded.
- **Large files.** A long execute run can produce several MB of transcripts, and so a large HTML file. Acceptable for a local file. Collapsed `<details>` keep it usable in a browser.

## Testing and validation

1. Unit tests: `python3 -m unittest discover tests`, using a small, hand-written fixture in `tests/fixtures/poe/sample-task/` with a main transcript, one worker transcript and meta file, one errored tool call, one unknown record type, and one malformed line. The fixture holds no real session data.
2. Real data: copy the transcripts of a real poe session from `~/.claude/projects/` into a scratch `poe/<slug>/logs/` (outside the repository, never committed), run the script, and check the report in a browser against the acceptance criteria above. Check the token totals with a short independent `python3` sum over the same files.
3. End to end: `claude --plugin-dir .` in a scratch directory, run `/poe:poe report <slug>` on that scratch task, and confirm that `report.html` is written and the skill reports its path.
4. Static checks: `grep -nE '(src|href)="https?:' report.html` finds no external resources (escaped URLs inside log text don't match), and `claude plugin validate .` passes.
