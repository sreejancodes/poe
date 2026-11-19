# Plan: terse-reply reminder at each reply step

## Objective
Concise rule (top of `skills/poe/SKILL.md`) slips in later turns. Repeat a short, concrete version at each step where a mode writes its chat reply.

## Scope
In — `skills/poe/SKILL.md` only, one line appended to:
- Plan step 5
- Split step 6
- Execute step 7 (per-unit update)
- Execute step 9 (completion report; `resume` reuses it)
- `report` mode bullet (reply = path only)

Line wording (≈):
- Plan/split/execute 7: `Reply terse: ≤5 bullet fragments, no prose, don't repeat file contents.`
- Execute 9: same, ≤10 bullets.
- Report: `Reply: report path + any failure, nothing else.`
- `Next:` block not counted in the limit.

Out:
- `phase-worker.md`, README, files poe writes (plan.md etc.), `poe_report.py`, tests.
- Changing the existing `## Output style` section.

## Assumptions
- Builds on uncommitted `less_verboosity` edits to SKILL.md. Keep them.
- Bullet caps (5/10) are a starting guess; tune after the check below.

## Acceptance criteria
- Each listed step ends with the reminder line; nothing else in SKILL.md changed.
- `claude plugin validate .` passes.
- Manual check: plan-mode final reply on a toy task ≤5 bullets + `Next:` block, shorter than baseline.

## Risks
- Hard caps could squeeze out required content (blockers, failed tests). Mitigation: Output style's "never drop required content" stays; execute 9 gets 10.
- Effect unproven; may not help. Mitigation: before/after comparison.

## Validation
- `claude plugin validate .`
- Baseline: word count of final plan-mode reply in an existing transcript under `poe/*/logs/`.
- After: `claude --plugin-dir .`, `/poe:poe plan <toy task>`; compare reply length and bullet count.
