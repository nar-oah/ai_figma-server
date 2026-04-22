from __future__ import annotations
from typing import Any
from app.doc_class_layout import get_axis_cls, get_gap_cls, get_grow_cls, get_pad_cls, get_size_cls
from app.doc_class_style import get_box_cls, get_rotate_cls, get_text_cls
from app.doc_name import get_clean_cls
from app.domain import TokDoc


def get_node_cls(node: dict[str, Any], tok: TokDoc, parent_mode: str | None) -> list[str]:
    out: list[str] = []
    kind = str(node.get("type", "FRAME"))
    mode = node.get("layoutMode")
    if mode == "HORIZONTAL":
        out.extend(["flex", "flex-row"])
    if mode == "VERTICAL":
        out.extend(["flex", "flex-col"])
    if mode:
        out.extend(get_axis_cls(node))
        out.extend(get_gap_cls(node, tok))
        out.extend(get_pad_cls(node, tok))
    if node.get("clipsContent"):
        out.append("overflow-hidden")
    out.extend(get_size_cls(node, tok, parent_mode))
    out.extend(get_grow_cls(node, parent_mode))
    out.extend(get_box_cls(node, tok))
    out.extend(get_text_cls(node, tok))
    rot = get_rotate_cls(node)
    if rot:
        out.append(rot)
    if kind in {"TEXT", "VECTOR", "RECTANGLE", "ELLIPSE"}:
        out.append("shrink-0")
    return get_clean_cls(out)
