# results-figure-size

## Decisions
- Results page figures capped by CSS: `max-width: min(100%, 7.2in)`, `max-height: 3.5in`, `width/height: auto` (never upscale); link opens full size. Why: one CSS rule covers old PNGs + oversized SVGs; matches paper caps (7.2 in multi-panel, ~3 in tall single).
- Multiple figures of one analysis wrap side by side (flex-wrap), one per row on narrow screens. Why: uses width freed by the cap.
- Confirmed by user 2026-11-20.

## Objective

- Figures on the results page (`poe/docs/all_analysis.html`) show at about paper-panel size, not stretched to the full column. Right now one barplot fills half the page.

## Scope

- `skills/poe/scripts/poe_results.py`: figure CSS and the wrapper markup around an analysis's figures.
- `tests/test_poe_results.py`: assertions for the cap and the wrapper.

Excluded:
- `poe_report.py` / `report.html`.
- Converting or resizing existing figure files; SKILL.md figure rules (already set).
- Lightbox, JS, reading PNG dpi.

## Assumptions

- `in` CSS units = 96 px/in → 7.2in ≈ 691px, 3.5in = 336px.
- Matplotlib SVGs carry `width/height` in pt → shown at true size when smaller than the cap; no upscaling because the size stays `auto`.
- Existing `<a href>` around `<img>` already opens the full-size file.
- Caption width follows the figure (figure = inline block), so long paths wrap under it.

## Approach

- `render_analysis`: wrap the figures in `<div class="figures">…</div>` only when there is at least one figure.
- CSS:
  - `.figures { display: flex; flex-wrap: wrap; gap: 8px 16px; align-items: flex-start; }`
  - `figure { margin: 8px 0; max-width: 100%; }`
  - `figure img { max-width: min(100%, 7.2in); max-height: 3.5in; width: auto; height: auto; … }` (keep border/bg)
- Missing figure (`<p>` link) stays inside the wrapper; fine as a flex item.

## Acceptance criteria

- Output contains `max-height: 3.5in` and `min(100%, 7.2in)` in the figure img rule.
- An analysis's figures sit inside `<div class="figures">`; an analysis with no figures has no empty wrapper.
- Existing tests pass; output byte-identical on rerun.
- Manual: rebuild on the project with the oversized barplot → figure ≤3.5in tall; two figures sit side by side; light + dark; narrow window → one per row, no horizontal scroll.

## Risks

- Very wide, short figures (e.g. 7.2x2) → still limited by width, fine. Tall multi-panel figures shrink to 3.5in tall → text small inline; click opens full size. Accepted.
- SVG without width/height attributes (non-matplotlib) → browser default 300x150 or fills the cap. Accepted; matplotlib always writes them.

## Validation

- `python3 -m unittest discover tests`
- `python3 skills/poe/scripts/poe_results.py tests/fixtures/results` → open page, check figure size.
