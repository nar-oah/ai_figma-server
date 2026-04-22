from typing import Any
from doc.classes import get_node_cls
from doc.names import get_prop_key
from doc.svg import get_svg_node
from domain import NodeDoc, RefDoc, TokDoc


def mod_node(
    node: dict[str, Any],
    tok: TokDoc,
    ref_map: dict[str, RefDoc],
    prop_map: dict[str, str],
    parent_mode: str | None,
) -> NodeDoc:
    def get_text_node() -> NodeDoc:
        ref = node.get("componentPropertyReferences", {}).get("characters")
        return NodeDoc(
            kind="TEXT",
            tag="p",
            name=str(node.get("name", "")),
            classes=get_node_cls(node, tok, None),
            text=str(node.get("characters", "")),
            expr=prop_map.get(str(ref)) if ref else None,
        )

    def get_inst_attr(ref: RefDoc) -> list[tuple[str, object]]:
        attrs = [
            (ref.prop.get(str(key), get_prop_key(str(key))), val.get("value", ""))
            for key, val in node.get("componentProperties", {}).items()
            if isinstance(val, dict)
        ]
        cls = " ".join(get_node_cls(node, tok, parent_mode))
        if cls:
            attrs.append(("class_name", cls))
        return attrs

    kind = str(node.get("type", "FRAME"))
    if kind == "INSTANCE":
        ref = ref_map.get(str(node.get("componentId", "")))
        if ref:
            attrs = get_inst_attr(ref)
            return NodeDoc(kind=kind, tag="", name=str(node.get("name", "")), comp=ref.tag, attrs=attrs)
    if kind == "TEXT":
        return get_text_node()
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
