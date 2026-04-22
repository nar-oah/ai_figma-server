from __future__ import annotations
from app.doc_css import get_num_css
from app.domain import TokDoc


def get_axis_cls(node: dict[str, object]) -> list[str]:
    main = {
        "MIN": "justify-start",
        "CENTER": "justify-center",
        "MAX": "justify-end",
        "SPACE_BETWEEN": "justify-between",
        "SPACE_AROUND": "justify-around",
        "SPACE_EVENLY": "justify-evenly",
    }
    side = {
        "MIN": "items-start",
        "CENTER": "items-center",
        "MAX": "items-end",
        "BASELINE": "items-baseline",
    }
    out: list[str] = []
    if node.get("primaryAxisAlignItems") in main:
        out.append(main[str(node["primaryAxisAlignItems"])])
    if node.get("counterAxisAlignItems") in side:
        out.append(side[str(node["counterAxisAlignItems"])])
    if node.get("layoutWrap") == "WRAP":
        out.append("flex-wrap")
    return out


def get_gap_cls(node: dict[str, object], tok: TokDoc) -> list[str]:
    gap = get_num_css(node, "itemSpacing", tok)
    if gap and gap != "0px":
        return [f"gap-[{gap}]"]
    return []


def get_pad_cls(node: dict[str, object], tok: TokDoc) -> list[str]:
    left = get_num_css(node, "paddingLeft", tok)
    right = get_num_css(node, "paddingRight", tok)
    top = get_num_css(node, "paddingTop", tok)
    bottom = get_num_css(node, "paddingBottom", tok)
    out: list[str] = []
    if left and right and left == right:
        out.append(f"px-[{left}]")
    else:
        if left:
            out.append(f"pl-[{left}]")
        if right:
            out.append(f"pr-[{right}]")
    if top and bottom and top == bottom:
        out.append(f"py-[{top}]")
    else:
        if top:
            out.append(f"pt-[{top}]")
        if bottom:
            out.append(f"pb-[{bottom}]")
    return out


def get_size_cls(node: dict[str, object], tok: TokDoc, parent_mode: str | None) -> list[str]:
    return get_axis_size(node, tok, parent_mode, "x") + get_axis_size(node, tok, parent_mode, "y")


def get_axis_size(node: dict[str, object], tok: TokDoc, parent_mode: str | None, axis: str) -> list[str]:
    key = "layoutSizingHorizontal" if axis == "x" else "layoutSizingVertical"
    cls = "w" if axis == "x" else "h"
    way = str(node.get(key, ""))
    if way == "HUG":
        return [f"{cls}-fit"]
    if way == "FILL":
        if (axis == "x" and parent_mode == "HORIZONTAL") or (axis == "y" and parent_mode == "VERTICAL"):
            return ["grow"]
        return [f"{cls}-full", "self-stretch"]
    raw = get_num_css(node, f"size.{axis}", tok)
    if raw:
        return [f"{cls}-[{raw}]"]
    return []


def get_grow_cls(node: dict[str, object], parent_mode: str | None) -> list[str]:
    if float(node.get("layoutGrow", 0) or 0) > 0:
        return ["grow"]
    if node.get("layoutAlign") == "STRETCH" and parent_mode in {"HORIZONTAL", "VERTICAL"}:
        return ["self-stretch"]
    return []
