"""Turns a model-authored lesson into paged steps, laid-out board patches, and a keyed check task.

The model chooses what to draw; this module decides where it goes and drops anything
that is not grounded (quotes need a real anchor, plots need a retained run).
"""
import logging
import math
import re
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlparse

from claimlab.contracts.whiteboard import (
    AddConnectorCommand,
    AddObjectCommand,
    BoardObject,
    BoardPatch,
    Dimensions,
    ObjectType,
    Position,
    RemoveObjectCommand,
    SceneGraph,
)
from claimlab.whiteboard.engine import (
    MAX_COMMANDS_PER_PATCH,
    WhiteboardValidationError,
    apply_atomic_patch,
    validate_safe_latex,
    validate_safe_text,
)

logger = logging.getLogger(__name__)

STEP_TAGS = ("source", "background", "web", "experiment", "interpretation", "assumption")
STEP_TEXT_KEYS = ("say", "body", "text", "content", "narration", "explanation", "description", "message")
STEP_TAG_KEYS = ("tag", "epistemic_tag", "epistemic", "type", "kind", "label")
STEP_DRAW_KEYS = ("draw", "board", "board_items", "items", "drawings", "draws", "objects", "visuals", "whiteboard")
STEP_URL_KEYS = ("url", "source_url", "link", "web_url", "citation")
FLAT_ITEM_KEYS = ("kind", "id", "title", "text", "description", "latex", "anchor_id", "run_id", "from", "relation")
# Live models name the same thing many ways; these map their words onto the declared enums.
TAG_SYNONYMS = {
    "observation": "experiment", "measured": "experiment", "measurement": "experiment", "experimental": "experiment",
    "result": "experiment", "results": "experiment", "paper": "source", "quote": "source", "citation": "source",
    "inference": "interpretation", "general": "background", "context": "background", "website": "web",
    "online": "web", "internet": "web", "web_source": "web",
}
KIND_SYNONYMS = {
    "concept_node": "concept", "node": "concept", "box": "concept", "card": "concept", "formula": "equation",
    "math": "equation", "latex": "equation", "chart": "plot", "graph": "plot", "plot_ref": "plot", "text": "note",
    "callout": "note", "source_quote": "quote", "citation": "quote",
}


def step_tag(raw: Dict[str, Any]) -> Optional[str]:
    for key in STEP_TAG_KEYS:
        value = str(raw.get(key) or "").strip().lower()
        value = TAG_SYNONYMS.get(value, value)
        if value in STEP_TAGS:
            return value
    return None


def step_items(raw: Dict[str, Any]) -> List[Dict[str, Any]]:
    """The board items of a step, under whichever key the model used."""
    for key in STEP_DRAW_KEYS:
        value = raw.get(key)
        value = [value] if isinstance(value, dict) else value
        if isinstance(value, list) and any(isinstance(item, dict) for item in value):
            return [item for item in value if isinstance(item, dict)]
    if raw.get("kind") or raw.get("latex") or raw.get("run_id"):
        # Flattened (observed live): the step itself carries one item's fields beside its prose.
        return [{key: raw[key] for key in FLAT_ITEM_KEYS if key in raw}]
    return []


def step_prose(value: Any) -> str:
    """Step text as models send it: a string, a list of sentences or bullets, or an object wrapping either."""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return "\n".join(text for text in map(step_prose, value) if text)
    if isinstance(value, dict):
        return next((text for key in STEP_TEXT_KEYS if (text := step_prose(value.get(key)))), "")
    return ""


def comparable_url(url: Any) -> str:
    parsed = urlparse(str(url or "").strip())
    if parsed.scheme not in ("http", "https"):
        return ""
    return f"{parsed.netloc.lower().removeprefix('www.')}{parsed.path.rstrip('/')}" + (f"?{parsed.query}" if parsed.query else "")
INLINE_CHOICE = re.compile(r"(?:^|\s)\(?([A-F])[).:]\s+(.+?)(?=\s+\(?[A-F][).:]\s|$)")
MAX_STEPS = 6
MAX_DRAW_PER_STEP = 4
MAX_TUTOR_OBJECTS = 36

BOARD_WIDTH = 780
MARGIN = 20
# Room between cards for arrows and their short labels.
GAP_X = 36
GAP_Y = 44
ITEM_SIZES = {
    "concept": (220, 96),
    "note": (220, 112),
    "quote": (360, 128),
    "equation": (360, 92),
    "plot": (740, 290),
}
# Retained output field each run kind draws from.
PLOT_FIELDS = {
    "attention_scaling_v1": "results",
    "softmax_sensitivity_v1": "scaled_probabilities",
    "causal_masking_v1": "masked_weights",
    "sandbox_python_v1": "series",
}


