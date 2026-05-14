from collections.abc import Iterable
from typing import Any


def get_raw(node: dict[str, Any], path: str) -> Any:
    if path == "size.x":
        return get_box(node).get("width")
    if path == "size.y":
        return get_box(node).get("height")
    cur: Any = node
    for part in path.split("."):
        if isinstance(cur, dict):
            cur = cur.get(part)
            continue
        if isinstance(cur, list) and part.isdigit():
            idx = int(part)
            cur = cur[idx] if idx < len(cur) else None
            continue
        return None
    return cur


def get_box(node: dict[str, Any]) -> dict[str, Any]:
    return (
        node.get("absoluteBoundingBox", {})
        or node.get("absoluteRenderBounds", {})
        or {}
    )


def get_ref_flat(data: Any, prefix: str = "") -> dict[str, str]:
    out: dict[str, str] = {}
    if isinstance(data, dict):
        if str(data.get("type")) == "VARIABLE_ALIAS":
            ref = str(data.get("id") or data.get("variableId") or "")
            if prefix and ref:
                out[prefix] = ref
            return out
        for key, val in data.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            out.update(get_ref_flat(val, path))
    if isinstance(data, list):
        for idx, val in enumerate(data):
            path = f"{prefix}.{idx}" if prefix else str(idx)
            out.update(get_ref_flat(val, path))
    return out


def get_walk(node: dict[str, Any]) -> Iterable[dict[str, Any]]:
    def get_child_walk(node: dict[str, Any]) -> Iterable[dict[str, Any]]:
        yield node
        for child in node.get("children", []):
            if isinstance(child, dict):
                yield from get_child_walk(child)

    return get_child_walk(node)
