from __future__ import annotations
from typing import Any
from app.doc_class import get_node_cls
from app.doc_name import get_prop_key
from app.doc_svg import get_svg_node
from app.domain import NodeDoc, RefDoc, TokDoc


def mod_node(
    node: dict[str, Any],
    tok: TokDoc,
    ref_map: dict[str, RefDoc],
    prop_map: dict[str, str],
    parent_mode: str | None,
) -> NodeDoc:
    kind = str(node.get("type", "FRAME"))
    if kind == "INSTANCE":
        ref = ref_map.get(str(node.get("componentId", "")))
        if ref:
            attrs = get_inst_attr(node, ref, tok, parent_mode)
            return NodeDoc(kind=kind, tag="", name=str(node.get("name", "")), comp=ref.tag, attrs=attrs)
    if kind == "TEXT":
        return get_text_node(node, tok, prop_map)
    if kind == "VECTOR":
        return get_svg_node(node, tok, parent_mode)
    children = [
        mod_node(child, tok, ref_map, prop_map, node.get("layoutMode"))
        for child in node.get("children", [])
        if isinstance(child, dict)
    ]
    return NodeDoc(
        kind=kind,
        tag="div",
        name=str(node.get("name", "")),
        classes=get_node_cls(node, tok, parent_mode),
        children=children,
    )


def get_text_node(node: dict[str, Any], tok: TokDoc, prop_map: dict[str, str]) -> NodeDoc:
    ref = node.get("componentPropertyReferences", {}).get("characters")
    return NodeDoc(
        kind="TEXT",
        tag="p",
        name=str(node.get("name", "")),
        classes=get_node_cls(node, tok, None),
        text=str(node.get("characters", "")),
        expr=prop_map.get(str(ref)) if ref else None,
    )


def get_inst_attr(node: dict[str, Any], ref: RefDoc, tok: TokDoc, parent_mode: str | None) -> list[tuple[str, object]]:
    attrs = [
        (ref.prop.get(str(key), get_prop_key(str(key))), val.get("value", ""))
        for key, val in node.get("componentProperties", {}).items()
        if isinstance(val, dict)
    ]
    cls = " ".join(get_node_cls(node, tok, parent_mode))
    if cls:
        attrs.append(("class_name", cls))
    return attrs
