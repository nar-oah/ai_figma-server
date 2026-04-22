from __future__ import annotations
from collections.abc import Iterable
from typing import Any
from app.doc_node import mod_node
from app.doc_prop import get_comp_doc, get_prop_list, get_ref_map
from app.doc_token import get_tok
from app.doc_name import get_pascal, get_route
from app.doc_walk import get_walk
from app.domain import GenDoc, PageDoc, RefDoc, TokDoc


def mod_doc(file_doc: dict[str, Any], var_doc: dict[str, Any] | None) -> GenDoc:
    tok = get_tok(file_doc, var_doc)
    comp_nodes = list(get_comp_node_list(file_doc))
    prop_by_tag = {get_pascal(node.get("name", "Component")): get_prop_list(node) for node in comp_nodes}
    ref_map = get_ref_map(comp_nodes, prop_by_tag)
    return GenDoc(
        key=str(file_doc.get("version", "")),
        name=str(file_doc.get("name", "Figma")),
        tokens=tok,
        comps=[get_comp_doc(node, tok, ref_map, prop_by_tag) for node in comp_nodes],
        pages=get_page_list(file_doc, tok, ref_map),
    )


def get_comp_node_list(file_doc: dict[str, Any]) -> Iterable[dict[str, Any]]:
    return (node for node in get_walk(file_doc.get("document", {})) if node.get("type") == "COMPONENT_SET")


def get_page_list(file_doc: dict[str, Any], tok: TokDoc, ref_map: dict[str, RefDoc]) -> list[PageDoc]:
    used: set[str] = set()
    out: list[PageDoc] = []
    for canvas in file_doc.get("document", {}).get("children", []):
        if not isinstance(canvas, dict) or canvas.get("type") != "CANVAS":
            continue
        if any(child.get("type") == "COMPONENT_SET" for child in canvas.get("children", []) if isinstance(child, dict)):
            continue
        for child in canvas.get("children", []):
            if not isinstance(child, dict):
                continue
            route = get_route(str(child.get("name", "page")), str(child.get("id", "")), used)
            out.append(PageDoc(name=str(child.get("name", "Page")), route=route, root=mod_node(child, tok, ref_map, {}, None)))
    return out