def clip(text: Any, limit: int) -> str:
    value = re.sub(r"\s+", " ", str(text or "")).strip()
    return value if len(value) <= limit else value[: limit - 1].rstrip() + "…"


def slug(text: Any, limit: int = 40) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", str(text or "").lower()).strip("-")
    return value[:limit].strip("-") or "item"


TAG_PATTERN = r"\[(Source|Background|Web|Experiment|Interpretation|Assumption|Observation)\]"
TAG_TITLES = {
    "source": "From the source",
    "background": "Background",
    "web": "From the web",
    "experiment": "What the experiment shows",
    "observation": "What the experiment shows",
    "interpretation": "What it means",
    "assumption": "An assumption",
}


def paginate_text(text: str, max_pages: int = 5) -> List[Dict[str, Any]]:
    """Split a plain reply into short pages so even unstructured replies read step by step.

    Headings and [Tag] lines start pages; long runs of paragraphs are split near 420 characters.
    """
    # Non-capturing split: re.split would otherwise return the captured tag names as blocks.
    split_before_tag = TAG_PATTERN.replace("(", "(?:")
    blocks = [b.strip() for b in re.split(rf"\n\s*\n|\n(?={split_before_tag})", text or "", flags=re.I) if b.strip()]
    pages: List[Dict[str, Any]] = []
    for block in blocks:
        heading = re.match(r"^#{1,4}\s+(.*)", block)
        tag = re.match(rf"^{TAG_PATTERN}\s*", block, re.I)
        if heading:
            block = block[heading.end():].strip()
        elif tag:
            block = block[tag.end():]
        too_long = bool(pages) and sum(len(b) for b in pages[-1]["blocks"]) + len(block) > 420
        if (heading or tag or not pages or too_long) and len(pages) < max_pages:
            pages.append({"heading": heading.group(1) if heading else None,
                          "tag": tag.group(1).lower() if tag else None, "blocks": []})
        if block:
            pages[-1]["blocks"].append(block)
    steps = []
    for index, page in enumerate(pages):
        tag = page["tag"] or "background"
        title = page["heading"] or (TAG_TITLES[page["tag"]] if page["tag"] else "Where we are" if index == 0 else f"Step {index + 1}")
        steps.append({
            "title": clip(title, 80),
            "body": "\n\n".join(page["blocks"]),
            "tag": "experiment" if tag == "observation" else tag,
            "object_ids": [],
        })
    return [s for s in steps if s["body"]]


def verbatim_excerpt(anchor_text: str, wanted: Any) -> Optional[str]:
    """The tutor's quote when every fragment of it appears in the anchor, in order; else None.

    Matching ignores case and whitespace (PDF line breaks); "..." separates elided fragments.
    Without a requested quote, a short anchor is shown whole and a long one is refused.
    """
    def norm(value: str) -> str:
        return re.sub(r"\s+", " ", value).strip().lower()

    if not str(wanted or "").strip():
        return anchor_text if len(anchor_text) <= 300 else None
    haystack, position = norm(anchor_text), 0
    for fragment in (norm(f) for f in re.split(r"\.\.\.|…", str(wanted))):
        if not fragment:
            continue
        found = haystack.find(fragment, position)
        if found < 0:
            return None
        position = found + len(fragment)
    return re.sub(r"\s+", " ", str(wanted)).strip()


def narration_from_steps(steps: List[Dict[str, Any]]) -> str:
    """Plain-text record of a paged lesson, one tagged line per step."""
    return "\n".join(f"[{s['tag'].title()}] {s['title']}: {s['body']}" for s in steps)


def board_bottom(objects: Iterable[BoardObject]) -> float:
    shapes = [o for o in objects if o.type != ObjectType.CONNECTOR]
    return max((o.position.y + o.dimensions.height for o in shapes), default=0.0)


def apply_commands(scene: SceneGraph, commands: List[Any]) -> SceneGraph:
    """Apply commands in engine-sized atomic chunks; an invalid chunk is skipped, never half-applied."""
    for start in range(0, len(commands), MAX_COMMANDS_PER_PATCH):
        chunk = commands[start:start + MAX_COMMANDS_PER_PATCH]
        try:
            scene = apply_atomic_patch(scene, BoardPatch(schema_version=1, base_board_revision=scene.board_revision, commands=chunk))
        except Exception as exc:
            logger.warning("Skipped invalid lesson board patch: %s", exc)
    return scene


