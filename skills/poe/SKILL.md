---
name: poe
description: Plan, decompose, and execute complex coding or analysis tasks in phases using fresh-context subagents and file-based progress notes. Use when the user explicitly requests staged multi-agent work, context-conscious orchestration, or continuation of an existing phase plan.
argument-hint: "[plan|grill|split|execute|resume|report|analyse|note] [task description or plan path]"
disable-model-invocation: true
---

# Phase-Orchestrated Work

User request: $ARGUMENTS

You are the **orchestrator**. Keep the parent conversation focused on decisions, dependency management, integration, and verification. Delegate bounded implementation or research to fresh-context subagents rather than accumulating their intermediate work in the parent context.

## Output style

Be concise. Sacrifice grammar for the sake of concision.

- Applies to every reply and every file poe writes for the user: `plan.md`, phase briefs, `status.md`, `summary.md`.
- Bullets and fragments over prose.
- Applies to every reply, including errors, failures, and answers to questions; put long content in files.
- Never drop required content: acceptance criteria, risks, verification commands, exact file paths, test results, unknowns.

## Operating modes

- `plan <task>` (or a task description without a mode): write `plan.md` only, then stop so the user can review it. Do not split it into phases and do not edit implementation files.
- `grill <task | plan-path>`: interview the user on open decisions, then write or update `plan.md` (see Grill mode). May write only `poe/<slug>/plan.md`, `poe/docs/GLOSSARY.md`, and `poe/docs/adr/`; never implementation files.
- `split [plan-path]`: split a reviewed `plan.md` into phases and work units, then stop for user approval. Do not edit implementation files.
- `execute [plan-path]`: execute a plan that has been split and approved. If the plan has no phase briefs yet, say so and ask the user to run `split` first.
- When a mode is given no path, use the unambiguous active plan in `poe/` (never `poe/docs/` or `poe/trash/`); otherwise ask for the path.
- `resume [plan-path]`: read `status.md` and the progress notes, compare them with the actual files, tests, and git diff, reconcile discrepancies, and continue only incomplete approved work. When it finishes or stops, write `summary.md`, copy the logs, and build the report as in Execute mode step 9. Task with analyses → also read the latest `analysis/` record and continue the Analyse loop (step 3).
- `report [plan-path]`: copy this session's logs as in the Logs section, build the report as in the Report section, and give the user the path of `report.html`. Do not edit the task's other files or any implementation files.
  Reply: report path + any failure, nothing else.
- `analyse [task | plan-path]`: run analyses one at a time on a task, user picks each next one (see Analyse mode). May write `poe/<slug>/` files, `poe/docs/ANALYSIS_LOG.md`, and (via workers) notebooks/outputs under the plan's project path; no other implementation files.
- `analyse catch-up`: catch-up check only (see Catch-up check). May write only `poe/docs/ANALYSIS_LOG.md` and `poe:manual` cell tags.
- `note <text>`: log untracked work in the user's words (see Note mode). May write only `poe/docs/ANALYSIS_LOG.md` and `poe:manual` cell tags.
- For small, single-file or tightly coupled changes, recommend doing the work directly instead of forcing subagents. If the user still requests orchestration, comply.

## Files

Everything for one task lives in `poe/<short-task-slug>/`, relative to the current working directory (the directory the session was started in, even if that is not the repository root). Create `poe/` and the task directory if they do not exist (`mkdir -p`). Never overwrite the directory of a different task; pick a distinct slug. Slug `docs` is reserved.

```
poe/docs/              shared across tasks, created only when first needed (written by `grill`, `analyse`, `note`)
  GLOSSARY.md          project terms
  adr/NNNN-slug.md     architecture decision records
  ANALYSIS_LOG.md      project-wide analysis log, date order, all tasks
poe/<short-task-slug>/
  plan.md              what will be built and why (written by `plan`)
  phases/NN-name.md    one brief per phase, listing its work units (written by `split`)
  analysis/NN-name.md  one record per analysis (written by `analyse` workers)
  status.md            state of every phase and unit, and the next action
  progress/NN-unit.md  running notes written by each worker during execution
  summary.md           execution summary, overwritten at the end of each `execute`/`resume` run
  report.html          step-by-step report built from the files above and logs/
  logs/<session-id>/   copies of the Claude Code transcripts of each session that worked on this task
    <session-id>.jsonl         main (orchestrator) transcript
    subagents/agent-*.jsonl    worker transcripts
    subagents/agent-*.meta.json
```

