# Phase 01: Concise prompts

Plan: `poe/poe-concise-output/plan.md`. Deps: none. Text-only edits.
Units 01a and 01b touch disjoint files → run in parallel.

## Unit 01a: SKILL.md (+ README line)
- **Goal:** add concise-output rules + `Next:` command block to `skills/poe/SKILL.md`, per plan Scope.
- **Read:** `plan.md`, `skills/poe/SKILL.md`, `README.md`.
- **May change:** `skills/poe/SKILL.md`, `README.md` (one line, only if natural place).
- **Do:**
  - New `## Output style` section near top: verbatim "Be concise. Sacrifice grammar for the sake of concision."; covers every reply + every file poe writes for user (plan, briefs, status, summary); bullets/fragments over prose; never drop required content (acceptance criteria, risks, verification commands, exact paths, test results, unknowns).
  - Plan step 2: plan.md short; no restating request, no background beyond what shapes decisions. Keep listed required sections.
  - Plan step 5, split step 6, execute steps 7 & 9: reply points to paths, doesn't repeat file contents.
  - Plan step 5 + split step 6: reply ends with `Next:` line + fenced block with exact command and full plan path (plan → `/poe:poe split poe/<slug>/plan.md`; split → `/poe:poe execute poe/<slug>/plan.md`). Nothing after block. Pasteable into fresh `/clear`ed session.
- **Non-goals:** no next-command for execute/resume/report; no changes to `poe_report.py`, tests, logs/report sections; no wording sprinkled everywhere; don't rewrite unrelated text.
- **Verify:**
  - `grep -n "Be concise. Sacrifice grammar for the sake of concision." skills/poe/SKILL.md`
  - `grep -n "Next:" skills/poe/SKILL.md` (hits in plan + split steps)
  - progress-note headings block still intact; plan.md required sections still listed.
  - `claude plugin validate .`
  - `python3 -m unittest discover tests`
- **Done when:** all verify steps pass; diff limited to allowed files.
- **Notes:** `poe/poe-concise-output/progress/01a-skill-md.md`

## Unit 01b: phase-worker.md
- **Goal:** add concise-output rule to `agents/phase-worker.md` for progress notes + final return message.
- **Read:** `plan.md`, `agents/phase-worker.md`.
- **May change:** `agents/phase-worker.md` only.
- **Do:** add verbatim "Be concise. Sacrifice grammar for the sake of concision." once, prominently; applies to progress notes + return message to orchestrator; notes keep required headings and enough detail for fresh agent to continue (paths, test results, unknowns).
- **Non-goals:** no change to frontmatter tools/model; no other behaviour changes.
- **Verify:**
  - `grep -n "Be concise. Sacrifice grammar for the sake of concision." agents/phase-worker.md`
  - `claude plugin validate .`
- **Done when:** verify passes; diff limited to allowed file.
- **Notes:** `poe/poe-concise-output/progress/01b-phase-worker.md`

## After phase (orchestrator)
- Review full diff vs plan acceptance criteria.
- Manual check (user): fresh `/poe:poe plan <small task>` → shorter plan.md + reply, required sections present, ends with `Next:` block.
