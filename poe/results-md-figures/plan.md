# results-md-figures

## Decisions
- Results page renders record markdown via small stdlib subset renderer in `poe_results.py` (paragraphs, nested bullets, tables, bold/italic, inline code, links); replaces escaped pre-wrap text. Why: page stays stdlib-only, no JS, self-contained.
- Figure size: default 4x3 in per single plot; small/square ≤3.5 in wide (e.g. scatter 3.5x3.5); multi-panel ≤7.2 in wide (double column); never larger. Why: plots drop into journal panels without resizing.
- Figure font: Arial 7 pt at final size; `svg.fonttype='none'` keeps text editable. Why: journal-typical size; Arial present in Inkscape almost everywhere.
- Figure rules live in Notebook rules (SKILL.md + phase-worker.md): one rcParams setup cell at notebook top (snippet given), figsize per plot, save `.svg` only. Why: notebook self-contained, reruns anywhere; no plugin-path dependency.
- Confirmed by user 2026-11-20.

## Objective

- Results page (`poe/docs/all_analysis.html`) renders record markdown properly (screenshot: literal `**`, `- `, `| table |`).
- Every analysis plot is paper-panel-ready: SVG, editable text, panel size.

## Scope

- `skills/poe/scripts/poe_results.py`: stdlib markdown-subset renderer for `## Result` and Interpretation; CSS for lists, tables, code.
- `tests/test_poe_results.py` + `tests/fixtures/results/`: record with nested bullets, table, bold, code, link.
- `skills/poe/SKILL.md` Notebook rules + `agents/phase-worker.md`: figure rules + setup-cell snippet; Analyse step 5 also checks figure paths end `.svg`.
- `README.md`: one line on figure rules, if README lists notebook rules.

Excluded:
- Converting existing PNGs or re-running old notebooks (forward only).
- Full CommonMark (headings inside sections, blockquotes, HTML passthrough, footnotes).
- Shipped `.mplstyle` / helper module; non-matplotlib libs beyond "same rules apply".
- Changes to `poe_report.py`.

## Assumptions

- Markdown subset: paragraphs; `-`/`*`/`1.` lists nested by indent (2+ spaces); pipe tables with `---` separator row; `**bold**`, `*italic*`, `` `code` ``, `[text](url)`. Anything else → escaped text in a paragraph. Everything escaped before inline markup applied (no HTML injection).
- Link targets that are session-relative paths → rewritten via existing `page_href`; `http(s)` kept.
- Interpretation: still first block only (paragraph or list), rendered with same renderer.
- Figures detection unchanged (`.svg` already an image extension); SVG inlined via `<img>`, `max-width: 100%`.
- Setup cell (top of notebook, tagged like other poe cells):
  ```python
  import matplotlib.pyplot as plt
  plt.rcParams.update({
      "svg.fonttype": "none",
      "font.family": "sans-serif",
      "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
      "font.size": 7,
      "axes.titlesize": 7, "axes.labelsize": 7,
      "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7,
      "figure.figsize": (4, 3),
  })
  ```
- Save: `fig.savefig("<name>.svg", bbox_inches="tight")`; no PNG. Dense artists (scatters ≳10k points, images) `rasterized=True`.
- Size caps: default 4x3 in; small/square ≤3.5 in wide (e.g. 3.5x3.5); multi-panel ≤7.2 in wide; never larger. Set per plot via `figsize`.
- seaborn/pandas plotting inherit rcParams → covered. Plotly etc. not used by default; if used, same SVG/size/font rules in spirit.
- Existing notebook lacking setup cell → worker adds it at top when it next appends.

## Approach

- `poe_results.py`: add `render_markdown(text, session_dir) -> str` (block pass: tables, lists via indent stack, paragraphs) + `render_inline(text)` (escape, then code → bold → italic → links). Replace `<div class="result">{escape(...)}` and interpretation `<p>` with it. Drop `white-space: pre-wrap`; add CSS for `ul/ol`, `table` (borders, padding, `overflow-x:auto` wrapper), `code`.
- SKILL.md Notebook rules: new bullets: figures SVG only; setup cell snippet; size caps; rasterize dense artists. Keep terse.
- phase-worker.md: same rules (or point to SKILL.md Notebook rules if worker already reads them); change example `fig.png` → `fig.svg`.

## Acceptance criteria

- Fixture record with nested bullets, table, bold, code, link renders as `<ul>` nesting, `<table>`, `<strong>`, `<code>`, `<a>`; no literal `**` or `|` row text in output.
- `<script>` in a record → escaped, not emitted raw.
- Byte-identical output on rerun; existing tests pass (update ones asserting old pre-wrap output).
- SKILL.md + phase-worker.md state: SVG only, `svg.fonttype: none`, Arial 7 pt, size caps, setup cell snippet.
- Manual: rebuild page on a real project with the screenshot record (`FLLQHLPLV`) → bullets/table render cleanly, light + dark.

## Risks

- Agent-written markdown is loose (odd indents, tables without leading `|`) → renderer misparses. Mitigation: tolerant parse; fallback = escaped paragraph, never crash.
- Arial missing on cluster/Linux → matplotlib falls back to DejaVu with warning; SVG still names Arial-first stack, Inkscape on Mac uses Arial. Accepted.
- Workers ignore rules → plots still big/PNG. Mitigation: rule in both SKILL.md and phase-worker.md; orchestrator Analyse step 5 checks figure paths end `.svg`.

## Validation

- `python3 -m unittest discover tests`
- `python3 skills/poe/scripts/poe_results.py tests/fixtures/results` → open page, check rendering light + dark.
- Grep: `grep -n "svg.fonttype" skills/poe/SKILL.md agents/phase-worker.md`.
