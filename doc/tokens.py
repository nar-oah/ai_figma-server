from typing import Any
from doc.css import get_node_paint
from doc.names import get_font_css, get_px, get_slug
from doc.vars import get_var_css, get_var_name
from doc.walk import get_ref_flat, get_walk
from domain import TokDoc


def get_tok(file_doc: dict[str, Any], var_doc: dict[str, Any] | None) -> TokDoc:
    def get_tok_name(ref: str, prefix: str) -> str:
        raw = style_meta.get(ref, {}).get("name") or f"{prefix}-{ref}"
        return get_slug(str(raw))

    def add_text_tok(node: dict[str, Any]) -> None:
        text_id = node.get("styles", {}).get("text")
        if not text_id or text_id in tok.text or node.get("type") != "TEXT":
            return
        name = get_tok_name(str(text_id), "text")
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

    def add_paint_tok(node: dict[str, Any]) -> None:
        styles = node.get("styles", {})
        refs = list(filter(None, [styles.get("fill"), styles.get("fills"), styles.get("stroke")]))
        for ref in refs:
            if ref in tok.paint:
                continue
            name = get_tok_name(str(ref), "color")
            css = get_node_paint(node, str(ref))
            if not css:
                continue
            tok.paint[str(ref)] = f"--figma-color-{name}"
            tok.root[tok.paint[str(ref)]] = css

    def add_var_tok(node: dict[str, Any]) -> None:
        for path, ref in get_ref_flat(node.get("boundVariables", {})).items():
            if ref in tok.var:
                continue
            css = get_var_css(var_doc, ref, node, path)
            if not css:
                continue
            tok.var[ref] = get_var_name(var_doc, ref)
            tok.root[tok.var[ref]] = css

    tok = TokDoc()
    style_meta = file_doc.get("styles", {})
    for node in get_walk(file_doc.get("document", {})):
        add_text_tok(node)
        add_paint_tok(node)
        add_var_tok(node)
    return tok
