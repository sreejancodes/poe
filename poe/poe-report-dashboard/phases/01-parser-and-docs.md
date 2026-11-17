# Phase 01: transcript parser, and skill/README docs

Depends on: approved split. Units 01a and 01b touch different files and run in parallel.

Plan: `poe/poe-report-dashboard/plan.md` (read Assumptions, Approach §1–3, Acceptance criteria).

## Unit 01a: load and timeline in `poe_report.py`, fixture, parsing tests

**Goal.** Create `skills/poe/scripts/poe_report.py` with the **Load** and **Build a simple timeline** parts of plan §1 (no HTML yet), the hand-written fixture, and the parsing tests. Phase 02 adds rendering to the same file on top of the interface below.

**Inputs to read.**

- `poe/poe-report-dashboard/plan.md`
- Sample real transcripts, to confirm field names (read with `head`/`python3`, never whole files; lines can be very long):
  - with workers: `~/.claude/projects/-private-tmp-claude-1128299617--Users-sbandyopadhyay-projects-SCRIPTS-custom-claude-plugins-poe-cb353a49-6d4d-41b6-911e-14acc86a0355-scratchpad-02a-e2e/7234187e-d86b-4afa-adca-ee152aac72bf.jsonl` and its `7234187e-.../subagents/`
  - `poe/poe-report-dashboard/logs/*/*.jsonl`

**Files it may change.** Create only:

- `skills/poe/scripts/poe_report.py`
- `tests/test_poe_report.py`
- `tests/fixtures/poe/sample-task/**`

**Interface for phase 02** (plain dataclasses, standard library only; names may be adjusted if recorded in the progress notes):

- `Step`: `index`, `timestamp` (str or None), `kind` (one of `user`, `assistant`, `thinking`, `tool_call`, `tool_result`, `system`), `text`, `tool_name`, `tool_use_id`, `is_error`, `is_denied`, `anchor` (unique HTML id string), `result` (the paired `tool_result` Step for a `tool_call`, else None), `worker` (the linked worker Transcript for an `Agent` call, else None).
- `Transcript`: `name` (session id or `agent-<id>`), `actor` (`orchestrator` or the worker's description/type), `agent_type`, `description`, `steps`, `models` (set), token totals (`input_tokens`, `output_tokens`, `cache_read_tokens`, `cache_creation_tokens`), `tool_calls`, `errors`, `first_timestamp`, `last_timestamp`, `cost_usd` (or None), `skipped` (count), `parent_step` (the `Agent` call Step, for workers).
- `Session`: `session_id`, `main` (Transcript), `workers` (list of Transcript).
- `Task`: `slug`, `task_dir`, `documents` (ordered list of `(relative_path, text)` for `plan.md`, `status.md`, `summary.md`, `phases/*.md`, `progress/*.md`), `sessions` (ordered by first timestamp), `skipped` (total).
- `load_task(task_dir: Path) -> Task`.

**Rules from the plan.** Skip unknown record types and malformed lines, counting them. Pair calls and results by `tool_use_id`. Link workers via `.meta.json` `toolUseId` regardless of the tool's name (`Agent` or older `Task`). Errors: `is_error` true; denied: `permissionDecision.decision` present and not `accept`. Keep file order. Never truncate text.

**Check before trusting usage.** Claude Code may write one `assistant` record per content block, each repeating the same `message.id` and `message.usage`. Check this in the real transcripts. If it happens, count usage once per `message.id`, and record the rule in the progress notes (phase 03's independent sum must use the same rule).

**Fixture** (hand-written, no real session data): `tests/fixtures/poe/sample-task/` with `plan.md`, `status.md`, one `phases/01-x.md`, one `progress/01a-x.md`, and `logs/<fake-session-id>/` holding a main transcript and `subagents/agent-<id>.jsonl` + `.meta.json`. Include: one `Agent` tool call linked to the worker, one tool result with `is_error: true`, one denied result, one tool result containing `<script>alert(1)</script>` (used by phase 02's escaping test), one unknown record type, one malformed line, and a `cost-state` record.

**Tests** (`unittest`): expected step count; each tool call paired with its result; error and denial flagged; worker linked via `toolUseId`; unknown type and malformed line skipped and counted; token totals; a task dir without `logs/` loads with no sessions.

**Non-goals.** No HTML rendering, no `main()` writing files, no SKILL.md/README edits, no pip packages.

**Verification.**

```sh
cd /Users/sbandyopadhyay/projects/SCRIPTS/custom_claude_plugins/poe
python3 -m unittest discover tests -v
python3 -c 'import sys; sys.path.insert(0,"skills/poe/scripts"); import poe_report as p; from pathlib import Path; t=p.load_task(Path("poe/poe-report-dashboard")); print([(s.session_id, len(s.main.steps), len(s.workers)) for s in t.sessions], t.skipped)'
```

**Completion criteria.** Tests pass (observed). `load_task` runs without error on `poe/poe-report-dashboard` and on a scratch copy of the 7234187e session with workers (copy into the scratchpad, not the repo), with workers linked. Interface and the usage-dedup finding recorded in the notes.

**Progress notes:** `poe/poe-report-dashboard/progress/01a-parser.md`

## Unit 01b: SKILL.md and README

**Goal.** Plan §2 and §3: document the `report` mode, the automatic build at the end of `execute` and `resume`, `report.html` in the Files layout, the manual command, and gitignore advice.

**Inputs to read.** `poe/poe-report-dashboard/plan.md` (§2, §3, Assumptions on `${CLAUDE_SKILL_DIR}`), `skills/poe/SKILL.md`, `README.md`.

**Files it may change.** `skills/poe/SKILL.md`, `README.md`.

**Steps.**

1. Confirm in the skills documentation (https://code.claude.com/docs/en/skills) whether `${CLAUDE_SKILL_DIR}` is substituted in `SKILL.md`. Use it if so; otherwise use `${CLAUDE_PLUGIN_ROOT}/skills/poe/scripts/poe_report.py`. Record the source in the notes.
2. Add `report [plan-path]` to Operating modes: copy the logs (as in the Logs section), run `python3 "<script>" poe/<slug>`, give the user the report path.
3. Execute step 9 and `resume`: after `summary.md` and the log copy, build the report; a failure is reported but never blocks, same as log copies. Mention `report` in the Logs section's list of modes that copy logs.
4. Files layout: add `report.html   step-by-step report built from the files above and logs/`.
5. README: `report` in the usage list, `report.html` in the layout, the manual command, and the note that `report.html` holds full transcripts so it belongs in `.gitignore` with `logs/`. Update `argument-hint` in SKILL.md frontmatter to include `report`.

Keep edits minimal and in the existing style; do not rewrite unrelated sections.

**Non-goals.** No script or test changes; no change to how logs are copied.

**Verification.**

```sh
cd /Users/sbandyopadhyay/projects/SCRIPTS/custom_claude_plugins/poe
git diff --stat
grep -n 'report' skills/poe/SKILL.md README.md
claude plugin validate .
```

**Completion criteria.** Every item in steps 2–5 present; README matches SKILL.md; `claude plugin validate .` passes (observed).

**Progress notes:** `poe/poe-report-dashboard/progress/01b-docs.md`
