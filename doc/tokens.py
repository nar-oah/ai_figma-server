from typing import Any
from doc.style_tokens import add_paint_tok, add_text_tok, add_var_tok
from doc.token_file import get_file_vars
from doc.walk import get_walk
from domain import TokDoc


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
    for item in get_file_vars(token_doc):
        tok.variables.append(item)
        tok.root[item.css_name] = item.css_value
        if item.ref:
            tok.var[item.ref] = item.css_name
