# poe: phase orchestrator for Claude Code

A Claude Code plugin with one skill (`poe`) and one subagent (`phase-worker`). It plans a task, splits it into work units sized for about 100k tokens each, and runs each unit in a fresh-context subagent that keeps file-based progress notes.

Requires Claude Code v2.1.296 or later.

## Installation

This repository is both the plugin and its own marketplace. Add the marketplace, then install the plugin:

```sh
claude plugin marketplace add sreejancodes/poe
claude plugin install poe@poe-tools
```

The same commands work inside a session as `/plugin marketplace add sreejancodes/poe` and `/plugin install poe@poe-tools`. Then run `/reload-plugins` or start a new session.

By default the plugin is installed at **user** scope, so it is available in every project. Add `--scope project` to enable it only for the current repository, recorded in `.claude/settings.json`.

### Update and uninstall

Third-party marketplaces do not update automatically. To get the latest version:

```sh
claude plugin marketplace update poe-tools
claude plugin update poe@poe-tools
```

To remove it:

```sh
claude plugin uninstall poe@poe-tools
claude plugin marketplace remove poe-tools
```

### Offering it to everyone on a project

Commit this to the project's `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "poe-tools": { "source": { "source": "github", "repo": "sreejancodes/poe" } }
  },
  "enabledPlugins": { "poe@poe-tools": true }
}
```

Once a collaborator trusts the folder, the marketplace is registered for them. They still need to run `claude plugin install poe@poe-tools --scope project` once.

## Usage

Plugin skills are namespaced, so the command is `/poe:poe`:

```text
/poe:poe plan Build an HPV ORF analysis pipeline with tests and reproducible outputs
/poe:poe split poe/hpv-orf-analysis/plan.md
/poe:poe execute poe/hpv-orf-analysis/plan.md
/poe:poe resume poe/hpv-orf-analysis/plan.md
/poe:poe report poe/hpv-orf-analysis/plan.md
```

- **Plan** writes `plan.md` from what you asked for, keeping the approach simple and the code human-readable, then stops. Review the file, edit it or ask for changes, and repeat until you are happy with it.
- **Split** takes the reviewed `plan.md` and splits it into phases and work units, each sized for one subagent at roughly 100k tokens. It then stops for approval.
- **Execute** hands each work unit to a fresh `poe:phase-worker` subagent, which writes progress notes as it works. The orchestrator verifies each unit before moving on.
- **Resume** uses the status file and progress notes to continue safely.
- **Report** copies the session's logs and (re)builds `report.html`, a step-by-step view of what the orchestrator and each worker did. Execute and resume also build it automatically at the end, after `summary.md` and the log copy; if the build fails, the reply says so and the task carries on.

## Files

Everything for one task is written under `poe/<task-slug>/` in the directory where Claude Code was started. `poe/` is created if it does not exist.

```
poe/<task-slug>/
  plan.md              what will be built and why
  phases/NN-name.md    one brief per phase, listing its work units
  status.md            state of every phase and unit
  progress/NN-unit.md  running notes written by each worker
  summary.md           execution summary, written at the end of execute/resume
  report.html          step-by-step report built from the files above and logs/
  logs/<session-id>/   copies of the Claude Code transcripts (.jsonl) of each session, including worker subagents
```

The copied logs contain the full conversation, including file contents and command output, and so does `report.html`. Normally add `poe/*/logs/` and `poe/*/report.html` (or all of `poe/`) to `.gitignore`.

To build the report by hand, without a Claude Code session (needs Python 3.9 or later, standard library only):

```sh
python3 <plugin>/skills/poe/scripts/poe_report.py poe/<task-slug>
```

`<plugin>` is this repository, or the installed plugin directory. The script writes `poe/<task-slug>/report.html` and prints its path. It is a single HTML file with no external resources, so it opens offline.

Tasks created by older versions in `plans/` can be moved with `mv plans/<slug> poe/<slug>`.

## Thinking text in the report

The report can only show thinking that Claude Code recorded in its transcripts. By default it records none, so each thinking step reads "thinking text not recorded". The overview and each transcript's totals show "thinking recorded: N of M blocks", so you can see whether it was on for a run.

To record it:

- Interactive sessions: set `"showThinkingSummaries": true` in `~/.claude/settings.json` (all projects) or in the project's `.claude/settings.json`. This also shows the summaries in the terminal. Workers are expected to inherit the setting from the session that starts them.
- Headless `claude -p` ignores that setting. Pass the flag instead: `claude -p --thinking-display summarized "..."`.

The recorded text is a summary of the reasoning, not the raw reasoning. Sessions that ran without it cannot be filled in later.

Steps labelled "narration" are short progress updates Claude Code writes alongside thinking; they are shown as they are and not counted as thinking.

## Context settings

The 100k figure is a soft target, not a hard cap. A worker nearing it finishes the step it is in the middle of, updates its progress notes, and returns. The orchestrator then starts a fresh worker from those notes.

`phase-worker` sets `autoCompactWindow: 150000`. This is a backstop above the target, so that automatic compaction does not interrupt a step at exactly 100k. It does not cap cumulative usage. Older Claude Code versions ignore the setting without warning.

The `CLAUDE_CODE_AUTO_COMPACT_WINDOW` environment variable takes precedence over a subagent's `autoCompactWindow`. Setting it to 100000 would make workers compact at 100k regardless, so leave it unset or set it above the target.

## Repository layout

```
.claude-plugin/plugin.json        plugin manifest
.claude-plugin/marketplace.json   marketplace listing this repo as the plugin source
skills/poe/SKILL.md               the /poe:poe orchestrator skill
skills/poe/scripts/poe_report.py  builds report.html for a task
agents/phase-worker.md            the worker subagent
```

To try local changes without installing: `claude --plugin-dir /path/to/this/repo`.

## References

- https://code.claude.com/docs/en/plugins
- https://code.claude.com/docs/en/skills
- https://code.claude.com/docs/en/sub-agents
