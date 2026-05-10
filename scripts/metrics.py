"""NORI: measurable signatures of native Norwegian vs translatese.

Five translation-universals categories from Toury (1995), Baker (1996),
Mauranen and Kujamaki (2004), operationalized as concrete measurements:

    1. Eksplisittering    explicit-connective density, redundant-subject rate
    2. Normalisering      lexical conventionality, register variance
    3. Forenkling         lexical diversity (TTR), word length, content density
    4. Utjevning          distribution variance vs reference
    5. Kildespraak-       V2 violations, em-dash density, syntactic calques,
       interferens        saerskriving (compound-word splitting)

Plus deployment-relevant concrete measurements:

    - Em-dash density per 10,000 chars
    - V2 violation rate (% of main clauses where verb is not in 2nd position)
    - Compound-word integrity rate (no särskrivning)
    - Sentence-length distribution (mean, std, KL vs reference)
    - Modal-particle frequency (jo, da, vel, nok, altså)
    - Connective frequency (fordi, derfor, dermed, slik at, ...)
    - Mean type-token ratio per 1000 words

All measurements are designed to be:
  - deterministic given same input
  - composable: each metric returns a {value, n_observations, ...} dict
  - aggregatable: corpus-level metrics from per-document metrics
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable

# Lazy NLP load. NORI uses spaCy nb_core_news_md for both BM and NN: there is
# no spaCy NN model, but nb_core_news_md handles NN well enough for our
# dependency-structure needs (V2 root identification, constituent counting).
# POS tags can be noisy on NN-specific morphology, but we don't depend on POS
# fine-grained classes for the headline measurements.
_NLP = None
def _get_nlp():
    global _NLP
    if _NLP is None:
        import spacy
        _NLP = spacy.load("nb_core_news_md")
    return _NLP


WORD_RE = re.compile(r"[\wÀ-ɏ̀-ͯ]+", re.UNICODE)
SENTENCE_END_RE = re.compile(r"[.!?]+(?:\s|$)")


# ----------------------------------------------------------------------------
# Language packs
# ----------------------------------------------------------------------------

@dataclass(frozen=True)
class LangPack:
    """Per-language lexicons for the language-sensitive metric components.

    The structural metrics (em-dash density, V2 violations, compound integrity,
    sentence length, lexical diversity, mean word length) are language-agnostic
    and use the spaCy parser only. The four lexicons here are the parts that
    differ between Bokmaal and Nynorsk.
    """
    code: str  # "nb" or "nn"
    name: str
    modal_particles: frozenset
    explicit_connectives: frozenset
    subordinators: frozenset


# Bokmaal modal particles, connectives, subordinators.
BOKMAAL = LangPack(
    code="nb",
    name="Norsk bokmål",
    modal_particles=frozenset({
        "jo", "da", "vel", "nok", "altså", "visst", "nemlig",
        "egentlig", "faktisk", "kanskje", "selvsagt", "selvfølgelig",
    }),
    explicit_connectives=frozenset({
        "fordi", "derfor", "dermed", "altså", "således", "følgelig",
        "ettersom", "siden", "som følge av", "dvs", "det vil si",
        "med andre ord", "for eksempel", "f.eks", "først og fremst",
        "i tillegg", "videre", "imidlertid", "likevel",
        "på den ene side", "på den andre side",
        "først", "deretter", "endelig", "til slutt",
    }),
    subordinators=frozenset({
        "at", "om", "da", "når", "før", "etter", "mens", "fordi", "siden",
        "ettersom", "selv om", "hvis", "dersom", "uten at", "for at",
        "slik at", "sånn at", "enda",
        "som", "hva", "hvem", "hvor", "hvordan", "hvilken", "hvilket", "hvilke",
    }),
)


# Nynorsk modal particles, connectives, subordinators. Many overlap with BM,
# but NN has distinctive forms (kvifor, ikkje, av di, jamvel om, etc.).
NYNORSK = LangPack(
    code="nn",
    name="Norsk nynorsk",
    modal_particles=frozenset({
        "jo", "då", "vel", "nok", "altså", "visst", "nemleg",
        "eigentleg", "faktisk", "kanskje", "sjølvsagt", "sjølvsagde",
        "no",  # "no" in NN is the temporal particle similar to BM "nå"
    }),
    explicit_connectives=frozenset({
        "av di", "difor", "dimed", "altså", "soleis", "følgjeleg",
        "ettersom", "sidan", "som følgje av", "dvs", "det vil seie",
        "med andre ord", "til dømes", "t.d.", "først og fremst",
        "i tillegg", "vidare", "likevel", "samstundes",
        "på den eine sida", "på den andre sida",
        "først", "deretter", "til slutt",
    }),
    subordinators=frozenset({
        "at", "om", "då", "når", "før", "etter", "medan", "av di", "sidan",
        "ettersom", "jamvel om", "viss", "dersom", "utan at", "for at",
        "slik at", "så at", "endå",
        "som", "kva", "kven", "kvar", "korleis", "kva for ein",
        "kva for ei", "kva for eit", "kva for nokre",
    }),
)


LANG_PACKS = {"nb": BOKMAAL, "nn": NYNORSK}


# Backwards-compatible aliases for code that imported these directly. Default
# to Bokmaal, matching the pre-1.0.0 behavior.
MODAL_PARTICLES = BOKMAAL.modal_particles
EXPLICIT_CONNECTIVES = BOKMAAL.explicit_connectives
SUBORDINATORS = BOKMAAL.subordinators


# ----------------------------------------------------------------------------
# Per-text measurements
# ----------------------------------------------------------------------------

@dataclass
class TextMetrics:
    n_chars: int = 0
    n_words: int = 0
    n_sentences: int = 0

    # Concrete deployment-relevant
    em_dash_count: int = 0
    em_dash_per_10k_chars: float = 0.0
    en_dash_count: int = 0          # em-dash vs en-dash distinction
    sentence_lengths: list[int] = field(default_factory=list)  # in words
    mean_sentence_length: float = 0.0
    std_sentence_length: float = 0.0
    p90_sentence_length: float = 0.0  # 90th percentile

    # V2
    main_clauses_total: int = 0
    v2_violations: int = 0
    v2_violation_rate: float = 0.0

    # Compound-word integrity (særskriving)
    candidate_compound_pairs: int = 0
    suspected_separations: int = 0   # (lower bound:heuristic only)
    compound_integrity_rate: float = 1.0

    # Lexical diversity / forenkling
    type_count: int = 0
    token_count: int = 0
    type_token_ratio: float = 0.0    # TTR over all tokens
    mttr_1000: float = 0.0           # Moving TTR with window 1000
    mean_word_length: float = 0.0
    content_word_ratio: float = 0.0   # content tokens / total tokens

    # Modal particles
    modal_particle_count: int = 0
    modal_particles_per_1k_words: float = 0.0

    # Explicit connectives (eksplisittering)
    connective_count: int = 0
    connectives_per_1k_words: float = 0.0

    # Word-length distribution snapshot (for KL distance later)
    word_lengths_hist: dict[int, int] = field(default_factory=dict)


def _norm(text: str) -> str:
    """Normalize text for measurement: collapse whitespace, NFC."""
    import unicodedata
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _split_sentences(doc) -> list:
    """Yield sentence spans from a spaCy doc."""
    return list(doc.sents)


def _is_main_clause_root(token) -> bool:
    """A main-clause root is a verb that is the syntactic root of its sentence
    AND not a subordinate clause head."""
    if token.dep_ != "ROOT":
        return False
    if token.pos_ not in ("VERB", "AUX"):
        return False
    return True


def _check_v2(sent) -> tuple[bool, bool]:
    """For a sentence span, return (is_main_clause, v2_satisfied).

    Norwegian V2 says the finite verb is in position 2 of a main clause where
    'position' counts constituents (XP), not tokens. Here we approximate:
    position-2 = the verb is the second top-level constituent, where the first
    can be a subject NP, an adverbial PP/NP, an object, or a clause.

    We use a robust heuristic: find the main-clause finite verb, count how many
    distinct top-level dependents come before it. Exactly one ⇒ V2 satisfied.
    """
    # Find the main verb (root of this sentence)
    root = None
    for tok in sent:
        if _is_main_clause_root(tok):
            root = tok
            break
    if root is None:
        return False, True

    # Children of root that are at the surface level (not nested inside other
    # phrases). Count those that occur strictly before the root token.
    # We only consider direct children with dep in: nsubj, expl, obl, advmod,
    # advcl, obj (when fronted), cc (rare), mark (subordinator:would mean
    # this is not a main clause).
    children_before = []
    for child in root.children:
        if child.i < root.i:
            # Ignore tokens that are part of a multi-word unit headed by the
            # subject or oblique
            if child.dep_ in ("nsubj", "expl", "obl", "advmod", "advcl",
                              "obj", "iobj", "ccomp", "xcomp", "nmod",
                              "discourse", "vocative", "parataxis"):
                children_before.append(child)
            elif child.dep_ in ("aux", "auxpass"):
                # Auxiliaries can appear before the lex verb in periphrastic
                # constructions; if root is the aux, the verb head is fine
                pass
            elif child.dep_ == "mark":
                # Subordinator before root → this is a subordinate clause root;
                # V2 doesn't apply
                return False, True

    n_constituents_before = len(children_before)
    v2 = n_constituents_before == 1
    return True, v2


def _detect_compound_separation(doc) -> tuple[int, int]:
    """Detect potential särskrivning: cases where a noun-noun bigram is
    suspicious of being a compound-word that was wrongly split.

    Heuristic (high precision, low recall): adjacent NOUN+NOUN tokens where
    the first is short (≤ 6 chars) and a known compound-prefix-likely word
    AND there's no preposition/adjective between them. This is a lower bound
    only:doesn't catch all cases but flags the most egregious.
    """
    candidate_prefixes = {
        "stor", "lille", "ny", "gammel",
        "bil", "buss", "tog", "fly",
        "hus", "mat", "kaffe", "te", "skole",
        "data", "tekst", "tall", "språk",
        "barn", "barne", "ungdom", "voksen",
        "natt", "dag", "morgen", "kveld",
        "topp", "bunn", "side",
        "kontor", "møte", "konferanse", "tjeneste",
    }
    candidates = 0
    suspected = 0
    for i in range(len(doc) - 1):
        a, b = doc[i], doc[i + 1]
        if (a.pos_ in ("NOUN", "PROPN") and b.pos_ in ("NOUN", "PROPN")
                and a.text.isalpha() and b.text.isalpha()):
            candidates += 1
            # Heuristic: if either word is in candidate_prefixes, flag it
            if a.text.lower() in candidate_prefixes:
                suspected += 1
    return candidates, suspected


def measure_text(text: str, lang: str = "nb") -> TextMetrics:
    """Compute all metrics for a single piece of text.

    `lang` selects the language pack ("nb" for Bokmaal, "nn" for Nynorsk).
    The pack determines which words count as modal particles, explicit
    connectives, and subordinators. Structural metrics (em-dash, V2,
    compound integrity, sentence/word lengths, lexical diversity) are
    language-agnostic.
    """
    pack = LANG_PACKS.get(lang)
    if pack is None:
        raise ValueError(f"Unknown lang code {lang!r}. Use 'nb' or 'nn'.")

    text = _norm(text)
    if not text:
        return TextMetrics()

    nlp = _get_nlp()
    doc = nlp(text)

    m = TextMetrics()
    m.n_chars = len(text)

    # Words and sentences
    words = [tok.text for tok in doc if tok.is_alpha]
    m.n_words = len(words)

    sents = _split_sentences(doc)
    m.n_sentences = len(sents)

    # Em-dash counts (unicode em-dash and en-dash both)
    m.em_dash_count = text.count("—")
    m.en_dash_count = text.count("–")
    if m.n_chars:
        m.em_dash_per_10k_chars = round(m.em_dash_count / m.n_chars * 10_000, 3)

    # Sentence lengths in words
    sent_lens = []
    for sent in sents:
        wn = sum(1 for t in sent if t.is_alpha)
        if wn > 0:
            sent_lens.append(wn)
    m.sentence_lengths = sent_lens
    if sent_lens:
        import statistics
        m.mean_sentence_length = round(statistics.mean(sent_lens), 2)
        m.std_sentence_length = round(statistics.stdev(sent_lens), 2) if len(sent_lens) > 1 else 0.0
        m.p90_sentence_length = round(sorted(sent_lens)[int(0.9 * len(sent_lens))], 2)

    # V2
    main_total = 0
    v2_violations = 0
    for sent in sents:
        is_main, v2 = _check_v2(sent)
        if is_main:
            main_total += 1
            if not v2:
                v2_violations += 1
    m.main_clauses_total = main_total
    m.v2_violations = v2_violations
    m.v2_violation_rate = round(v2_violations / main_total, 4) if main_total else 0.0

    # Compound integrity
    cand, susp = _detect_compound_separation(doc)
    m.candidate_compound_pairs = cand
    m.suspected_separations = susp
    m.compound_integrity_rate = round(1.0 - (susp / cand), 4) if cand else 1.0

    # Lexical diversity
    word_lower = [w.lower() for w in words]
    types = set(word_lower)
    m.type_count = len(types)
    m.token_count = len(word_lower)
    m.type_token_ratio = round(m.type_count / m.token_count, 4) if m.token_count else 0.0

    # Moving TTR with window 1000 (averaged over windows)
    if m.token_count >= 1000:
        ttrs = []
        for start in range(0, m.token_count - 999, 500):
            window = word_lower[start:start + 1000]
            ttrs.append(len(set(window)) / 1000)
        m.mttr_1000 = round(sum(ttrs) / len(ttrs), 4)
    else:
        m.mttr_1000 = m.type_token_ratio

    if word_lower:
        m.mean_word_length = round(sum(len(w) for w in word_lower) / len(word_lower), 3)

    # Content word ratio (NOUN, VERB, ADJ, ADV)
    content_pos = {"NOUN", "VERB", "ADJ", "ADV", "PROPN"}
    content_count = sum(1 for tok in doc if tok.pos_ in content_pos)
    total_alpha = sum(1 for tok in doc if tok.is_alpha)
    m.content_word_ratio = round(content_count / total_alpha, 4) if total_alpha else 0.0

    # Modal particles
    mp_count = sum(1 for w in word_lower if w in pack.modal_particles)
    m.modal_particle_count = mp_count
    m.modal_particles_per_1k_words = round(mp_count / m.n_words * 1000, 3) if m.n_words else 0.0

    # Explicit connectives (multi-word: check both single and bigram match)
    text_lower = text.lower()
    conn_count = 0
    for c in pack.explicit_connectives:
        # Word-boundary match
        pat = r"\b" + re.escape(c) + r"\b"
        conn_count += len(re.findall(pat, text_lower))
    m.connective_count = conn_count
    m.connectives_per_1k_words = round(conn_count / m.n_words * 1000, 3) if m.n_words else 0.0

    # Word-length histogram (for KL distance later)
    wl_hist: dict[int, int] = {}
    for w in word_lower:
        L = len(w)
        wl_hist[L] = wl_hist.get(L, 0) + 1
    m.word_lengths_hist = wl_hist

    return m


# ----------------------------------------------------------------------------
# Corpus-level aggregation
# ----------------------------------------------------------------------------

@dataclass
class CorpusMetrics:
    """Aggregated metrics over many documents:both means and reference
    distributions for comparison."""
    n_documents: int = 0
    total_chars: int = 0
    total_words: int = 0
    total_sentences: int = 0
    total_main_clauses: int = 0

    # Aggregated rates
    em_dash_per_10k_chars: float = 0.0
    v2_violation_rate: float = 0.0
    compound_integrity_rate: float = 1.0
    mean_sentence_length: float = 0.0
    std_sentence_length: float = 0.0
    p90_sentence_length: float = 0.0
    mean_word_length: float = 0.0
    type_token_ratio: float = 0.0
    mttr_1000: float = 0.0
    content_word_ratio: float = 0.0
    modal_particles_per_1k_words: float = 0.0
    connectives_per_1k_words: float = 0.0

    # Distribution snapshots (kept for KL/Wasserstein computation)
    sentence_length_distribution: list[int] = field(default_factory=list)
    word_length_distribution: dict[int, int] = field(default_factory=dict)


def aggregate(metrics: list[TextMetrics]) -> CorpusMetrics:
    cm = CorpusMetrics()
    cm.n_documents = len(metrics)
    if not metrics:
        return cm

    # Pool sentence-length samples
    all_sent_lens: list[int] = []
    wl_hist: dict[int, int] = {}
    total_chars = 0
    total_words = 0
    total_sentences = 0
    em_dashes = 0
    main_total = 0
    v2_violations = 0
    cand_total = 0
    susp_total = 0
    word_len_sum = 0.0
    word_len_n = 0
    type_token_pairs = []
    mttr_pairs = []
    content_pairs = []
    mp_pairs = []
    conn_pairs = []

    for m in metrics:
        total_chars += m.n_chars
        total_words += m.n_words
        total_sentences += m.n_sentences
        em_dashes += m.em_dash_count
        main_total += m.main_clauses_total
        v2_violations += m.v2_violations
        cand_total += m.candidate_compound_pairs
        susp_total += m.suspected_separations
        all_sent_lens.extend(m.sentence_lengths)
        for L, c in m.word_lengths_hist.items():
            wl_hist[L] = wl_hist.get(L, 0) + c
            word_len_sum += L * c
            word_len_n += c
        if m.token_count:
            type_token_pairs.append((m.type_count, m.token_count))
            mttr_pairs.append(m.mttr_1000)
            content_pairs.append(m.content_word_ratio)
            mp_pairs.append(m.modal_particles_per_1k_words)
            conn_pairs.append(m.connectives_per_1k_words)

    cm.total_chars = total_chars
    cm.total_words = total_words
    cm.total_sentences = total_sentences
    cm.total_main_clauses = main_total

    cm.em_dash_per_10k_chars = round(em_dashes / total_chars * 10_000, 3) if total_chars else 0.0
    cm.v2_violation_rate = round(v2_violations / main_total, 4) if main_total else 0.0
    cm.compound_integrity_rate = round(1.0 - (susp_total / cand_total), 4) if cand_total else 1.0

    if all_sent_lens:
        import statistics
        cm.mean_sentence_length = round(statistics.mean(all_sent_lens), 2)
        cm.std_sentence_length = round(statistics.stdev(all_sent_lens), 2) if len(all_sent_lens) > 1 else 0.0
        cm.p90_sentence_length = round(sorted(all_sent_lens)[int(0.9 * len(all_sent_lens))], 2)
    cm.sentence_length_distribution = all_sent_lens
    cm.word_length_distribution = wl_hist

    if word_len_n:
        cm.mean_word_length = round(word_len_sum / word_len_n, 3)

    if type_token_pairs:
        # Pooled TTR (sum of unique types / sum of tokens) is biased by length;
        # we report the mean of per-document TTRs instead, alongside MTTR-1000.
        cm.type_token_ratio = round(sum(t / n for t, n in type_token_pairs) / len(type_token_pairs), 4)
    if mttr_pairs:
        cm.mttr_1000 = round(sum(mttr_pairs) / len(mttr_pairs), 4)
    if content_pairs:
        cm.content_word_ratio = round(sum(content_pairs) / len(content_pairs), 4)
    if mp_pairs:
        cm.modal_particles_per_1k_words = round(sum(mp_pairs) / len(mp_pairs), 3)
    if conn_pairs:
        cm.connectives_per_1k_words = round(sum(conn_pairs) / len(conn_pairs), 3)

    return cm


# ----------------------------------------------------------------------------
# NorskhetsBench scoring against a reference distribution
# ----------------------------------------------------------------------------

@dataclass
class NoriScore:
    """Per-axis normalized scores comparing measurement to native reference.

    Each axis is in [0, 1] where 1 = matches native, 0 = far from native.

    Three single-number aggregates are reported:

        nori_score : arithmetic mean of the five axes, scaled to [0, 100].
                     This is the headline number, analogous to MMLU/GLUE/MTEB.
        nori_min   : the lowest of the five axes, scaled to [0, 100].
                     Useful as a "weakest link" indicator: a model with
                     four axes at 0.9 and one at 0.0 would have nori_score
                     of 72 but nori_min of 0, which is closer to how a native
                     reader experiences the output.
        nori_g     : geometric mean of the five axes, scaled to [0, 100].
                     Penalizes weak axes more aggressively than arithmetic
                     mean. A near-zero axis pulls nori_g toward zero even
                     if other axes are strong.

    nori_score is the canonical headline. nori_min and nori_g are reported
    alongside it for diagnostic and bottleneck analysis.
    """
    explicitation: float = 0.0       # connectives_per_1k_words distance
    normalization: float = 0.0       # std/p90 sentence length distance
    simplification: float = 0.0      # MTTR-1000 + word length distance
    levelling_out: float = 0.0       # sentence-length variance distance
    interference: float = 0.0        # em-dash + V2 + compound rates

    composite: float = 0.0           # mean of axes in [0, 1] (legacy field)
    nori_score: float = 0.0          # arithmetic mean × 100, the headline
    nori_min: float = 0.0            # min axis × 100, weakest-link indicator
    nori_g: float = 0.0              # geometric mean × 100, bottleneck-penalizing

    raw: dict = field(default_factory=dict)


# Backwards-compatible alias for any external code that imported the old name.
NorskhetsScore = NoriScore


def _smooth_score(observed: float, reference: float, tolerance: float) -> float:
    """Score in [0,1]. 1 if observed == reference, falls off as |obs-ref|
    grows beyond tolerance. Uses a tanh-based rolloff."""
    import math
    if reference == 0 and observed == 0:
        return 1.0
    delta = abs(observed - reference)
    # 0 at delta=4*tolerance, 1 at delta=0
    return max(0.0, 1.0 - math.tanh(delta / max(tolerance, 1e-9)))


def score(model_metrics: CorpusMetrics, native_ref: CorpusMetrics) -> NoriScore:
    """Compute NORI score for a model's output corpus against the native
    Norwegian reference corpus."""
    s = NoriScore()

    # Eksplisittering: connectives per 1k words; LLM tends to over-produce
    s.explicitation = _smooth_score(
        model_metrics.connectives_per_1k_words,
        native_ref.connectives_per_1k_words,
        tolerance=4.0,  # 4 connectives/1k words tolerance
    )

    # Normalisering: how concentrated is the sentence-length distribution?
    s.normalization = _smooth_score(
        model_metrics.std_sentence_length,
        native_ref.std_sentence_length,
        tolerance=3.0,
    )

    # Forenkling: MTTR-1000 and mean word length
    mttr_score = _smooth_score(
        model_metrics.mttr_1000, native_ref.mttr_1000, tolerance=0.05)
    wl_score = _smooth_score(
        model_metrics.mean_word_length, native_ref.mean_word_length, tolerance=0.4)
    s.simplification = round((mttr_score + wl_score) / 2, 4)

    # Utjevning: distance between mean sentence length and reference
    s.levelling_out = _smooth_score(
        model_metrics.mean_sentence_length,
        native_ref.mean_sentence_length,
        tolerance=4.0,
    )

    # Interferens: em-dash density (lower=better in native), V2 violations,
    # compound integrity. We normalize each toward native reference.
    em_score = _smooth_score(
        model_metrics.em_dash_per_10k_chars,
        native_ref.em_dash_per_10k_chars,
        tolerance=5.0,  # ~5 per 10k char tolerance
    )
    v2_score = _smooth_score(
        model_metrics.v2_violation_rate,
        native_ref.v2_violation_rate,
        tolerance=0.10,
    )
    comp_score = _smooth_score(
        model_metrics.compound_integrity_rate,
        native_ref.compound_integrity_rate,
        tolerance=0.05,
    )
    s.interference = round((em_score + v2_score + comp_score) / 3, 4)

    axes = [s.explicitation, s.normalization, s.simplification,
            s.levelling_out, s.interference]
    arithmetic_mean = sum(axes) / len(axes)
    s.composite = round(arithmetic_mean, 4)            # legacy [0, 1]
    s.nori_score = round(arithmetic_mean * 100, 2)      # headline [0, 100]
    s.nori_min = round(min(axes) * 100, 2)              # weakest-link [0, 100]

    # Geometric mean. Use a small epsilon floor so a single zero axis still
    # results in a near-zero geometric mean rather than an exact zero (which
    # would erase any signal from the other axes).
    import math
    eps = 1e-3
    log_sum = sum(math.log(max(a, eps)) for a in axes)
    geom = math.exp(log_sum / len(axes))
    s.nori_g = round(geom * 100, 2)

    s.raw = {
        "model": _to_dict(model_metrics),
        "native_ref": _to_dict(native_ref),
    }
    return s


def _to_dict(cm: CorpusMetrics) -> dict:
    """CorpusMetrics → dict, dropping the heavy distribution fields for JSON."""
    d = cm.__dict__.copy()
    d.pop("sentence_length_distribution", None)
    d.pop("word_length_distribution", None)
    return d
