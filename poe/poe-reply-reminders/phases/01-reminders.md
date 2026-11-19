# Phase 01: reply reminders

Depends on: none. Units run sequentially (U2 needs U1's edit).

## Unit 01-edit: add reminder lines to SKILL.md
- Goal: append one reminder line to each reply step listed in `plan.md` Scope.
- Read: `poe/poe-reply-reminders/plan.md`, `skills/poe/SKILL.md`, `git diff skills/poe/SKILL.md` (uncommitted `less_verboosity` edits; keep them).
- May change: `skills/poe/SKILL.md` only.
- Lines to add (end of each step/bullet):
  - Plan step 5, Split step 6, Execute step 7: `Reply terse: ≤5 bullet fragments, no prose, don't repeat file contents.`
  - Execute step 9: same, `≤10` bullets.
  - `report` mode bullet: `Reply: report path + any failure, nothing else.`
  - Plan 5 / Split 6: line must not land after the `Next:` fenced block (spec: nothing after block in reply; reminder may say `Next:` block not counted). Place it before the block's lead-in or within step text.
- Non-goals: `## Output style` section, `phase-worker.md`, README, `poe_report.py`, tests, any other wording.
- Verify:
  - `git diff skills/poe/SKILL.md` — only the 5 added lines beyond pre-existing edits (compare to `git stash`-free baseline: save `git diff` before editing to `progress/01-edit.baseline.diff`).
  - `claude plugin validate .` passes.
- Done when: 5 lines present, nothing else changed, validate passes.
- Notes: `poe/poe-reply-reminders/progress/01-edit.md`

## Unit 01-check: before/after reply length
- Goal: measure whether plan-mode final reply got shorter.
- Read: `plan.md` Validation; transcripts under `poe/*/logs/**/*.jsonl` (main transcripts only, not subagents).
- May change: nothing in repo outside `poe/poe-reply-reminders/progress/`. Run the toy task in the session scratchpad dir (or a `mktemp -d`), not the repo.
- Steps:
  - Baseline: final assistant text of a plan-mode turn from an existing transcript → word count, bullet count.
  - After: `cd <tmpdir> && claude -p --plugin-dir <repo> "/poe:poe plan <toy task>"` (toy task e.g. "add a --version flag to a hello.py CLI"; create minimal hello.py first). Capture final reply → word + bullet count.
  - If `claude -p` can't run (auth, refused), record as blocked; don't fake numbers.
- Non-goals: editing SKILL.md, tuning caps.
- Done when: notes hold baseline + after numbers (or explicit blocker), and verdict: ≤5 bullets + `Next:` block? shorter than baseline?
- Notes: `poe/poe-reply-reminders/progress/01-check.md`
