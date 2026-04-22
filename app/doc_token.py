from __future__ import annotations
from typing import Any
from app.doc_css import get_node_paint
from app.doc_name import get_font_css, get_px, get_slug
from app.doc_var import get_var_css, get_var_name
from app.doc_walk import get_ref_flat, get_walk
from app.domain import TokDoc


def get_tok(file_doc: dict[str, Any], var_doc: dict[str, Any] | None) -> TokDoc:
    tok = TokDoc()
    style_meta = file_doc.get("styles", {})
    for node in get_walk(file_doc.get("document", {})):
        add_text_tok(tok, style_meta, node)
        add_paint_tok(tok, style_meta, node)
        add_var_tok(tok, var_doc, node)
    return tok


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
    refs = list(filter(None, [styles.get("fill"), styles.get("fills"), styles.get("stroke")]))
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
