import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from doc.tokens import TokRefs, get_tok
from domain import BoxNode, CompDoc, CompNode, Flex, GenDoc, TextNode


def mod_doc(file_doc: dict[str, Any], token_doc: dict[str, Any] | None = None) -> GenDoc:
    tokens, refs = get_tok(file_doc, token_doc)
    comps = get_comps(file_doc, refs)
    return GenDoc(tokens=tokens, comps=comps, pages=get_pages(file_doc, refs, comps))


def get_doc_data(doc: GenDoc) -> dict[str, object]:
    return asdict(doc)


def add_doc_json(doc: GenDoc, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(get_doc_data(doc), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def get_comps(file_doc: dict[str, Any], refs: TokRefs) -> dict[str, CompDoc]:
    out: dict[str, CompDoc] = {}
    for node in walk(file_doc.get("document", {})):
        if node.get("type") != "COMPONENT_SET":
            continue
        name = str(node.get("name", "Component"))
        prop_map = get_prop_map(node)
        out[name] = CompDoc(
            props=get_props(node),
            roots={
                str(child.get("name", "")): [get_node(child, refs, prop_map, {})]
                for child in node.get("children", [])
                if isinstance(child, dict)
            },
            description=get_comp_desc(file_doc, node),
        )
    return out


def get_pages(
    file_doc: dict[str, Any],
    refs: TokRefs,
    comps: dict[str, CompDoc],
) -> dict[str, list[TextNode | BoxNode | CompNode]]:
    comp_names = set(comps)
    out: dict[str, list[TextNode | BoxNode | CompNode]] = {}
    for canvas in file_doc.get("document", {}).get("children", []):
        if not isinstance(canvas, dict) or canvas.get("type") != "CANVAS":
            continue
        if any(child.get("name") in comp_names for child in canvas.get("children", []) if isinstance(child, dict)):
            continue
        out.update(
            {
                str(child.get("name", "Page")): [get_node(child, refs, {}, get_ref_map(file_doc))]
                for child in canvas.get("children", [])
                if isinstance(child, dict)
            }
        )
    return out


def get_node(
    node: dict[str, Any],
    refs: TokRefs,
    prop_map: dict[str, str],
    comp_refs: dict[str, str],
) -> TextNode | BoxNode | CompNode:
    if node.get("type") == "INSTANCE":
        return CompNode(props=get_inst_props(node), comp=comp_refs.get(str(node.get("componentId", "")), ""))
    if node.get("type") == "TEXT":
        text_ref = node.get("componentPropertyReferences", {}).get("characters")
        text = "{" + prop_map[str(text_ref)] + "}" if text_ref and str(text_ref) in prop_map else str(node.get("characters", ""))
        return TextNode(text=text, font=get_font(node, refs), color=get_color(node, refs))
    return BoxNode(
        width=get_size(node, refs, "x"),
        height=get_size(node, refs, "y"),
        flex=get_flex(node, refs),
        padding=get_padding(node, refs),
        color=get_color(node, refs),
        children=[
            get_node(child, refs, prop_map, comp_refs)
            for child in node.get("children", [])
            if isinstance(child, dict)
        ],
    )


def get_props(node: dict[str, Any]) -> dict[str, str]:
    return {
        get_prop_name(str(raw), str(item.get("type", "")).lower()): get_prop_text(item)
        for raw, item in node.get("componentPropertyDefinitions", {}).items()
    }


def get_prop_map(node: dict[str, Any]) -> dict[str, str]:
    return {
        str(raw): get_prop_name(str(raw), str(item.get("type", "")).lower())
        for raw, item in node.get("componentPropertyDefinitions", {}).items()
    }


def get_inst_props(node: dict[str, Any]) -> dict[str, str]:
    return {
        get_prop_name(str(raw), str(item.get("type", "")).lower()): str(item.get("value", ""))
        for raw, item in node.get("componentProperties", {}).items()
        if isinstance(item, dict)
    }


def get_prop_name(raw: str, kind: str) -> str:
    base = raw.split("#", 1)[0]
    return "text" if kind == "text" and base.lower() == "text" else base


def get_prop_text(item: dict[str, Any]) -> str:
    values = item.get("variantOptions", [])
    opts = ",".join(map(str, values)) if isinstance(values, list) else ""
    default = str(item.get("defaultValue", ""))
    kind = str(item.get("type", "")).lower()
    return f"{kind} default={default}" + (f" options={opts}" if opts else "")


def get_comp_desc(file_doc: dict[str, Any], node: dict[str, Any]) -> str:
    item = file_doc.get("componentSets", {}).get(str(node.get("id", "")), {})
    return str(item.get("description", "")) if isinstance(item, dict) else ""


def get_ref_map(file_doc: dict[str, Any]) -> dict[str, str]:
    comp_sets = file_doc.get("componentSets", {})
    return {
        str(comp_id): str(comp_sets.get(str(item.get("componentSetId", "")), {}).get("name", ""))
        for comp_id, item in file_doc.get("components", {}).items()
        if isinstance(item, dict)
    }


def get_font(node: dict[str, Any], refs: TokRefs) -> str:
    return refs.font.get(str(node.get("styles", {}).get("text", "")), "")


def get_color(node: dict[str, Any], refs: TokRefs) -> str:
    styles = node.get("styles", {})
    return refs.color.get(str(styles.get("fill") or styles.get("fills") or styles.get("stroke") or ""), "")


def get_size(node: dict[str, Any], refs: TokRefs, axis: str) -> str:
    ref = get_ref_flat(node.get("boundVariables", {})).get(f"size.{axis}")
    if ref and ref in refs.var:
        return refs.var[ref]
    key = "layoutSizingHorizontal" if axis == "x" else "layoutSizingVertical"
    return str(node.get(key, "")).lower()


def get_padding(node: dict[str, Any], refs: TokRefs) -> list[str]:
    var_refs = get_ref_flat(node.get("boundVariables", {}))
    return [refs.var.get(var_refs.get(key, ""), "") for key in ["paddingTop", "paddingRight", "paddingBottom", "paddingLeft"]]


def get_flex(node: dict[str, Any], refs: TokRefs) -> Flex:
    var_refs = get_ref_flat(node.get("boundVariables", {}))
    return Flex(
        direction=str(node.get("layoutMode", "")).lower(),
        justify=str(node.get("primaryAxisAlignItems", "")).lower(),
        align=str(node.get("counterAxisAlignItems", "")).lower(),
        gap=refs.var.get(var_refs.get("itemSpacing", ""), ""),
    )


def get_ref_flat(data: Any, prefix: str = "") -> dict[str, str]:
    if isinstance(data, dict) and str(data.get("type")) == "VARIABLE_ALIAS":
        ref = str(data.get("id") or data.get("variableId") or "")
        return {prefix: ref} if prefix and ref else {}
    out: dict[str, str] = {}
    if isinstance(data, dict):
        for key, val in data.items():
            out.update(get_ref_flat(val, f"{prefix}.{key}" if prefix else str(key)))
    return out


def walk(node: dict[str, Any]) -> list[dict[str, Any]]:
    out = [node]
    for child in node.get("children", []):
        if isinstance(child, dict):
            out.extend(walk(child))
    return out


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    api = json.loads((root / "output" / "samples" / "api_response.json").read_text(encoding="utf-8"))
    tokens = json.loads((root / "Mode 1.tokens.json").read_text(encoding="utf-8"))
    add_doc_json(mod_doc(api, tokens), Path("output/doc.json"))
    print("output/doc.json")
