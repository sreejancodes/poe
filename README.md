# poe: phase orchestrator for Claude Code

A Claude Code plugin with one skill (`poe`) and one subagent (`phase-worker`). It plans a task, splits it into work units sized for about 100k tokens each, and runs each unit in a fresh-context subagent that keeps file-based progress notes.

Requires Claude Code v2.1.296 or later. `analyse` also needs `jupyter` (for `nbconvert`) in the task's environment.

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
/poe:poe grill Build an HPV ORF analysis pipeline with tests and reproducible outputs
/poe:poe grill poe/hpv-orf-analysis/plan.md
/poe:poe split poe/hpv-orf-analysis/plan.md
/poe:poe execute poe/hpv-orf-analysis/plan.md
/poe:poe resume poe/hpv-orf-analysis/plan.md
/poe:poe report poe/hpv-orf-analysis/plan.md
/poe:poe analyse poe/hpv-orf-analysis/plan.md
/poe:poe analyse catch-up
/poe:poe note Plotted ORF lengths per genotype in notebooks/hpv-orf-analysis/orfs.ipynb
```

- **Plan** writes `plan.md` from what you asked for, keeping the approach simple and the code human-readable, then stops. Review the file, edit it or ask for changes, and repeat until you are happy with it. If it finds open decisions that only you can make, it switches to grill instead of guessing.
- **Grill** interviews you before planning. It asks one question at a time in a dialog: pick an option (the recommended one comes first), or type your own answer under Other. Each question shows `Q1 of ~N`, an estimate revised as answers add or remove questions. `grill <task>` starts from scratch and writes `plan.md` once you confirm; `grill <plan-path>` questions an existing plan's assumptions and open points and updates it in place. Decisions are added to `plan.md` under `## Decisions` after every answer; project terms and hard-to-reverse decisions go to the shared `poe/docs/`.
- **Split** takes the reviewed `plan.md` and splits it into phases and work units, each sized for one subagent at roughly 100k tokens. It then stops for approval.
- **Execute** hands each work unit to a fresh `poe:phase-worker` subagent, which writes progress notes as it works. The orchestrator verifies each unit before moving on.
- **Resume** uses the status file and progress notes to continue safely.
- **Report** copies the session's logs and (re)builds `report.html`, a step-by-step view of what the orchestrator and each worker did. Execute and resume also build it automatically at the end, after `summary.md` and the log copy; if the build fails, the reply says so and the task carries on.
- **Analyse** runs data analyses one at a time in a Jupyter notebook; you pick each next one. See [Analysis](#analysis).
- **Analyse catch-up** finds notebook cells poe did not write and logs them, with your confirmation.
- **Note** logs analysis you did yourself, in your own words.

Use `plan` when the task is clear. Use `grill` when you want to be interviewed, or to challenge a draft plan.

Output is deliberately terse: replies point to files instead of repeating them, and plan and split replies end with the next command to paste.

## Analysis

One task can hold both coding and analysis. Use `plan`, `split` and `execute` to build tools and `analyse` to explore data; switch by running the other mode on the same `plan.md`. Phases and analyses share `status.md` and `report.html`.

- **Start**: `/poe:poe analyse <task>`. Without a plan, it writes a short `plan.md` (question, data paths, notebook/output path, environment and how to call `jupyter`) and stops for review. Then run `/poe:poe analyse poe/<task-slug>/plan.md`.
- **Each analysis**: a fresh worker adds cells under a heading `## NN: <question>`, runs the notebook headless (`jupyter nbconvert --to notebook --execute --inplace`), writes a record `poe/<task-slug>/analysis/NN-name.md` and appends an entry to `poe/docs/ANALYSIS_LOG.md`. It proposes 2-3 next analyses; pick one or say done. Done writes `summary.md`, copies logs and builds the report, as execute does. `NN` continues across runs.
- **Notebook rules**: cells poe writes are tagged `poe:<task-slug>/<NN>` in cell metadata. New cells go into the existing notebook; a new notebook is started only when a full re-run takes over ~5 min or the topic changes, and the record says why. Failed attempts are removed from the notebook and described in the record. Notebooks, figures and intermediates live in the project path from `plan.md`, not under `poe/`.
- **Open notebooks**: `--inplace` rewrites the file, so save your edits before an analysis runs. The worker stops with a warning if the notebook was saved by someone else after it read it.
- **Analysis log**: `poe/docs/ANALYSIS_LOG.md` is one chronology for the whole project, across tasks, meant for writing up. Each entry gives the date, question, a one-line result, who did it (poe, user, other agent) and links.
- **Untracked work** (analysis done outside poe, by you or another agent) shows up as untagged code cells. Every `analyse` run starts with a catch-up check (`analyse catch-up` runs it alone): for each group of adjacent untagged cells it drafts a `manual` log entry, asks you to confirm or fix it, appends it and tags the cells `poe:manual` so they are not asked about again. `note <text>` logs such work directly in your words.
- **Well-defined analyses** can also be planned as work units in `split`/`execute`; the worker follows the same notebook rules and writes a record and log entry. Units that write the log run one at a time.
- `report.html` shows analysis records as text; notebooks and figures are not embedded.

Record, log entry and notebook rules in full: [`skills/poe/SKILL.md`](skills/poe/SKILL.md).

## Files

Everything for one task is written under `poe/<task-slug>/` in the directory where Claude Code was started. `poe/` is created if it does not exist. `poe/docs/` is shared across tasks, so `docs` is not used as a task slug.

```
poe/docs/              shared across tasks, written by grill, analyse and note, created when first needed
  GLOSSARY.md          project terms
  adr/NNNN-slug.md     architecture decision records
  ANALYSIS_LOG.md      project-wide analysis log, date order, all tasks
poe/<task-slug>/
  plan.md              what will be built and why
  phases/NN-name.md    one brief per phase, listing its work units
  analysis/NN-name.md  one record per analysis
  status.md            state of every phase and unit
  progress/NN-unit.md  running notes written by each worker
  summary.md           execution summary, written at the end of execute/resume
  report.html          step-by-step report built from the files above and logs/
  logs/<session-id>/   copies of the Claude Code transcripts (.jsonl) of each session, including worker subagents
```

Commit all of `poe/`, including `logs/` and `report.html`. Together with the plan, briefs and progress notes, the transcripts are what make an agentic workflow reproducible: anyone can see what was asked, what each agent did and why. The copied logs contain the full conversation, including file contents and command output, and so does `report.html`. Check them for secrets or data that must not leave the machine before pushing, and add only those paths to `.gitignore` if needed. Do not ignore all of `poe/`, so that `poe/docs/` stays in git.

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
skills/poe/GRILLING.md            the interview method used by grill
skills/poe/scripts/poe_report.py  builds report.html for a task
agents/phase-worker.md            the worker subagent
```

To try local changes without installing: `claude --plugin-dir /path/to/this/repo`.

## References

- https://code.claude.com/docs/en/plugins
- https://code.claude.com/docs/en/skills
- https://code.claude.com/docs/en/sub-agents
- Grill mode adapts the grilling and domain-modeling method from Matt Pocock's skills, https://github.com/mattpocock/skills (MIT, © 2026 Matt Pocock).
