from __future__ import annotations
from pathlib import Path
from app.domain import GenDoc
from app.gen_static import get_css, get_layout, get_meta, get_uno
from app.gen_svelte import get_comp_file, get_page_file


def add_front(doc: GenDoc, root: Path) -> list[str]:
    files = get_file_map(doc)
    for rel, text in files.items():
        add_file(root / rel, text)
    return sorted(files)


def get_file_map(doc: GenDoc) -> dict[str, str]:
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
    return files


def add_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
