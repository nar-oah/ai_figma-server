from typing import Any
from doc.css import get_val_css
from doc.names import get_slug
from doc.walk import get_raw


def get_var_name(ref: str) -> str:
    return f"--figma-var-{get_slug(ref.replace(':', '-'))}"


def get_var_css(node: dict[str, Any], path: str) -> str | None:
    return get_val_css(get_raw(node, path), path)
