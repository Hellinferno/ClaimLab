# Shared Whiteboard Specification

## Product behavior

The board is a structured teaching surface. The agent adds and updates meaningful objects; the student can select an object, answer a connection task, submit a short annotation, or ask for an explanation. Stable identities connect objects to source anchors, concepts, and experiment values.

Freehand strokes are optional saved annotations. The first release does not claim unrestricted handwriting recognition. Keyboard controls provide equivalent supported semantic tasks.

## Scene model

Objects have an ID, type, position, dimensions, accessible label, concept ID, source references when applicable, and a typed content payload. Supported types are `text`, `equation`, `concept_node`, `matrix`, `connector`, `plot_ref`, `group`, and `annotation`.

`plot_ref` references a retained run ID and an allowlisted output field. It cannot contain model-invented series. `equation` holds bounded LaTeX rendered through safe settings. Connectors reference existing object IDs and a labelled relationship.

## Agent command grammar

| Operation | Rule |
| --- | --- |
| `add_object` | ID is unique; type/payload/geometry valid; count remains at most 100 |
| `update_object` | Existing ID; immutable type/identity preserved; only allowed fields change |
| `add_connector` | Endpoints exist and are valid for the current task |
| `highlight_objects` | Existing IDs and a supported emphasis style |
| `remove_object` | Remove or update dependent connectors in the same patch |
| `set_active_group` | Existing group; preserve the rest of the scene |
| `clear_highlights` | Remove presentation emphasis only |

A patch has `schema_version`, `base_board_revision`, and at most 20 commands. Validate the entire patch on a copy before committing it. If any command fails, apply none. Model responses never supply executable markup, script, CSS, or arbitrary attributes.

## Teaching-step relationship

`present_teaching_step` pairs narration, board patch, optional source references, a teaching decision, and at most one active task. The student sees the drawing steps in a meaningful sequence. The authoritative stored board is the final committed patch result; animation is presentation only.

Reduced-motion mode reveals the same content without movement. A browser reload restores the committed scene rather than restarting the full animation.

## Student actions

Selection and dragging are local drafts. A semantic submission sends stable object IDs and the expected session revision. A connect task can use two labelled dropdowns plus an Add connection action as a keyboard alternative. Annotation text has a 1,000-character limit and is treated as data.

The student does not write arbitrary scene state directly to the database. The server validates submissions against the current task and scene. A stale object/task yields a clear refresh state; it must not be interpreted against a different diagram.

## Numerical synchronization

Charts display current run IDs and exact parameter summaries. Editing lab inputs marks earlier output as stale. A new run may produce a new scene reference; old results remain inspectable as prior runs, not silently relabelled.

Matrix cells, axes, labels, and highlighted values derive from the same output JSON. Round display values without changing the stored precision. Provide units or dimension labels and distinguish representative samples from aggregate statistics.

## Layout and accessibility

Fit content to the available pane, with labelled zoom/pan only when necessary. Avoid tiny text by reflowing groups and allowing readable detail views. Preserve contrast and visible focus. Provide text summaries for diagrams and matrices, use labels alongside color, and keep important information available without hover.

KaTeX is rendered with unsafe trusted extensions disabled. Render plain text through framework escaping. Source PDF scripts and attachments are never executed as teaching content.

## Required checks

Atomic rejection, duplicate IDs, dangling connectors, stale bases, excessive objects/commands, malformed LaTeX, malicious text, reduced-motion behavior, keyboard connection tasks, and run-to-chart consistency. Visual polish must not hide failed state validation.
