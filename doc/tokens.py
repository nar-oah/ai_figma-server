from typing import Any
from doc.css import get_node_paint
from doc.names import get_font_css, get_px, get_slug
from doc.token_file import get_file_vars
from doc.vars import get_var_css, get_var_name
from doc.walk import get_ref_flat, get_walk
from domain import TokDoc, TokenValueDoc


def get_tok(file_doc: dict[str, Any], token_doc: dict[str, Any] | None = None) -> TokDoc:
    def get_tok_name(ref: str, prefix: str) -> str:
        raw = style_meta.get(ref, {}).get("name") or f"{prefix}-{ref}"
        return get_slug(str(raw))

    def add_file_var_tok() -> None:
        for item in get_file_vars(token_doc):
            tok.variables.append(item)
            tok.root[item.css_name] = item.css_value
            if item.ref:
                tok.var[item.ref] = item.css_name

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
            tok.colors.append(
                TokenValueDoc(
                    name=name,
                    kind="color",
                    css_name=tok.paint[str(ref)],
                    css_value=css,
                    value=css,
                    ref=str(ref),
                )
            )

    def add_var_tok(node: dict[str, Any]) -> None:
        for path, ref in get_ref_flat(node.get("boundVariables", {})).items():
            if ref in tok.var:
                continue
            css = get_var_css(node, path)
            if not css:
                continue
            tok.var[ref] = get_var_name(ref)
            tok.root[tok.var[ref]] = css
            tok.variables.append(
                TokenValueDoc(
                    name=get_slug(ref.replace(":", "-")),
                    kind="api",
                    css_name=tok.var[ref],
                    css_value=css,
                    value=css,
                    ref=ref,
                )
            )

    tok = TokDoc()
    style_meta = file_doc.get("styles", {})
    add_file_var_tok()
    for node in get_walk(file_doc.get("document", {})):
        add_text_tok(node)
        add_paint_tok(node)
        add_var_tok(node)
    return tok
