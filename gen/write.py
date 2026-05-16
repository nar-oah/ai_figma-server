from pathlib import Path
import sys

if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from domain import GenDoc
from gen.static import get_css, get_layout, get_meta, get_uno
from gen.svelte import get_comp_file, get_page_file


def add_site(doc: GenDoc, root: Path) -> list[str]:
    def add_file(path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

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


if __name__ == "__main__":
    import json
    from doc.build import mod_doc

    def get_json(path: Path) -> dict[str, object]:
        return json.loads(path.read_text(encoding="utf-8"))

    root_dir = Path(__file__).resolve().parents[1]
    api_path = root_dir / "output" / "samples" / "api_response.json"
    token_path = root_dir / "Mode 1.tokens.json"
    doc = mod_doc(get_json(api_path), get_json(token_path))
    files = add_site(doc, Path("output"))
    print(json.dumps(files, ensure_ascii=False, indent=2))
