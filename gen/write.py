from pathlib import Path
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


def add_test_site(tmp_path: Path) -> None:
    import json
    from doc import mod_doc

    def get_sample() -> dict[str, object]:
        path = Path(__file__).resolve().parents[1] / "output" / "samples" / "api_response.json"
        return json.loads(path.read_text(encoding="utf-8"))

    doc = mod_doc(get_sample())
    files = add_site(doc, tmp_path)
    assert "uno.config.ts" in files
    assert "src/lib/generated/components/Tab.svelte" in files
    assert f"src/routes/generated/{doc.pages[0].route}/+page.svelte" in files
    code = (tmp_path / "src" / "lib" / "generated" / "components" / "Tab.svelte").read_text(encoding="utf-8")
    assert "export let text" in code
    assert "class_name" in code
