# Phase 01: report changes, tests and README

Depends on: nothing. One unit.

Read first: `poe/poe-thinking-capture/plan.md` (the whole plan; the "Findings" and "Scope" sections define the behaviour).

## Unit 01a: thinking and narration in `poe_report.py`, tests, README

**Goal.** Implement the `poe_report.py`, test and README items of the plan's Scope:

1. Thinking text with content is shown like assistant text: first lines visible via the existing `collapsible_text` helper (use `TEXT_PREVIEW_LINES`), rest in `<details>`. It is no longer fully collapsed.
2. New step kind `narration`: an assistant `thinking` block whose `signature` base64-decodes to bytes containing the tag `narration` near the start is labelled `narration`, with its own CSS colour (light and dark) and label. A missing, empty or undecodable signature, or one without the tag, stays `thinking`. Write one small, defensive function for this (no exceptions escape it). Known real prefixes: `CAQSxQYKEQgTGAI4AUIJbmFycmF0aW9u` decodes to bytes ending in `narration`; `CAQS0AUKEAgTGAI4AUIIdGhpbmtpbmc=` decodes to bytes ending in `thinking`. Decode only a short prefix of the signature (signatures can be several KB); pad the base64 so a cut prefix decodes.
3. Empty thinking shows "(thinking text not recorded; see README: Thinking text in the report)".
4. Count thinking blocks per transcript (narration excluded): recorded (non-empty) and total. Show "thinking recorded: N of M blocks" in the overview cards (task totals) and in each transcript's totals line.
5. README: add a section `## Thinking text in the report` (place it after the report/`.gitignore` text, before `## Context settings`). Cover: the report can only show what Claude Code recorded; interactive sessions need `"showThinkingSummaries": true` in `~/.claude/settings.json` or the project's `.claude/settings.json`; headless `claude -p` ignores that setting and needs `--thinking-display summarized`; the text is a summary, not the raw reasoning; earlier sessions cannot be filled in; workers in interactive sessions are expected to inherit the setting (to be confirmed by the user's interactive check). Mention "narration" steps in one sentence. Keep it short, in the style of the existing README. Do not describe the signature internals.

**Files to read.** `skills/poe/scripts/poe_report.py` (thinking handling is in `TimelineBuilder.add_assistant_block` and `render_step`; totals in `totals_line` and `render_overview`; colours in the CSS block near `TOOL_PREVIEW_LINES`), `tests/test_poe_report.py`, `tests/fixtures/poe/sample-task/`, `README.md`.

**Files it may change.** `skills/poe/scripts/poe_report.py`, `tests/test_poe_report.py`, files under `tests/fixtures/poe/sample-task/`, `README.md`. Nothing else.

**Fixture.** Add to the fixture (main or worker transcript, hand-written, no real session data): one thinking block with text (include a `<script>` string in it for the escaping test), one empty thinking block, one narration block (text plus a signature starting with the narration prefix above), and one thinking block with text and a garbage signature. Update existing test expectations that change because of the new blocks; do not weaken unrelated assertions.

**Tests to add.** Summarized thinking text visible in the HTML outside a collapsed `<details>` (first line present before any `<details>` of that step); narration labelled `narration`; garbage or missing signature falls back to `thinking`; empty block shows the new message; the overview and transcript totals show the right "N of M"; `<script>` in thinking is escaped.

**Non-goals.** No changes to `SKILL.md`, `agents/`, `.claude/` or any settings file. No new dependencies (standard library only, Python 3.9+). No other report features. Do not edit or regenerate `poe/poe-report-dashboard/report.html` (it is committed).

**Verification commands.**

```sh
python3 -m unittest discover tests
# real data, on a scratch copy so the committed report is not overwritten:
rm -rf /private/tmp/claude-1128299617/-Users-sbandyopadhyay-projects-SCRIPTS-custom-claude-plugins-poe/e14b4624-c91b-4dff-997e-f974b19aece8/scratchpad/01a && mkdir -p /private/tmp/claude-1128299617/-Users-sbandyopadhyay-projects-SCRIPTS-custom-claude-plugins-poe/e14b4624-c91b-4dff-997e-f974b19aece8/scratchpad/01a && cp -R poe/poe-report-dashboard /private/tmp/claude-1128299617/-Users-sbandyopadhyay-projects-SCRIPTS-custom-claude-plugins-poe/e14b4624-c91b-4dff-997e-f974b19aece8/scratchpad/01a/
python3 skills/poe/scripts/poe_report.py /private/tmp/claude-1128299617/-Users-sbandyopadhyay-projects-SCRIPTS-custom-claude-plugins-poe/e14b4624-c91b-4dff-997e-f974b19aece8/scratchpad/01a/poe-report-dashboard
grep -o 'thinking recorded: [0-9]* of [0-9]*' /private/tmp/claude-1128299617/-Users-sbandyopadhyay-projects-SCRIPTS-custom-claude-plugins-poe/e14b4624-c91b-4dff-997e-f974b19aece8/scratchpad/01a/poe-report-dashboard/report.html | head
grep -c 'kind-narration' /private/tmp/claude-1128299617/-Users-sbandyopadhyay-projects-SCRIPTS-custom-claude-plugins-poe/e14b4624-c91b-4dff-997e-f974b19aece8/scratchpad/01a/poe-report-dashboard/report.html
grep -nE '(src|href)="https?:' /private/tmp/claude-1128299617/-Users-sbandyopadhyay-projects-SCRIPTS-custom-claude-plugins-poe/e14b4624-c91b-4dff-997e-f974b19aece8/scratchpad/01a/poe-report-dashboard/report.html || echo "no external refs"
git status --short
```

**Completion criteria.** All unit tests pass (observed). On the scratch copy the overview shows "thinking recorded: 0 of 109 blocks" and there are 5 narration steps (if the numbers differ, explain why in the notes rather than forcing them). No external refs. `git status` shows only the allowed files changed (plus the untracked `poe/poe-thinking-capture/`).

**Progress notes.** `poe/poe-thinking-capture/progress/01a-report.md`
