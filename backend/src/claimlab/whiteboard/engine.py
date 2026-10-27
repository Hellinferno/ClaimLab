"""Atomic Whiteboard Patch Engine ensuring scene graph invariants and safe rendering."""
import copy
import re
from typing import Dict, List, Optional

from claimlab.contracts.whiteboard import (
    BoardObject,
    BoardPatch,
    ObjectType,
    Position,
    Dimensions,
    SceneGraph,
)

MAX_BOARD_OBJECTS = 100
MAX_COMMANDS_PER_PATCH = 20
MAX_LABEL_LENGTH = 500

UNSAFE_LATEX_PATTERNS = [
    r"\\write",
    r"\\immediate",
    r"\\input",
    r"\\include",
    r"\\catcode",
    r"\\def",
    r"\\let",
    r"\\url",
    r"\\href",
    r"<script",
    r"javascript:",
    r"onerror",
    r"onload",
]


class WhiteboardValidationError(ValueError):
    """Raised when an atomic board patch fails validation."""
    pass


def validate_safe_text(text: str, field_name: str = "text") -> None:
    if len(text) > MAX_LABEL_LENGTH:
        raise WhiteboardValidationError(f"{field_name} exceeds max length of {MAX_LABEL_LENGTH} chars")
    # Check for script injection
    lower = text.lower()
    if "<script" in lower or "javascript:" in lower:
        raise WhiteboardValidationError(f"Forbidden markup pattern in {field_name}")


def validate_safe_latex(latex: str) -> None:
    if len(latex) > 2000:
        raise WhiteboardValidationError("LaTeX string exceeds maximum length of 2000 chars")
    lower = latex.lower()
    for pattern in UNSAFE_LATEX_PATTERNS:
        if re.search(pattern, lower):
            raise WhiteboardValidationError(f"Forbidden LaTeX or HTML injection pattern: {pattern}")


def apply_atomic_patch(current_scene: SceneGraph, patch: BoardPatch) -> SceneGraph:
    """
    Validates and applies an atomic patch of commands to a SceneGraph.
    If ANY command fails validation, no changes are committed (atomic guarantee).
    """
    if patch.base_board_revision != current_scene.board_revision:
        raise WhiteboardValidationError(
            f"Stale base revision: patch expects {patch.base_board_revision}, but current is {current_scene.board_revision}"
        )

    if len(patch.commands) > MAX_COMMANDS_PER_PATCH:
        raise WhiteboardValidationError(
            f"Patch exceeds maximum of {MAX_COMMANDS_PER_PATCH} commands (received {len(patch.commands)})"
        )

    # Work on a deep copy to ensure atomicity
    working_objects: List[BoardObject] = copy.deepcopy(current_scene.objects)
    active_group: Optional[str] = current_scene.active_group

    def get_obj_map() -> Dict[str, BoardObject]:
        return {obj.id: obj for obj in working_objects}

    for cmd in patch.commands:
        op = cmd.op
        obj_map = get_obj_map()

        if op == "add_object":
            new_obj = cmd.object
            if new_obj.id in obj_map:
                raise WhiteboardValidationError(f"Duplicate object ID: '{new_obj.id}' already exists")
            if len(working_objects) >= MAX_BOARD_OBJECTS:
                raise WhiteboardValidationError(f"Scene cannot exceed {MAX_BOARD_OBJECTS} objects")

            validate_safe_text(new_obj.label, "label")
            if new_obj.type == ObjectType.EQUATION:
                latex = new_obj.payload.get("latex", "")
                validate_safe_latex(latex)

            working_objects.append(new_obj)

        elif op == "update_object":
            if cmd.object_id not in obj_map:
                raise WhiteboardValidationError(f"Cannot update non-existent object '{cmd.object_id}'")
            target = obj_map[cmd.object_id]

            if cmd.position is not None:
                target.position = cmd.position
            if cmd.dimensions is not None:
                target.dimensions = cmd.dimensions
            if cmd.label is not None:
                validate_safe_text(cmd.label, "label")
                target.label = cmd.label
            if cmd.concept_id is not None:
                target.concept_id = cmd.concept_id
            if cmd.payload is not None:
                if target.type == ObjectType.EQUATION and "latex" in cmd.payload:
                    validate_safe_latex(cmd.payload["latex"])
                target.payload = {**target.payload, **cmd.payload}

        elif op == "add_connector":
            if cmd.connector_id in obj_map:
                raise WhiteboardValidationError(f"Duplicate connector ID '{cmd.connector_id}'")
            if cmd.from_object_id not in obj_map:
                raise WhiteboardValidationError(f"Connector endpoint 'from_object_id' '{cmd.from_object_id}' not found")
            if cmd.to_object_id not in obj_map:
                raise WhiteboardValidationError(f"Connector endpoint 'to_object_id' '{cmd.to_object_id}' not found")
            if len(working_objects) >= MAX_BOARD_OBJECTS:
                raise WhiteboardValidationError(f"Scene cannot exceed {MAX_BOARD_OBJECTS} objects")

            conn_obj = BoardObject(
                id=cmd.connector_id,
                type=ObjectType.CONNECTOR,
                position=Position(x=0, y=0),
                dimensions=Dimensions(width=0, height=0),
                label=cmd.label or cmd.relationship,
                payload={
                    "from_object_id": cmd.from_object_id,
                    "to_object_id": cmd.to_object_id,
                    "relationship": cmd.relationship,
                },
            )
            working_objects.append(conn_obj)

        elif op == "highlight_objects":
            for oid in cmd.object_ids:
                if oid not in obj_map:
                    raise WhiteboardValidationError(f"Cannot highlight non-existent object '{oid}'")
                obj_map[oid].highlight_style = cmd.style

        elif op == "clear_highlights":
            for obj in working_objects:
                obj.highlight_style = None

        elif op == "set_active_group":
            if cmd.group_id is not None and cmd.group_id not in obj_map:
                raise WhiteboardValidationError(f"Group ID '{cmd.group_id}' does not exist")
            active_group = cmd.group_id

        elif op == "remove_object":
            if cmd.object_id not in obj_map:
                raise WhiteboardValidationError(f"Cannot remove non-existent object '{cmd.object_id}'")

            # Remove object and cascade remove any connectors that connected to/from it
            working_objects = [
                obj for obj in working_objects
                if obj.id != cmd.object_id and not (
                    obj.type == ObjectType.CONNECTOR
                    and (
                        obj.payload.get("from_object_id") == cmd.object_id
                        or obj.payload.get("to_object_id") == cmd.object_id
                    )
                )
            ]

    # Return new validated SceneGraph
    return SceneGraph(
        schema_version=current_scene.schema_version,
        board_revision=current_scene.board_revision + 1,
        objects=working_objects,
        active_group=active_group,
    )
