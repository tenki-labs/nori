"""Issue #6: compound-separation detector should rely on the spaCy vocabulary,
not a 30-prefix curated list.
"""
from metrics import measure_text, _looks_like_compound_in_vocab, _get_nlp


def test_known_compound_in_vocab():
    nlp = _get_nlp()
    # 'datasenter' is a common Norwegian compound; should be in the vocab.
    assert _looks_like_compound_in_vocab(nlp, "data", "senter") is True


def test_random_bigram_not_in_vocab():
    nlp = _get_nlp()
    # Two unrelated nouns; should not look like a single compound word.
    assert _looks_like_compound_in_vocab(nlp, "møbel", "hjelm") is False


def test_too_short_bigram_rejected():
    nlp = _get_nlp()
    # The check requires combined length >= 6 to avoid false positives.
    assert _looks_like_compound_in_vocab(nlp, "a", "b") is False


def test_serskriving_detected_in_text():
    """A sentence with 'data senter' should flag at least one separation."""
    text = "Vi bygger et nytt data senter i Oslo. Det er en stor investering."
    m = measure_text(text, lang="nb")
    # data + senter is a real compound. The detector should flag the pair.
    assert m.suspected_separations >= 1
