# Grilling method

Interview method for `grill` mode: settle every open decision with the user, recording terms and hard decisions as you go.

Adapted from the `grilling` and `domain-modeling` skills by Matt Pocock: https://github.com/mattpocock/skills

> MIT License. Copyright (c) 2026 Matt Pocock.
> Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
> The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
> THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## Decision tree

- Task = tree of decisions. A decision depends on others when its options only make sense once they are settled.
- **Frontier** = open decisions whose prerequisites are all settled. Ask one frontier decision at a time; deeper questions wait until their prerequisites are answered.
- `grill <plan-path>`: tree = the plan's assumptions, open points, risky points. Settled `## Decisions` entries are not re-asked.

## Facts vs decisions

- Facts (what the code does, what exists, versions, conventions, test setup): look them up in the code, or with read-only exploration subagents. Never ask the user.
- Decisions (what the user wants, trade-offs only they can weigh): ask.
- Missing detail with an obvious default = not a question. Use the default; note it under Assumptions.

## Questions

- Ask exactly one question per turn: the frontier decision that most other decisions depend on.
- Ask it with `AskUserQuestion`, one question per call. Never batch questions.
  - `question`: terse, self-contained (the dialog may be all the user sees); include any finding it depends on.
  - `header`: decision label, ≤12 chars.
  - Options: 2–4 concrete, mutually exclusive answers. Recommended first, label ends `(Recommended)`, `description` = short why. Other options' `description` = trade-off.
  - No manual "Other" option (added automatically). `multiSelect` only when answers genuinely combine.
  - `preview` only when comparing concrete artifacts (layouts, snippets).
- Open-ended decision (no sensible option list, e.g. naming a term) → still the dialog: 2 best candidates as options; user types own via "Other".
- Tool unavailable or call rejected → fall back to plain text: one question + `Rec:` line, then stop.
- Pick the next question only after the answer; an answer may add, remove, or change later questions.
- Recommendations follow SKILL.md Plan step 3 "Do not overengineer": simplest option meeting the stated need, repo's existing tools/patterns, no speculative features or config.
- Skip trivia: no question whose answer would not change the plan. A clear task may need one question or none.

## Domain modeling

While grilling, sharpen the language:
- Term used loosely, or two words for one thing → ask which one and what exactly it means.
- Probe a term with a concrete edge-case scenario ("note edited after archiving: still archived?").
- Check terms against existing code names and `poe/docs/GLOSSARY.md`; flag conflicts.

## Writing after every answer

After each answer, before asking the next question:
1. Append the settled decision to `## Decisions` in `poe/<slug>/plan.md` (one bullet: decision + short why).
2. Add or update glossary entries for terms the answer resolved.
3. Write an ADR for any decision that qualifies (below).

Nothing settled lives only in the chat; `/clear` then `grill <plan-path>` must resume without re-asking.

## Glossary

- Path: `poe/docs/GLOSSARY.md`. Create only when the first term is resolved.
- Project-specific terms only. No generic programming words. No implementation detail (file names, classes, schemas).
- Entry format:
  ```
  **Term**: 1–2 sentence definition.
  _Avoid_: synonym, other synonym
  ```
- Keep entries alphabetical; edit an existing entry instead of adding a duplicate.

## ADRs

- Path: `poe/docs/adr/NNNN-slug.md`. Create `adr/` only when the first ADR is written.
- Write one only when all three hold:
  1. Hard to reverse (costly to change later).
  2. Surprising (a future reader would ask "why this way?").
  3. Real trade-off (viable alternatives were rejected).
- Otherwise the decision lives only in `plan.md` `## Decisions`. Zero ADRs is normal.
- Number = highest existing number + 1, 4 digits (`0001` if none). Slug = short kebab-case title.
- Format:
  ```
  # NNNN: <Title>

  <1–3 sentences: context, decision, why.>
  ```
  Add sections (Considered options, Consequences) only when they add real value.

## Finish

- Frontier empty → summarize understanding in ≤5 bullets as plain text, then `AskUserQuestion` "Matches your understanding?": `Yes, write the plan (Recommended)` / `Needs correction`.
- Correction → ask what in plain text; re-ask the affected decisions, one at a time.
- Confirmed → grilling done; continue Grill mode in SKILL.md.
