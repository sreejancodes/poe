# 01b: figure rules in docs

Status: done

## Done so far
- SKILL.md Notebook rules: new "Figures paper-panel-ready" bullet group: setup-cell snippet (from plan Assumptions, tagged, add when missing), `.svg` only + `bbox_inches="tight"`, `svg.fonttype: none` Arial 7 pt, size caps via figsize, `rasterized=True` dense artists, seaborn/pandas/other libs note.
- SKILL.md Analyse step 5: also check record figure paths end `.svg`, else send back to worker.
- phase-worker.md Analysis units: same figure bullets + snippet (inline; file doesn't defer to SKILL.md); example `fig.png` → `fig.svg`.
- README.md Analysis > Notebook rules bullet: one sentence on figure rules.

## Files changed or produced
- skills/poe/SKILL.md (+20/-1)
- agents/phase-worker.md (+20/-1)
- README.md (1 line extended)

## Tests run and observed results
- `grep -n "svg.fonttype" skills/poe/SKILL.md agents/phase-worker.md` → hits SKILL.md:176,185; phase-worker.md:34,43.
- `grep -n "fig.png\|\.png" agents/phase-worker.md skills/poe/SKILL.md README.md` → no hits.
- `python3 -m unittest discover tests` → Ran 67 tests, OK (parallel 01a worker's poe_results.py not yet in diff at run time).

## Decisions and assumptions
- phase-worker.md repeats rules inline (worker doesn't read SKILL.md) → full rules + snippet duplicated there.

## Next step / remaining work
- None. Orchestrator: review diff; not committed.
