from typing import Any
from doc.meta import get_comp_note
from doc.names import get_pair_map, get_pascal, get_prop_key
from doc.node import mod_node
from domain import CompDoc, PropDoc, RefDoc, TokDoc, VariantDoc


def get_ref_map(
    comp_nodes: list[dict[str, Any]],
    prop_by_tag: dict[str, list[PropDoc]],
) -> dict[str, RefDoc]:
    out: dict[str, RefDoc] = {}
    for node in comp_nodes:
        tag = get_pascal(node.get("name", "Component"))
        raw_map = {item.raw: item.name for item in prop_by_tag[tag]}
        for child in node.get("children", []):
            if isinstance(child, dict) and child.get("id"):
                out[str(child["id"])] = RefDoc(tag=tag, prop=raw_map)
    return out


def get_comp_doc(
    file_doc: dict[str, Any],
    node: dict[str, Any],
    tok: TokDoc,
    ref_map: dict[str, RefDoc],
    prop_by_tag: dict[str, list[PropDoc]],
) -> CompDoc:
    def get_variant(child: dict[str, Any]) -> VariantDoc:
        when = {
            key_map.get(get_prop_key(key), get_prop_key(key)): val
            for key, val in get_pair_map(str(child.get("name", ""))).items()
        }
        return VariantDoc(
            name=str(child.get("name", "")),
            when=when,
            root=mod_node(child, tok, ref_map, raw_map, None),
        )

    tag = get_pascal(node.get("name", "Component"))
    props = prop_by_tag[tag]
    raw_map = {item.raw: item.name for item in props}
    key_map = {get_prop_key(item.raw): item.name for item in props if item.kind == "variant"}
    variants = [get_variant(child) for child in node.get("children", []) if isinstance(child, dict)]
    desc, meta = get_comp_note(file_doc, node)
    return CompDoc(
        name=str(node.get("name", "Component")),
        tag=tag,
        props=props,
        variants=variants,
        description=desc,
        meta=meta,
    )


def get_prop_list(node: dict[str, Any]) -> list[PropDoc]:
    def get_prop_name(raw: str, kind: str) -> str:
        base = get_prop_key(raw)
        name = "text" if kind == "text" and base == "text" else base
        if kind == "text" and name != "text":
            name = f"{name}_text"
        if name not in seen:
            return name
        idx = 2
        while f"{name}_{idx}" in seen:
            idx += 1
        return f"{name}_{idx}"

    seen: set[str] = set()
    out: list[PropDoc] = []
    for raw, item in node.get("componentPropertyDefinitions", {}).items():
        kind = str(item.get("type", "TEXT")).lower()
        name = get_prop_name(str(raw), kind)
        seen.add(name)
        out.append(
            PropDoc(
                raw=str(raw),
                name=name,
                kind=kind,
                default=str(item.get("defaultValue", "")),
                options=[str(val) for val in item.get("variantOptions", [])],
            )
        )
    return out
