# poe index

## Decisions

_None settled yet. Round 1 asked: purpose of the index, alongside vs integrate vs native, where visualisations live._

## Facts gathered

- repowise: Python 3.11+ CLI (`uv tool install repowise`), AGPL-3.0; dashboard needs Node 20+.
- `repowise init --yes --no-prose`: graph, git intelligence, health, dead code, change risk; zero LLM calls, no key.
- LLM (own key or Ollama) only for wiki prose, decision mining, refactor codegen.
- Ships MCP server (10 default tools, staleness `_meta`), Claude Code plugin, hooks, CLAUDE.md generation; `repowise update` incremental.
- Source: https://github.com/repowise-dev/repowise (README, fetched 2026-11-19; not installed or tested locally).
- poe today: SKILL.md + one stdlib-only script (`poe_report.py`, 871 lines), Python 3.9+, no dependencies.
