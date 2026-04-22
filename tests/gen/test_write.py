import json
from pathlib import Path
from doc import mod_doc
from gen import add_site


def test_add_site(tmp_path: Path) -> None:
    def get_sample() -> dict[str, object]:
        path = Path(__file__).resolve().parents[2] / "output" / "samples" / "api_response.json"
        return json.loads(path.read_text(encoding="utf-8"))

    doc = mod_doc(get_sample(), None)
    files = add_site(doc, tmp_path)
    assert "uno.config.ts" in files
    assert "src/lib/generated/components/Tab.svelte" in files
    assert f"src/routes/generated/{doc.pages[0].route}/+page.svelte" in files
    code = (tmp_path / "src" / "lib" / "generated" / "components" / "Tab.svelte").read_text(encoding="utf-8")
    assert "export let text" in code
    assert "class_name" in code
