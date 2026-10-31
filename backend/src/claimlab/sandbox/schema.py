"""Output contract for agent-written experiments: bounded, finite, and JSON-safe."""
from typing import Annotated, Dict, List, Literal, Optional, Union

from pydantic import Field, FiniteFloat, StringConstraints, field_validator, model_validator

from claimlab.contracts.common import StrictModel

ShortText = Annotated[str, StringConstraints(max_length=200)]
Label = Annotated[str, StringConstraints(max_length=60)]
Scalar = Union[bool, int, FiniteFloat, ShortText]

RESULT_KEYS = ("summary", "metrics", "chart", "series", "table", "checks")


class ExperimentChart(StrictModel):
    title: str = Field(..., max_length=120)
    x_label: str = Field("", max_length=60)
    y_label: str = Field("", max_length=60)
    kind: Literal["line", "bar"] = "line"


class ExperimentSeries(StrictModel):
    name: Label
    x: Optional[List[FiniteFloat]] = Field(None, max_length=500)
    y: List[FiniteFloat] = Field(..., min_length=1, max_length=500)

    @model_validator(mode="after")
    def x_matches_y(self) -> "ExperimentSeries":
        if self.x is None:
            self.x = [float(index) for index in range(len(self.y))]
        if len(self.x) != len(self.y):
            raise ValueError(f"series '{self.name}' has {len(self.x)} x values and {len(self.y)} y values")
        return self


class ExperimentTable(StrictModel):
    columns: List[Label] = Field(..., min_length=1, max_length=8)
    rows: List[List[Optional[Scalar]]] = Field(default_factory=list, max_length=50)

    @model_validator(mode="after")
    def rows_match_columns(self) -> "ExperimentTable":
        for index, row in enumerate(self.rows):
            if len(row) != len(self.columns):
                raise ValueError(f"table row {index} has {len(row)} cells for {len(self.columns)} columns")
        return self


class ExperimentCheck(StrictModel):
    name: str = Field(..., max_length=80)
    passed: bool
    detail: str = Field("", max_length=300)


class SandboxOutput(StrictModel):
    summary: str = Field("", max_length=600)
    metrics: Dict[Label, Scalar] = Field(default_factory=dict)
    chart: Optional[ExperimentChart] = None
    series: List[ExperimentSeries] = Field(default_factory=list, max_length=6)
    table: Optional[ExperimentTable] = None
    checks: List[ExperimentCheck] = Field(default_factory=list, max_length=10)

    @field_validator("metrics")
    @classmethod
    def bounded_metrics(cls, value: Dict[str, Scalar]) -> Dict[str, Scalar]:
        if len(value) > 24:
            raise ValueError(f"metrics has {len(value)} entries; the limit is 24")
        return value
