"""Metric functions for the eval harness. Kept dependency-light and pure
(no DB/LLM calls) so `tests/test_eval_harness.py` can exercise them
deterministically in CI as a regression gate — see run_eval.py for the
fuller harness that actually invokes retrieval/generation against the
golden set.
"""

from __future__ import annotations


def recall_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int) -> float:
    if not relevant_ids:
        return 0.0
    top_k = set(retrieved_ids[:k])
    return len(top_k & relevant_ids) / len(relevant_ids)


def mean_reciprocal_rank(retrieved_ids: list[str], relevant_ids: set[str]) -> float:
    for rank, doc_id in enumerate(retrieved_ids, start=1):
        if doc_id in relevant_ids:
            return 1.0 / rank
    return 0.0


def precision_recall_f1(predicted: list[str], gold: list[str]) -> dict[str, float]:
    """Micro-averaged precision/recall/F1 for single-label classification
    (used for the triage agent's severity/category output)."""
    if len(predicted) != len(gold):
        raise ValueError("predicted and gold must be the same length")
    if not predicted:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}

    correct = sum(1 for p, g in zip(predicted, gold) if p == g)
    precision = recall = correct / len(predicted)
    f1 = precision  # micro precision == micro recall == accuracy for single-label
    return {"precision": precision, "recall": recall, "f1": f1}


def rouge_l(prediction: str, reference: str) -> float:
    """ROUGE-L F1 via longest common subsequence over whitespace tokens.
    Swap for the `rouge-score` package's implementation if stemming/synonym
    handling starts mattering — this is a dependency-free approximation."""
    pred_tokens = prediction.split()
    ref_tokens = reference.split()
    if not pred_tokens or not ref_tokens:
        return 0.0

    lcs_len = _lcs_length(pred_tokens, ref_tokens)
    if lcs_len == 0:
        return 0.0

    precision = lcs_len / len(pred_tokens)
    recall = lcs_len / len(ref_tokens)
    return 2 * precision * recall / (precision + recall)


def _lcs_length(a: list[str], b: list[str]) -> int:
    dp = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp[-1][-1]
