from typing import Any
from doc.classes import get_node_cls
from doc.css import get_fill_css, get_num_css, get_stroke_css
from doc.names import get_num_text
from doc.walk import get_raw
from domain import NodeDoc, TokDoc


def get_svg_node(node: dict[str, Any], tok: TokDoc, parent_mode: str | None) -> NodeDoc:
    def get_path_list() -> list[str]:
        data = node.get("vectorPaths") or node.get("strokeGeometry") or node.get("fillGeometry") or []
        stroke = get_stroke_css(node, tok)
        stroke_w = get_num_css(node, "strokeWeight", tok)
        fill = get_fill_css(node, tok)
        out: list[str] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            raw = item.get("data")
            if not raw:
                continue
            attrs = [f'd="{raw}"', f'fill="{fill}"' if fill else 'fill="none"']
            if stroke:
                attrs.append(f'stroke="{stroke}"')
            if stroke_w:
                attrs.append(f'stroke-width="{stroke_w.removesuffix("px")}"')
            if node.get("strokeLineCap") or node.get("strokeCap"):
                cap = str(node.get("strokeLineCap") or node.get("strokeCap")).lower()
                attrs.append(f'stroke-linecap="{cap}"')
            if node.get("strokeJoin"):
                attrs.append(f'stroke-linejoin="{str(node.get("strokeJoin")).lower()}"')
            out.append(f"<path {' '.join(attrs)} />")
        return out

    width = get_num_text(get_raw(node, "size.x"))
    height = get_num_text(get_raw(node, "size.y"))
    return NodeDoc(
        kind="VECTOR",
        tag="svg",
        name=str(node.get("name", "")),
        classes=get_node_cls(node, tok, parent_mode),
        attrs=[
            ("viewBox", f"0 0 {width or '1'} {height or '1'}"),
            ("fill", "none"),
            ("xmlns", "http://www.w3.org/2000/svg"),
            ("aria-hidden", "true"),
        ],
        raw="\n".join(get_path_list()),
    )
