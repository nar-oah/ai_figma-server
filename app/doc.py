from __future__ import annotations
import re
from collections.abc import Iterable
from dataclasses import asdict
from typing import Any
from app.domain import CompDoc, GenDoc, NodeDoc, PageDoc, PropDoc, RefDoc, TokDoc, VariantDoc


def mod_doc(file_doc: dict[str, Any], var_doc: dict[str, Any] | None) -> GenDoc:
    tok = get_tok(file_doc, var_doc)
    comp_nodes = list(get_comp_node_list(file_doc))
    prop_by_tag = {get_pascal(node.get("name", "Component")): get_prop_list(node) for node in comp_nodes}
    ref_map: dict[str, RefDoc] = {}
    for node in comp_nodes:
        tag = get_pascal(node.get("name", "Component"))
        raw_map = {item.raw: item.name for item in prop_by_tag[tag]}
        for child in node.get("children", []):
            if isinstance(child, dict) and child.get("id"):
                ref_map[child["id"]] = RefDoc(tag=tag, prop=raw_map)
    comp_list = list(map(lambda node: get_comp_doc(node, tok, ref_map, prop_by_tag), comp_nodes))
    page_list = get_page_list(file_doc, tok, ref_map)
    return GenDoc(
        key=str(file_doc.get("version", "")),
        name=str(file_doc.get("name", "Figma")),
        tokens=tok,
        comps=comp_list,
        pages=page_list,
    )


def get_tok(file_doc: dict[str, Any], var_doc: dict[str, Any] | None) -> TokDoc:
    tok = TokDoc()
    style_meta = file_doc.get("styles", {})
    for node in get_walk(file_doc.get("document", {})):
        add_text_tok(tok, style_meta, node)
        add_paint_tok(tok, style_meta, node)
        add_var_tok(tok, var_doc, node)
    return tok


def get_comp_node_list(file_doc: dict[str, Any]) -> Iterable[dict[str, Any]]:
    return filter(lambda node: node.get("type") == "COMPONENT_SET", get_walk(file_doc.get("document", {})))


def get_page_list(file_doc: dict[str, Any], tok: TokDoc, ref_map: dict[str, RefDoc]) -> list[PageDoc]:
    used: set[str] = set()
    out: list[PageDoc] = []
    doc = file_doc.get("document", {})
    for canvas in doc.get("children", []):
        if not isinstance(canvas, dict) or canvas.get("type") != "CANVAS":
            continue
        if any(child.get("type") == "COMPONENT_SET" for child in canvas.get("children", []) if isinstance(child, dict)):
            continue
        for child in canvas.get("children", []):
            if not isinstance(child, dict):
                continue
            route = get_route(child.get("name", "page"), child.get("id", ""), used)
            out.append(PageDoc(name=str(child.get("name", "Page")), route=route, root=mod_node(child, tok, ref_map, {}, None)))
    return out


def get_comp_doc(
    node: dict[str, Any],
    tok: TokDoc,
    ref_map: dict[str, RefDoc],
    prop_by_tag: dict[str, list[PropDoc]],
) -> CompDoc:
    tag = get_pascal(node.get("name", "Component"))
    props = prop_by_tag[tag]
    raw_map = {item.raw: item.name for item in props}
    key_map = {get_prop_key(item.raw): item.name for item in props if item.kind == "variant"}
    variants = list(
        map(
            lambda child: VariantDoc(
                name=str(child.get("name", "")),
                when={key_map.get(get_prop_key(key), get_prop_key(key)): val for key, val in get_pair_map(str(child.get("name", ""))).items()},
                root=mod_node(child, tok, ref_map, raw_map, None),
            ),
            filter(lambda child: isinstance(child, dict), node.get("children", [])),
        )
    )
    return CompDoc(name=str(node.get("name", "Component")), tag=tag, props=props, variants=variants)


