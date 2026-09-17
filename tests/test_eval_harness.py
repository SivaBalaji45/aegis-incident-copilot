import pytest

from aegis.eval.metrics import mean_reciprocal_rank, precision_recall_f1, recall_at_k, rouge_l


def test_recall_at_k_counts_hits_within_k():
    retrieved = ["c1", "c2", "c3", "c4"]
    relevant = {"c2", "c4", "c9"}

    assert recall_at_k(retrieved, relevant, k=2) == pytest.approx(1 / 3)
    assert recall_at_k(retrieved, relevant, k=4) == pytest.approx(2 / 3)


def test_recall_at_k_no_relevant_docs_is_zero():
    assert recall_at_k(["c1"], set(), k=5) == 0.0


def test_mean_reciprocal_rank_first_hit_position():
    assert mean_reciprocal_rank(["a", "b", "c"], {"b"}) == pytest.approx(0.5)
    assert mean_reciprocal_rank(["a", "b", "c"], {"z"}) == 0.0
    assert mean_reciprocal_rank(["a", "b", "c"], {"a"}) == 1.0


def test_precision_recall_f1_perfect_predictions():
    scores = precision_recall_f1(["major", "minor"], ["major", "minor"])
    assert scores == {"precision": 1.0, "recall": 1.0, "f1": 1.0}


def test_precision_recall_f1_partial_predictions():
    scores = precision_recall_f1(["major", "minor", "critical"], ["major", "major", "critical"])
    assert scores["f1"] == pytest.approx(2 / 3)


def test_precision_recall_f1_length_mismatch_raises():
    with pytest.raises(ValueError):
        precision_recall_f1(["major"], ["major", "minor"])


def test_rouge_l_identical_strings_is_one():
    assert rouge_l("database failover resolved the incident", "database failover resolved the incident") == pytest.approx(1.0)


def test_rouge_l_disjoint_strings_is_zero():
    assert rouge_l("alpha beta gamma", "delta epsilon zeta") == 0.0


def test_rouge_l_partial_overlap_between_zero_and_one():
    score = rouge_l("upstream database latency caused errors", "database latency caused the errors")
    assert 0.0 < score < 1.0
