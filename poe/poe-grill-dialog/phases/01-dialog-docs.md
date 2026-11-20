# Phase 01: switch grill questions to AskUserQuestion

- Depends on: approved `plan.md`.
- One unit (2 small doc edits, tightly coupled wording) → no parallelism.
- All edits: follow SKILL.md Output style (terse); nothing beyond plan; `git status` first — `README.md`, `skills/poe/SKILL.md`, `skills/poe/GRILLING.md` hold **uncommitted user changes**: edit in place, never revert/overwrite them; no commits.

## Unit 01a: GRILLING.md + README
- Goal: grill asks every decision via `AskUserQuestion` dialog (one question per call), plain-text fallback only when tool unavailable/rejected.
- Read: `poe/poe-grill-dialog/plan.md` (Approach, Acceptance criteria); `skills/poe/GRILLING.md`; `README.md` Grill bullet (~line 66); `skills/poe/SKILL.md` Grill mode section (check only).
- May change: `skills/poe/GRILLING.md`, `README.md`. `skills/poe/SKILL.md` only if Grill steps contradict the dialog (expected: no change).
- Changes:
  - GRILLING.md `## Questions`: remove "Plain text only. No AskUserQuestion.", `"yes" = accept the rec` reply rule, `Q<n>. / Rec:` format block. Add dialog rules per plan Approach: one question per call; self-contained `question`; `header` ≤12 chars; 2–4 mutually exclusive options, recommended first with `(Recommended)` suffix + short-why `description`, others = trade-off; no manual "Other"; `multiSelect` only when answers combine; `preview` only for concrete artifact comparison; open-ended → 2 best candidates, user picks "Other"; fallback plain text (one question + `Rec:` line, stop). Keep: frontier/one decision per turn, next question only after answer, skip trivia, recs follow do-not-overengineer.
  - GRILLING.md `## Finish`: summary ≤5 bullets as text, then dialog "Matches your understanding?" → `Yes, write the plan (Recommended)` / `Needs correction`; correction → ask what, re-ask affected decisions one at a time.
  - `## Writing after every answer`: wording "before asking the next question" fine; adjust only if it references the text format.
  - README Grill bullet: replace `reply "yes" to accept it, or give your own answer` with dialog description (pick an option, recommended first, or type your own via Other).
- Non-goals: decision tree, facts vs decisions, domain modeling, glossary, ADR sections; batching questions; `poe_report.py`; tests; other modes.
- Verify (from repo root `/Users/sbandyopadhyay/projects/SCRIPTS/custom_claude_plugins/poe`):
  - `grep -rn 'reply "yes"\|No AskUserQuestion\|Plain text only\|Rec:' skills/ README.md` → only the fallback line in GRILLING.md
  - `grep -n 'AskUserQuestion\|Recommended\|Other' skills/poe/GRILLING.md README.md`
  - `git diff --stat` + `git diff README.md` → only Grill bullet changed vs prior working tree (earlier uncommitted grill docs intact)
  - `python3 -m pytest tests/ -q` → passes (sanity)
  - `claude plugin validate .` (if available; record output or absence)
- Done when: all Changes present; greps as expected; tests pass (observed); manual dialog run left to user (plan Validation, Manual).
- Progress notes: `poe/poe-grill-dialog/progress/01a-grilling-dialog.md`