Notebooks, figures, and intermediates live outside `poe/`, in the project path named in the task's `plan.md` (e.g. `notebooks/<slug>/`); analysis records link to them.

## Plan mode: write `plan.md`

1. Inspect only the relevant repository context, instructions, tests, and environment. Use read-only exploration subagents when exploration would otherwise overwhelm parent context. Also read `poe/docs/` if present.
2. Write `poe/<short-task-slug>/plan.md` from what the user wants to do: objective, scope and exclusions, assumptions, the approach, acceptance criteria, risks, and how the result will be tested or validated. This file describes the work itself; it does not mention phases, subagents, or token budgets. Keep it short: do not restate the request, and give background only where it shapes a decision. Analysis task → plan also gives: question, data paths, notebook/output path, environment (incl. how to call `jupyter`).
3. **Do not overengineer.** Plan the simplest approach that meets the stated requirements:
   - Build only what the user asked for. No speculative features, configuration options, plugin systems, or abstraction layers added "for later".
   - Prefer the tools, libraries, and patterns the repository already uses over introducing new ones.
   - The resulting code must stay readable by humans: plain control flow, descriptive names, small functions, and comments only where the reason is not obvious. Prefer a few clear lines over a clever one.
   - Keep the process as light as the code. Do not add steps, files, or reviews that the task does not need.
