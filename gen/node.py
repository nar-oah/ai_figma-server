import json
from domain import NodeDoc


def get_node_code(node: NodeDoc, depth: int, root: bool) -> str:
    def get_class_attr(items: list[str]) -> str:
        text = " ".join(items)
        if root and text:
            return f'class="{text} {{class_name}}"'
        if root:
            return "class={class_name}"
        if text:
            return f'class="{text}"'
        return ""

    def get_attr_val(val: object) -> str:
        return json.dumps(val, ensure_ascii=False)

    def get_attr_list(items: list[tuple[str, object]]) -> str:
        return " ".join(f"{key}={{{get_attr_val(val)}}}" for key, val in items)

    if node.comp:
        attrs = get_attr_list(node.attrs)
        extra = f" {attrs}" if attrs else ""
        return f"{get_tab(depth)}<{node.comp}{extra} />"
    attrs = get_attr_list(node.attrs)
    cls = get_class_attr(node.classes)
    open_tag = " ".join(filter(None, [node.tag, cls, attrs]))
    if not node.children and node.text is None and node.expr is None and not node.raw:
        return f"{get_tab(depth)}<{open_tag}></{node.tag}>"
    lines = [f"{get_tab(depth)}<{open_tag}>"]
    if node.expr:
        lines.append(f"{get_tab(depth + 1)}{{{node.expr}}}")
    elif node.text:
        lines.append(f"{get_tab(depth + 1)}{node.text}")
    if node.raw:
        lines.extend(f"{get_tab(depth + 1)}{row}" for row in node.raw.splitlines())
    for child in node.children:
        lines.append(get_node_code(child, depth + 1, False))
    lines.append(f"{get_tab(depth)}</{node.tag}>")
    return "\n".join(lines)


def get_tab(depth: int) -> str:
    return "  " * depth
