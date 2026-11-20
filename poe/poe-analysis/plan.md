# poe-analysis

## Decisions
- Work shape: both. New step-loop mode for exploratory analysis (one step, record, user picks next) + existing plan/split/execute for well-defined analyses. Why: exploration must react to data; fixed analyses still benefit from batch.
- Code home: agent-run notebook. Agent adds cells to a .ipynb and executes headless; outputs stay in notebook; user opens same file. Why: matches existing Jupyter workflow, no extra tooling.
- Switching: one task, mixed. Single poe/<slug>/ holds analysis steps and coding phases; one plan, status, report. Switch = run other mode on same dir. Why: one story, nothing to link.
- Step record: step file + notebook. poe/<slug>/steps/NN-name.md per step (question, what run, result, interpretation, next step) pointing to notebook cells; notebook gets short markdown heading per step. Why: poe files drive resume/report; notebook readable alone.
- Notebook layout: agent decides per task. Start one notebook; start a new one + save intermediates when full re-runs get slow. Why: user choice; avoids forcing many files on small analyses. Plan must state a clear rule for when to split.
- Step runner: fresh worker per step. Subagent writes cells, runs, writes step file, returns short result. Why: keeps main session small; same pattern as execute.
- File home: project path fixed in plan.md (e.g. notebooks/<slug>/); step files in poe/<slug>/ link to notebooks/outputs. Why: deliverables where collaborators expect; large data out of poe/.
- Report: step files rendered as text + links to notebooks/figures; nothing embedded. Why (user): report.html tracks what the agent did, not outcomes.
- Naming: unit of analysis work = "analysis" (not "analysis step"); records in poe/<slug>/analysis/NN-name.md. Mode name `analyse` (verb, like other modes) = my interpretation, to confirm. Why: avoids clash with report "step" (transcript event).
- Timeline: one project-wide poe/docs/ANALYSIS_LOG.md, worker appends dated entry per analysis (question, one-line result, links to record/notebook/figures, which analysis it follows). Why: months of analyses across tasks must read as one chronology for the paper. Must not assume all work is agent/poe-done (hand edits: see next).
- Hand edits: both. `note <text>` mode logs user work in own words on demand; catch-up check at start of every `analyse` run (and on demand) finds notebook cells not covered by records, drafts "manual" log entries, user confirms. Why: not all analysis is agent/poe-done; log must have no holes.
- Few files: human must read every bit of analysis. Notebooks kept to as few as organisation and runtime need; new notebook only for a stated reason. Refines "Notebook layout".
- Untracked work = any work done outside poe: by the user or by a non-poe agent (rare). Catch-up and `note` cover both.
- Confirmed by user 2026-11-20, mode name `analyse` included.

## Objective

Let one poe task hold both coding and data analysis, with every analysis recorded and one project-wide chronology usable at paper write-up.

## Scope

- `skills/poe/SKILL.md`: new modes `analyse`, `note`; analysis files in Files section; analysis-record format; catch-up check; notebook rules; analysis units in `split`/`execute`.
- `agents/phase-worker.md`: rules for an analysis unit (notebook, tagging, record, log entry).
- `skills/poe/scripts/poe_report.py` + `tests/test_poe_report.py`: render `analysis/` records.
- `README.md`: document the above.

Excluded:
- Live-kernel / Jupyter MCP execution.
- Embedding figures or notebooks in `report.html`.
- Entry status (kept / superseded / dead end) in the log.
- Where analysis runs (local vs HPC): per-task, stated in that task's plan.
- R / non-Python notebooks.

## Assumptions

- Headless execution: `jupyter nbconvert --to notebook --execute --inplace <nb>`; worker reports and stops if `jupyter` missing.
- Agent-written cells tagged in cell metadata (`tags: ["poe:<slug>/<NN>"]`); untagged code cells = untracked work.
- Analysis numbering `NN` continues across `analyse` runs within a task.
- `analyse` loop ends when user says done → `summary.md`, logs, report as in Execute step 9.
- Next-analysis choice asked via `AskUserQuestion`, worker proposes 2–3 options.
- `resume` on a task with analyses: reads `status.md` + latest analysis record, continues loop.

