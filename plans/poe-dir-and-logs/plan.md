# Plan: move poe output to `poe/` and keep copies of Claude session logs

## Objective

1. Write everything poe produces (plans, phase briefs, status, progress notes, execution summaries) under `poe/<task-slug>/` instead of `plans/<task-slug>/`.
2. Keep a copy of the Claude Code session transcripts (`.jsonl`) for each poe task inside that task's directory, including the transcripts of the `phase-worker` subagents, so that they can later feed visualisations, dashboards, and evaluation of what poe and its agents did.

## Scope

In scope:

- `skills/poe/SKILL.md`: rename the output root, add an execution summary file, and add a log-copy step.
- `README.md`: update paths, the file layout, and add a short note on the log copies.
- `agents/phase-worker.md`: only if it mentions the output path (it currently does not; expected to stay unchanged).

Out of scope:

- Any visualisation, dashboard, parser, or evaluation tooling. This change only collects the raw data.
- Transforming, filtering, or summarising the `.jsonl` files. They are copied byte for byte.
- Automatic migration of existing `plans/` directories in user projects.
- Hooks, scripts, or new configuration options.

## Assumptions

- Claude Code stores the main transcript at `~/.claude/projects/<encoded-cwd>/<session-id>.jsonl` and subagent transcripts at `~/.claude/projects/<encoded-cwd>/<session-id>/subagents/agent-<id>.jsonl` (plus `agent-<id>.meta.json`). This layout was observed on this machine.
- Skills support the `${CLAUDE_SESSION_ID}` substitution, so the skill text can name the current session's transcript. **To be confirmed during implementation** against the Claude Code skills documentation; if it is not available, fall back to the most recently modified `.jsonl` in the project's transcript folder and say so in the plan's risks.
- A task may span several sessions (e.g. `plan` in one, `execute` or `resume` in another). Each session's logs are kept separately, never merged.
- "Execution summary logs" means a written summary of an `execute`/`resume` run. The current skill only reports this in chat; it will now also be written to a file.

## Approach

### 1. New directory layout

```
poe/<task-slug>/
  plan.md              what will be built and why
  phases/NN-name.md    one brief per phase
  status.md            state of every phase and unit
  progress/NN-unit.md  running notes written by each worker
  summary.md           execution summary written at the end of execute/resume
  logs/<session-id>/   copies of Claude Code transcripts for each session that worked on this task
    <session-id>.jsonl         main (orchestrator) transcript
    subagents/agent-*.jsonl    worker transcripts
    subagents/agent-*.meta.json
```

In `SKILL.md`, replace every `plans/` reference with `poe/` (the Files section, the default-path rule for modes, and the plan-mode step).

### 2. Execution summary

At the end of `execute` (and of `resume` when it finishes or stops), the orchestrator writes `summary.md` with what it already reports in chat: what passed, what remains uncertain, blockers, and where the files are. Overwrite it on each run; `status.md` remains the source of truth for state.

### 3. Log copy step

Add a short "Logs" section to `SKILL.md`. At the end of every mode (`plan`, `split`, `execute`, `resume`), and when stopping for user input mid-execution, the orchestrator runs one copy command, roughly:

```sh
dest="poe/<task-slug>/logs/${CLAUDE_SESSION_ID}"
src=$(find ~/.claude/projects -name "${CLAUDE_SESSION_ID}.jsonl" | head -1)
mkdir -p "$dest"
cp "$src" "$dest/"
[ -d "${src%.jsonl}/subagents" ] && cp -R "${src%.jsonl}/subagents" "$dest/"
```

- Re-running it overwrites the earlier copy with the longer, current transcript, so repeating it is safe.
- The copy is a snapshot: anything after the last copy (e.g. the final reply of the turn) is not included. That is acceptable; the next mode run refreshes it.
- If the source file cannot be found, the orchestrator says so in its reply and carries on; a missing log never blocks the task.

Locating the transcript with `find` avoids re-implementing Claude Code's path encoding.

### 4. README

- Update the usage examples and the Files section to `poe/`.
- Add `summary.md` and `logs/` to the layout.
- Note that the copied logs contain the full conversation, including file contents and command output, so users should normally add `poe/*/logs/` (or `poe/`) to `.gitignore`.
- One line for existing users: old tasks in `plans/` can be moved with `mv plans/<slug> poe/<slug>`.

## Acceptance criteria

- `grep -rn "plans/" skills agents README.md` returns no references to the poe output directory.
- `SKILL.md` and `README.md` describe the same layout, including `summary.md` and `logs/`.
- Running `/poe:poe plan <small task>` with `claude --plugin-dir .` in a scratch directory creates `poe/<slug>/plan.md` and `poe/<slug>/logs/<session-id>/<session-id>.jsonl`, and that file is a valid copy (`diff` against the original shows only appended lines missing at the end, if any).
- Running `split` then `execute` on that small task produces `summary.md` and copies `logs/<session-id>/subagents/agent-*.jsonl` for the worker(s).
- The plugin manifests still validate (`claude plugin validate .`, if available in the installed version).

## Risks

- **`${CLAUDE_SESSION_ID}` unavailable or renamed** in the skill substitution: the copy would target the wrong file. Mitigation: confirm in the docs before writing; fall back to the newest `.jsonl` in the project folder.
- **Transcript location changes** (Claude Code updates, or `CLAUDE_CONFIG_DIR` set to a non-default folder): the `find` misses. Mitigation: search `${CLAUDE_CONFIG_DIR:-~/.claude}/projects`; report a missing log rather than failing.
- **Sensitive data in logs**: transcripts can include secrets or private data read during the session. Mitigation: README gitignore advice; logs stay local and are never uploaded by poe.
- **Disk use**: transcripts are typically hundreds of KB to a few MB per session; acceptable.
- **Breaking change for existing users**: `resume`/`execute` with no path will no longer find tasks in `plans/`. Mitigation: README migration line; an explicit path to an old `plans/...` file still works because the skill accepts paths.

## Testing and validation

There is no test suite in this repository; validation is manual:

1. Static checks: the `grep` above, and reading `SKILL.md`/`README.md` side by side for consistency.
2. End-to-end in a scratch directory with `claude --plugin-dir /path/to/this/repo`: run `plan`, `split`, `execute` on a trivial task (e.g. "add a hello.txt file") and inspect `poe/<slug>/` for the expected files and log copies.
3. Confirm the copied main `.jsonl` parses line by line (`python3 -c 'import json,sys; [json.loads(l) for l in open(sys.argv[1])]' <file>`).
