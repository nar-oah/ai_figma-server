import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from doc.names import get_pascal, get_route
from doc.node import mod_node
from doc.props import get_comp_doc, get_ref_map
from doc.props import get_prop_list
from doc.tokens import get_tok
from doc.walk import get_walk
from domain import GenDoc, PageDoc, PropDoc, RefDoc, TokDoc


def mod_doc(file_doc: dict[str, Any], token_doc: dict[str, Any] | None = None) -> GenDoc:
    tok = get_tok(file_doc, token_doc)
    comp_nodes = get_comp_node_list(file_doc)
    prop_by_tag = get_prop_by_tag(comp_nodes)
    ref_map = get_ref_map(comp_nodes, prop_by_tag)
    return GenDoc(
        key=str(file_doc.get("version", "")),
        name=str(file_doc.get("name", "Figma")),
        tokens=tok,
        comps=[get_comp_doc(file_doc, node, tok, ref_map, prop_by_tag) for node in comp_nodes],
        pages=get_page_list(file_doc, tok, ref_map),
    )


def get_doc_data(doc: GenDoc) -> dict[str, object]:
    return asdict(doc)


def add_doc_json(doc: GenDoc, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(get_doc_data(doc), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def get_comp_node_list(file_doc: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        node
        for node in get_walk(file_doc.get("document", {}))
        if node.get("type") == "COMPONENT_SET"
    ]


def get_prop_by_tag(comp_nodes: list[dict[str, Any]]) -> dict[str, list[PropDoc]]:
    return {
        get_pascal(node.get("name", "Component")): get_prop_list(node)
        for node in comp_nodes
    }


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
        if any(
            child.get("type") == "COMPONENT_SET"
            for child in canvas.get("children", [])
            if isinstance(child, dict)
        ):
            continue
        for child in canvas.get("children", []):
            if not isinstance(child, dict):
                continue
            route = get_route(str(child.get("name", "page")), str(child.get("id", "")), used)
            out.append(
                PageDoc(
                    name=str(child.get("name", "Page")),
                    route=route,
                    root=mod_node(child, tok, ref_map, {}, None),
                )
            )
    return out


if __name__ == "__main__":

    def get_sample() -> dict[str, object]:
        path = Path(__file__).resolve().parents[1] / "output" / "samples" / "api_response.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def get_sample_tokens() -> dict[str, object]:
        path = Path(__file__).resolve().parents[1] / "Mode 1.tokens.json"
        return json.loads(path.read_text(encoding="utf-8"))

    doc = mod_doc(get_sample(), get_sample_tokens())
    path = Path("output/doc.json")
    add_doc_json(doc, path)
    print(path)
