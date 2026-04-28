import json
from dataclasses import asdict
from pathlib import Path
from typing import Any
from doc.names import get_pascal, get_route
from doc.node import mod_node
from doc.props import get_comp_doc, get_prop_list, get_ref_map
from doc.tokens import get_tok
from doc.walk import get_walk
from domain import GenDoc, PageDoc, RefDoc, TokDoc


def mod_doc(file_doc: dict[str, Any], var_doc: dict[str, Any] | None) -> GenDoc:
    def get_comp_node_list() -> list[dict[str, Any]]:
        return [node for node in get_walk(file_doc.get("document", {})) if node.get("type") == "COMPONENT_SET"]

    def get_prop_by_tag(comp_nodes: list[dict[str, Any]]) -> dict[str, list]:
        return {get_pascal(node.get("name", "Component")): get_prop_list(node) for node in comp_nodes}

    def get_page_list(tok: TokDoc, ref_map: dict[str, RefDoc]) -> list[PageDoc]:
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
                out.append(
                    PageDoc(
                        name=str(child.get("name", "Page")),
                        route=route,
                        root=mod_node(child, tok, ref_map, {}, None),
                    )
                )
        return out

    tok = get_tok(file_doc, var_doc)
    comp_nodes = get_comp_node_list()
    prop_by_tag = get_prop_by_tag(comp_nodes)
    ref_map = get_ref_map(comp_nodes, prop_by_tag)
    return GenDoc(
        key=str(file_doc.get("version", "")),
        name=str(file_doc.get("name", "Figma")),
        tokens=tok,
        comps=[get_comp_doc(node, tok, ref_map, prop_by_tag) for node in comp_nodes],
        pages=get_page_list(tok, ref_map),
    )


def get_doc_data(doc: GenDoc) -> dict[str, object]:
    return asdict(doc)


def add_doc_json(doc: GenDoc, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(get_doc_data(doc), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def mod_test_doc(tmp_path: Path) -> None:
    def get_sample() -> dict[str, object]:
        path = Path(__file__).resolve().parents[1] / "output" / "samples" / "api_response.json"
        return json.loads(path.read_text(encoding="utf-8"))

    doc = mod_doc(get_sample(), None)
    add_doc_json(doc, tmp_path / "doc.json")
    data = json.loads((tmp_path / "doc.json").read_text(encoding="utf-8"))
    assert len(doc.comps) == 3
    assert len(doc.pages) == 1
    assert any(item.tag == "Tab" for item in doc.comps)
    assert any(name.startswith("--figma-color-") for name in doc.tokens.root)
    assert any(name.startswith("--figma-var-") for name in doc.tokens.root)
    assert data["pages"][0]["route"] == doc.pages[0].route
