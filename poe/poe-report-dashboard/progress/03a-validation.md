# 03a-validation: done

Scratch root (S): `/private/tmp/claude-1128299617/-Users-sbandyopadhyay-projects-SCRIPTS-custom-claude-plugins-poe/e1650fd1-5110-41f6-944b-7f0774e47f42/scratchpad/03a`

## Done so far
- Step 1 done: scratch task `S/work/poe/real-check/` built:
  - `plan.md`, `status.md` copied from `plans/poe-dir-and-logs/`.
  - `logs/7234187e-d86b-4afa-adca-ee152aac72bf/` (main + `subagents/agent-a1c06f9ad1f6bb6e9.{jsonl,meta.json}`) from the `...-scratchpad-02a-e2e` project dir.
  - `logs/cb353a49-6d4d-41b6-911e-14acc86a0355/` (main + 2 workers: agent-a6495cd98f9349f8a, agent-a8e2955718436159a) and `logs/a6c2b2e1-a969-4ad4-bc89-d4a6b937c5be/` (main only) from `~/.claude/projects/-Users-sbandyopadhyay-projects-SCRIPTS-custom-claude-plugins-poe/`.
  - logs total 2.5 MB.
- Step 2 done (all checks PASS), see below.
- Step 3 done: e2e report built (after adding `--` before the prompt); log copy denied as expected.
- Step 4 done: plugin validate passed with pre-existing warnings.
- Independent checker: `S/tools/check.py` (does not import poe_report; parses JSONL with json and report.html with regex + html.unescape).

## Files changed or produced
- Repo: only this notes file.
- Scratch: `S/work/poe/real-check/` (task + `report.html`), `S/tools/check.py`.

## Tests run and observed results

### Step 2: script on real data
`cd S/work && python3 <repo>/skills/poe/scripts/poe_report.py poe/real-check`
```
poe/real-check/report.html
exit 0
-rw-r--r--  353945 bytes  poe/real-check/report.html
```
`grep -nE '(src|href)="https?:' poe/real-check/report.html` -> no lines, exit 1 (PASS). `<script` count 0.

`python3 -I S/tools/check.py S/work/poe/real-check` (trimmed):
```
7234187e-...: tool_use blocks 12, tool-call rows 12, results 12, is_error 3, usage msgs 9 ids + 0 no id, tokens [18, 4246, 255181, 20782]
agent-a1c06f9ad1f6bb6e9: tool_use blocks 4, rows 4, results 4, is_error 1, usage 5 ids, tokens [10, 1630, 79074, 21961]
session 7234187e: tokens [28, 5876, 334255, 42743]
a6c2b2e1-...: tool_use blocks 0, rows 0, results 0, usage 0, tokens [0, 0, 0, 0]
cb353a49-...: tool_use blocks 13, rows 13, results 13, is_error 0, usage 10 ids, tokens [22, 8971, 519712, 39504]
agent-a6495cd98f9349f8a: tool_use blocks 17, rows 17, results 17, is_error 2, usage 16 ids, tokens [34, 11592, 694685, 61242]
agent-a8e2955718436159a: tool_use blocks 22, rows 22, results 22, is_error 3, usage 21 ids, tokens [42, 15535, 996161, 64865]
session cb353a49: tokens [98, 36098, 2210558, 165611]
grand total tokens: [126, 41974, 2544813, 208354] sum 2795267
sections in HTML: 6; transcripts on disk: 6
tool_use blocks 68, tool-call rows 68, tool_results 68
is_error results 9, Errors section items 9 (heading 9)
RESULT: PASS
```
What the checker verifies, per transcript: a `transcript-<name>` section exists for every main and worker file (and none extra); the i-th tool-call row has the same tool name and the same input text (`json.dumps(input, indent=2, ensure_ascii=False)`, preview + rest re-joined) as the i-th `tool_use` block in file order; row anchors increase; each row's "result #N" link resolves to a tool_result step whose text equals the JSONL tool_result content; every `is_error: true` result's anchor is in the Errors section list; the orchestrator-only, worker, session and overview token lines (and the overview Tokens card 2,795,267) equal the independent sum (usage counted once per `message.id` per transcript; records without id each counted; none occurred).

Extra HTML checks (python): 224 ids, 0 duplicates; 307 internal links, 0 unresolved; html.parser tag balance: 0 mismatches, nothing unclosed. Overview cards: Sessions 3, Workers 3, Tool calls 68, Errors 9, Tokens 2,795,267, Cost $2.7922, Duration 30m 52s, Skipped records 0.

Browser: no browser tool available; the report was NOT visually checked.

## Decisions and assumptions
- Chose cb353a49 (finished session, 2 workers) and a6c2b2e1 (small, no workers). Did not use e1650fd1 (live orchestrator).
- The raw string `"type":"tool_use"` appears more often than real calls because `api-request-blob` records replay earlier assistant messages. Checked: in every file the blob tool_use ids are a subset of the `assistant` tool_use ids and blob messages carry no `usage`, so counting only `assistant` records is correct (and matches the parser, which ignores `api-request-blob`).
- a6c2b2e1 turned out to be degenerate: 2 user records (a `/poe:poe plan` invocation), 6 `api-request` records, no `assistant` records, cost-state 0. The report shows it with 2 user steps, 0 tool calls, 0 tokens, cost $0.0000, duration 0s. Correct for the data; kept as an edge case.

