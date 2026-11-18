# 01a-parser: done

## Done so far
- Read phase brief (Unit 01a) and plan.
- Inspected real transcripts (7234187e main + worker agent-a1c06f9ad1f6bb6e9; poe/poe-report-dashboard/logs/*) with scratch scripts in the session scratchpad (inspect.py, shapes.py). Findings under Decisions.
- Wrote `poe_report.py` (Load + Timeline only; no HTML, no main()), the hand-written fixture, and 15 unittest tests.
- Verified on the fixture, on `poe/poe-report-dashboard`, and on a scratch copy of the 7234187e session with its worker.

## Files changed or produced
- `skills/poe/scripts/poe_report.py` (new)
- `tests/test_poe_report.py` (new)
- `tests/fixtures/poe/sample-task/` (new): `plan.md`, `status.md`, `phases/01-x.md`, `progress/01a-x.md`, `logs/11111111-2222-3333-4444-555555555555/11111111-2222-3333-4444-555555555555.jsonl`, `.../subagents/agent-a0000000000000001.jsonl` + `.meta.json`. All fake data. Main transcript contains: Agent call `toolu_agent_1` linked to the worker; `is_error` result (`toolu_error_1`); denied result (`toolu_denied_1`, decision `reject`, also `is_error` as in real data); `<script>alert(1)</script>` result (`toolu_read_1`, for phase 02's escaping test); unknown type `mystery-record`; one malformed line (line 14); a `cost-state` record (0.1234); `msg_main_1` split over two records (dedup test); ignored internal types `session-owner` and (worker) `attachment`.
- Scratch only (not in repo): `/private/tmp/claude-1128299617/-Users-sbandyopadhyay-projects-SCRIPTS-custom-claude-plugins-poe/e1650fd1-5110-41f6-944b-7f0774e47f42/scratchpad/poe/hello-txt/logs/7234187e-d86b-4afa-adca-ee152aac72bf/` (copy of the real session with subagents/).

## Tests run and observed results
- `python3 -m unittest discover tests -v`: Ran 15 tests, OK.
- Brief's one-liner on `poe/poe-report-dashboard`: `[('b046f754-...', 23, 0), ('5d0a8152-...', 19, 0)] 0` (2 sessions, no workers, 0 skipped).
- Scratch 7234187e task: 1 session, main 36 steps, 1 worker (`agent-a1c06f9ad1f6bb6e9`, actor "Execute unit 01-a hello.txt") linked to the `Agent` call `toolu_01WorK1HYL13BQvuibYY95jR` both ways; every tool call paired (0 unpaired); 3 denied Bash results flagged (is_error and is_denied); 1 worker error; skipped 0; main cost_usd 0.460544.
- Deduped session token sum (main + worker) = input 28, output 5876, cache read 334255, cache creation 42743, which matches the main transcript's `cost-state.modelUsage` exactly.

## Decisions and assumptions
- **Usage dedup (confirmed):** Claude Code writes one `assistant` record per content block; all records of one API message repeat the same `message.id` and an identical `message.usage` (7234187e main: 21 records / 9 ids, 0 ids with differing usage; worker 6/5; repo logs 10/5 and 12/6). **Rule: count usage once per `message.id` within a transcript; records without an id are each counted.** Phase 03's independent sum must use the same rule. With this rule the totals equal cost-state `modelUsage` (see above).
- cost-state in the main transcript covers the whole session including workers. `Transcript.cost_usd` = last `cost-state.totalCostUSD` in that transcript (so main only; workers None). Phase 02 should show the session cost from `main.cost_usd` and not add worker costs.
- Token mapping: `input_tokens`, `output_tokens`, `cache_read_input_tokens` -> `cache_read_tokens`, `cache_creation_input_tokens` -> `cache_creation_tokens`.
- Skipped counting: malformed lines, non-object lines, unknown record types, user/assistant records without usable content, unknown assistant/user block shapes, and a cost-state without a numeric totalCostUSD. Known internal types (`INTERNAL_RECORD_TYPES` + prefix `file-history-`, from the plan's list plus `api-request-shape`) are ignored and NOT counted, so the skipped count signals real format drift instead of being always large.
- `errors` counts tool results with `is_error` or `is_denied` (real denials carry both).
- Steps: `index` is 1-based within a transcript; `anchor` = `step-<transcript name>-<index>` (unique across a task since session ids and agent ids are unique). Tool call `text` is `json.dumps(input, indent=2, ensure_ascii=False)`. Tool result `text` flattens list content: text blocks joined by newline, other blocks as `[<type> block]`. Tool results also get `tool_name` copied from their call. Non-text user blocks (e.g. image) become a `user` step `[<type> block]`. `redacted_thinking` is treated as `thinking`. Thinking text is empty in current transcripts (redacted), kept as an empty `thinking` step.
- System step text: `content` if a non-empty string, else the `subtype`; non-empty `hookErrors` are appended as JSON.
- Timestamps: `first_timestamp`/`last_timestamp` are min/max of step timestamps (ISO strings compare correctly).
- Worker linking searches tool calls in main and all workers of the session (covers nested workers), by `.meta.json` `toolUseId`, regardless of tool name. Missing/malformed meta -> worker unlinked, `actor` falls back to agent_type then `agent-<id>`.
- Ordering: sessions by main first timestamp (no timestamp last, then by id); workers likewise by first timestamp. Documents: plan.md, status.md, summary.md, then sorted phases/*.md, then sorted progress/*.md.
- A missing main `<session-id>.jsonl` gives an empty main Transcript (still lists workers).

## Interface deviations from the brief
- None in names/fields. Additions: `load_task` raises `FileNotFoundError` if the task directory does not exist (phase 02's main() should catch it and exit non-zero). Helper `TimelineBuilder` class and module constants `INTERNAL_RECORD_TYPES`, `TASK_DOCUMENT_NAMES`, `TASK_DOCUMENT_FOLDERS` exist but are internal.

## Next step / remaining work
- None for 01a. Phase 02 adds rendering and `main()` on top of `load_task`.