def get_prop_list(node: dict[str, Any]) -> list[PropDoc]:
    seen: set[str] = set()
    out: list[PropDoc] = []
    defs = node.get("componentPropertyDefinitions", {})
    for raw, item in defs.items():
        kind = str(item.get("type", "TEXT")).lower()
        name = get_prop_name(str(raw), kind, seen)
        seen.add(name)
        out.append(
            PropDoc(
                raw=str(raw),
                name=name,
                kind=kind,
                default=str(item.get("defaultValue", "")),
                options=list(map(str, item.get("variantOptions", []))),
            )
        )
    return out


def get_prop_name(raw: str, kind: str, seen: set[str]) -> str:
    base = get_prop_key(raw).replace("-", "_")
    name = "text" if kind == "text" and base == "text" else base
    name = f"{name}_text" if kind == "text" and name != "text" else name
    if name not in seen:
        return name
    idx = 2
    while f"{name}_{idx}" in seen:
        idx += 1
    return f"{name}_{idx}"


def get_prop_key(raw: str) -> str:
    return get_slug(raw.split("#", 1)[0]).replace("-", "_")


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
    tag = "div"
    children = list(
        map(
            lambda child: mod_node(child, tok, ref_map, prop_map, node.get("layoutMode")),
            filter(lambda child: isinstance(child, dict), node.get("children", [])),
        )
    )
    return NodeDoc(
        kind=kind,
        tag=tag,
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
        expr=prop_map.get(str(ref), None) if ref else None,
    )


def get_svg_node(node: dict[str, Any], tok: TokDoc, parent_mode: str | None) -> NodeDoc:
    width = get_num_text(get_raw(node, "size.x"))
    height = get_num_text(get_raw(node, "size.y"))
    paths = get_svg_path_list(node, tok)
    return NodeDoc(
        kind="VECTOR",
        tag="svg",
        name=str(node.get("name", "")),
        classes=get_node_cls(node, tok, parent_mode),
        attrs=[
            ("viewBox", f"0 0 {width or '1'} {height or '1'}"),
            ("fill", "none"),
            ("xmlns", "http://www.w3.org/2000/svg"),
            ("aria-hidden", "true"),
        ],
        raw="\n".join(paths) if paths else "",
    )


def get_svg_path_list(node: dict[str, Any], tok: TokDoc) -> list[str]:
    data = node.get("vectorPaths") or node.get("strokeGeometry") or node.get("fillGeometry") or []
    stroke = get_stroke_css(node, tok)
    stroke_w = get_num_css(node, "strokeWeight", tok)
    fill = get_fill_css(node, tok)
    out: list[str] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        raw = item.get("data")
        if not raw:
            continue
        attrs = [f'd="{raw}"']
        attrs.append(f'fill="{fill}"' if fill else 'fill="none"')
        if stroke:
            attrs.append(f'stroke="{stroke}"')
        if stroke_w:
            attrs.append(f'stroke-width="{stroke_w.removesuffix("px")}"')
        if node.get("strokeLineCap") or node.get("strokeCap"):
            attrs.append(f'stroke-linecap="{str(node.get("strokeLineCap") or node.get("strokeCap")).lower()}"')
        if node.get("strokeJoin"):
            attrs.append(f'stroke-linejoin="{str(node.get("strokeJoin")).lower()}"')
        out.append(f"<path {' '.join(attrs)} />")
    return out


def get_inst_attr(node: dict[str, Any], ref: RefDoc, tok: TokDoc, parent_mode: str | None) -> list[tuple[str, object]]:
    attrs = list(
        map(
            lambda item: (ref.prop.get(str(item[0]), get_prop_key(str(item[0]))), item[1].get("value", "")),
            filter(lambda item: isinstance(item[1], dict), node.get("componentProperties", {}).items()),
        )
    )
    cls = " ".join(get_node_cls(node, tok, parent_mode))
    return attrs + ([("class_name", cls)] if cls else [])


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


