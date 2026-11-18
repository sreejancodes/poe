# Plan: Capture thinking text in the poe report

## Objective

Make `report.html` show what the orchestrator and each worker were thinking, not just what they did. Today every thinking step in the report reads "(thinking text not recorded)". This plan makes the text get recorded and makes the report show it clearly.

## Findings that shape the plan

Checked on this machine (Claude Code 2.1.326, Opus 5.5 and Haiku 5.5):

- **The text is missing from the transcripts, not from the report.** In `poe/poe-report-dashboard/logs/`, all 109 real thinking blocks have `"thinking": ""` and only a `signature`. `poe_report.py` already renders thinking text when it is present.
- **Why it is empty.** Claude Code asks the API for `thinking: {"display": "omitted"}`. The exact parameter is logged in each `api-request` record of the transcript. For Opus 4.7 and later models, `omitted` is also the API default. The API never returns raw thinking. The most it returns is `"summarized"`, a prose summary of the reasoning.
- **What switches it on** (read from the Claude Code bundle and checked by test runs):
  - Interactive sessions: the `showThinkingSummaries: true` setting (user or project `settings.json`, default `false`) requests `summarized`.
  - Headless `claude -p` with text or json output: the setting is **ignored**, and `display` is forced to `omitted`. Only the CLI flag `--thinking-display summarized` turns it on. Tested: with the setting alone, the thinking stayed empty. With the flag, the transcript held a 98-character summary.
  - Subagents: in interactive sessions they inherit the parent's display mode. In headless sessions they are forced to `omitted` unless the display was set explicitly with the flag. This comes from reading the bundle and is **not yet tested**.
- **Some "thinking" blocks are narration.** The 5 thinking blocks that do have text are short progress updates ("All 01a checks pass …, so I'm marking 01a verified"). Their base64 `signature` decodes to a tag `narration`, while real thinking blocks carry `thinking`. The report currently labels both "thinking".
- **Thinking from past sessions cannot be recovered.** The encrypted `signature` is only for the API. The existing transcripts in `poe/poe-report-dashboard/logs/` will keep showing "not recorded".

## Scope

In scope:

- `README.md`: a short "Thinking text in the report" section explaining that the report can only show thinking that Claude Code recorded, and how to turn it on:
  - interactive: `"showThinkingSummaries": true` in `~/.claude/settings.json` (all projects) or the project's `.claude/settings.json`;
  - headless: `claude -p --thinking-display summarized …`;
  - it is a summary, not the raw reasoning, and past sessions cannot be filled in.
  Also add `--thinking-display summarized` to the README's headless example, if there is one.
- `skills/poe/scripts/poe_report.py`:
  - **Show the text.** A thinking step with text is shown like assistant text: the first lines visible, the rest in `<details>`. It is no longer fully collapsed.
  - **Label narration.** A thinking block whose `signature` decodes to the `narration` tag is shown as kind `narration`, with its own label and colour. Anything that does not decode, or carries no tag, stays `thinking`. One small function reads it defensively.
  - **Say why it is empty.** The empty-thinking message becomes "(thinking text not recorded; see README: Thinking text in the report)".
  - **Count it.** The overview cards and the per-transcript totals add "thinking recorded: N of M blocks", so it is obvious whether capture was on for a run.
- `tests/test_poe_report.py` and the fixture: add a summarized thinking block, an empty one, and a narration block. Test the labels, the counts, the empty message, and HTML escaping of thinking text.

Out of scope:

- Changing the user's settings or the repository's `.claude/settings.json` automatically. Turning on summaries also changes what the user sees in the terminal, so it is the user's choice. The README tells them how.
- Shipping the setting inside the plugin. Whether a plugin can set `showThinkingSummaries` is not documented, so it is not relied on.
- Recovering thinking for existing transcripts, and any attempt to get raw (unsummarized) thinking.
- Changes to `SKILL.md` or `phase-worker.md`. The skill cannot change the display mode of the session it runs in.
- Other dashboard features (search, charts, live view, JSON export).

## Assumptions

- The `narration` and `thinking` tags in the signature are undocumented internals. If they disappear or change, the fallback is to label the block `thinking`, which is today's behaviour. Nothing breaks.
- Summarized thinking is written to the transcript in the same `thinking` field as before. This was observed in a headless run. The interactive path writes through the same transcript code, and the end-to-end check below confirms it.

## Acceptance criteria

- `python3 -m unittest discover tests` passes, including the new tests:
  - a summarized thinking block appears in the report with its text visible;
  - a narration block is labelled `narration`, and a block with an unreadable or missing signature falls back to `thinking`;
  - an empty block shows the "not recorded" message, and the overview shows the right "N of M" count;
  - a `<script>` string inside thinking text is escaped.
- A real poe run with summaries on produces thinking text in the main transcript **and** in the worker transcripts, and `report.html` shows it.
- Running the script on the existing `poe/poe-report-dashboard/` still works. It shows "thinking recorded: 0 of 109" and 5 narration steps.
- `README.md` explains the setting, the flag, and the limits. `claude plugin validate .` still passes.

## Risks

- **Undocumented internals.** Both the thinking display logic and the signature tag come from reading the bundle, and may change in a later Claude Code version. Mitigation: the report only reads data defensively, and the README describes the documented setting and flag, not the internals.
- **Subagent inheritance not yet seen.** If interactive workers do not inherit summarized display, worker thinking stays empty. The "N of M" count makes this visible per worker, and the README would say so. There is no setting to force it per agent, so this would be reported, not worked around.
- **Cost and latency.** Summaries are produced on the API side. Any extra latency or cost is not documented. The flag is opt-in, so the default behaviour is unchanged.
- **Sensitive data.** The report gains reasoning text. The existing gitignore advice already covers `report.html` and `logs/`.

## Testing and validation

1. Unit tests: `python3 -m unittest discover tests` with the extended hand-written fixture. The fixture holds no real session data.
2. Existing data: run `python3 skills/poe/scripts/poe_report.py poe/poe-report-dashboard`. Check the 0-of-109 count and the 5 narration steps, and that nothing else changed (diff the step counts against the current report).
3. Headless end to end: in a scratch directory, run `claude -p --thinking-display summarized --output-format json "<prompt that spawns one general-purpose subagent to do a small reasoning task>"`. Copy the main and subagent transcripts into a scratch `poe/<slug>/logs/`, build the report, and check that thinking text appears for both. This also tests the headless subagent path.
4. Interactive check (manual, by the user): with `"showThinkingSummaries": true` set, run one small `/poe:poe` task that starts a worker, then `/poe:poe report`. Check that the main and worker sections both show thinking text. This is the only way to confirm interactive subagent inheritance.
5. Static checks: no external URLs in the report, and `claude plugin validate .` passes.
