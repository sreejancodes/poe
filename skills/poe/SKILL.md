---
name: poe
description: Plan, decompose, and execute complex coding or analysis tasks in phases using fresh-context subagents and file-based progress notes. Use when the user explicitly requests staged multi-agent work, context-conscious orchestration, or continuation of an existing phase plan.
argument-hint: "[plan|split|execute|resume] [task description or plan path]"
disable-model-invocation: true
---

# Phase-Orchestrated Work

User request: $ARGUMENTS

You are the **orchestrator**. Keep the parent conversation focused on decisions, dependency management, integration, and verification. Delegate bounded implementation or research to fresh-context subagents rather than accumulating their intermediate work in the parent context.

## Operating modes

- `plan <task>` (or a task description without a mode): write `plan.md` only, then stop so the user can review it. Do not split it into phases and do not edit implementation files.
- `split [plan-path]`: split a reviewed `plan.md` into phases and work units, then stop for user approval. Do not edit implementation files.
- `execute [plan-path]`: execute a plan that has been split and approved. If the plan has no phase briefs yet, say so and ask the user to run `split` first.
- When a mode is given no path, use the unambiguous active plan in `plans/`; otherwise ask for the path.
- `resume [plan-path]`: read `status.md` and the progress notes, compare them with the actual files, tests, and git diff, reconcile discrepancies, and continue only incomplete approved work.
- For small, single-file or tightly coupled changes, recommend doing the work directly instead of forcing subagents. If the user still requests orchestration, comply.

## Files

Everything for one task lives in `plans/<short-task-slug>/`, relative to the current working directory (the directory the session was started in, even if that is not the repository root). Create `plans/` and the task directory if they do not exist (`mkdir -p`). Never overwrite the directory of a different task; pick a distinct slug.

```
plans/<short-task-slug>/
  plan.md              what will be built and why (written by `plan`)
  phases/NN-name.md    one brief per phase, listing its work units (written by `split`)
  status.md            state of every phase and unit, and the next action
  progress/NN-unit.md  running notes written by each worker during execution
```

## Plan mode: write `plan.md`

1. Inspect only the relevant repository context, instructions, tests, and environment. Use read-only exploration subagents when exploration would otherwise overwhelm parent context.
2. Write `plans/<short-task-slug>/plan.md` from what the user wants to do: objective, scope and exclusions, assumptions, the approach, acceptance criteria, risks, and how the result will be tested or validated. This file describes the work itself; it does not mention phases, subagents, or token budgets.
3. **Do not overengineer.** Plan the simplest approach that meets the stated requirements:
   - Build only what the user asked for. No speculative features, configuration options, plugin systems, or abstraction layers added "for later".
   - Prefer the tools, libraries, and patterns the repository already uses over introducing new ones.
   - The resulting code must stay readable by humans: plain control flow, descriptive names, small functions, and comments only where the reason is not obvious. Prefer a few clear lines over a clever one.
   - Keep the process as light as the code. Do not add steps, files, or reviews that the task does not need.
4. Do not silently choose a major architecture if it needs user approval; ask before writing it into the plan.
5. Show a short summary of the plan, state the path of `plan.md`, and stop. The user reviews the file and may ask for changes; apply requested changes to `plan.md` and stop again. Do not proceed to the split until the user runs `split`.

## Split mode: split `plan.md` into phases and work units

Read `plan.md` as it currently is on disk, including any edits the user made by hand. If phase briefs already exist from an earlier split and no unit has been started, replace them; if work has started, ask before changing them.

1. Split the plan into ordered **phases** with explicit dependencies, and each phase into **work units**. One work unit is handled by one fresh subagent and must be independently verifiable.
2. Size each unit so that one subagent can finish it in roughly 100k tokens of context, counting the files it must read, the edits, and the test output. Split a unit that looks larger; merge units that are trivially small. Use as few phases and units as the work actually needs.
3. Identify which units can run in parallel because they do not modify overlapping files or share mutable state. Run dependent or overlapping units sequentially, or isolate them in separate git worktrees and integrate deliberately.
4. Write one brief per phase at `phases/NN-name.md`. For each unit give: goal, inputs and files to read, files it may change, explicit non-goals, exact verification commands, completion criteria, and its progress-notes path.
5. Write `status.md` listing every phase and unit as pending.
6. Show the phase split, state where the files are, and ask for approval. Do not start implementation in `split` mode.

## Execute mode

1. Read `plan.md`, `status.md`, and the brief of the next phase. Verify that the plan is approved and the prerequisites of the next unit are satisfied.
2. Dispatch a **fresh non-fork subagent** for each work unit. Prefer the `poe:phase-worker` subagent bundled with this plugin (if it is not available under that name, look for `phase-worker`); otherwise use an appropriate built-in agent capable of doing the work. Do not use a fork for routine delegation: it inherits the parent's history.
3. Give the worker only: the goal, the phase-brief path, necessary repository paths, interfaces and dependencies, allowed files, completion criteria, and its progress-notes path. Do not paste the parent conversation or large tool output.
4. The worker implements or analyzes only its assigned unit and runs the relevant tests. It writes its progress notes **as it works**, not only at the end: it updates the notes file after each meaningful step, so that the notes are current if the worker stops, is compacted, or fails.
5. Run independent, non-overlapping units in parallel only when safe. Never silently overwrite another agent's edits.
6. Check the worker's claims against the actual files, test outputs, and git diff. For significant or high-risk changes, use a separate fresh-context reviewer before marking the unit verified. Fix or reassign failed units with a new scoped brief.
7. Update `status.md` after every unit. Keep the parent response concise: phase, tests, blockers, and next action. Reference files rather than returning large transcripts.
8. Move to the next approved phase after verification. Stop for genuinely ambiguous requirements, security-sensitive changes, destructive operations, deployments, or decisions beyond the approved plan.
9. At completion, run integration tests, review the full change set, and report what passed, what remains uncertain, and where the files were saved.

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