## Approach

### Files

```
poe/docs/ANALYSIS_LOG.md      project-wide, date order, all tasks
poe/<slug>/analysis/NN-name.md   one record per analysis
<project path from plan.md>/     notebooks, figures, intermediates
```

- Task `plan.md` for analysis work adds: question, data paths, notebook/output path, environment.

### `analyse [task | plan-path]`

1. No plan → write short `plan.md` (question, data, paths), stop for review as Plan mode. Plan exists → continue.
2. Catch-up check (below).
3. Dispatch fresh `phase-worker` with: question for this analysis, notebook path, record path, previous record path, log path.
4. Worker: add tagged cells under a markdown heading `## NN: <question>`, execute, write record, append log entry, return ≤5 bullets + 2–3 proposed next analyses.
5. Orchestrator: verify notebook executed without error and record exists; update `status.md`; ask user for next analysis; repeat from 3.
6. Need a tool → `plan`/`split`/`execute` on same task dir; phases and analyses share `status.md`. Back → `analyse` again.

### Analysis record (`analysis/NN-name.md`)

```
# NN: <question>: status (done | failed | abandoned)
## Follows from
## What was run        notebook path + heading, inputs
## Result              numbers, figure/table paths
## Interpretation
## Caveats
## Next                options proposed; option chosen
```

### Notebook rules (worker)

- Default: append to the task's existing notebook. Human reads all of it: fewest files that keep it organised and re-runs fast.
- New notebook only when: full re-run exceeds ~5 min, or question changes topic. Then save intermediates the next notebook loads; state the reason in the record.
- No dead cells: failed attempts removed from notebook, described in record.

### Log entry (`poe/docs/ANALYSIS_LOG.md`)

```
## YYYY-MM-DD: <question>  [<slug>/NN | manual]
- Result: one line
- By: poe | user | other agent
- Follows: <slug>/NN
- Links: record, notebook#heading, figures
```

### Catch-up check

- Runs at start of every `analyse`; also `analyse catch-up` alone.
- Scan notebooks under the plan's path for untagged code cells (and notebooks with no record).
- Per group of adjacent untagged cells: draft `manual` log entry from code + outputs, ask user to confirm/fix wording, append. Tag cells `poe:manual` so they are not re-asked.

### `note <text>`

- Append `manual` log entry in user's words; link notebook if named or unambiguous; tag matching untagged cells `poe:manual`. No worker. Reply: entry path only.

### `split` / `execute` with analysis units

- Unit brief gains: notebook path, record path. Worker follows same notebook rules, writes record + log entry in addition to progress notes.

### Report

- Add `analysis` to `TASK_DOCUMENT_FOLDERS`; records render as text with links, in file order. No embedding.

## Acceptance criteria

- `SKILL.md` documents `analyse`, `note`, catch-up, record format, log format, notebook rules.
- `phase-worker.md` covers analysis units.
- `poe_report.py` shows `analysis/*.md` in Documents; test added; `python3 -m unittest discover tests` passes.
- Dry run on a toy dataset: `analyse` ×2 → one notebook, 2 tagged sections, 2 records, 2 log entries; hand-add a cell → next `analyse` drafts a `manual` entry; `note` appends an entry; `execute` on same task leaves analyses intact and `report.html` shows both.
- Glossary terms used consistently: [GLOSSARY](../docs/GLOSSARY.md).

## Risks

- Many record files per task vs "few files" wish: records are short and agent-facing; human reads notebook + `ANALYSIS_LOG.md`. Revisit if noisy.
- Catch-up misreads hand edits to tagged cells (edits inside agent cells not detected). Accepted; `note` covers it.
- `nbconvert --inplace` rewrites notebook while user has it open → conflict. Worker checks git status / warns before executing.
- Whole-notebook re-run cost grows; ~5 min rule is a judgement.
- Log entries appended by parallel workers could interleave: analysis units that write the log run sequentially.

## Validation

- `python3 -m unittest discover tests`
- Manual dry run above in a scratch directory; inspect notebook, records, log, `report.html`.