class FlowLayout:
    """Left-to-right rows below the existing drawing; plots take a full row."""

    def __init__(self, top: float):
        self.x, self.y, self.row_height = MARGIN, top, 0.0

    def _new_row(self) -> None:
        if self.x > MARGIN:
            self.y += self.row_height + GAP_Y
            self.x, self.row_height = MARGIN, 0.0

    def place(self, kind: str) -> Tuple[Position, Dimensions]:
        width, height = ITEM_SIZES[kind]
        if kind == "plot" or self.x + width > BOARD_WIDTH - MARGIN + 1:
            self._new_row()
        position = Position(x=self.x, y=self.y)
        self.x += width + GAP_X
        self.row_height = max(self.row_height, height)
        if kind == "plot":
            self._new_row()
        return position, Dimensions(width=width, height=height)


def build_lesson(
    args: Dict[str, Any],
    scene: SceneGraph,
    anchors: Dict[str, str],
    runs: Dict[str, str],
    turn: str,
    auto_plot_run: Optional[str] = None,
    allowed_urls: Iterable[str] = (),
) -> Tuple[SceneGraph, List[Dict[str, Any]]]:
    """Lay out the lesson's drawings and return the new scene with its paged steps.

    anchors maps anchor id -> quote; runs maps retained run id -> recipe id for this session;
    allowed_urls are pages web research actually returned, the only ones a step may cite.
    """
    # Cited and fetched forms of a URL differ in trivia (scheme, www, trailing slash); match on the rest.
    citable = {comparable_url(url): url for url in allowed_urls if comparable_url(url)}
    raw_steps = [s for s in (args.get("steps") or []) if isinstance(s, dict)][:MAX_STEPS]
    commands: List[Any] = []
    if args.get("board_mode", "new") != "extend":
        scene = apply_commands(scene, [RemoveObjectCommand(object_id=o.id) for o in scene.objects
                                       if o.type != ObjectType.CONNECTOR and o.payload.get("author") == "tutor"])
    remaining = list(scene.objects)
    room = MAX_TUTOR_OBJECTS - sum(1 for o in remaining if o.payload.get("author") == "tutor")
    layout = FlowLayout(top=board_bottom(remaining) + (34 if remaining else 20))
    known_ids = {o.id for o in remaining}
    alias: Dict[str, str] = {}
    plotted_runs = set()
    steps: List[Dict[str, Any]] = []
    connectors: List[AddConnectorCommand] = []

    for index, raw in enumerate(raw_steps):
        items = step_items(raw)
        tag = step_tag(raw)
        if tag is None:
            # Untagged: a cited anchor is a source statement, a drawn run is a measurement.
            tag = ("source" if raw.get("anchor_id") in anchors else
                   "experiment" if any(_item_kind(d) == "plot" for d in items) else "background")
        # Models drift from "say"; any of these carries the step's prose.
        body = next((text for key in STEP_TEXT_KEYS if (text := step_prose(raw.get(key)))), "")
        if not body:
            # Live turns sent title-only steps; the step's own board items still say what it teaches.
            body = "\n".join(f"- **{clip(item.get('title') or item.get('label'), 60)}**: {clip(item.get('text') or item.get('description'), 160)}"
                             for item in items if _item_kind(item) in ("concept", "note") and (item.get("text") or item.get("description")))
        if not body or not items:
            # Shape only, never content: shows the next schema drift instead of silently losing it.
            logger.warning("Lesson step without %s (keys=%s, text types=%s)", "prose" if not body else "drawings", sorted(raw),
                           {key: type(raw[key]).__name__ for key in STEP_TEXT_KEYS if key in raw})
        step = {
            "title": clip(raw.get("title") or f"Step {index + 1}", 80),
            "body": body[:1500],
            "tag": tag,
            "object_ids": [],
        }
        if raw.get("anchor_id") in anchors:
            step["anchor_id"] = raw["anchor_id"]
        cited = next((citable[comparable_url(raw[key])] for key in STEP_URL_KEYS if comparable_url(raw.get(key)) in citable), None)
        if cited:
            step["url"] = cited
            if tag == "background":
                step["tag"] = "web"
        elif tag == "web":
            # An uncited web claim is general background, not a sourced statement.
            step["tag"] = "background"

        for item in items[:MAX_DRAW_PER_STEP]:
            if room <= 0:
                break
            obj = _board_object(item, index, turn, anchors, runs)
            if obj is None:
                continue
            base_id = obj.id
            suffix = 2
            while obj.id in known_ids:
                obj.id = f"{base_id[:56]}-{suffix}"
                suffix += 1
            kind = obj.payload["kind"]
            obj.position, obj.dimensions = layout.place(kind)
            known_ids.add(obj.id)
            alias[str(item.get("id") or "")] = obj.id
            alias.setdefault(slug(item.get("title")), obj.id)
            if kind == "plot":
                plotted_runs.add(obj.payload["run_id"])
            commands.append(AddObjectCommand(object=obj))
            step["object_ids"].append(obj.id)
            room -= 1
            source = str(item.get("from") or "")
            if source:
                connectors.append(AddConnectorCommand(
                    connector_id=f"c-{turn}-{len(connectors) + 1}",
                    from_object_id=alias.get(source, source),
                    to_object_id=obj.id,
                    relationship=clip(item.get("relation") or "leads to", 40),
                ))
        for focus in raw.get("focus") or []:
            target = alias.get(str(focus), str(focus))
            if target in known_ids and target not in step["object_ids"]:
                step["object_ids"].append(target)
        if step["body"] or step["object_ids"]:
            steps.append(step)

    # A run the tutor measured this turn belongs on the board even if it forgot to draw it.
    if auto_plot_run and auto_plot_run not in plotted_runs and steps and room > 0:
        obj = _board_object({"kind": "plot", "run_id": auto_plot_run, "title": "Measured result"}, 0, turn, anchors, runs)
        if obj:
            target = next((s for s in steps if s["tag"] == "experiment"), steps[-1])
            obj.payload["step"] = steps.index(target)
            obj.position, obj.dimensions = layout.place("plot")
            commands.append(AddObjectCommand(object=obj))
            target["object_ids"].append(obj.id)

    valid_ids = known_ids | {c.object.id for c in commands if isinstance(c, AddObjectCommand)}
    commands += [c for c in connectors if c.from_object_id in valid_ids and c.from_object_id != c.to_object_id]
    return apply_commands(scene, commands), steps


