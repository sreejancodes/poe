# 01b phase-worker.md

## Status
done

## Done
- Read brief (phases/01-prompts-and-report.md Unit 1b), plan.md, GLOSSARY.md, agents/phase-worker.md.
- Added `## Analysis units` section after rule 8 (+33 lines, no deletions): trigger (brief gives notebook path), tagged cells under `## NN: <question>`, fewest-files/new-notebook rule, no dead cells, pre-execute git status check + warn/stop, headless nbconvert in plan env, jupyter missing → blocked, record format + log format verbatim from plan.md, log created with `# Analysis log` if absent, return ≤5 bullets + 2–3 next analyses.

## Files changed
- agents/phase-worker.md

## Decisions
- Numbered rules 1–8 + frontmatter untouched.
- Record/log formats copied verbatim from plan.md.
- Added "leave untagged / poe:manual cells alone" (follows rule 1: preserve user changes).
- Return bullets mention "reload notebook in Jupyter" warning (plan risk: --inplace vs open notebook).

## Verify
- `grep -n "nbconvert\|ANALYSIS_LOG\|tags\|Analysis units" agents/phase-worker.md` → hits lines 20, 24, 28, 41: all present.
- `head -5 agents/phase-worker.md` → frontmatter unchanged.
- `grep -n -i "analysis step"` → none.
- `git diff --stat` → 33 insertions, 0 deletions.

## Next
- none (orchestrator review)
