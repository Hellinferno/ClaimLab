"""Retained experiment runs for tutor-written code executed in the isolated sandbox."""
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import ValidationError

from claimlab.contracts.experiment import CheckResult, ExperimentRunResponse, RecipeId, SandboxParameterSpec
from claimlab.numerics.runner import compute_parameter_hash
from claimlab.sandbox import run_python_experiment

MAX_PARAMETERS = 6
BASE_ASSUMPTIONS = [
    "Tutor-written code ran in an isolated sandbox (numpy only, no files or network); it is not a reviewed recipe.",
    "A toy-scale illustration of the mechanism with synthetic inputs, not a reproduction of the paper's benchmark.",
]


class SandboxSpecError(ValueError):
    """The experiment description is invalid; the message is safe to show the model or learner."""


def normalize_spec(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Validated, canonical experiment description: title, question, code, knobs, assumptions."""
    code = raw.get("code")
    if not isinstance(code, str) or not code.strip():
        raise SandboxSpecError("Experiment code is required.")
    specs: List[Dict[str, Any]] = []
    for item in (raw.get("parameters") or raw.get("parameter_specs") or [])[:MAX_PARAMETERS]:
        try:
            spec = SandboxParameterSpec(**item) if isinstance(item, dict) else None
        except ValidationError as exc:
            raise SandboxSpecError(f"Invalid parameter: {exc.errors()[0]['msg']}") from exc
        if spec is None or not spec.min <= spec.value <= spec.max:
            raise SandboxSpecError("Each parameter needs min <= value <= max.")
        specs.append(spec.model_dump())
    if len({s["name"] for s in specs}) != len(specs):
        raise SandboxSpecError("Parameter names must be unique.")
    return {
        "title": str(raw.get("title") or "Experiment")[:80],
        "question": str(raw.get("question") or "")[:300],
        "code": code,
        "parameter_specs": specs,
        "assumptions": [str(a)[:200] for a in (raw.get("assumptions") or []) if str(a).strip()][:4],
    }


def resolve_values(specs: List[Dict[str, Any]], overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Defaults from the specs, overridden only by in-range numbers for declared knobs."""
    values: Dict[str, Any] = {}
    overrides = overrides or {}
    unknown = set(overrides) - {s["name"] for s in specs}
    if unknown:
        raise SandboxSpecError(f"Unknown parameter: {sorted(unknown)[0]}")
    for spec in specs:
        value = overrides.get(spec["name"], spec["value"])
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise SandboxSpecError(f"{spec['label'] or spec['name']} must be a number.")
        if not spec["min"] <= value <= spec["max"]:
            raise SandboxSpecError(f"{spec['label'] or spec['name']} must be from {spec['min']:g} to {spec['max']:g}.")
        values[spec["name"]] = int(round(value)) if spec["integer"] else float(value)
    return values


def execute_sandbox_experiment(spec: Dict[str, Any], overrides: Optional[Dict[str, Any]] = None) -> ExperimentRunResponse:
    """Run a normalized spec and keep everything needed to inspect or re-run it."""
    started_at = datetime.now(timezone.utc).isoformat()
    values = resolve_values(spec["parameter_specs"], overrides)
    result = run_python_experiment(spec["code"], values)

    checks = [CheckResult(
        name="ran_in_isolated_sandbox",
        status="passed" if result.status == "succeeded" else "failed",
        detail=(f"Finished in {result.duration_ms} ms ({result.environment})." if result.status == "succeeded"
                else result.error or f"Run {result.status}."),
    )]
    output: Dict[str, Any]
    if result.output is not None:
        checks.append(CheckResult(name="outputs_finite_and_bounded", status="passed",
                                  detail="Every reported number is finite and within the output limits."))
        checks += [CheckResult(name=f"claim: {c.name}"[:80], status="passed" if c.passed else "failed", detail=c.detail[:300])
                   for c in result.output.checks]
        output = {**result.output.model_dump(), "stdout": result.stdout}
    else:
        output = {"error": result.error or f"Run {result.status}.", "stdout": result.stdout}

    parameters = {**spec, "values": values}
    seed = values.get("seed", 0)
    return ExperimentRunResponse(
        run_id=str(uuid.uuid4()),
        recipe_id=RecipeId.SANDBOX_PYTHON,
        parameters=parameters,
        parameter_hash=compute_parameter_hash(RecipeId.SANDBOX_PYTHON.value, parameters),
        seed=int(seed) if isinstance(seed, (int, float)) and 0 <= seed < 2**32 else 0,
        status=result.status if result.output is not None or result.status != "succeeded" else "failed",
        output=output,
        checks=checks,
        assumptions=BASE_ASSUMPTIONS + spec["assumptions"],
        runner_digest=f"sandbox-python-v1/{result.environment}/{hashlib.sha256(spec['code'].encode('utf-8')).hexdigest()[:12]}",
        numpy_version=result.numpy_version or "not used",
        started_at=started_at,
        completed_at=datetime.now(timezone.utc).isoformat(),
    )


def tool_summary(run: ExperimentRunResponse) -> Dict[str, Any]:
    """What the tutor sees after its experiment: enough to explain or fix it, nothing more."""
    output = run.output or {}
    summary: Dict[str, Any] = {"run_id": run.run_id, "status": run.status, "values": run.parameters.get("values")}
    if run.status == "succeeded":
        summary.update(
            summary=output.get("summary"),
            metrics=output.get("metrics"),
            series=[{"name": s["name"], "points": len(s["x"]),
                     "y_first": s["y"][:3], "y_last": s["y"][-3:]} for s in output.get("series") or []],
            table=output.get("table"),
            checks=[c.model_dump() for c in run.checks],
        )
    else:
        summary["error"] = output.get("error")
    if output.get("stdout"):
        summary["stdout"] = output["stdout"][:1500]
    return summary
