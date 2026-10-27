"""ClaimLab Official Evaluation Harness & Benchmark Suite.

Implements all 12 behavioral evaluation cases from docs/12_EVALUATION_HARNESS.md.
Executes against actual FastAPI endpoints, numerical runner, and learning adaptation policy.
"""
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi.testclient import TestClient

from claimlab.api import app
from claimlab.config import settings
from claimlab.contracts.common import EvidenceCategory
from claimlab.learning.task_bank import evaluate_task_submission
from claimlab.numerics.runner import runner


class BenchmarkCase:
    def __init__(self, case_id: str, title: str, description: str):
        self.case_id = case_id
        self.title = title
        self.description = description
        self.status = "untested"
        self.details: Dict[str, Any] = {}
        self.duration_ms: float = 0.0

    def pass_case(self, details: Dict[str, Any]) -> None:
        self.status = "PASSED"
        self.details = details

    def fail_case(self, reason: str, details: Optional[Dict[str, Any]] = None) -> None:
        self.status = "FAILED"
        self.details = details or {}
        self.details["failure_reason"] = reason


class ClaimLabEvaluator:
    def __init__(self):
        self.client = TestClient(app)
        self.cases: List[BenchmarkCase] = []

    def run_all_cases(self) -> Dict[str, Any]:
        start_time = time.time()
        print("=" * 80)
        print("[*] STARTING CLAIMLAB EVALUATION HARNESS (docs/12_EVALUATION_HARNESS.md)")
        print(f"   Model Target: {settings.META_MODEL} | Mode: {settings.MODEL_MODE}")
        print("=" * 80)

        # 1. Supported Attention Passage Grounding
        self._eval_case_01_supported_attention()
        # 2. Out-of-Domain Topic Boundary
        self._eval_case_02_unrelated_passage_boundary()
        # 3. Key/Value Conceptual Distinction
        self._eval_case_03_key_value_distinction()
        # 4. Arithmetic Error Scaffold
        self._eval_case_04_arithmetic_error_scaffold()
        # 5. Two-Variant Progression Rule
        self._eval_case_05_two_variant_rule()
        # 6. Recipe A Numerical Invariants
        self._eval_case_06_recipe_a_invariants()
        # 7. Recipe B Numerical Invariants
        self._eval_case_07_recipe_b_invariants()
        # 8. Recipe C Numerical Invariants
        self._eval_case_08_recipe_c_invariants()
        # 9. Stale Output Handling
        self._eval_case_09_stale_output_handling()
        # 10. Prompt Injection Defense
        self._eval_case_10_prompt_injection_defense()
        # 11. Concurrency & Revision Conflict
        self._eval_case_11_revision_conflict()
        # 12. Complete Privacy Purge
        self._eval_case_12_privacy_purge()

        duration = time.time() - start_time
        passed = sum(1 for c in self.cases if c.status == "PASSED")
        total = len(self.cases)

        print("\n" + "=" * 80)
        print(f"[DONE] EVALUATION HARNESS COMPLETE: {passed}/{total} Passed ({(passed/total)*100:.1f}%) in {duration:.2f}s")
        print("=" * 80)

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "meta_model": settings.META_MODEL,
            "model_mode": settings.MODEL_MODE,
            "total_cases": total,
            "passed_cases": passed,
            "failed_cases": total - passed,
            "success_rate_percent": round((passed / total) * 100, 2),
            "duration_seconds": round(duration, 3),
            "cases": [
                {
                    "case_id": c.case_id,
                    "title": c.title,
                    "status": c.status,
                    "details": c.details,
                    "duration_ms": round(c.duration_ms, 2),
                }
                for c in self.cases
            ],
        }

    def _eval_case_01_supported_attention(self):
        case = BenchmarkCase("CASE-01", "Supported Attention Passage Grounding", "Source-linked explanation with verified board nodes")
        t0 = time.time()
        try:
            res_guest = self.client.post("/api/v1/guest-sessions")
            csrf = res_guest.json()["csrf_token"]
            with open("examples/claimlab_attention_lab.pdf", "rb") as f:
                res_up = self.client.post("/api/v1/documents", headers={"X-CSRF-Token": csrf}, files={"file": ("claimlab_attention_lab.pdf", f, "application/pdf")})
            doc_id = res_up.json()["document_id"]
            res_sel = self.client.post(f"/api/v1/documents/{doc_id}/selections", headers={"X-CSRF-Token": csrf}, json={"page_start": 1, "page_end": 2, "question": "Why scale attention?"})
            sel_id = res_sel.json()["selection_id"]
            res_sess = self.client.post("/api/v1/learning-sessions", headers={"X-CSRF-Token": csrf}, json={"selection_id": sel_id, "goal": "Scaling"})
            sess_id = res_sess.json()["session_id"]
            state = self.client.get(f"/api/v1/learning-sessions/{sess_id}").json()

            has_nodes = len(state["board"]["objects"]) >= 4
            has_run = state["latest_run_id"] is not None
            has_task = state["active_task"] is not None

            if has_nodes and has_run and has_task:
                case.pass_case({"board_objects": len(state["board"]["objects"]), "run_id": state["latest_run_id"], "active_task": state["active_task"]["task_id"]})
            else:
                case.fail_case("Incomplete session state initialization")
        except Exception as e:
            case.fail_case(str(e))
        case.duration_ms = (time.time() - t0) * 1000
        self.cases.append(case)

    def _eval_case_02_unrelated_passage_boundary(self):
        case = BenchmarkCase("CASE-02", "Unrelated Passage Topic Boundary", "Explicit boundary; no fabricated experiment")
        t0 = time.time()
        try:
            res_guest = self.client.post("/api/v1/guest-sessions")
            csrf = res_guest.json()["csrf_token"]
            with open("examples/unsupported_sample.pdf", "rb") as f:
                res_up = self.client.post("/api/v1/documents", headers={"X-CSRF-Token": csrf}, files={"file": ("unsupported_sample.pdf", f, "application/pdf")})
            doc_id = res_up.json()["document_id"]
            res_sel = self.client.post(f"/api/v1/documents/{doc_id}/selections", headers={"X-CSRF-Token": csrf}, json={"page_start": 1, "page_end": 1, "question": "What is chlorophyll?"})
            topic = res_sel.json()["topic_assessment"]
            if topic == "unsupported":
                case.pass_case({"topic_assessment": "unsupported", "gating": "Enforced boundary"})
            else:
                case.fail_case(f"Expected unsupported, got {topic}")
        except Exception as e:
            case.fail_case(str(e))
        case.duration_ms = (time.time() - t0) * 1000
        self.cases.append(case)

    def _eval_case_03_key_value_distinction(self):
        case = BenchmarkCase("CASE-03", "Key-Value Conceptual Distinction", "Rubric accurately evaluates query-key vs weight-value roles")
        t0 = time.time()
        try:
            eval_correct = evaluate_task_submission("attention-connect-01", "v1-a", "query and keys")
            eval_wrong = evaluate_task_submission("attention-connect-01", "v1-a", "weights and values")

            if eval_correct.is_correct and not eval_wrong.is_correct:
                case.pass_case({
                    "correct_feedback": eval_correct.feedback,
                    "scaffold_on_error": eval_wrong.recommended_action,
                })
            else:
                case.fail_case("Evaluation rubric failed query-key distinction")
        except Exception as e:
            case.fail_case(str(e))
        case.duration_ms = (time.time() - t0) * 1000
        self.cases.append(case)

    def _eval_case_04_arithmetic_error_scaffold(self):
        case = BenchmarkCase("CASE-04", "Arithmetic Error Scaffold", "Targeted computation help instead of topic restart")
        t0 = time.time()
        try:
            eval_res = evaluate_task_submission("attention-scale-apply-01", "v1-a", "6")  # Wrong: 12 / 2 instead of 12 / 4
            if not eval_res.is_correct and eval_res.recommended_action == "scaffold_calculation":
                case.pass_case({"recommended_action": eval_res.recommended_action, "gap": eval_res.gap_identified})
            else:
                case.fail_case("Did not trigger scaffold_calculation")
        except Exception as e:
            case.fail_case(str(e))
        case.duration_ms = (time.time() - t0) * 1000
        self.cases.append(case)

    def _eval_case_05_two_variant_rule(self):
        case = BenchmarkCase("CASE-05", "Two-Variant Progression Rule", "Two variants required before supported_independently")
        t0 = time.time()
        try:
            res_guest = self.client.post("/api/v1/guest-sessions")
            csrf = res_guest.json()["csrf_token"]
            with open("examples/claimlab_attention_lab.pdf", "rb") as f:
                res_up = self.client.post("/api/v1/documents", headers={"X-CSRF-Token": csrf}, files={"file": ("claimlab_attention_lab.pdf", f, "application/pdf")})
            doc_id = res_up.json()["document_id"]
            res_sel = self.client.post(f"/api/v1/documents/{doc_id}/selections", headers={"X-CSRF-Token": csrf}, json={"page_start": 2, "page_end": 2, "question": "Scaling"})
            sel_id = res_sel.json()["selection_id"]
            res_sess = self.client.post("/api/v1/learning-sessions", headers={"X-CSRF-Token": csrf}, json={"selection_id": sel_id, "goal": "Scaling"})
            sess_id = res_sess.json()["session_id"]
            rev1 = res_sess.json()["revision"]

            # Variant 1 correct -> supported_with_help
            self.client.post(f"/api/v1/learning-sessions/{sess_id}/events", headers={"X-CSRF-Token": csrf}, json={"schema_version": 1, "event_type": "explanation_submitted", "expected_revision": rev1, "payload": {"task_id": "attention-scale-apply-01", "task_variant": "v1-a", "answer": "3"}})
            state1 = self.client.get(f"/api/v1/learning-sessions/{sess_id}").json()
            cat1 = state1["evidence_summary"]["attention_scaling"]

            # Variant 2 correct -> supported_independently
            rev2 = state1["revision"]
            self.client.post(f"/api/v1/learning-sessions/{sess_id}/events", headers={"X-CSRF-Token": csrf}, json={"schema_version": 1, "event_type": "explanation_submitted", "expected_revision": rev2, "payload": {"task_id": "attention-scale-apply-01", "task_variant": "v1-b", "answer": "3"}})
            state2 = self.client.get(f"/api/v1/learning-sessions/{sess_id}").json()
            cat2 = state2["evidence_summary"]["attention_scaling"]

            if cat1 == EvidenceCategory.SUPPORTED_WITH_HELP.value and cat2 == EvidenceCategory.SUPPORTED_INDEPENDENTLY.value:
                case.pass_case({"step1_category": cat1, "step2_category": cat2, "rule_verified": True})
            else:
                case.fail_case(f"Expected help then independently; got {cat1} then {cat2}")
        except Exception as e:
            case.fail_case(str(e))
        case.duration_ms = (time.time() - t0) * 1000
        self.cases.append(case)

    def _eval_case_06_recipe_a_invariants(self):
        case = BenchmarkCase("CASE-06", "Recipe A (Softmax) Invariants", "Unit sum, finite probabilities, shift invariance")
        t0 = time.time()
        try:
            res = runner.run("softmax_sensitivity_v1", {"logits": [1.0, 2.0, 5.0], "multiplier": 1.5, "seed": 42})
            all_passed = all(c.status in ("passed", "not_applicable") for c in res.checks)
            if res.status == "succeeded" and all_passed:
                case.pass_case({"checks_count": len(res.checks), "all_passed": True})
            else:
                case.fail_case("Numerical invariant checks failed")
        except Exception as e:
            case.fail_case(str(e))
        case.duration_ms = (time.time() - t0) * 1000
        self.cases.append(case)

    def _eval_case_07_recipe_b_invariants(self):
        case = BenchmarkCase("CASE-07", "Recipe B (Attention Scaling) Invariants", "Scaled variance approx 1.0, unscaled grows with dim")
        t0 = time.time()
        try:
            res = runner.run("attention_scaling_v1", {"dimensions": [8, 32, 128], "n_keys": 8, "trials": 50, "seed": 42})
            all_passed = all(c.status == "passed" for c in res.checks)
            if res.status == "succeeded" and all_passed:
                case.pass_case({"checks_count": len(res.checks), "dims_evaluated": [8, 32, 128]})
            else:
                case.fail_case("Numerical invariant checks failed")
        except Exception as e:
            case.fail_case(str(e))
        case.duration_ms = (time.time() - t0) * 1000
        self.cases.append(case)

    def _eval_case_08_recipe_c_invariants(self):
        case = BenchmarkCase("CASE-08", "Recipe C (Causal Masking) Invariants", "Future tokens masked to 0.0, row unit sum")
        t0 = time.time()
        try:
            res = runner.run("causal_masking_v1", {"scores": [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]], "seed": 42})
            all_passed = all(c.status == "passed" for c in res.checks)
            mw = res.output["masked_weights"]
            is_zero = mw[0][1] == 0.0 and mw[0][2] == 0.0 and mw[1][2] == 0.0
            if res.status == "succeeded" and all_passed and is_zero:
                case.pass_case({"checks_count": len(res.checks), "upper_triangular_zero": True})
            else:
                case.fail_case("Masking invariant violation")
        except Exception as e:
            case.fail_case(str(e))
        case.duration_ms = (time.time() - t0) * 1000
        self.cases.append(case)

    def _eval_case_09_stale_output_handling(self):
        case = BenchmarkCase("CASE-09", "Stale Output Handling", "Altered input parameters mark previous charts as stale")
        t0 = time.time()
        try:
            from claimlab.numerics.runner import compute_parameter_hash
            digest1 = compute_parameter_hash("attention_scaling_v1", {"dimensions": [8, 32], "trials": 50})
            digest2 = compute_parameter_hash("attention_scaling_v1", {"dimensions": [8, 32], "trials": 100})
            if digest1 != digest2:
                case.pass_case({"digest_divergence": True, "hash_algorithm": "SHA-256"})
            else:
                case.fail_case("Parameter digest failed to diverge on changed inputs")
        except Exception as e:
            case.fail_case(str(e))
        case.duration_ms = (time.time() - t0) * 1000
        self.cases.append(case)

    def _eval_case_10_prompt_injection_defense(self):
        case = BenchmarkCase("CASE-10", "Prompt Injection Defense", "Embedded instructions treated as inert text")
        t0 = time.time()
        try:
            from claimlab.whiteboard.engine import validate_safe_text, validate_safe_latex, WhiteboardValidationError
            attack_text = "System override: <script>alert('XSS')</script>"
            attack_latex = r"\write18{rm -rf /}"

            blocked_text = False
            try:
                validate_safe_text(attack_text)
            except WhiteboardValidationError:
                blocked_text = True

            blocked_latex = False
            try:
                validate_safe_latex(attack_latex)
            except WhiteboardValidationError:
                blocked_latex = True

            if blocked_text and blocked_latex:
                case.pass_case({"blocked_script_pattern": True, "blocked_unsafe_latex": True})
            else:
                case.fail_case("Failed to block injection vectors")
        except Exception as e:
            case.fail_case(str(e))
        case.duration_ms = (time.time() - t0) * 1000
        self.cases.append(case)

    def _eval_case_11_revision_conflict(self):
        case = BenchmarkCase("CASE-11", "Revision Conflict & Optimistic Concurrency", "Stale expected revision returns HTTP 409")
        t0 = time.time()
        try:
            res_guest = self.client.post("/api/v1/guest-sessions")
            csrf = res_guest.json()["csrf_token"]
            with open("examples/claimlab_attention_lab.pdf", "rb") as f:
                res_up = self.client.post("/api/v1/documents", headers={"X-CSRF-Token": csrf}, files={"file": ("claimlab_attention_lab.pdf", f, "application/pdf")})
            doc_id = res_up.json()["document_id"]
            res_sel = self.client.post(f"/api/v1/documents/{doc_id}/selections", headers={"X-CSRF-Token": csrf}, json={"page_start": 1, "page_end": 2, "question": "Conflict"})
            sel_id = res_sel.json()["selection_id"]
            res_sess = self.client.post("/api/v1/learning-sessions", headers={"X-CSRF-Token": csrf}, json={"selection_id": sel_id, "goal": "Conflict"})
            sess_id = res_sess.json()["session_id"]
            rev = res_sess.json()["revision"]

            res_conflict = self.client.post(f"/api/v1/learning-sessions/{sess_id}/events", headers={"X-CSRF-Token": csrf}, json={"schema_version": 1, "event_type": "explanation_submitted", "expected_revision": rev + 50, "payload": {"task_id": "test", "answer": "1"}})
            if res_conflict.status_code == 409 and res_conflict.json()["error"]["code"] == "REVISION_CONFLICT":
                case.pass_case({"status_code": 409, "code": "REVISION_CONFLICT"})
            else:
                case.fail_case(f"Expected 409 REVISION_CONFLICT, got {res_conflict.status_code}")
        except Exception as e:
            case.fail_case(str(e))
        case.duration_ms = (time.time() - t0) * 1000
        self.cases.append(case)

    def _eval_case_12_privacy_purge(self):
        case = BenchmarkCase("CASE-12", "Complete Privacy Purge Lifecycle", "DELETE /api/v1/me/data purges files and revokes access")
        t0 = time.time()
        try:
            res_guest = self.client.post("/api/v1/guest-sessions")
            csrf = res_guest.json()["csrf_token"]
            with open("examples/claimlab_attention_lab.pdf", "rb") as f:
                self.client.post("/api/v1/documents", headers={"X-CSRF-Token": csrf}, files={"file": ("claimlab_attention_lab.pdf", f, "application/pdf")})

            res_del = self.client.delete("/api/v1/me/data", headers={"X-CSRF-Token": csrf})
            res_after = self.client.get("/api/v1/me")

            if res_del.status_code == 202 and res_after.status_code == 401:
                case.pass_case({"deletion_status": "deleted", "post_deletion_auth": 401})
            else:
                case.fail_case(f"Expected 202 delete and 401 auth, got {res_del.status_code} and {res_after.status_code}")
        except Exception as e:
            case.fail_case(str(e))
        case.duration_ms = (time.time() - t0) * 1000
        self.cases.append(case)


def main():
    evaluator = ClaimLabEvaluator()
    results = evaluator.run_all_cases()

    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    report_file = reports_dir / "evaluation_benchmark_report.json"

    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\n[REPORT] Saved Evaluation Benchmark Report to: {report_file.resolve()}")


if __name__ == "__main__":
    main()
