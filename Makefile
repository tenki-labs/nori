# NORI v1.0 reproduction.
#
# NORI ships two parallel benchmarks: NORI for Bokmaal, NORI-NN for Nynorsk.
# `make reproduce` runs both end-to-end.

PYTHON := C:/Python313/python.exe
VENV_LIB := D:/Einar/Programmering2026/tenki-ting/forskning/zero-knowledge-llm/Lib/site-packages
ENV := PYTHONPATH="$(VENV_LIB)" PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1 \
       CUBLAS_WORKSPACE_CONFIG=:4096:8

S := scripts

.PHONY: all reproduce \
        data data-nb data-nn \
        baseline baseline-nb baseline-nn \
        generate generate-nb generate-nn \
        score score-nb score-nn \
        test \
        clean help

help:
	@echo "NORI v1.0 reproduction targets:"
	@echo ""
	@echo "  make reproduce      end-to-end, both languages"
	@echo ""
	@echo "  make data           acquire reference corpora for both nb and nn"
	@echo "  make data-nb        Bokmaal only (Wikipedia + Project Gutenberg)"
	@echo "  make data-nn        Nynorsk only (Wikipedia)"
	@echo ""
	@echo "  make baseline       compute reference baselines for both nb and nn"
	@echo "  make baseline-nb    Bokmaal only"
	@echo "  make baseline-nn    Nynorsk only"
	@echo ""
	@echo "  make generate       run benchmark generations for both nb and nn"
	@echo "  make generate-nb    Bokmaal only"
	@echo "  make generate-nn    Nynorsk only"
	@echo ""
	@echo "  make score          score both NORI and NORI-NN"
	@echo "  make score-nb       NORI (Bokmaal) only"
	@echo "  make score-nn       NORI-NN (Nynorsk) only"
	@echo ""
	@echo "  make test           run unit tests for the metric library"
	@echo ""
	@echo "  make clean          remove generated outputs (keeps reference data)"

all: reproduce
reproduce: data baseline generate score

# Both languages
data: data-nb data-nn
baseline: baseline-nb baseline-nn
generate: generate-nb generate-nn
score: score-nb score-nn

# Bokmaal only
data-nb:
	$(ENV) $(PYTHON) -u $(S)/00_acquire_reference.py --lang nb

baseline-nb:
	$(ENV) $(PYTHON) -u $(S)/10_compute_baseline.py --lang nb

generate-nb:
	$(ENV) $(PYTHON) -u $(S)/20_run_models.py --lang nb

score-nb:
	$(ENV) $(PYTHON) -u $(S)/30_score.py --lang nb

# Nynorsk only
data-nn:
	$(ENV) $(PYTHON) -u $(S)/00_acquire_reference.py --lang nn

baseline-nn:
	$(ENV) $(PYTHON) -u $(S)/10_compute_baseline.py --lang nn

generate-nn:
	$(ENV) $(PYTHON) -u $(S)/20_run_models.py --lang nn

score-nn:
	$(ENV) $(PYTHON) -u $(S)/30_score.py --lang nn

test:
	$(ENV) $(PYTHON) -u tests/run_tests.py

clean:
	rm -rf data/outputs data/outputs_nn \
	       results/scorecard.json results/scorecard.md \
	       results/scorecard_nn.json results/scorecard_nn.md
	@echo "Cleaned generated outputs. Reference corpora and baselines preserved."
