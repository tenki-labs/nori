# NORI scorecard

**NORI score** is the headline number: arithmetic mean of the five axes, scaled to [0, 100]. Higher is more native. Per-axis scores are in [0, 1] where 1.0 matches the native distribution within tolerance.

`nori_min` = lowest axis × 100 (weakest-link indicator).  `nori_g` = geometric mean × 100 (penalizes weak axes).

| Model | NORI score | nori_min | nori_g | explicitation | normalization | simplification | levelling | interference |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| gemma-4-e4b-it | **46.3** | 25.0 | 42.3 | 0.333 | 0.250 | 0.457 | 0.420 | 0.854 |
| normistral-7b-warm | **35.3** | 11.3 | 29.1 | 0.282 | 0.191 | 0.113 | 0.568 | 0.610 |
| qwen25-1_5b-instruct | **37.1** | 5.0 | 26.7 | 0.661 | 0.263 | 0.050 | 0.250 | 0.630 |
| qwen25-3b-instruct | **29.2** | 0.7 | 12.8 | 0.777 | 0.214 | 0.007 | 0.074 | 0.390 |
| qwen25-3b-norsk-lora | **34.6** | 0.7 | 12.2 | 0.821 | 0.007 | 0.033 | 0.245 | 0.623 |
| qwen35-4b-base | **33.8** | 4.5 | 26.3 | 0.430 | 0.045 | 0.389 | 0.363 | 0.462 |