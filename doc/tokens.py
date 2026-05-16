from typing import Any
from doc.css import get_color_css, get_node_paint
from doc.names import get_font_css, get_px, get_slug
from doc.vars import get_var_css, get_var_name
from doc.walk import get_ref_flat, get_walk
from domain import TokDoc, TokenValueDoc


def get_tok(file_doc: dict[str, Any], token_doc: dict[str, Any] | None = None) -> TokDoc:
    tok = TokDoc()
    style_meta = file_doc.get("styles", {})
    add_file_var_tok(tok, token_doc)
    for node in get_walk(file_doc.get("document", {})):
        add_text_tok(node, tok, style_meta)
        add_paint_tok(node, tok, style_meta)
        add_var_tok(node, tok)
    return tok


def add_file_var_tok(tok: TokDoc, token_doc: dict[str, Any] | None) -> None:
    for item in get_file_vars(token_doc, []):
        tok.variables.append(item)
        tok.root[item.css_name] = item.css_value
        if item.ref:
            tok.var[item.ref] = item.css_name


def add_text_tok(node: dict[str, Any], tok: TokDoc, style_meta: dict[str, Any]) -> None:
    text_id = node.get("styles", {}).get("text")
    if not text_id or text_id in tok.text or node.get("type") != "TEXT":
        return
    name = get_style_name(style_meta, str(text_id), "text")
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
    tok.fonts.append(
        TokenValueDoc(
            name=name,
            kind="text",
            css_name=cls,
            css_value=tok.classes[cls],
            value={
                "fontFamily": style.get("fontFamily", "sans-serif"),
                "fontSize": style.get("fontSize", 16),
                "lineHeightPx": style.get("lineHeightPx", style.get("fontSize", 16)),
                "letterSpacing": style.get("letterSpacing", 0),
                "fontWeight": style.get("fontWeight", 400),
            },
            ref=str(text_id),
        )
    )


def add_paint_tok(node: dict[str, Any], tok: TokDoc, style_meta: dict[str, Any]) -> None:
    styles = node.get("styles", {})
    refs = list(filter(None, [styles.get("fill"), styles.get("fills"), styles.get("stroke")]))
    for ref in refs:
        if ref in tok.paint:
            continue
        name = get_style_name(style_meta, str(ref), "color")
        css = get_node_paint(node, str(ref))
        if not css:
            continue
        tok.paint[str(ref)] = f"--figma-color-{name}"
        tok.root[tok.paint[str(ref)]] = css
        tok.colors.append(TokenValueDoc(name, "color", tok.paint[str(ref)], css, css, str(ref)))


def add_var_tok(node: dict[str, Any], tok: TokDoc) -> None:
    for path, ref in get_ref_flat(node.get("boundVariables", {})).items():
        if ref in tok.var:
            continue
        css = get_var_css(node, path)
        if not css:
            continue
        tok.var[ref] = get_var_name(ref)
        tok.root[tok.var[ref]] = css
        name = get_slug(ref.replace(":", "-"))
        tok.variables.append(TokenValueDoc(name, "api", tok.var[ref], css, css, ref))


def get_file_vars(data: Any, path: list[str]) -> list[TokenValueDoc]:
    if not isinstance(data, dict):
        return []
    if "$value" in data:
        item = get_file_var(data, path)
        return [item] if item else []
    out: list[TokenValueDoc] = []
    for key, val in data.items():
        if not str(key).startswith("$"):
            out.extend(get_file_vars(val, path + [str(key)]))
    return out


def get_file_var(data: dict[str, Any], path: list[str]) -> TokenValueDoc | None:
    name = get_slug("-".join(path))
    kind = str(data.get("$type", "token")).lower()
    value = data.get("$value")
    css = get_token_css(value, kind)
    ext = data.get("$extensions", {})
    ref = ext.get("com.figma.variableId") if isinstance(ext, dict) else None
    if not css:
        return None
    return TokenValueDoc(name, kind, f"--figma-var-{name}", css, value, str(ref) if ref else None)


def get_token_css(value: Any, kind: str) -> str | None:
    if isinstance(value, dict):
        return get_color_css(value)
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, float)):
        return str(value) if kind == "opacity" else get_px(float(value))
    if isinstance(value, str):
        text = value.strip()
        if text.startswith("{") and text.endswith("}"):
            return f"var(--figma-var-{get_slug(text[1:-1])})"
        return text
    return None


def get_style_name(style_meta: dict[str, Any], ref: str, prefix: str) -> str:
    raw = style_meta.get(ref, {}).get("name") or f"{prefix}-{ref}"
    return get_slug(str(raw))