def get_axis_cls(node: dict[str, Any]) -> list[str]:
    out: list[str] = []
    main = {
        "MIN": "justify-start",
        "CENTER": "justify-center",
        "MAX": "justify-end",
        "SPACE_BETWEEN": "justify-between",
        "SPACE_AROUND": "justify-around",
        "SPACE_EVENLY": "justify-evenly",
    }
    side = {
        "MIN": "items-start",
        "CENTER": "items-center",
        "MAX": "items-end",
        "BASELINE": "items-baseline",
    }
    if node.get("primaryAxisAlignItems") in main:
        out.append(main[str(node["primaryAxisAlignItems"])])
    if node.get("counterAxisAlignItems") in side:
        out.append(side[str(node["counterAxisAlignItems"])])
    if node.get("layoutWrap") == "WRAP":
        out.append("flex-wrap")
    return out


def get_gap_cls(node: dict[str, Any], tok: TokDoc) -> list[str]:
    gap = get_num_css(node, "itemSpacing", tok)
    return [f"gap-[{gap}]"] if gap and gap != "0px" else []


def get_pad_cls(node: dict[str, Any], tok: TokDoc) -> list[str]:
    left = get_num_css(node, "paddingLeft", tok)
    right = get_num_css(node, "paddingRight", tok)
    top = get_num_css(node, "paddingTop", tok)
    bottom = get_num_css(node, "paddingBottom", tok)
    out: list[str] = []
    if left and right and left == right:
        out.append(f"px-[{left}]")
    else:
        if left:
            out.append(f"pl-[{left}]")
        if right:
            out.append(f"pr-[{right}]")
    if top and bottom and top == bottom:
        out.append(f"py-[{top}]")
    else:
        if top:
            out.append(f"pt-[{top}]")
        if bottom:
            out.append(f"pb-[{bottom}]")
    return out


def get_size_cls(node: dict[str, Any], tok: TokDoc, parent_mode: str | None) -> list[str]:
    return get_axis_size(node, tok, parent_mode, "x") + get_axis_size(node, tok, parent_mode, "y")


def get_axis_size(node: dict[str, Any], tok: TokDoc, parent_mode: str | None, axis: str) -> list[str]:
    key = "layoutSizingHorizontal" if axis == "x" else "layoutSizingVertical"
    cls = "w" if axis == "x" else "h"
    way = str(node.get(key, ""))
    if way == "HUG":
        return [f"{cls}-fit"]
    if way == "FILL":
        if (axis == "x" and parent_mode == "HORIZONTAL") or (axis == "y" and parent_mode == "VERTICAL"):
            return ["grow"]
        return [f"{cls}-full", "self-stretch"]
    raw = get_num_css(node, f"size.{axis}", tok)
    if raw:
        return [f"{cls}-[{raw}]"]
    return []


def get_grow_cls(node: dict[str, Any], parent_mode: str | None) -> list[str]:
    if float(node.get("layoutGrow", 0) or 0) > 0:
        return ["grow"]
    if node.get("layoutAlign") == "STRETCH" and parent_mode in {"HORIZONTAL", "VERTICAL"}:
        return ["self-stretch"]
    return []


def get_box_cls(node: dict[str, Any], tok: TokDoc) -> list[str]:
    out: list[str] = []
    fill = get_fill_css(node, tok)
    if fill and node.get("type") != "TEXT":
        out.append(f"bg-[{fill}]")
    stroke = get_stroke_css(node, tok)
    if stroke:
        out.append("border-solid")
        out.append(f"border-[{get_num_css(node, 'strokeWeight', tok) or '1px'}]")
        out.append(f"border-[{stroke}]")
    out.extend(get_radius_cls(node, tok))
    return out


def get_text_cls(node: dict[str, Any], tok: TokDoc) -> list[str]:
    if node.get("type") != "TEXT":
        return []
    out: list[str] = ["m-0", "whitespace-pre-wrap"]
    text_id = node.get("styles", {}).get("text")
    if text_id and text_id in tok.text:
        out.append(tok.text[str(text_id)])
    else:
        out.extend(get_text_raw_cls(node))
    fill = get_fill_css(node, tok)
    if fill:
        out.append(f"text-[{fill}]")
    align = str(node.get("style", {}).get("textAlignHorizontal", "LEFT"))
    out.append({"LEFT": "text-left", "CENTER": "text-center", "RIGHT": "text-right"}.get(align, "text-left"))
    return out


