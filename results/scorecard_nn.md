# NORI-NN scorecard

**NORI score** is the headline number: arithmetic mean of the five axes, scaled to [0, 100]. Higher is more native. Per-axis scores are in [0, 1] where 1.0 matches the native distribution within tolerance.

`nori_min` = lowest axis × 100 (weakest-link indicator).  `nori_g` = geometric mean × 100 (penalizes weak axes).

| Model | NORI score | nori_min | nori_g | explicitation | normalization | simplification | levelling | interference |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| qwen25-1_5b-instruct | **35.5** | 0.9 | 19.2 | 0.486 | 0.371 | 0.009 | 0.258 | 0.653 |
| qwen25-3b-instruct | **23.9** | 0.1 | 4.4 | 0.375 | 0.004 | 0.001 | 0.104 | 0.709 |