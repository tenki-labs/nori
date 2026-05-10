# NorskhetsBench reproduction.

PYTHON := C:/Python313/python.exe
VENV_LIB := D:/Einar/Programmering2026/tenki-ting/forskning/zero-knowledge-llm/Lib/site-packages
ENV := PYTHONPATH="$(VENV_LIB)" PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1 \
       CUBLAS_WORKSPACE_CONFIG=:4096:8

S := scripts

.PHONY: all reproduce data baseline generate score clean help

help:
	@echo "Targets:"
	@echo "  make reproduce   - end-to-end (data + baseline + generate + score)"
	@echo "  make data        - acquire native Norwegian reference corpus"
	@echo "  make baseline    - compute reference distribution"
	@echo "  make generate    - run benchmark generations from model panel"
	@echo "  make score       - compute scorecards"
	@echo "  make clean       - remove generated outputs (keeps reference data)"

all: reproduce
reproduce: data baseline generate score

data:
	$(ENV) $(PYTHON) -u $(S)/00_acquire_reference.py

baseline:
	$(ENV) $(PYTHON) -u $(S)/10_compute_baseline.py

generate:
	$(ENV) $(PYTHON) -u $(S)/20_run_models.py

score:
	$(ENV) $(PYTHON) -u $(S)/30_score.py

clean:
	rm -rf data/outputs results/scorecard.json results/scorecard.md
	@echo "Cleaned generated outputs. Reference corpus + baseline preserved."
