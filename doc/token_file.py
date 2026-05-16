from typing import Any
from doc.css import get_color_css
from doc.names import get_px, get_slug
from domain import TokenValueDoc

FIGMA_VAR_ID = "com.figma.variableId"


def get_file_vars(data: dict[str, Any] | None) -> list[TokenValueDoc]:
    if not isinstance(data, dict):
        return []
    return list(get_group_vars(data, []))


def get_group_vars(data: dict[str, Any], path: list[str]) -> list[TokenValueDoc]:
    out: list[TokenValueDoc] = []
    if "$value" in data:
        item = get_token_var(data, path)
        return [item] if item else []
    for key, val in data.items():
        if key.startswith("$") or not isinstance(val, dict):
            continue
        out.extend(get_group_vars(val, path + [key]))
    return out


def get_token_var(data: dict[str, Any], path: list[str]) -> TokenValueDoc | None:
    name = get_slug("-".join(path))
    kind = str(data.get("$type", "token")).lower()
    value = data.get("$value")
    css_value = get_token_css(value, kind)
    if not css_value:
        return None
    return TokenValueDoc(
        name=name,
        kind=kind,
        css_name=f"--figma-var-{name}",
        css_value=css_value,
        value=value,
        ref=get_figma_ref(data),
    )


def get_figma_ref(data: dict[str, Any]) -> str | None:
    ext = data.get("$extensions", {})
    if not isinstance(ext, dict):
        return None
    ref = ext.get(FIGMA_VAR_ID)
    return str(ref) if ref else None


def get_token_css(value: Any, kind: str) -> str | None:
    if isinstance(value, dict):
        return get_color_css(value)
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, float)):
        return str(value) if kind == "opacity" else get_px(float(value))
    if isinstance(value, str):
        return get_string_css(value, kind)
    return None


def get_string_css(value: str, kind: str) -> str:
    text = value.strip()
    if text.startswith("{") and text.endswith("}"):
        return f"var(--figma-var-{get_slug(text[1:-1])})"
    return text
