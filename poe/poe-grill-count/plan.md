# Grill mode: show question count (Q1 of N)

## Objective

- User sees how many grill questions to expect: each question shows `Q<k> of ~<N>`.

## Decisions

- Total = estimate, revised: count open decisions at start, show `Q1 of ~N`; N updated when an answer adds/removes questions. Why: keeps adaptive one-at-a-time grilling, honest about uncertainty.
- Placement = prefix of `question` text: `Q1 of ~4: <question>`. Why: always visible; 12-char header stays the decision label.

## Scope

- `skills/poe/GRILLING.md` `## Questions`: counter rule.
- `README.md` line 69 Grill bullet: mention `Q1 of ~N` counter.

Excluded:
- `SKILL.md` (Grill step 3 "Ask one question, then stop" still correct).
- Decision tree, writes-after-answer, glossary, ADR rules; `poe_report.py`; tests.

## Assumptions

- N = all open decisions visible at start (whole tree, not just frontier), excl. final confirm.
- `~` always shown (estimate by nature).
- Final "Matches your understanding?" dialog: no prefix, not counted.
- Plain-text fallback (`GRILLING.md:34`) uses same prefix.
- `grill <plan-path>`: N counts only the open points being grilled; settled `## Decisions` not counted.
- k never resets within one grill run; resumed run after `/clear` restarts at Q1 (count not persisted; no extra state file).

## Approach

Add to GRILLING.md `## Questions`, after "Ask exactly one question per turn" (line 26):

- Before Q1, estimate N = open decisions known so far (excl. final confirm).
- Prefix every `question`: `Q<k> of ~<N>: `. Header unchanged.
- After each answer, re-estimate N (asked + still open); show the new N on the next question.

Extend fallback line 34: plain-text question carries same prefix.

README Grill bullet: add "each question shows `Q1 of ~N`, an estimate revised as answers add or remove questions".

## Acceptance criteria

- GRILLING.md states: estimate before Q1, `Q<k> of ~<N>: ` prefix on `question`, re-estimate after each answer, fallback uses prefix, final confirm unprefixed.
- README Grill bullet mentions the counter.
- `grep -n 'of ~' skills/poe/GRILLING.md README.md` → hits in both.
- Manual run: prefix on every grill dialog; k increments by 1; N changes when an answer opens/closes questions; confirm dialog unprefixed.

## Risks

- Estimate wrong → user surprised by overruns. Mitigation: `~` + revision each turn.
- Model forgets prefix mid-run. Mitigation: rule sits beside "one question per turn" rule.
- Installed plugin lags repo; test with `--plugin-dir`.

## Validation

- `grep` check above.
- `python3 -m pytest tests/` passes (sanity; no code touched).
- Manual: `claude --plugin-dir /Users/sbandyopadhyay/projects/SCRIPTS/custom_claude_plugins/poe`, `/poe:poe grill add archiving for old notes` in scratch repo; answer ≥3 questions; check prefix, k, N revision, unprefixed confirm.
