# Plan: Concise poe output

## Objective
Cut verbosity of poe: chat replies (stdout) and written files (plan.md, phase briefs, status.md, summary.md, progress notes). Past plans ran 1200–1700 words; too long to review.

Instruction to add, verbatim: **"Be concise. Sacrifice grammar for the sake of concision."** Applies to all user-facing output.

## Scope
In:
- `skills/poe/SKILL.md`
  - New short section near top, e.g. `## Output style`: the verbatim instruction; applies to every reply and every file poe writes for the user (plan, briefs, status, summary). Bullets/fragments over prose.
  - Plan mode step 2: plan.md short; no restating request, no background beyond what shapes decisions.
  - Plan mode step 5 / split step 6 / execute step 7 & 9: replies point to file paths, don't repeat file contents.
  - **Next command.** Plan mode step 5 and split step 6: reply ends with a clearly labelled `Next:` line + fenced code block holding the exact command to run, with full plan path, so it can be pasted into a fresh `/clear`ed session with no other context. E.g.
    ````
    Next:
    ```
    /poe:poe split poe/<slug>/plan.md
    ```
    ````
    Plan → `split <path>`; split → `execute <path>`. Nothing else after the block.
- `agents/phase-worker.md`: same instruction for progress notes and final return message to orchestrator. Notes stay terse but must still let a fresh agent continue (keep the required headings).
- `README.md`: one line noting poe output is deliberately terse. Only if a natural place exists; skip otherwise.

Out:
- `poe_report.py`, tests, report.html format.
- Config option / toggle for verbosity.
- Changing code-comment or commit-message style.
- Next-command block for execute/resume/report (not requested).
- Rewriting existing plans in `poe/` or `plans/`.

## Assumptions
- "Interacting with the user" = chat replies + files user reads. Worker→orchestrator messages included (they feed parent context, so terse helps too).
- Concision must not drop required content: acceptance criteria, risks, verification commands, exact file paths, test results, unknowns.

## Approach
Text-only edits to two prompt files (+ maybe one README line). Place instruction once, prominently, in each file; tighten the few existing steps that invite long output. No duplicate wording sprinkled everywhere.

## Acceptance criteria
- Verbatim instruction present in `SKILL.md` and `phase-worker.md`.
- SKILL.md still lists required plan.md sections and progress-note headings.
- Plan and split replies end with `Next:` + fenced block holding full command with full plan path (checked in manual run).
- `claude plugin validate .` passes.
- `python3 -m unittest discover tests` still passes (sanity; no code change).
- Manual check: fresh `/poe:poe plan <small task>` run gives a noticeably shorter plan.md and reply than past plans (~1200+ words), with all required sections present.

## Risks
- Too terse → plans/notes ambiguous for fresh workers. Mitigation: explicit "don't drop required content" line.
- Model may ignore style instruction in long runs. Mitigation: put it near top of SKILL.md, not buried.

## Validation
Run the commands above; do manual plan-mode run on a throwaway task and compare length.
