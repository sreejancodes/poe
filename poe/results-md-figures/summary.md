# Summary: results-md-figures

## Passed
- `python3 -m unittest discover tests` → 83 tests OK.
- Results page renders markdown: nested lists, indented tables, bold/italic, code, links, `#` headings; `<script>` escaped.
- Rerun byte-identical (fixture + real project copy).
- Real FLLQHLPLV page (copy of `.../Mandy_HNSCC_Immunoverse/poe_tests/patient_searches/poe` in scratchpad) screenshotted light + dark: no literal `**`, `|---|`, `###`; `A*02:01` intact.
- Figure rules (SVG only, `svg.fonttype: none`, Arial 7 pt, 4x3 / ≤3.5 / ≤7.2 in, rasterize dense, setup cell) in `skills/poe/SKILL.md` Notebook rules + `agents/phase-worker.md`; Analyse step 5 checks `.svg`; README line.

## Uncertain / not done
- Real project's `poe/docs/all_analysis.html` not rebuilt (only scratch copy); run `/poe:poe results` there.
- Record titles show `: status done` in heading (pre-existing title parse; out of scope).
- Figure rules untested in a live analysis run; workers' compliance unverified.
- Old PNG figures unchanged (forward only, by decision).
- Nothing committed.

## Files
- `skills/poe/scripts/poe_results.py`, `tests/test_poe_results.py`, `tests/fixtures/results/poe/clustering/analysis/01-leiden.md`
- `skills/poe/SKILL.md`, `agents/phase-worker.md`, `README.md`
- Progress: `poe/results-md-figures/progress/01a-markdown.md`, `01b-figure-rules.md`
