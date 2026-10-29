"""Pytest integration for the ClaimLab Behavioral Evaluation Benchmark Suite."""
from claimlab.config import settings
from claimlab.evaluation.benchmark import ClaimLabEvaluator


def test_claimlab_official_evaluation_benchmark_all_12_cases(monkeypatch):
    """Runs all 12 behavioral evaluation cases from docs/12_EVALUATION_HARNESS.md.

    Verifies 100% pass rate across numerical proofs, pedagogical adaptation,
    topic boundaries, prompt injection defense, and guest revocation.
    This benchmark does not establish complete database content erasure.
    """
    monkeypatch.setattr(settings, "MODEL_MODE", "fixture")
    evaluator = ClaimLabEvaluator()
    results = evaluator.run_all_cases()

    assert results["total_cases"] == 12
    assert results["passed_cases"] == 12
    assert results["failed_cases"] == 0
    assert results["success_rate_percent"] == 100.0
