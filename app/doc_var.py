from __future__ import annotations
from typing import Any
from app.doc_css import get_val_css
from app.doc_name import get_slug
from app.doc_walk import get_raw


def get_var_name(var_doc: dict[str, Any] | None, ref: str) -> str:
    meta = get_var_meta(var_doc, ref)
    raw = meta.get("name") if meta else ref.replace(":", "-")
    return f"--figma-var-{get_slug(str(raw))}"


def get_var_css(var_doc: dict[str, Any] | None, ref: str, node: dict[str, Any], path: str) -> str | None:
    val = get_var_val(var_doc, ref, {ref})
    if val is None:
        val = get_raw(node, path)
    return get_val_css(val, path)


def get_var_val(var_doc: dict[str, Any] | None, ref: str, seen: set[str]) -> Any | None:
    meta = get_var_meta(var_doc, ref)
    if not meta:
        return None
    col = get_col_meta(var_doc, str(meta.get("variableCollectionId", "")))
    mode = col.get("defaultModeId") if col else None
    val = meta.get("valuesByMode", {}).get(mode) if mode else None
    if isinstance(val, dict) and str(val.get("type")) == "VARIABLE_ALIAS":
        key = str(val.get("id") or val.get("variableId") or "")
        if not key or key in seen:
            return None
        return get_var_val(var_doc, key, seen | {key})
    return val


def get_var_meta(var_doc: dict[str, Any] | None, ref: str) -> dict[str, Any] | None:
    meta = (var_doc or {}).get("meta", {})
    return meta.get("variables", {}).get(ref)


def get_col_meta(var_doc: dict[str, Any] | None, ref: str) -> dict[str, Any] | None:
    meta = (var_doc or {}).get("meta", {})
    return meta.get("variableCollections", {}).get(ref)
