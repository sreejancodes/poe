# all-analysis-html

## Decisions
- Build: stdlib Python script rebuilds whole HTML from files each run; add = regenerate. Why: user choice; no drift, no tokens.
- Purpose: results view only, not chronology. One page user opens after each analysis to see new result in context of the rest. Sparse notes (some interpretation kept; user interprets). Why: ANALYSIS_LOG.md covers when/who; report.html covers agent activity; this covers results.
- Separate from report.html (agent-activity dashboard) and ANALYSIS_LOG.md (chronology). Why: user.
- Grouping: section per poe task; inside, analyses nested by `Follows from` chain. Why: existing fields only; new result sits under the one it follows.
- Location: `poe/docs/all_analysis.html`, beside ANALYSIS_LOG.md. Why: project-wide poe file; root stays clean.
- Figures: inline `<img>` with path relative to `poe/docs/`; plus links to notebook + record. Why: page must show results; stays small. Accepted: breaks if files moved.
- Triggers: orchestrator rebuilds after every analysis (analyse step 5), `note`, and catch-up; new mode `results` rebuilds on demand (creates page if absent). Why: page always current; explicit cleanup when wanted.
- Untracked work shown, in context where possible: log entry with `Follows: <slug>/NN` → nested under that analysis; else notebook belongs to a task's notebook path → that task's section; else fallback "Untracked work" section. `note`/catch-up fill `Follows` when inferable (cells sit after a poe-tagged group, or user names it). Why: user — no holes, context over separation.
- Confirmed by user 2026-11-20.

## Objective

One project-wide **results page** (`poe/docs/all_analysis.html`) the user opens after each analysis to see every result, new ones in context. Script-built, always regenerable.

## Scope

- New `skills/poe/scripts/poe_results.py` (stdlib only, Python 3.9+, like `poe_report.py`).
- `skills/poe/SKILL.md`: new `results` mode; rebuild call in Analyse step 5, Note mode, Catch-up check; `note`/catch-up fill `Follows` when inferable; Files section lists `all_analysis.html`.
- `agents/phase-worker.md`: only if record format needs a tweak for parsing (e.g. figure paths one per line under `## Result`).
- `tests/test_poe_results.py` + fixture under `tests/fixtures/`.
- `README.md`: document results page + `results` mode.

Excluded:
- Changes to `report.html` / `poe_report.py`.
- Base64-embedded figures, JavaScript, external resources.
- Topic tags, cross-task grouping, dates/chronology on the page.
- Rendering notebook outputs directly (only saved figures named in records/log).

## Assumptions

- Input: `poe/docs/ANALYSIS_LOG.md` + every `poe/<slug>/analysis/NN-*.md` (skip `poe/docs/`, `poe/trash/`). Page built from these only.
- Per analysis shown: question, status, `## Result` text, first paragraph of `## Interpretation` (sparse), inline images, links to record + notebook#heading. Caveats and Next omitted.
- Figures = paths in `## Result` / log `Links` ending `.png .jpg .jpeg .svg .gif`; other paths (csv, pdf) shown as links. Paths resolved relative to session dir, emitted relative to `poe/docs/`. Missing file → link marked missing, no crash.
- Newest = last entry in `ANALYSIS_LOG.md`; marked "latest" and linked from top of page.
- Thread order: roots (no/unknown `Follows`) in NN order; children nested under parent in NN order. Unknown parent → treated as root.
- Untracked placement: `Follows` → under that analysis; else notebook path under a task plan's notebook path → task section; else "Untracked work" section.
- Abandoned/failed analyses shown, dimmed, so threads stay intact.
- Missing log or no analyses → page still written with an empty-state line.
- Page: single self-contained HTML, inline CSS, light/dark via `prefers-color-scheme`, no JS.
- Malformed record/log entry → skipped and counted in page footer, never fatal (as `poe_report.py`).

## Approach

- `poe_results.py <session-dir>` (default `.`): Load (parse log entries + records) → Arrange (tasks → thread trees, untracked placement) → Render (write `poe/docs/all_analysis.html`, print path). Overwrites every run = add and cleanup in one.
- SKILL.md:
  - Mode `results`: run script; reply path only. Allowed writes: `poe/docs/all_analysis.html`.
  - Analyse step 5, Note mode, Catch-up check: run script after log write. Failure → say so, never blocks (as Report).
  - Note mode / catch-up: set `Follows: <slug>/NN` when cells follow a poe-tagged group or user names it.
- Reuse small helpers from `poe_report.py` only by copy if trivial; no shared module unless obviously cleaner.

## Acceptance criteria

- `python3 skills/poe/scripts/poe_results.py <fixture>` writes `poe/docs/all_analysis.html` with: task sections, nested thread, inline img for existing figure, missing-figure marker, untracked entry placed under its `Follows` analysis, one in fallback section, latest marked.
- Second run on same input → byte-identical output.
- No-log / no-analysis dir → page with empty-state, exit 0.
- SKILL.md documents `results` mode and the auto-rebuild points; README updated.
- Existing tests still pass.

## Risks

- Record/log are free-form markdown written by agents → parsing brittle. Mitigation: parse only headings + the fixed log bullet keys; tolerate gaps.
- Relative image paths break if `poe/docs/` or figures moved. Accepted (Decisions).
- Large projects: many images on one page → slow load. Accepted for now; `loading="lazy"` on img.

## Validation

- `python3 -m unittest discover tests`
- Manual: run script on fixture, open HTML, check grouping/figures in light + dark.
