# NORI-NN scorecard

**NORI score** is the headline number: arithmetic mean of the five axes, scaled to [0, 100]. Higher is more native. Per-axis scores are in [0, 1] where 1.0 matches the native distribution within tolerance.

`nori_min` = lowest axis × 100 (weakest-link indicator).  `nori_g` = geometric mean × 100 (penalizes weak axes).

| Model | NORI score | nori_min | nori_g | explicitation | normalization | simplification | levelling | interference |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| gemma-4-e4b-it | **48.0** | 16.3 | 40.5 | 0.419 | 0.845 | 0.271 | 0.163 | 0.700 |
| normistral-7b-warm | **35.4** | 0.1 | 12.8 | 0.326 | 0.522 | 0.001 | 0.349 | 0.570 |
| qwen25-1_5b-instruct | **34.2** | 0.9 | 18.8 | 0.486 | 0.371 | 0.009 | 0.258 | 0.586 |
| qwen25-3b-instruct | **22.2** | 0.1 | 4.3 | 0.375 | 0.004 | 0.001 | 0.104 | 0.625 |
| qwen25-3b-norsk-lora | **45.6** | 0.1 | 14.6 | 0.769 | 0.600 | 0.001 | 0.145 | 0.763 |