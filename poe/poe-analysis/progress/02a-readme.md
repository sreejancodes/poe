# 2a-readme: done
## Done so far
- Read brief, plan, GLOSSARY, SKILL.md, phase-worker.md "Analysis units", README (+ diff: uncommitted grill edits, preserved)
- README.md edits:
  - line 5: `jupyter` requirement for `analyse`
  - Usage block: `analyse <plan>`, `analyse catch-up`, `note <text>` examples
  - Mode bullets: Analyse, Analyse catch-up, Note
  - New `## Analysis` section (before `## Files`): one task coding+analysis, start, per-analysis flow, notebook rules, open-notebook warning, ANALYSIS_LOG, untracked work + catch-up + note, analysis units in split/execute, report; links SKILL.md for full formats
  - Files tree: `ANALYSIS_LOG.md`, `analysis/NN-name.md`; poe/docs "written by grill, analyse and note"
## Files changed or produced
- README.md
- poe/poe-analysis/progress/02a-readme.md
## Tests run and observed results
- `grep -n "analyse\|note\|ANALYSIS_LOG" README.md` → hits at lines 5, 63-65, 74-75, 84-95, 102, 105 (present)
- `git diff --stat README.md` → 37 ins, 4 del; removed lines = 2 HEAD lines already changed by user's edits + "Requires..." line (extended, not dropped). Grill edits intact (grill/GRILLING/Pocock lines still present, 8 hits)
- Claims cross-checked vs SKILL.md modes/Analyse/Notebook rules/Catch-up/Note and phase-worker.md Analysis units; report claim checked vs `TASK_DOCUMENT_FOLDERS` in poe_report.py (includes "analysis")
## Decisions and assumptions
- Report described as "records as text" (not "with links") to avoid over-claiming link rendering
- Catch-up "notebooks with no record" detail omitted from README (in SKILL.md)
- Example note text invented (ORF plot) to match existing hpv-orf example slug
## Next step / remaining work
- none; orchestrator review
