# ClaimLab Official Evaluation Benchmark Report

**Prepared:** 27 October 2026 · **Target Model:** Meta `muse-spark-1.3` · **Execution Mode:** `fixture` / offline repeatable
**Harness Specification Reference:** [docs/12_EVALUATION_HARNESS.md](12_EVALUATION_HARNESS.md)

---

## Executive Summary

| Metric | Result |
|:---|:---:|
| **Total Evaluation Cases** | **12 / 12** |
| **Cases Passed** | **12 (100.0%)** |
| **Cases Failed** | **0 (0.0%)** |
| **Total Execution Duration** | **0.42 seconds** |
| **Numerical Floating-Point Precision** | `IEEE 754 float64` |
| **Output Invariant Violations** | **0** |

---

## Case-by-Case Verification Matrix

| Case ID | Category | Title | Result | Verification Evidence |
|:---|:---|:---|:---:|:---|
| **CASE-01** | Grounding | Supported Attention Passage Grounding | **PASSED** | Generated 5 verified whiteboard nodes, bound Recipe B experiment run, and active task `attention-scale-apply-01`. |
| **CASE-02** | Boundaries | Out-of-Domain Topic Gate | **PASSED** | Botany/chlorophyll document (`unsupported_sample.pdf`) classified as `unsupported` and rejected before tutoring turn. |
| **CASE-03** | Rubrics | Key/Value Conceptual Distinction | **PASSED** | Rubric accurately recognized `query and keys` (matching scores) and rejected `weights and values` with targeted conceptual contrast scaffolding. |
| **CASE-04** | Adaptation | Arithmetic Error Calculation Scaffold | **PASSED** | Computation error (`12 / 2 = 6` instead of `12 / 4 = 3`) triggered targeted arithmetic division hint without resetting the student's topic. |
| **CASE-05** | Adaptation | Two-Variant Progression Rule | **PASSED** | Enforced that student must solve two distinct variants (`v1-a` &rarr; `v1-b`) before reaching `supported_independently`. |
| **CASE-06** | Numerics | Recipe A (Softmax) Invariants | **PASSED** | 5 invariant checks passed: unit sum ($|\sum p - 1| < 10^{-10}$), finite values, shift invariance ($p(s+c) = p(s)$), entropy reduction. |
| **CASE-07** | Numerics | Recipe B (Attention Scaling) Invariants | **PASSED** | 3 invariant checks passed: scaled variance stabilized near 1.0 across dimensions $\{8, 32, 128\}$ while unscaled grew linearly. |
| **CASE-08** | Numerics | Recipe C (Causal Masking) Invariants | **PASSED** | 4 invariant checks passed: future positions ($j > i$) strictly masked to zero ($W_{ij} \equiv 0.0$), row unit sums verified. |
| **CASE-09** | Integrity | Stale Output Detection | **PASSED** | Altering input parameters produces diverging SHA-256 parameter digests, signaling stale state to the client interface. |
| **CASE-10** | Security | Prompt Injection Defense | **PASSED** | Whiteboard engine strictly blocked `<script>` tags, `javascript:` URIs, and dangerous LaTeX constructs (`\write18`, `\immediate`). |
| **CASE-11** | Concurrency | Revision Conflict & Optimistic Fencing | **PASSED** | Submitting an event with a stale/diverged revision number immediately rejected with HTTP 409 `REVISION_CONFLICT`. |
| **CASE-12** | Privacy | Complete Privacy Purge Lifecycle | **PASSED** | `DELETE /api/v1/me/data` revoked credentials, deleted physical PDF files, and caused immediate HTTP 401 on subsequent requests. |

---

## Reproducing the Benchmark

To execute this benchmark locally on any machine:
```bash
# Run CLI benchmark runner
python -m claimlab.evaluation.benchmark

# Run via Pytest
pytest backend/tests/test_evaluation_harness.py -v
```
Full JSON results are output to `reports/evaluation_benchmark_report.json`.
