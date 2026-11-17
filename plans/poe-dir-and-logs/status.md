# Status: poe-dir-and-logs

Plan: `plans/poe-dir-and-logs/plan.md` — split approved (user ran `execute`).

| Phase | Unit | Description | Depends on | Status |
|---|---|---|---|---|
| 01 docs | 01a | Rename `plans/`→`poe/`, add `summary.md` and Logs section to SKILL.md, update README | — | verified (diff reviewed by orchestrator; grep, validate, copy-command test in progress/01a-docs.md) |
| 02 e2e validation | 02a | Run plan/split/execute headless in a scratch dir; check `poe/<slug>/` and log copies | 01a | done — log-copy criteria FAIL (see progress/02a-e2e.md); awaiting user decision |

## Decisions

- 02a permission mode (user-approved): `--permission-mode acceptEdits --allowedTools "Bash(mkdir:*) Bash(cp:*) Bash(find:*)"`, scratch dir only.
- `${CLAUDE_SESSION_ID}` is documented (https://code.claude.com/docs/en/skills). Open: whether `${CLAUDE_CONFIG_DIR:-$HOME/.claude}` survives skill substitution unchanged — 02a checks this.

## 02a result (verified by orchestrator)

- plan/split/execute produced plan.md, phases/, status.md, progress/, summary.md, hello.txt: pass.
- `${CLAUDE_SESSION_ID}` substituted; `${CLAUDE_CONFIG_DIR:-$HOME/.claude}` passed through unchanged: pass.
- No `logs/` in any session: the copy block was denied. Brace expansions and `$(...)` can't be auto-approved ("can't be checked before it runs", seen 3x in the plan transcript), and `find` outside the working directory is blocked. The same command run by hand copies all four .jsonl files correctly.
- Minor: summary.md says "Blockers: None" even though the logs are missing.

## Next action

User chooses how to fix the log-copy permission problem (decision is beyond the approved plan).
