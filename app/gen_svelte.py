from __future__ import annotations
import json
from collections.abc import Iterable
from app.domain import CompDoc, NodeDoc, PageDoc, VariantDoc
from app.gen_node import get_node_code, get_tab


def get_comp_file(comp: CompDoc) -> str:
    imports = get_import_code(get_use_list(item.root for item in comp.variants), "./")
    props = "\n".join(
        f"  export let {item.name} = {json.dumps(item.default, ensure_ascii=False)}" for item in comp.props
    )
    script = "\n".join(
        filter(None, ['<script lang="ts">', "  export let class_name = ''", props, imports, "</script>"])
    )
    return f"""{script}

{get_variant_block(comp.variants, 0, True)}
"""


def get_page_file(page: PageDoc) -> str:
    imports = get_import_code(get_use_list([page.root]), "$lib/generated/components/")
    script = f"<script lang=\"ts\">\n{imports}\n</script>" if imports else ""
    return f"""{script}

<main class="min-h-screen w-full flex justify-center py-8">
{get_node_code(page.root, 1, False)}
</main>
"""


def get_import_code(items: list[str], base: str) -> str:
    return "\n".join(f"  import {item} from '{base}{item}.svelte'" for item in items)


def get_use_list(nodes: Iterable[NodeDoc]) -> list[str]:
    out: list[str] = []
    for node in nodes:
        add_use(node, out)
    return out


def add_use(node: NodeDoc, out: list[str]) -> None:
    if node.comp and node.comp not in out:
        out.append(node.comp)
    for child in node.children:
        add_use(child, out)


def get_variant_block(items: list[VariantDoc], depth: int, root: bool) -> str:
    if not items:
        return ""
    lines: list[str] = []
    for idx, item in enumerate(items):
        head = "{#if" if idx == 0 else "{:else if"
        cond = " && ".join(
            f"{key} === {json.dumps(val, ensure_ascii=False)}" for key, val in item.when.items()
        ) or "true"
        lines.append(f"{get_tab(depth)}{head} {cond}}}")
        lines.append(get_node_code(item.root, depth + 1, root))
    lines.append(f"{get_tab(depth)}{{/if}}")
    return "\n".join(lines)
