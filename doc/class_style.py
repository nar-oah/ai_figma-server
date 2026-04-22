import math
from doc.css import get_fill_css, get_num_css, get_stroke_css
from doc.names import get_font_css, get_px
from domain import TokDoc


def get_box_cls(node: dict[str, object], tok: TokDoc) -> list[str]:
    def get_radius_cls() -> list[str]:
        if node.get("type") == "ELLIPSE":
            return ["rounded-full"]
        if node.get("cornerRadius") is not None:
            css = get_num_css(node, "cornerRadius", tok)
            if css:
                return [f"rounded-[{css}]"]
            return []
        vals = node.get("rectangleCornerRadii", [])
        if not isinstance(vals, list) or not vals:
            return []
        text = [get_px(float(item)) for item in vals]
        if len(set(text)) == 1 and text[0] != "0px":
            return [f"rounded-[{text[0]}]"]
        keys = ["rounded-tl", "rounded-tr", "rounded-br", "rounded-bl"]
        return [f"{key}-[{val}]" for key, val in zip(keys, text, strict=False) if val != "0px"]

    out: list[str] = []
    fill = get_fill_css(node, tok)
    if fill and node.get("type") != "TEXT":
        out.append(f"bg-[{fill}]")
    stroke = get_stroke_css(node, tok)
    if stroke:
        out.extend(
            [
                "border-solid",
                f"border-[{get_num_css(node, 'strokeWeight', tok) or '1px'}]",
                f"border-[{stroke}]",
            ]
        )
    out.extend(get_radius_cls())
    return out


def get_text_cls(node: dict[str, object], tok: TokDoc) -> list[str]:
    def get_text_raw_cls() -> list[str]:
        style = node.get("style", {})
        out: list[str] = []
        if style.get("fontFamily"):
            out.append(f"font-[{get_font_css(str(style['fontFamily']))}]")
        if style.get("fontSize") is not None:
            out.append(f"text-[length:{get_px(float(style['fontSize']))}]")
        if style.get("lineHeightPx") is not None:
            out.append(f"leading-[{get_px(float(style['lineHeightPx']))}]")
        if style.get("letterSpacing") is not None:
            out.append(f"tracking-[{get_px(float(style['letterSpacing']))}]")
        if style.get("fontWeight") is not None:
            out.append(f"font-[{int(style['fontWeight'])}]")
        return out

    if node.get("type") != "TEXT":
        return []
    out: list[str] = ["m-0", "whitespace-pre-wrap"]
    text_id = node.get("styles", {}).get("text")
    if text_id and text_id in tok.text:
        out.append(tok.text[str(text_id)])
    else:
        out.extend(get_text_raw_cls())
    fill = get_fill_css(node, tok)
    if fill:
        out.append(f"text-[{fill}]")
    align = str(node.get("style", {}).get("textAlignHorizontal", "LEFT"))
    out.append({"LEFT": "text-left", "CENTER": "text-center", "RIGHT": "text-right"}.get(align, "text-left"))
    return out


def get_rotate_cls(node: dict[str, object]) -> str | None:
    raw = node.get("rotation")
    if raw is None:
        return None
    deg = round(float(raw) * 180 / math.pi)
    if deg in {90, -270}:
        return "rotate-90"
    if deg in {180, -180}:
        return "rotate-180"
    if deg in {270, -90}:
        return "rotate-270"
    if deg:
        return f"rotate-[{deg}deg]"
    return None
