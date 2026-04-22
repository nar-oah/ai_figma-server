from typing import Any
from doc.names import get_px
from doc.walk import get_raw, get_ref_flat
from domain import TokDoc


def get_fill_css(node: dict[str, Any], tok: TokDoc) -> str | None:
    styles = node.get("styles", {})
    style_id = styles.get("fill") or styles.get("fills")
    if style_id and style_id in tok.paint:
        return f"var({tok.paint[str(style_id)]})"
    refs = get_ref_flat(node.get("boundVariables", {}))
    alias = refs.get("fills.0.color") or refs.get("background.0.color")
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
    fill = get_color_css(get_paint(node.get("fills", [])))
    if node.get("type") == "TEXT":
        return fill
    return fill or get_color_css(node.get("backgroundColor"))


def get_node_stroke(node: dict[str, Any]) -> str | None:
    return get_color_css(get_paint(node.get("strokes", [])))


def get_node_paint(node: dict[str, Any], ref: str) -> str | None:
    if node.get("styles", {}).get("stroke") == ref:
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
    if isinstance(raw, (int, float)):
        return get_px(float(raw))
    return None
