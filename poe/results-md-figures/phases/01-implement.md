# Phase 01: implement

Depends on: none. Units 01a + 01b run in parallel (disjoint files).

Shared inputs (both units):
- `poe/results-md-figures/plan.md` (Decisions, Assumptions, Acceptance criteria)
- `poe/docs/GLOSSARY.md`
- No ADRs.

## 01a: markdown rendering on results page

- Goal: `poe_results.py` renders record `## Result` + Interpretation as markdown subset (plan Assumptions) instead of escaped pre-wrap text.
- Read: `skills/poe/scripts/poe_results.py`, `tests/test_poe_results.py`, `tests/fixtures/results/`.
- May change:
  - `skills/poe/scripts/poe_results.py`
  - `tests/test_poe_results.py`
  - `tests/fixtures/results/**` (add/extend a record with nested bullets, pipe table, bold, italic, code, link, `<script>`)
- Work:
  - `render_inline(text)`: escape first, then code → bold → italic → links; session-relative link targets via `page_href`, `http(s)` kept.
  - `render_markdown(text, ...)`: blocks = pipe tables (header + `---` row), lists (`-`/`*`/`1.`, nested by indent), paragraphs; unknown → escaped paragraph; never raises.
  - Use in `render_analysis` for result + interpretation; drop `white-space: pre-wrap`; CSS for `ul/ol`, `table` (border, padding, scroll wrapper), `code`, light + dark.
- Non-goals: full CommonMark, headings/blockquotes/HTML passthrough, JS, deps, `poe_report.py`, figure detection changes.
- Verify:
  - `python3 -m unittest discover tests`
  - `python3 skills/poe/scripts/poe_results.py tests/fixtures/results` twice → `cmp` outputs identical (copy first output aside).
  - `grep -c '\*\*' tests/fixtures/results/poe/docs/all_analysis.html` → 0 for rendered bold.
- Done when: tests pass incl. new ones (nested `<ul>`, `<table>`, `<strong>`, `<code>`, `<a>`, escaped `<script>`, malformed table no crash); rerun byte-identical; old pre-wrap assertions updated.
- Progress notes: `poe/results-md-figures/progress/01a-markdown.md`

## 01b: figure rules in docs

- Goal: workers make paper-panel-ready figures: SVG only, `svg.fonttype: none`, Arial 7 pt, size caps, setup cell; orchestrator checks `.svg`.
- Read: `skills/poe/SKILL.md` (Notebook rules, Analyse mode step 5), `agents/phase-worker.md`, `README.md` (Analysis section, line ~91 Notebook rules).
- May change: `skills/poe/SKILL.md`, `agents/phase-worker.md`, `README.md`.
- Work:
  - SKILL.md Notebook rules: terse bullets: figures `.svg` only (no PNG), `bbox_inches="tight"`; setup cell at notebook top (snippet from plan Assumptions, tagged like other poe cells; add when missing); size caps (4x3 default, ≤3.5 in wide small/square, ≤7.2 in multi-panel, never larger, set via `figsize`); dense artists `rasterized=True`.
  - SKILL.md Analyse step 5: also check figure paths in record end `.svg`; else send back to worker.
  - phase-worker.md: same rules (or explicit pointer if it already defers to SKILL.md Notebook rules); example `fig.png` → `fig.svg`.
  - README.md: extend Notebook rules bullet with one sentence on figure rules.
- Non-goals: code changes, converting old PNGs, `.mplstyle`/helper module, changing other modes.
- Verify:
  - `grep -n "svg.fonttype" skills/poe/SKILL.md agents/phase-worker.md`
  - `grep -n "fig.png\|\.png" agents/phase-worker.md skills/poe/SKILL.md` → no PNG examples left as recommended output.
  - `python3 -m unittest discover tests` (unchanged pass).
- Done when: both files state all 4 rules + snippet; Analyse step 5 has `.svg` check; README mentions rules; output style terse (SKILL.md Output style).
- Progress notes: `poe/results-md-figures/progress/01b-figure-rules.md`

## Phase verification (orchestrator)

- `python3 -m unittest discover tests`
- Manual: rebuild page on real project with `FLLQHLPLV` record → bullets/table render, light + dark.
