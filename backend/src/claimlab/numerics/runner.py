"""Numerical recipe runner service with parameter hashing and isolation boundaries."""
import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict
import numpy as np
import uuid

from claimlab.contracts.experiment import (
    RecipeId,
    SoftmaxSensitivityParams,
    AttentionScalingParams,
    CausalMaskingParams,
    ExperimentRunResponse,
)
from claimlab.numerics.recipes import (
    run_softmax_sensitivity,
    run_attention_scaling,
    run_causal_masking,
)


def compute_parameter_hash(recipe_id: str, params: Dict[str, Any]) -> str:
    """Canonical parameter hash: sorted keys, compact separators, sha256."""
    canonical_json = json.dumps({"recipe_id": recipe_id, "parameters": params}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


class NumericalRunner:
    """Executes reviewed numerical recipes under validated bounds."""

    def __init__(self, backend: str = "local"):
        self.backend = backend

    def run(self, recipe_id: str, parameters: Dict[str, Any]) -> ExperimentRunResponse:
        started_at = datetime.now(timezone.utc).isoformat()
        param_hash = compute_parameter_hash(recipe_id, parameters)
        run_id = str(uuid.uuid4())
        seed = int(parameters.get("seed", 42))

        assumptions: list[str] = []

        if recipe_id == RecipeId.SOFTMAX_SENSITIVITY.value:
            validated_params = SoftmaxSensitivityParams(**parameters)
            assumptions = [
                "Stable softmax subtraction of max logit prevents floating-point overflow.",
                "Entropy is computed in natural units (nats); 0*ln(0) evaluates to 0.",
            ]
            output, checks = run_softmax_sensitivity(validated_params)
            output_dict = output.model_dump()

        elif recipe_id == RecipeId.ATTENTION_SCALING.value:
            validated_params = AttentionScalingParams(**parameters)
            assumptions = [
                "Queries and keys are drawn from independent standard normal distributions N(0, 1).",
                "Unscaled dot products have variance growing linearly with key dimension d.",
                "Scaling scores by 1/sqrt(d) stabilizes score variance near 1.0 across dimensions.",
            ]
            output, checks = run_attention_scaling(validated_params)
            output_dict = output.model_dump()

        elif recipe_id == RecipeId.CAUSAL_MASKING.value:
            validated_params = CausalMaskingParams(**parameters)
            assumptions = [
                "Causal masking forbids attending to positions j > i (future positions).",
                "Row-wise softmax is computed only over allowed positions {0, ..., i}.",
                "Forbidden future positions are assigned exact probability 0.0.",
            ]
            output, checks = run_causal_masking(validated_params)
            output_dict = output.model_dump()

        else:
            raise ValueError(f"Unsupported recipe: {recipe_id}")

        completed_at = datetime.now(timezone.utc).isoformat()
        all_passed = all(c.status in ("passed", "not_applicable") for c in checks)

        return ExperimentRunResponse(
            run_id=run_id,
            recipe_id=RecipeId(recipe_id),
            parameters=parameters,
            parameter_hash=param_hash,
            seed=seed,
            status="succeeded" if all_passed else "failed",
            output=output_dict,
            checks=checks,
            assumptions=assumptions,
            runner_digest=f"{self.backend}-runner-v1",
            numpy_version=np.__version__,
            started_at=started_at,
            completed_at=completed_at,
        )


runner = NumericalRunner()
