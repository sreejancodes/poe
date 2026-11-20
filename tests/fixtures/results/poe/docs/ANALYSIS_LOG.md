# Analysis log

## 2026-11-01: How many counts per cell?  [rna-qc/01]
- Result: median 2300 counts per cell
- By: poe
- Follows: -
- Links: poe/rna-qc/analysis/01-counts.md, notebooks/rna-qc/qc.ipynb#01: How many counts per cell?, notebooks/rna-qc/figures/counts.png

## 2026-11-02: Does normalisation remove the depth effect?  [rna-qc/02]
- Result: depth effect gone after log-normalisation
- By: poe
- Follows: rna-qc/01
- Links: poe/rna-qc/analysis/02-normalise.md, notebooks/rna-qc/qc.ipynb#02

## 2026-11-03: Quick look at mito fraction  [manual]
- Result: mito fraction below 5% in most cells
- By: user
- Follows: rna-qc/01
- Links: notebooks/rna-qc/qc.ipynb

## 2026-11-04: Which Leiden clusters appear?  [clustering/01]
- Result: 12 clusters at resolution 1.0
- By: poe
- Follows: -
- Links: [record](poe/clustering/analysis/01-leiden.md), `notebooks/clustering/leiden.ipynb`

## 2026-11-05: Tried resolution 0.5  [manual]
- Result: 8 clusters
- By: user
- Links: notebooks/clustering/resolution.ipynb

## 2026-11-06 this heading has no reference
- Result: should be skipped

## 2026-11-07: Checked raw file sizes  [manual]
- Result: all files above 1 GB
- By: other agent
- Links: scripts/sizes.py

## 2026-11-08: Do marker genes separate clusters?  [clustering/02]
- Result: failed, marker table empty
- By: poe
- Follows: clustering/01
- Links: poe/clustering/analysis/02-markers.md

## 2026-11-09: Is a batch effect visible?  [rna-qc/03]
- Result: abandoned, batch labels missing
- By: poe
- Follows: rna-qc/02
- Links: poe/rna-qc/analysis/03-batch.md
