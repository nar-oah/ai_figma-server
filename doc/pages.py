from typing import Any
from doc.names import get_route
from doc.node import mod_node
from domain import PageDoc, RefDoc, TokDoc


def get_page_list(
    file_doc: dict[str, Any],
    tok: TokDoc,
    ref_map: dict[str, RefDoc],
) -> list[PageDoc]:
    used: set[str] = set()
    out: list[PageDoc] = []
    for canvas in file_doc.get("document", {}).get("children", []):
        if not isinstance(canvas, dict) or canvas.get("type") != "CANVAS":
            continue
        if get_has_component_set(canvas):
            continue
        for child in canvas.get("children", []):
            if isinstance(child, dict):
                out.append(get_page_doc(child, tok, ref_map, used))
    return out


def get_has_component_set(canvas: dict[str, Any]) -> bool:
    return any(
        child.get("type") == "COMPONENT_SET"
        for child in canvas.get("children", [])
        if isinstance(child, dict)
    )


def get_page_doc(
    child: dict[str, Any],
    tok: TokDoc,
    ref_map: dict[str, RefDoc],
    used: set[str],
) -> PageDoc:
    route = get_route(str(child.get("name", "page")), str(child.get("id", "")), used)
    return PageDoc(
        name=str(child.get("name", "Page")),
        route=route,
        root=mod_node(child, tok, ref_map, {}, None),
    )
