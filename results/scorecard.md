# NORI scorecard

**NORI score** is the headline number: arithmetic mean of the five axes, scaled to [0, 100]. Higher is more native. Per-axis scores are in [0, 1] where 1.0 matches the native distribution within tolerance.

`nori_min` = lowest axis × 100 (weakest-link indicator).  `nori_g` = geometric mean × 100 (penalizes weak axes).

| Model | NORI score | nori_min | nori_g | explicitation | normalization | simplification | levelling | interference |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| gemma-4-e4b-it | **48.5** | 25.0 | 44.1 | 0.333 | 0.250 | 0.553 | 0.420 | 0.869 |
| qwen25-1_5b-instruct | **39.7** | 5.0 | 27.8 | 0.661 | 0.263 | 0.050 | 0.250 | 0.760 |
| qwen25-3b-instruct | **34.9** | 0.7 | 14.2 | 0.777 | 0.214 | 0.007 | 0.074 | 0.673 |