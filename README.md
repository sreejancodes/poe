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
/poe:poe split plans/hpv-orf-analysis/plan.md
/poe:poe execute plans/hpv-orf-analysis/plan.md
/poe:poe resume plans/hpv-orf-analysis/plan.md
```

- **Plan** writes `plan.md` from what you asked for, keeping the approach simple and the code human-readable, then stops. Review the file, edit it or ask for changes, and repeat until you are happy with it.
- **Split** takes the reviewed `plan.md` and splits it into phases and work units, each sized for one subagent at roughly 100k tokens. It then stops for approval.
- **Execute** hands each work unit to a fresh `poe:phase-worker` subagent, which writes progress notes as it works. The orchestrator verifies each unit before moving on.
- **Resume** uses the status file and progress notes to continue safely.

## Files

Everything for one task is written under `plans/<task-slug>/` in the directory where Claude Code was started. `plans/` is created if it does not exist.

```
plans/<task-slug>/
  plan.md              what will be built and why
  phases/NN-name.md    one brief per phase, listing its work units
  status.md            state of every phase and unit
  progress/NN-unit.md  running notes written by each worker
```

Decide per repository whether to track `plans/` in git or add it to `.gitignore`.

## Context settings

The 100k figure is a soft target, not a hard cap. A worker nearing it finishes the step it is in the middle of, updates its progress notes, and returns. The orchestrator then starts a fresh worker from those notes.

`phase-worker` sets `autoCompactWindow: 150000`. This is a backstop above the target, so that automatic compaction does not interrupt a step at exactly 100k. It does not cap cumulative usage. Older Claude Code versions ignore the setting without warning.

The `CLAUDE_CODE_AUTO_COMPACT_WINDOW` environment variable takes precedence over a subagent's `autoCompactWindow`. Setting it to 100000 would make workers compact at 100k regardless, so leave it unset or set it above the target.

## Repository layout

```
.claude-plugin/plugin.json        plugin manifest
.claude-plugin/marketplace.json   marketplace listing this repo as the plugin source
skills/poe/SKILL.md               the /poe:poe orchestrator skill
agents/phase-worker.md            the worker subagent
```

To try local changes without installing: `claude --plugin-dir /path/to/this/repo`.

## References

- https://code.claude.com/docs/en/plugins
- https://code.claude.com/docs/en/skills
- https://code.claude.com/docs/en/sub-agents
