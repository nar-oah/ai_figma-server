from dataclasses import dataclass, field
from typing import Any
from domain import FontDoc, TokDoc, Token, Ext


@dataclass(slots=True)
class TokRefs:
    color: dict[str, str] = field(default_factory=dict)
    font: dict[str, str] = field(default_factory=dict)
    var: dict[str, str] = field(default_factory=dict)


def get_tok(
    file_doc: dict[str, Any], token_doc: dict[str, Token] | None
) -> tuple[TokDoc, TokRefs]:
    tok = TokDoc()
    refs = TokRefs()
    if isinstance(token_doc, dict):
        add_vars(tok, refs, token_doc)
    for node in walk(file_doc.get("document", {})):
        add_color(tok, refs, node, file_doc.get("styles", {}))
        add_font(tok, refs, node, file_doc.get("styles", {}))
    return tok, refs


def add_vars(tok: TokDoc, refs: TokRefs, tokens: dict[str, Token]) -> None:
    def add_toc(name: str, token: Token) -> Ext:
        if isinstance(val := token.get("$value"), int):
            tok.variables[name] = val
        return ext if isinstance(ext := token.get("$extensions"), dict) else {}

    def add_refs(name: str, ext: Ext) -> None:
        if isinstance(ref := ext.get("com.figma.variableId"), str):
            refs.var[str(ref)] = name

    for name, token in tokens.items():
        add_refs(name, add_toc(name, token))


def add_color(
    tok: TokDoc,
    refs: TokRefs,
    node: dict[str, Any],
    styles: dict[str, Any],
) -> None:
    node_styles = node.get("styles", {})
    for key in ["fill", "fills", "stroke"]:
        ref = node_styles.get(key)
        if not ref or ref in refs.color:
            continue
        name = get_style_name(styles, str(ref))
        color = get_node_color(node, key)
        if color:
            refs.color[str(ref)] = name
            tok.colors[name] = color


def add_font(
    tok: TokDoc,
    refs: TokRefs,
    node: dict[str, Any],
    styles: dict[str, Any],
) -> None:
    ref = node.get("styles", {}).get("text")
    if not ref or ref in refs.font or node.get("type") != "TEXT":
        return
    name = get_style_name(styles, str(ref))
    style = node.get("style", {})
    refs.font[str(ref)] = name
    tok.fonts[name] = FontDoc(
        fontFamily=str(style.get("fontFamily", "sans-serif")),
        fontSize=float(style.get("fontSize", 16)),
        lineHeightPx=float(style.get("lineHeightPx", style.get("fontSize", 16))),
        letterSpacing=float(style.get("letterSpacing", 0)),
        fontWeight=int(style.get("fontWeight", 400)),
    )


def get_style_name(styles: dict[str, Any], ref: str) -> str:
    item = styles.get(ref, {})
    return str(item.get("name") or ref) if isinstance(item, dict) else ref


def get_node_color(node: dict[str, Any], style_key: str) -> str:
    if style_key == "stroke":
        return get_color(get_paint(node.get("strokes", [])))
    return get_color(get_paint(node.get("fills", []))) or get_color(
        node.get("backgroundColor")
    )


def get_paint(data: Any) -> dict[str, Any] | None:
    if not isinstance(data, list):
        return None
    for item in data:
        if (
            isinstance(item, dict)
            and item.get("visible") is not False
            and item.get("type") == "SOLID"
        ):
            return item.get("color")
    return None


def get_color(data: Any) -> str:
    if not isinstance(data, dict):
        return ""
    red = round(float(data.get("r", 0)) * 255)
    green = round(float(data.get("g", 0)) * 255)
    blue = round(float(data.get("b", 0)) * 255)
    alpha = float(data.get("a", 1))
    return "" if alpha <= 0 else f"rgba({red},{green},{blue},{alpha:.3f})"


def walk(node: dict[str, Any]) -> list[dict[str, Any]]:
    out = [node]
    for child in node.get("children", []):
        if isinstance(child, dict):
            out.extend(walk(child))
    return out