def _item_kind(item: Dict[str, Any]) -> str:
    kind = str(item.get("kind") or item.get("type") or "note").strip().lower()
    return KIND_SYNONYMS.get(kind, kind)


def _board_object(item: Dict[str, Any], step: int, turn: str, anchors: Dict[str, str], runs: Dict[str, str]) -> Optional[BoardObject]:
    kind = _item_kind(item)
    title = clip(item.get("title") or item.get("label") or item.get("name") or item.get("heading") or "", 80)
    item = {**item, "text": item.get("text") or item.get("description") or item.get("content") or item.get("detail") or ""}
    text = clip(item["text"], 180)
    payload: Dict[str, Any] = {"author": "tutor", "turn": turn, "step": step, "kind": kind}
    source_refs: List[str] = []
    if kind == "concept":
        obj_type = ObjectType.CONCEPT_NODE
        payload.update(title=title or "Concept", description=clip(text, 140))
    elif kind == "equation":
        latex = str(item.get("latex") or item.get("text") or "").strip().strip("$").strip()
        if not latex or len(latex) > 400:
            return None
        obj_type = ObjectType.EQUATION
        payload["latex"] = latex
    elif kind == "quote":
        anchor_id = str(item.get("anchor_id") or "")
        if anchor_id not in anchors:
            logger.warning("Dropped quote without a valid source anchor")
            return None
        excerpt = verbatim_excerpt(anchors[anchor_id], item.get("text"))
        if excerpt is None:
            logger.warning("Dropped quote that is not verbatim in its anchor")
            return None
        obj_type = ObjectType.TEXT
        payload.update(text=clip(excerpt, 230), anchor_id=anchor_id)
        source_refs = [anchor_id]
        title = title or "From the source"
    elif kind == "plot":
        run_id = str(item.get("run_id") or "")
        if run_id not in runs:
            logger.warning("Dropped plot without a retained run")
            return None
        obj_type = ObjectType.PLOT_REF
        payload.update(run_id=run_id, field=PLOT_FIELDS.get(runs[run_id], "series"), title=title or "Measured result")
    else:
        kind = payload["kind"] = "note"
        if not (title or text):
            return None
        obj_type = ObjectType.TEXT
        payload["text"] = text
    try:
        # Reject unsafe items one by one so a single bad formula cannot void a whole patch.
        validate_safe_text(title, "label")
        validate_safe_text(str(payload.get("text") or payload.get("description") or ""), "text")
        if obj_type == ObjectType.EQUATION:
            validate_safe_latex(payload["latex"])
    except WhiteboardValidationError as exc:
        logger.warning("Dropped unsafe board item: %s", exc)
        return None
    return BoardObject(
        id=f"t-{slug(item.get('id') or title, 30)}",
        type=obj_type,
        position=Position(x=0, y=0),
        dimensions=Dimensions(width=1, height=1),
        label=title or clip(text, 60) or kind.title(),
        concept_id=slug(item.get("concept_id"), 48).replace("-", "_") if item.get("concept_id") else None,
        source_refs=source_refs,
        payload=payload,
    )


