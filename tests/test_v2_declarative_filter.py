"""Issue #1: V2 violation rate should be measured on declarative main clauses
only. Imperatives, interrogatives, and fragments must not count.
"""
from metrics import measure_text, _is_declarative_candidate, _get_nlp


def _sents(text: str):
    return list(_get_nlp()(text).sents)


def test_question_is_not_declarative():
    sents = _sents("Hva er klokka?")
    assert _is_declarative_candidate(sents[0]) is False


def test_exclamation_is_not_declarative():
    sents = _sents("Kom hit nå!")
    assert _is_declarative_candidate(sents[0]) is False


def test_fragment_too_short_is_not_declarative():
    sents = _sents("Ja.")
    assert _is_declarative_candidate(sents[0]) is False


def test_normal_declarative_is_declarative():
    sents = _sents("Han kommer til byen i morgen.")
    assert _is_declarative_candidate(sents[0]) is True


def test_questions_excluded_from_v2_count():
    """A text that is all questions has zero main_clauses_total."""
    text = "Hva er klokka? Hvor skal vi? Kommer du?"
    m = measure_text(text, lang="nb")
    assert m.main_clauses_total == 0, (
        "questions must not be counted as declarative main clauses"
    )
    assert m.v2_violation_rate == 0.0


def test_imperatives_excluded_from_v2_count():
    text = "Kom hit! Sett deg ned! Vær så snill, hør på meg!"
    m = measure_text(text, lang="nb")
    assert m.main_clauses_total == 0


def test_declaratives_included_in_v2_count():
    text = ("Jeg går på butikken. "
            "Hun leser en bok i sofaen. "
            "De spiser middag sammen klokken seks.")
    m = measure_text(text, lang="nb")
    assert m.main_clauses_total >= 2, "should count declarative main clauses"