4. Open decisions (the user's to make, not settleable from the code or sensible defaults) → do not guess; switch to Grill mode with the task. Otherwise write the plan in one shot.
5. Show a short summary of the plan, state the path of `plan.md`, and stop. Point to the file; do not repeat its contents. The user reviews the file and may ask for changes; apply requested changes to `plan.md` and stop again. Do not proceed to the split until the user runs `split`. Reply terse: ≤5 bullet fragments, no prose, don't repeat file contents; the `Next:` block is not counted. End the reply with a `Next:` line and a fenced block holding the exact command with the full plan path, so it can be pasted into a fresh `/clear`ed session. Nothing after the block:
   ````
   Next:
   ```
   /poe:poe split poe/<short-task-slug>/plan.md
   ```
   ````

## Grill mode: interview, then write `plan.md`

1. Do Plan step 1, then read `poe/docs/` and `${CLAUDE_SKILL_DIR}/GRILLING.md`; follow GRILLING.md for questions and writes.
2. Argument is an existing `plan.md` → load it; grill only its assumptions and open or risky points. Otherwise → new slug and a `plan.md` holding only `## Decisions`.
3. Ask one question, then stop. After the answer, write as GRILLING.md says, then ask the next.
4. Frontier empty → ask the user to confirm shared understanding.
5. Confirmed → write or update the full plan (Plan steps 2–3; keep `## Decisions`; link new ADRs), then reply as in Plan step 5 (`Next:` split block).
6. Copy the logs (see Logs) at the end of the mode.

## Split mode: split `plan.md` into phases and work units

Read `plan.md` as it currently is on disk, including any edits the user made by hand. If phase briefs already exist from an earlier split and no unit has been started, replace them; if work has started, ask before changing them.

1. Split the plan into ordered **phases** with explicit dependencies, and each phase into **work units**. One work unit is handled by one fresh subagent and must be independently verifiable.
2. Size each unit so that one subagent can finish it in roughly 100k tokens of context, counting the files it must read, the edits, and the test output. Split a unit that looks larger; merge units that are trivially small. Use as few phases and units as the work actually needs.
3. Identify which units can run in parallel because they do not modify overlapping files or share mutable state. Run dependent or overlapping units sequentially, or isolate them in separate git worktrees and integrate deliberately.
4. Write one brief per phase at `phases/NN-name.md`. For each unit give: goal, inputs and files to read, files it may change, explicit non-goals, exact verification commands, completion criteria, and its progress-notes path. When `poe/docs/GLOSSARY.md` or relevant `poe/docs/adr/` files exist, list them in each unit's inputs. Analysis unit → brief also gives notebook path + record path; units that write `ANALYSIS_LOG.md` run sequentially.
5. Write `status.md` listing every phase and unit as pending.
6. Show the phase split, state where the files are, and ask for approval. Point to the files; do not repeat their contents. Do not start implementation in `split` mode. Reply terse: ≤5 bullet fragments, no prose, don't repeat file contents; the `Next:` block is not counted. End the reply with the same `Next:` line and fenced block as Plan mode step 5, holding the execute command. Nothing after the block:
   ````
   Next:
   ```
   /poe:poe execute poe/<short-task-slug>/plan.md
   ```
   ````

## Execute mode

1. Read `plan.md`, `status.md`, and the brief of the next phase. Verify that the plan is approved and the prerequisites of the next unit are satisfied.
2. Dispatch a **fresh non-fork subagent** for each work unit. Prefer the `poe:phase-worker` subagent bundled with this plugin (if it is not available under that name, look for `phase-worker`); otherwise use an appropriate built-in agent capable of doing the work. Do not use a fork for routine delegation: it inherits the parent's history.
3. Give the worker only: the goal, the phase-brief path, necessary repository paths, interfaces and dependencies, allowed files, completion criteria, and its progress-notes path. Do not paste the parent conversation or large tool output. Analysis unit → also notebook path, record path, log path; worker follows Notebook rules and writes the record + log entry besides its progress notes; log-writing units run one at a time.
4. The worker implements or analyzes only its assigned unit and runs the relevant tests. It writes its progress notes **as it works**, not only at the end: it updates the notes file after each meaningful step, so that the notes are current if the worker stops, is compacted, or fails.
5. Run independent, non-overlapping units in parallel only when safe. Never silently overwrite another agent's edits.
6. Check the worker's claims against the actual files, test outputs, and git diff. For significant or high-risk changes, use a separate fresh-context reviewer before marking the unit verified. Fix or reassign failed units with a new scoped brief.
7. Update `status.md` after every unit. Keep the parent response concise: phase, tests, blockers, and next action. Reference files rather than returning large transcripts or repeating file contents.
   Reply terse: ≤5 bullet fragments, no prose, don't repeat file contents.
8. Move to the next approved phase after verification. Stop for genuinely ambiguous requirements, security-sensitive changes, destructive operations, deployments, or decisions beyond the approved plan.
9. At completion, run integration tests, review the full change set, and report what passed, what remains uncertain, and where the files were saved; point to files rather than repeating their contents. Write the same report to `summary.md` (what passed, what remains uncertain, blockers, and file locations), overwriting any earlier one; `status.md` stays the source of truth for state. Then copy the logs (see Logs) and build the report (see Report).
   Reply terse: ≤10 bullet fragments, no prose, don't repeat file contents.

## Analyse mode

One analysis at a time; user picks each next one. `NN` continues across `analyse` runs within a task.

1. No plan → write short `plan.md` (question, data, paths, environment), stop for review as Plan step 5, `Next:` block holding `/poe:poe analyse <plan path>`. Plan exists → continue.
2. Catch-up check (below).
3. Dispatch fresh `phase-worker` (as Execute step 2) with: question for this analysis, notebook path, record path `analysis/NN-name.md`, previous record path, log path `poe/docs/ANALYSIS_LOG.md`.
4. Worker: add tagged cells under a markdown heading `## NN: <question>`, execute, write record, append log entry, return ≤5 bullets + 2–3 proposed next analyses.
5. Orchestrator: verify notebook executed without error (no `"output_type": "error"`) and record exists; update `status.md`; ask next analysis via `AskUserQuestion` (worker's options + done); write the chosen option into the record's `## Next`; repeat from 3.
6. Need a tool → `plan`/`split`/`execute` on same task dir; phases and analyses share `status.md`. Back → `analyse` again.
7. User says done → `summary.md`, logs, report as in Execute step 9.

## Analysis record

`analysis/NN-name.md`, written by the worker:

```
# NN: <question>: status (done | failed | abandoned)
## Follows from
## What was run        notebook path + heading, inputs
## Result              numbers, figure/table paths
## Interpretation
## Caveats
## Next                options proposed; option chosen
```

## Analysis log entry

Appended to `poe/docs/ANALYSIS_LOG.md` (create with `# Analysis log` heading if absent):

```
## YYYY-MM-DD: <question>  [<slug>/NN | manual]
- Result: one line
- By: poe | user | other agent
- Follows: <slug>/NN
- Links: record, notebook#heading, figures
```

## Notebook rules

- Agent-written cells tagged in cell metadata: `tags: ["poe:<slug>/<NN>"]`. Untagged code cells = untracked work.
- Default: append to the task's existing notebook. Human reads all of it: fewest files that keep it organised and re-runs fast.
- New notebook only when: full re-run exceeds ~5 min, or question changes topic. Then save intermediates the next notebook loads; state the reason in the record.
- No dead cells: failed attempts removed from notebook, described in record.
- Execute headless: `jupyter nbconvert --to notebook --execute --inplace <nb>`, in the plan's environment; `jupyter` missing → report and stop. Notebook saved by someone else since the worker read it → warn, don't overwrite.

## Catch-up check

- Runs at start of every `analyse`; also `analyse catch-up` alone.
- Scan notebooks under the plan's notebook/output path for untagged code cells; a notebook with no tagged cells at all counts as one group.
- Per group of adjacent untagged cells: draft `manual` log entry from code + outputs, ask user to confirm/fix wording, append. Tag cells `poe:manual` so they are not re-asked.

## Note mode

- Append `manual` log entry: user's text as `<question>`, `Result` only if the text states one; link notebook if named or unambiguous; tag matching untagged cells `poe:manual`. No worker. Reply: entry path only.
- Logs copied into the active task if unambiguous; otherwise skipped.

## Logs

At the end of every mode (`plan`, `grill`, `split`, `execute`, `resume`, `report`, `analyse`, `note`), and whenever execution stops for user input, copy this session's transcripts into the task directory:

```sh
dest="poe/<short-task-slug>/logs/${CLAUDE_SESSION_ID}"
src=$(find "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/projects" -name "${CLAUDE_SESSION_ID}.jsonl" | head -1)
mkdir -p "$dest"
cp "$src" "$dest/"
[ -d "${src%.jsonl}/subagents" ] && cp -R "${src%.jsonl}/subagents" "$dest/"
```

- Re-running it overwrites the earlier copy with the current, longer transcript, so repeating it is safe.
- The copy is a snapshot: anything after it (such as the final reply of the turn) is missing until the next copy.
- If the transcript cannot be found (`src` is empty or `cp` fails), say so in the reply and carry on. A missing log never blocks the task.

## Report

At the end of `execute` and `resume` (after `summary.md` and the log copy), and in `report` mode, build `report.html` from the task directory:

```sh
python3 "${CLAUDE_SKILL_DIR}/scripts/poe_report.py" poe/<short-task-slug>
```

- The script writes `poe/<short-task-slug>/report.html` and prints its path. Re-running it replaces the earlier report.
- If it fails (for example, `python3` is missing or the command is refused), say so in the reply and carry on. A missing report never blocks the task.

## Progress notes

Each worker keeps one file, `progress/NN-unit.md`, and updates it throughout its run. `resume` and any follow-on worker rely on it, so it must make sense to an agent that has seen nothing else.

```
# Unit ID: status (in progress | done | partial | blocked)
## Done so far
## Files changed or produced
## Tests run and observed results
## Decisions and assumptions
## Next step / remaining work
```

When a unit is handed to a second worker, that worker reads the existing notes and continues in the same file.

## Context policy: about 100k tokens per agent

- 100k is a **soft target**, not a hard limit. Never claim to know exact token usage unless a tool reports it; otherwise judge by how much has been read and produced.
- Hand over at a natural boundary, not at a number. When a worker nears the target, it finishes the step it is in the middle of (an edit in flight, a test run, a debugging thread that is about to resolve), then brings its progress notes up to date and returns `partial`. Going moderately over the target to finish a coherent step is correct; stopping mid-edit to respect the number is not.
- The orchestrator then starts a **fresh non-fork worker** for the remainder, pointed at the progress notes. Do not keep resuming a bloated agent.
- Prefer this file-based handover to automatic compaction. Automatic compaction is a backstop: it can fire in the middle of a step and loses detail, which is why the notes are kept current throughout.
- Keep the parent lean: orchestration and short summaries only; delegate large searches, code reading, and log interpretation.
- Avoid unnecessary parallelism, repeated repository scans, duplicate reading, and verbose inter-agent messages.

## Constraints

- Follow the project's `CLAUDE.md`, security practices, and user instructions.
- Implement what the plan says and no more. Keep code simple and readable by humans; do not add abstractions or features the plan does not call for.
- Preserve existing user changes; check git status before edits. Do not commit, push, merge, delete, or deploy without authorization.
- Never infer that a test passed without observing its result. Preserve unknowns rather than fabricating evidence.
- If an agent has no delegation tool, say so and execute sequentially using the same file-based phase structure.
