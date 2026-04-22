import json
from pathlib import Path
from doc import add_doc_json, mod_doc


def test_mod_doc(tmp_path: Path) -> None:
    def get_sample() -> dict[str, object]:
        path = Path(__file__).resolve().parents[2] / "output" / "samples" / "api_response.json"
        return json.loads(path.read_text(encoding="utf-8"))

    doc = mod_doc(get_sample(), None)
    add_doc_json(doc, tmp_path / "doc.json")
    data = json.loads((tmp_path / "doc.json").read_text(encoding="utf-8"))
    assert len(doc.comps) == 3
    assert len(doc.pages) == 1
    assert any(item.tag == "Tab" for item in doc.comps)
    assert any(name.startswith("--figma-color-") for name in doc.tokens.root)
    assert any(name.startswith("--figma-var-") for name in doc.tokens.root)
    assert data["pages"][0]["route"] == doc.pages[0].route
