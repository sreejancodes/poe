# Grill mode: ask via AskUserQuestion dialog

## Objective

- Grill questions appear in Claude Code's native question dialog (`AskUserQuestion` tool: selectable options + free-text "Other"), not as plain-text `Q<n>. / Rec:` blocks.

## Scope

- `skills/poe/GRILLING.md`: rewrite `## Questions`; adjust `## Finish`.
- `README.md`: Grill bullet (line ~66) — drop `reply "yes"`, describe pick-an-option.
- `skills/poe/SKILL.md`: Grill step 3 only if wording conflicts (currently "Ask one question, then stop" — fine).

Excluded:
- Decision tree, facts-vs-decisions, domain modeling, write-after-every-answer, glossary, ADR rules: unchanged.
- Batching several questions per dialog (tool allows 4): not done; one frontier decision per call stays.
- `poe_report.py`, tests, other modes.

## Assumptions

- `AskUserQuestion` limits: 1–4 questions/call, 2–4 options/question, header ≤12 chars, "Other" free-text added automatically.
- Skill frontmatter has no `allowed-tools` restriction → tool callable from the skill.
- One-question-per-turn was a deliberate choice (answers reshape later questions) → kept.

## Approach

Replace GRILLING.md `## Questions` rules:

- Remove `Plain text only. No AskUserQuestion.` and the `Q<n>. / Rec:` format block and the `"yes" = accept the rec` reply rule.
- Ask every decision with `AskUserQuestion`, one question per call:
  - `question`: terse, self-contained (dialog may be all the user sees) — include any finding it depends on.
  - `header`: ≤12-char decision label.
  - Options: 2–4 concrete, mutually exclusive answers. Recommended first, label ends `(Recommended)`; its `description` = short why. Other descriptions = trade-off.
  - No "Other" option (automatic). `multiSelect` only when answers genuinely combine.
  - `preview` only when comparing concrete artifacts (layouts, snippets).
- Open-ended decision (no sensible option list, e.g. naming a term) → still the dialog: 2 best candidate answers as options; user uses "Other" for own.
- Tool unavailable or call rejected (non-interactive session) → fall back to plain text: one question + `Rec:` line, then stop.
- Unchanged: one frontier decision per turn; next question picked only after the answer; write decisions/glossary/ADRs after every answer, before the next dialog; skip trivia; recs follow "Do not overengineer".

`## Finish`:
- Summary (≤5 bullets) as plain text, then `AskUserQuestion`: "Matches your understanding?" → `Yes, write the plan (Recommended)` / `Needs correction`. Correction → ask what via follow-up text, re-ask affected decisions.

## Acceptance criteria

- GRILLING.md contains no "Plain text only" / "No AskUserQuestion" rule; `## Questions` specifies the dialog rules above incl. fallback.
- README Grill bullet matches new behaviour; no stale `reply "yes"`.
- `grep -rn 'reply "yes"\|No AskUserQuestion\|Rec:' skills/ README.md` → only the fallback line.
- Manual run: every grill question arrives as a dialog, one per turn, recommended option first; `plan.md` `## Decisions` grows after each answer; final confirmation is a dialog.
- "Other" free-text answer recorded correctly as the decision.

## Risks

- Dialog hides preceding chat text → question lacks context. Mitigation: self-contained `question` rule.
- 4-option cap forces lossy option lists. Mitigation: "Other" always available; options = best candidates only.
- Model drifts to batching 4 questions per call. Mitigation: explicit "one question per call" rule.
- Loaded skill text in the installed plugin may lag the repo (this session's SKILL.md said "rounds", repo says "one question"). Test with `claude --plugin-dir <repo>`.

## Validation

- `grep` check above.
- `python3 -m pytest tests/` still passes (no code touched; sanity only).
- Manual: `claude --plugin-dir /Users/sbandyopadhyay/projects/SCRIPTS/custom_claude_plugins/poe`, then `/poe:poe grill add archiving for old notes` in a scratch repo; answer 3 questions (one recommended, one other option, one "Other" text); check dialogs, `## Decisions`, final confirm dialog.
