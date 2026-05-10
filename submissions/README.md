# Submissions

This directory is intentionally lightweight. To submit a new model to NORI, follow the protocol in [CONTRIBUTING.md](../CONTRIBUTING.md).

The actual submission goes under `data/outputs/<model-id>/`:

```
data/outputs/<your-model-id>/
  meta.json
  ed01.txt   ed02.txt   ...   ed05.txt
  pe01.txt   pe02.txt   ...   pe05.txt
  te01.txt   te02.txt   ...   te05.txt
  ar01.txt   ar02.txt   ...   ar05.txt
  le01.txt   le02.txt   ...   le05.txt
```

Open a pull request using the `model_submission.md` template. The validate-submission GitHub Action will check format and recompute scores against the native baseline.

For the meta.json schema, see CONTRIBUTING.md.