def get_text_raw_cls(node: dict[str, Any]) -> list[str]:
    style = node.get("style", {})
    out: list[str] = []
    if style.get("fontFamily"):
        out.append(f"font-[{get_font_css(str(style['fontFamily']))}]")
    if style.get("fontSize") is not None:
        out.append(f"text-[length:{get_px(float(style['fontSize']))}]")
    if style.get("lineHeightPx") is not None:
        out.append(f"leading-[{get_px(float(style['lineHeightPx']))}]")
    if style.get("letterSpacing") is not None:
        out.append(f"tracking-[{get_px(float(style['letterSpacing']))}]")
    if style.get("fontWeight") is not None:
        out.append(f"font-[{int(style['fontWeight'])}]")
    return out


def get_radius_cls(node: dict[str, Any], tok: TokDoc) -> list[str]:
    if node.get("type") == "ELLIPSE":
        return ["rounded-full"]
    if node.get("cornerRadius") is not None:
        css = get_num_css(node, "cornerRadius", tok)
        return [f"rounded-[{css}]"] if css else []
    vals = node.get("rectangleCornerRadii", [])
    if not isinstance(vals, list) or not vals:
        return []
    text = list(map(lambda item: get_px(float(item)), vals))
    if len(set(text)) == 1 and text[0] != "0px":
        return [f"rounded-[{text[0]}]"]
    keys = ["rounded-tl", "rounded-tr", "rounded-br", "rounded-bl"]
    return [f"{key}-[{val}]" for key, val in zip(keys, text, strict=False) if val != "0px"]


def get_rotate_cls(node: dict[str, Any]) -> str | None:
    raw = node.get("rotation")
    if raw is None:
        return None
    deg = round(float(raw) * 180 / 3.141592653589793)
    if deg in {90, -270}:
        return "rotate-90"
    if deg in {180, -180}:
        return "rotate-180"
    if deg in {270, -90}:
        return "rotate-270"
    return f"rotate-[{deg}deg]" if deg else None


def add_text_tok(tok: TokDoc, style_meta: dict[str, Any], node: dict[str, Any]) -> None:
    text_id = node.get("styles", {}).get("text")
    if not text_id or text_id in tok.text or node.get("type") != "TEXT":
        return
    name = get_tok_name(style_meta, str(text_id), "text")
    root = f"--figma-text-{name}"
    style = node.get("style", {})
    tok.root[f"{root}-family"] = get_font_css(str(style.get("fontFamily", "sans-serif")))
    tok.root[f"{root}-size"] = get_px(float(style.get("fontSize", 16)))
    tok.root[f"{root}-line"] = get_px(float(style.get("lineHeightPx", style.get("fontSize", 16))))
    tok.root[f"{root}-track"] = get_px(float(style.get("letterSpacing", 0)))
    tok.root[f"{root}-weight"] = str(int(style.get("fontWeight", 400)))
    cls = f"tx-{name}"
    tok.classes[cls] = "; ".join(
        [
            f"font-family: var({root}-family)",
            f"font-size: var({root}-size)",
            f"line-height: var({root}-line)",
            f"letter-spacing: var({root}-track)",
            f"font-weight: var({root}-weight)",
        ]
    )
    tok.text[str(text_id)] = cls


def add_paint_tok(tok: TokDoc, style_meta: dict[str, Any], node: dict[str, Any]) -> None:
    styles = node.get("styles", {})
    refs = list(
        filter(
            None,
            [styles.get("fill"), styles.get("fills"), styles.get("stroke")],
        )
    )
    for ref in refs:
        if ref in tok.paint:
            continue
        name = get_tok_name(style_meta, str(ref), "color")
        css = get_node_paint(node, str(ref))
        if not css:
            continue
        tok.paint[str(ref)] = f"--figma-color-{name}"
        tok.root[tok.paint[str(ref)]] = css


def add_var_tok(tok: TokDoc, var_doc: dict[str, Any] | None, node: dict[str, Any]) -> None:
    for path, ref in get_ref_flat(node.get("boundVariables", {})).items():
        if ref in tok.var:
            continue
        css = get_var_css(var_doc, ref, node, path)
        if not css:
            continue
        tok.var[ref] = get_var_name(var_doc, ref)
        tok.root[tok.var[ref]] = css


