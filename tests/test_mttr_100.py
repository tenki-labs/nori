"""Issue #2: mttr_100 must be well-defined on short documents and decoupled
from document length below 1000 tokens.
"""
from metrics import measure_text, aggregate, score, CorpusMetrics


def test_mttr_100_defined_on_short_output():
    """A typical 200 to 400 word LLM output should produce a real MTTR-100,
    not fall back to plain TTR."""
    text = " ".join([
        "Norge er et langstrakt land med fjorder og fjell.",
        "Klimaet varierer fra mildt langs kysten til kaldt i innlandet.",
        "Befolkningen bor for det meste sør i landet.",
        "Olje og fiskeri er viktige naeringer.",
        "Mange turister besøker landet hvert år for å se nordlys og midnattssol.",
    ] * 10)
    m = measure_text(text, lang="nb")
    assert m.token_count >= 100
    assert 0.0 < m.mttr_100 <= 1.0
    assert m.mttr_100 != m.type_token_ratio, (
        "MTTR-100 should differ from full-document TTR on a 500+ token text"
    )


def test_mttr_100_in_simplification_score():
    """The simplification axis should respond to MTTR-100, not MTTR-1000."""
    native = CorpusMetrics(mttr_100=0.75, mttr_1000=0.55, mean_word_length=5.0)
    model_close = CorpusMetrics(mttr_100=0.75, mttr_1000=0.20, mean_word_length=5.0)
    model_far = CorpusMetrics(mttr_100=0.40, mttr_1000=0.55, mean_word_length=5.0)
    s_close = score(model_close, native)
    s_far = score(model_far, native)
    assert s_close.simplification > s_far.simplification, (
        "score() must penalize MTTR-100 distance, not MTTR-1000 distance"
    )


def test_mttr_1000_kept_for_diagnostics():
    """Backward compatibility: mttr_1000 field must still be populated."""
    text = ("Norge har mange fjorder. " * 50)
    m = measure_text(text, lang="nb")
    assert hasattr(m, "mttr_1000")
    assert m.mttr_1000 >= 0.0
