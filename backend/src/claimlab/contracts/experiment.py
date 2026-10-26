"""Contracts and schemas for the three reviewed experiment recipes."""
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from pydantic import Field, field_validator
from claimlab.contracts.common import StrictModel


class RecipeId(str, Enum):
    SOFTMAX_SENSITIVITY = "softmax_sensitivity_v1"
    ATTENTION_SCALING = "attention_scaling_v1"
    CAUSAL_MASKING = "causal_masking_v1"


# --- Recipe A: Softmax Sensitivity ---
class SoftmaxSensitivityParams(StrictModel):
    logits: List[float] = Field(..., min_length=2, max_length=12)
    multiplier: float = Field(..., ge=0.25, le=4.0)
    seed: int = Field(default=42, ge=0, le=2**32 - 1)

    @field_validator("logits")
    @classmethod
    def validate_logits(cls, v: List[float]) -> List[float]:
        for x in v:
            if not (-20.0 <= x <= 20.0):
                raise ValueError(f"Logit {x} is out of bounds [-20, 20]")
        return v


class SoftmaxSensitivityOutput(StrictModel):
    input_logits: List[float]
    scaled_logits: List[float]
    base_probabilities: List[float]
    scaled_probabilities: List[float]
    base_max_prob: float
    scaled_max_prob: float
    base_entropy: float
    scaled_entropy: float


# --- Recipe B: Attention Scaling ---
class AttentionScalingParams(StrictModel):
    dimensions: List[int] = Field(..., min_length=1, max_length=4)
    n_keys: int = Field(..., ge=2, le=16)
    trials: int = Field(..., ge=20, le=200)
    seed: int = Field(default=42, ge=0, le=2**32 - 1)

    @field_validator("dimensions")
    @classmethod
    def validate_dimensions(cls, v: List[int]) -> List[int]:
        if len(v) != len(set(v)):
            raise ValueError("Dimensions must be unique")
        for d in v:
            if not (1 <= d <= 256):
                raise ValueError(f"Dimension {d} must be in [1, 256]")
        return v


class DimensionResult(StrictModel):
    dimension: int
    unscaled_variance: float
    scaled_variance: float
    unscaled_mean_entropy: float
    scaled_mean_entropy: float
    first_trial_unscaled_scores: List[float]
    first_trial_scaled_scores: List[float]
    first_trial_unscaled_weights: List[float]
    first_trial_scaled_weights: List[float]


class AttentionScalingOutput(StrictModel):
    dimensions: List[int]
    n_keys: int
    trials: int
    seed: int
    results: List[DimensionResult]


# --- Recipe C: Causal Masking ---
class CausalMaskingParams(StrictModel):
    scores: List[List[float]] = Field(..., min_length=2, max_length=8)
    seed: int = Field(default=42, ge=0, le=2**32 - 1)

    @field_validator("scores")
    @classmethod
    def validate_matrix(cls, v: List[List[float]]) -> List[List[float]]:
        size = len(v)
        for row in v:
            if len(row) != size:
                raise ValueError("Scores matrix must be square")
            for val in row:
                if not (-20.0 <= val <= 20.0):
                    raise ValueError(f"Score {val} out of bounds [-20, 20]")
        return v


class CausalMaskingOutput(StrictModel):
    size: int
    scores: List[List[float]]
    allowed_mask: List[List[bool]]
    unmasked_weights: List[List[float]]
    masked_weights: List[List[float]]


# Check results
class CheckResult(StrictModel):
    name: str
    status: Literal["passed", "failed", "not_applicable"]
    tolerance: Optional[float] = None
    detail: str


class ExperimentRunResponse(StrictModel):
    run_id: str
    recipe_id: RecipeId
    parameters: Dict[str, Any]
    parameter_hash: str
    seed: int
    status: str
    output: Optional[Dict[str, Any]] = None
    checks: List[CheckResult] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    runner_digest: str = "local-runner-v1"
    numpy_version: str
    started_at: str
    completed_at: Optional[str] = None