def get_tok_name(style_meta: dict[str, Any], ref: str, prefix: str) -> str:
    raw = style_meta.get(ref, {}).get("name") or f"{prefix}-{ref}"
    return get_slug(str(raw))


def get_var_name(var_doc: dict[str, Any] | None, ref: str) -> str:
    meta = get_var_meta(var_doc, ref)
    raw = meta.get("name") if meta else ref.replace(":", "-")
    return f"--figma-var-{get_slug(str(raw))}"


def get_var_css(var_doc: dict[str, Any] | None, ref: str, node: dict[str, Any], path: str) -> str | None:
    val = get_var_val(var_doc, ref, set())
    if val is None:
        val = get_raw(node, path)
    return get_val_css(val, path)


def get_var_val(var_doc: dict[str, Any] | None, ref: str, seen: set[str]) -> Any | None:
    meta = get_var_meta(var_doc, ref)
    if not meta or ref in seen:
        return None
    col = get_col_meta(var_doc, str(meta.get("variableCollectionId", "")))
    mode = col.get("defaultModeId") if col else None
    val = meta.get("valuesByMode", {}).get(mode) if mode else None
    if isinstance(val, dict) and str(val.get("type")) == "VARIABLE_ALIAS":
        key = str(val.get("id") or val.get("variableId") or "")
        return get_var_val(var_doc, key, seen | {ref})
    return val


def get_var_meta(var_doc: dict[str, Any] | None, ref: str) -> dict[str, Any] | None:
    meta = (var_doc or {}).get("meta", {})
    return meta.get("variables", {}).get(ref)


def get_col_meta(var_doc: dict[str, Any] | None, ref: str) -> dict[str, Any] | None:
    meta = (var_doc or {}).get("meta", {})
    return meta.get("variableCollections", {}).get(ref)


def get_fill_css(node: dict[str, Any], tok: TokDoc) -> str | None:
    styles = node.get("styles", {})
    style_id = styles.get("fill") or styles.get("fills")
    if style_id and style_id in tok.paint:
        return f"var({tok.paint[str(style_id)]})"
    alias = get_ref_flat(node.get("boundVariables", {})).get("fills.0.color") or get_ref_flat(node.get("boundVariables", {})).get("background.0.color")
    if alias and alias in tok.var:
        return f"var({tok.var[alias]})"
    return get_node_fill(node)


def get_stroke_css(node: dict[str, Any], tok: TokDoc) -> str | None:
    style_id = node.get("styles", {}).get("stroke")
    if style_id and style_id in tok.paint:
        return f"var({tok.paint[str(style_id)]})"
    alias = get_ref_flat(node.get("boundVariables", {})).get("strokes.0.color")
    if alias and alias in tok.var:
        return f"var({tok.var[alias]})"
    return get_node_stroke(node)


def get_node_fill(node: dict[str, Any]) -> str | None:
    if node.get("type") == "TEXT":
        return get_color_css(get_paint(node.get("fills", [])))
    return get_color_css(get_paint(node.get("fills", []))) or get_color_css(node.get("backgroundColor"))


def get_node_stroke(node: dict[str, Any]) -> str | None:
    return get_color_css(get_paint(node.get("strokes", [])))


def get_node_paint(node: dict[str, Any], ref: str) -> str | None:
    styles = node.get("styles", {})
    if styles.get("stroke") == ref:
        return get_node_stroke(node)
    return get_node_fill(node)


def get_paint(data: Any) -> dict[str, Any] | None:
    if not isinstance(data, list):
        return None
    for item in data:
        if not isinstance(item, dict):
            continue
        if item.get("visible") is False:
            continue
        if item.get("type") == "SOLID":
            return item.get("color")
    return None


def get_color_css(data: Any) -> str | None:
    if not isinstance(data, dict):
        return None
    red = round(float(data.get("r", 0)) * 255)
    green = round(float(data.get("g", 0)) * 255)
    blue = round(float(data.get("b", 0)) * 255)
    alpha = float(data.get("a", 1))
    if alpha <= 0:
        return None
    return f"rgba({red},{green},{blue},{alpha:.3f})"