## Observations (not failures)
- Token totals vs cost-state: for 7234187e the deduped sum equals cost-state `modelUsage` exactly (as 01a found). For cb353a49 it does not: cost-state `modelUsage` has `claude-haiku-5-5` input 73,731 / output 2,670 (side queries, no assistant records) and `claude-opus-5-5` input 6,912 / output 36,372 / cache read 2,898,174 / cache creation 173,301, versus the transcripts' 98 / 36,098 / 2,210,558 / 165,611. So cost-state counts API calls that are not written as assistant records. The report's tokens (from transcripts) and its cost (from cost-state, $2.3316 for cb353a49) therefore come from different scopes; the token figures can be lower than what was billed. The acceptance criterion (match a sum over `message.usage` in the same files) is met. Possibly worth a one-line note in the report or README; out of scope for this unit.
- Session duration uses step timestamps only, so a6c2b2e1 shows 0s although its api-request records span 09:49-09:51.

### Step 3: end to end (headless `/poe:poe report`)
Setup: `S/e2e/poe/real-check/` = copy of `S/work/poe/real-check/` with `report.html` removed (only `logs/`, `plan.md`, `status.md`). Claude Code 2.1.326.

Attempt 1, the brief's command verbatim (approved permissions):
```
cd S/e2e && claude -p --plugin-dir /Users/sbandyopadhyay/projects/SCRIPTS/custom_claude_plugins/poe \
  --permission-mode acceptEdits --allowedTools "Bash(python3:*) Bash(mkdir:*) Bash(cp:*) Bash(find:*)" "/poe:poe report poe/real-check"
```
-> exit 1, stderr: `"/poe:poe report poe/real-check" was read as a value of --allowedTools, not as a prompt · put a prompt before --allowedTools or after --` / `Error: Input must be provided either through stdin or as a prompt argument when using --print`. FINDING (docs only): `--allowedTools` is variadic, so the command as written in the phase brief (the approved form in status.md) does not run as typed; it needs `--` before the prompt (or the prompt before `--allowedTools`). README.md and SKILL.md do not mention `--allowedTools` (grep), so no shipped doc is affected.

Attempt 2, same permissions, only `--` added before the prompt:
```
cd S/e2e && claude -p --plugin-dir /Users/sbandyopadhyay/projects/SCRIPTS/custom_claude_plugins/poe \
  --permission-mode acceptEdits --allowedTools "Bash(python3:*) Bash(mkdir:*) Bash(cp:*) Bash(find:*)" -- "/poe:poe report poe/real-check"
```
-> exit 0. Reply (trimmed):
```
I built the report for `poe/real-check`, but this session's own transcript isn't in it because I couldn't copy it.
**Report:** `poe/real-check/report.html`
**Missing log:** Claude Code's sandbox only lets this session search its working directory, so it couldn't look in
`~/.claude/projects` for this session's transcript (`4aebfe57-…`). The report includes the three earlier sessions ...
To add this session, copy its `.jsonl` into `poe/real-check/logs/4aebfe57-34c0-40ad-8ff2-b48fc3a3bcc7/` and run `report` again.
```
`S/e2e/poe/real-check/report.html` written: 353,945 bytes. Differs from the step-2 report only in the "Generated" card (15:34 vs 15:37). `S/tools/check.py` on it: RESULT PASS (68/68 calls, 9/9 errors). External-ref grep: no lines.

Tool calls in the e2e session (from its transcript `~/.claude/projects/-private-tmp-...-scratchpad-03a-e2e/4aebfe57-34c0-40ad-8ff2-b48fc3a3bcc7.jsonl`):
1. `ls -la poe/real-check; ls poe` -> ok.
2. SKILL log-copy block (`find "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/projects" ...`, mkdir, cp) -> DENIED: "A variable in braces in this command can't be checked before it runs".
3. `find "$HOME/.claude/projects" ...` -> DENIED: "A variable in this command can't be checked before it runs".
4. `find /Users/.../.claude/projects -name ...` -> DENIED: "find in '/Users/sbandyopadhyay/.claude/projects' was blocked ... may only search files in the allowed working directories".
5. `ls -R poe/real-check/logs | head -30; python3 /Users/.../poe/skills/poe/scripts/poe_report.py poe/real-check` -> ok (the model used the resolved skill path).
Outcome: report build allowed and done; log copy denied (acceptable, documented outcome per status.md). The reply names the report path and explains the missing log. Nothing was written outside `S/e2e/` by the run (it only created report.html; the mkdir for the log dir never ran).

### Step 4: `claude plugin validate .` (repo root)
```
⚠ version: No version specified. Consider adding a version following semver
Provides: skills: poe:poe / agents: poe:phase-worker
⚠ plugin directory warning: .claude-plugin/plugin.json icon: No icon (ICON_MISSING)
✔ Validation passed with warnings
exit 0
```
Same pre-existing warnings as 01b. PASS.

## Next step / remaining work
- None for 03a. For the orchestrator: (a) decide whether README/SKILL/plan should show the headless command with `--` before the prompt; (b) optional note that report tokens come from transcripts while cost comes from cost-state (different scope, see Observations); (c) the log copy cannot run under the approved acceptEdits allow-list (variable expansion + find outside the working dir), already a known limitation.
