import re
from typing import Any


def get_pair_map(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for part in filter(None, map(str.strip, text.split(","))):
        if "=" not in part:
            continue
        key, val = map(str.strip, part.split("=", 1))
        out[key] = val
    return out


def get_route(name: str, node_id: str, used: set[str]) -> str:
    base = get_slug(name) or get_slug(node_id)
    if base not in used:
        used.add(base)
        return base
    idx = 2
    while f"{base}-{idx}" in used:
        idx += 1
    route = f"{base}-{idx}"
    used.add(route)
    return route


def get_slug(text: str) -> str:
    raw = "".join(
        ch.lower()
        if ch.isascii() and ch.isalnum()
        else "-"
        if ch in {" ", "-", "_", "/"}
        else f"-u{ord(ch):x}-"
        for ch in str(text)
    )
    return re.sub(r"-+", "-", raw).strip("-") or "node"


def get_pascal(text: str) -> str:
    return "".join(part[:1].upper() + part[1:] for part in get_slug(text).replace("_", "-").split("-"))


def get_prop_key(raw: str) -> str:
    return get_slug(raw.split("#", 1)[0]).replace("-", "_")


def get_font_css(text: str) -> str:
    return f'"{text}"'


def get_px(val: float) -> str:
    return f"{int(val)}px" if float(val).is_integer() else f"{val}px"


def get_num_text(val: Any) -> str | None:
    if isinstance(val, (int, float)):
        return str(int(val) if float(val).is_integer() else val)
    return None


def get_clean_cls(items: list[str]) -> list[str]:
    out: list[str] = []
    for item in items:
        if item and item not in out:
            out.append(item)
    return out
