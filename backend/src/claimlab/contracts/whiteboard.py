"""Whiteboard models, scene graph, and patch commands."""
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import Field
from claimlab.contracts.common import StrictModel


class ObjectType(str, Enum):
    TEXT = "text"
    EQUATION = "equation"
    CONCEPT_NODE = "concept_node"
    MATRIX = "matrix"
    CONNECTOR = "connector"
    PLOT_REF = "plot_ref"
    GROUP = "group"
    ANNOTATION = "annotation"


class Position(StrictModel):
    x: float
    y: float


class Dimensions(StrictModel):
    width: float
    height: float


class BoardObject(StrictModel):
    id: str = Field(..., max_length=64, description="Bounded unique slug")
    type: ObjectType
    position: Position
    dimensions: Dimensions
    label: str = Field(..., max_length=500)
    concept_id: Optional[str] = None
    source_refs: Optional[List[str]] = Field(default_factory=list)
    payload: Dict[str, Any] = Field(default_factory=dict)
    highlight_style: Optional[str] = None


class SceneGraph(StrictModel):
    schema_version: int = 1
    board_revision: int = 0
    objects: List[BoardObject] = Field(default_factory=list)
    active_group: Optional[str] = None


# Board patch commands
class AddObjectCommand(StrictModel):
    op: Literal["add_object"] = "add_object"
    object: BoardObject


class UpdateObjectCommand(StrictModel):
    op: Literal["update_object"] = "update_object"
    object_id: str
    position: Optional[Position] = None
    dimensions: Optional[Dimensions] = None
    label: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    concept_id: Optional[str] = None


class AddConnectorCommand(StrictModel):
    op: Literal["add_connector"] = "add_connector"
    connector_id: str
    from_object_id: str
    to_object_id: str
    relationship: str
    label: Optional[str] = None


class HighlightObjectsCommand(StrictModel):
    op: Literal["highlight_objects"] = "highlight_objects"
    object_ids: List[str]
    style: str = "primary"  # e.g. "primary", "warning", "success"


class RemoveObjectCommand(StrictModel):
    op: Literal["remove_object"] = "remove_object"
    object_id: str


class SetActiveGroupCommand(StrictModel):
    op: Literal["set_active_group"] = "set_active_group"
    group_id: Optional[str] = None


class ClearHighlightsCommand(StrictModel):
    op: Literal["clear_highlights"] = "clear_highlights"


BoardCommand = Union[
    AddObjectCommand,
    UpdateObjectCommand,
    AddConnectorCommand,
    HighlightObjectsCommand,
    RemoveObjectCommand,
    SetActiveGroupCommand,
    ClearHighlightsCommand,
]


class BoardPatch(StrictModel):
    schema_version: int = 1
    base_board_revision: int
    commands: List[BoardCommand] = Field(..., max_length=20)
