# 01: Which Leiden clusters appear?: done
## Follows from
-
## What was run
`notebooks/clustering/leiden.ipynb` heading `## 01`
## Result
12 clusters at resolution 1.0.

- **Clusters**: 12 at resolution 1.0
  - 3 small clusters under 50 cells
  - largest cluster holds *one third* of cells

- **Classes**: cells per class
  | Class | Samples | Obs |
  |---|---|---|
  | T cell | 4 | 1200 |
  | B cell | 3 | 800 |

- **Method**: `sc.tl.leiden(adata, resolution=1.0)`, see [notebook](notebooks/clustering/leiden.ipynb) and [docs](https://scanpy.readthedocs.io/en/stable/)
- **Note**: raw label text <script>alert(1)</script> kept as text
## Interpretation
More clusters than *expected*.