# --- Check questions authored by the tutor (graded against a private key) ---

def build_check(check: Any, revision: int) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Public task and its private answer key; the key never reaches the learner's browser."""
    if not isinstance(check, dict) or not str(check.get("question") or "").strip():
        return None, None
    answer_type = str(check.get("answer_type") or "text").lower()
    answer = check.get("answer")
    question = str(check["question"])
    # The UI letters nothing, so "A) ..." prefixes the model adds are dropped.
    choices = [clip(re.sub(r"^\s*\(?[A-Fa-f][).:]\s+", "", str(c)), 120) for c in (check.get("choices") or []) if str(c).strip()][:6]
    inline = INLINE_CHOICE.findall(question)
    if not choices and len(inline) >= 2 and [letter for letter, _ in inline] == list("ABCDEF"[:len(inline)]):
        # Options written into the question ("A) ... B) ...") become real choices.
        choices = [clip(text, 120) for _, text in inline][:6]
        question = question[:INLINE_CHOICE.search(question).start()].strip()
        answer_type = "choice" if answer_type in ("choice", "text") else answer_type
    if answer_type == "number":
        number = _first_number(answer)
        if number is None:
            answer_type = "text"
        else:
            answer = number
    if answer_type == "choice":
        unlettered = re.sub(r"^\s*\(?[A-Fa-f][).:]\s*", "", str(answer or ""))
        match = next((c for c in choices if _norm(c) in (_norm(answer), _norm(unlettered))), None)
        index = _letter_index(answer)
        if match is None and index is not None and index < len(choices):
            match = choices[index]
        if len(choices) < 2 or match is None:
            answer_type = "text"
        answer = match
    if answer_type not in ("number", "choice", "text"):
        answer_type = "text"
    concept = slug(check.get("concept_id") or check.get("concept") or "core idea", 48).replace("-", "_")
    public = {
        "task_id": f"open-{concept.replace('_', '-')}"[:64],
        "task_variant": f"r{revision}",
        "question": clip(question, 400),
        "expected_type": answer_type,
    }
    if answer_type == "choice":
        public["choices"] = choices
    tolerance = check.get("tolerance")
    key = {
        "answer_type": answer_type,
        "answer": answer if answer_type != "text" else clip(answer or "", 400),
        "choices": choices if answer_type == "choice" else [],
        "tolerance": float(tolerance) if isinstance(tolerance, (int, float)) and tolerance >= 0 else None,
        "key_points": [clip(p, 200) for p in (check.get("key_points") or []) if str(p).strip()][:5],
        "concept_id": concept,
        "concept_label": clip(check.get("concept_label") or concept.replace("_", " "), 60),
    }
    return public, key


def grade_open_answer(key: Dict[str, Any], answer: Any) -> Optional[bool]:
    """Deterministic verdict for number and choice checks; None means the tutor must assess it."""
    if key.get("answer_type") == "number":
        value, expected = _first_number(answer), key.get("answer")
        if value is None or not isinstance(expected, (int, float)):
            return False
        tolerance = key.get("tolerance")
        tolerance = tolerance if tolerance is not None else max(1e-6, 0.02 * abs(expected))
        return math.isclose(value, expected, abs_tol=tolerance)
    if key.get("answer_type") == "choice":
        choices, index = key.get("choices") or [], _letter_index(answer)
        if index is not None and index < len(choices):
            answer = choices[index]
        return _norm(answer) == _norm(key.get("answer"))
    return None


def _first_number(value: Any) -> Optional[float]:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value) if math.isfinite(value) else None
    match = re.search(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?", str(value or "").replace(",", ""))
    return float(match.group()) if match else None


def _norm(value: Any) -> str:
    return re.sub(r"[^a-z0-9.]+", " ", str(value or "").lower()).strip()


def _letter_index(value: Any) -> Optional[int]:
    text = str(value or "").strip().lower().rstrip(").")
    return ord(text) - ord("a") if len(text) == 1 and "a" <= text <= "f" else None
