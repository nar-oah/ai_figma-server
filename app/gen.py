from __future__ import annotations
import json
from pathlib import Path
from app.domain import CompDoc, GenDoc, NodeDoc, PageDoc, VariantDoc


def add_front(doc: GenDoc, root: Path) -> list[str]:
    files: dict[str, str] = {
        "uno.config.ts": get_uno(doc),
        "src/app.css": get_css(),
        "src/routes/+layout.svelte": get_layout(),
        "src/lib/generated/meta.json": get_meta(doc),
    }
    for comp in doc.comps:
        files[f"src/lib/generated/components/{comp.tag}.svelte"] = get_comp_file(comp)
    for page in doc.pages:
        files[f"src/routes/generated/{page.route}/+page.svelte"] = get_page_file(page)
    for rel, text in files.items():
        add_file(root / rel, text)
    return sorted(files)


def add_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def get_uno(doc: GenDoc) -> str:
    root_css = "\n".join(map(lambda item: f"  {item[0]}: {item[1]};", sorted(doc.tokens.root.items())))
    class_css = "\n".join(map(lambda item: f".{item[0]} {{ {item[1]} }}", sorted(doc.tokens.classes.items())))
    return f"""import {{ defineConfig, presetUno }} from 'unocss'

const rootCss = `:root {{
{root_css}
}}`

const extraCss = `
{class_css}
`

export default defineConfig({{
  presets: [presetUno()],
  content: {{
    filesystem: ['src/**/*.{{svelte,ts,js}}'],
  }},
  preflights: [
    {{
      getCSS: () => `${{rootCss}}\\n${{extraCss}}`,
    }},
  ],
}})
"""


def get_css() -> str:
    return """@unocss preflights;
@unocss default;
@unocss utilities;

html,
body {
  margin: 0;
  min-height: 100%;
}

body {
  min-height: 100vh;
}

* {
  box-sizing: border-box;
}

p {
  margin: 0;
}
"""


def get_layout() -> str:
    return """<script lang="ts">
  import '../app.css'
</script>

<slot />
"""


def get_meta(doc: GenDoc) -> str:
    data = {
        "name": doc.name,
        "key": doc.key,
        "pages": list(map(lambda item: {"name": item.name, "route": item.route}, doc.pages)),
        "components": list(map(lambda item: {"name": item.name, "tag": item.tag}, doc.comps)),
        "warnings": doc.warns,
    }
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def get_comp_file(comp: CompDoc) -> str:
    imports = get_import_code(get_use_list(map(lambda item: item.root, comp.variants)), "./")
    props = "\n".join(
        map(
            lambda item: f"  export let {item.name} = {json.dumps(item.default, ensure_ascii=False)}",
            comp.props,
        )
    )
    body = get_variant_block(comp.variants, 0, True)
    script = "\n".join(filter(None, ["<script lang=\"ts\">", "  export let class_name = ''", props, imports, "</script>"]))
    return f"""{script}

{body}
"""


def get_page_file(page: PageDoc) -> str:
    imports = get_import_code(get_use_list([page.root]), "$lib/generated/components/")
    script = f"<script lang=\"ts\">\n{imports}\n</script>" if imports else ""
    body = get_node_code(page.root, 1, False)
    return f"""{script}

<main class="min-h-screen w-full flex justify-center py-8">
{body}
</main>
"""


def get_import_code(items: list[str], base: str) -> str:
    return "\n".join(map(lambda item: f"  import {item} from '{base}{item}.svelte'", items))


def get_use_list(nodes: list[NodeDoc] | object) -> list[str]:
    out: list[str] = []
    def add_node(node: NodeDoc) -> None:
        if node.comp and node.comp not in out:
            out.append(node.comp)
        for child in node.children:
            add_node(child)
    for node in nodes:
        add_node(node)
    return out


def get_variant_block(items: list[VariantDoc], depth: int, root: bool) -> str:
    if not items:
        return ""
    lines: list[str] = []
    for idx, item in enumerate(items):
        head = "{#if" if idx == 0 else "{:else if"
        cond = " && ".join(map(lambda pair: f"{pair[0]} === {json.dumps(pair[1], ensure_ascii=False)}", item.when.items())) or "true"
        lines.append(f"{get_tab(depth)}{head} {cond}}}")
        lines.append(get_node_code(item.root, depth + 1, root))
    lines.append(f"{get_tab(depth)}{{/if}}")
    return "\n".join(lines)


def get_node_code(node: NodeDoc, depth: int, root: bool) -> str:
    if node.comp:
        attrs = get_attr_list(node.attrs)
        return f"{get_tab(depth)}<{node.comp}{(' ' + attrs) if attrs else ''} />"
    attrs = get_attr_list(node.attrs)
    cls = get_class_attr(node.classes, root)
    open_tag = " ".join(filter(None, [node.tag, cls, attrs]))
    if node.tag == "svg" and not node.children and not node.text and not node.expr and not node.raw:
        return f"{get_tab(depth)}<svg {cls} {attrs}></svg>".rstrip()
    if not node.children and node.text is None and node.expr is None and not node.raw:
        return f"{get_tab(depth)}<{open_tag}></{node.tag}>"
    lines = [f"{get_tab(depth)}<{open_tag}>"]
    if node.expr:
        lines.append(f"{get_tab(depth + 1)}{{{node.expr}}}")
    elif node.text:
        lines.append(f"{get_tab(depth + 1)}{node.text}")
    if node.raw:
        lines.extend(map(lambda row: f"{get_tab(depth + 1)}{row}", node.raw.splitlines()))
    for child in node.children:
        lines.append(get_node_code(child, depth + 1, False))
    lines.append(f"{get_tab(depth)}</{node.tag}>")
    return "\n".join(lines)


def get_class_attr(items: list[str], root: bool) -> str:
    text = " ".join(items)
    if root and text:
        return f'class="{text} {{class_name}}"'
    if root:
        return 'class={class_name}'
    return f'class="{text}"' if text else ""


def get_attr_list(items: list[tuple[str, object]]) -> str:
    return " ".join(map(lambda item: f"{item[0]}={{{get_attr_val(item[1])}}}", items))


def get_attr_val(val: object) -> str:
    return json.dumps(val, ensure_ascii=False)


def get_tab(depth: int) -> str:
    return "  " * depth