def get_val_css(val: Any, path: str) -> str | None:
    if val is None:
        return None
    if isinstance(val, dict):
        return get_color_css(val)
    if isinstance(val, bool):
        return "1" if val else "0"
    if isinstance(val, (int, float)):
        return get_px(float(val)) if path != "opacity" else str(val)
    if isinstance(val, str):
        return val
    return None


def get_num_css(node: dict[str, Any], path: str, tok: TokDoc) -> str | None:
    ref = get_ref_flat(node.get("boundVariables", {})).get(path)
    if ref and ref in tok.var:
        return f"var({tok.var[ref]})"
    raw = get_raw(node, path)
    return get_px(float(raw)) if isinstance(raw, (int, float)) else None


def get_raw(node: dict[str, Any], path: str) -> Any:
    if path == "size.x":
        return get_box(node).get("width")
    if path == "size.y":
        return get_box(node).get("height")
    cur: Any = node
    for part in path.split("."):
        if isinstance(cur, dict):
            cur = cur.get(part)
            continue
        if isinstance(cur, list) and part.isdigit():
            idx = int(part)
            cur = cur[idx] if idx < len(cur) else None
            continue
        return None
    return cur


def get_box(node: dict[str, Any]) -> dict[str, Any]:
    return node.get("absoluteBoundingBox", {}) or node.get("absoluteRenderBounds", {}) or {}


def get_ref_flat(data: Any, prefix: str = "") -> dict[str, str]:
    out: dict[str, str] = {}
    if isinstance(data, dict):
        if str(data.get("type")) == "VARIABLE_ALIAS":
            ref = str(data.get("id") or data.get("variableId") or "")
            if prefix and ref:
                out[prefix] = ref
            return out
        for key, val in data.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            out.update(get_ref_flat(val, path))
    if isinstance(data, list):
        for idx, val in enumerate(data):
            path = f"{prefix}.{idx}" if prefix else str(idx)
            out.update(get_ref_flat(val, path))
    return out


def get_walk(node: dict[str, Any]) -> Iterable[dict[str, Any]]:
    if not isinstance(node, dict):
        return []
    def get_iter(cur: dict[str, Any]) -> Iterable[dict[str, Any]]:
        yield cur
        for child in cur.get("children", []):
            if isinstance(child, dict):
                yield from get_iter(child)
    return get_iter(node)


def get_pair_map(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for part in filter(None, map(str.strip, text.split(","))):
        if "=" not in part:
            continue
        key, val = map(str.strip, part.split("=", 1))
        out[key] = val
    return out


def get_route(name: str, node_id: str, used: set[str]) -> str:
    base = get_slug(name) or get_slug(node_id)
    if base not in used:
        used.add(base)
        return base
    idx = 2
    while f"{base}-{idx}" in used:
        idx += 1
    used.add(f"{base}-{idx}")
    return f"{base}-{idx}"


def get_slug(text: str) -> str:
    raw = "".join(
        map(
            lambda ch: ch.lower()
            if ch.isascii() and ch.isalnum()
            else "-"
            if ch in {" ", "-", "_", "/"}
            else f"-u{ord(ch):x}-",
            str(text),
        )
    )
    return re.sub(r"-+", "-", raw).strip("-") or "node"


def get_pascal(text: str) -> str:
    return "".join(map(lambda part: part[:1].upper() + part[1:], get_slug(text).replace("_", "-").split("-")))


def get_font_css(text: str) -> str:
    return f'"{text}"'


def get_px(val: float) -> str:
    return f"{int(val)}px" if float(val).is_integer() else f"{val}px"


def get_num_text(val: Any) -> str | None:
    if isinstance(val, (int, float)):
        return str(int(val) if float(val).is_integer() else val)
    return None


def get_clean_cls(items: list[str]) -> list[str]:
    out: list[str] = []
    for item in items:
        if item and item not in out:
            out.append(item)
    return out
