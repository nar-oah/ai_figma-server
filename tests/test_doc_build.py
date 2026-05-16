import json
from pathlib import Path
from doc.build import add_doc_json, mod_doc

ROOT = Path(__file__).resolve().parents[1]
API_SAMPLE = ROOT / "output" / "samples" / "api_response.json"
TOKEN_SAMPLE = ROOT / "Mode 1.tokens.json"
DOC_OUTPUT = ROOT / "output" / "doc.json"


def get_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_doc_builds_from_local_api_sample() -> None:
    doc = mod_doc(get_json(API_SAMPLE), get_json(TOKEN_SAMPLE))
    add_doc_json(doc, DOC_OUTPUT)

    assert doc.name == "Test Degin"
    assert [page.name for page in doc.pages] == ["登陆页"]
    assert {comp.tag for comp in doc.comps} == {"Tab", "Input", "Icon"}
    assert DOC_OUTPUT.exists()


def test_uploaded_tokens_define_global_variables() -> None:
    doc = mod_doc(get_json(API_SAMPLE), get_json(TOKEN_SAMPLE))

    assert doc.tokens.var["VariableID:2001:237"] == "--figma-var-input-width"
    assert doc.tokens.root["--figma-var-input-width"] == "393px"
    assert doc.tokens.root["--figma-var-page-height"] == "400px"
    assert {item.name for item in doc.tokens.variables} >= {"input-width", "page-height"}


def test_component_props_and_notes_are_preserved() -> None:
    doc = mod_doc(get_json(API_SAMPLE), get_json(TOKEN_SAMPLE))
    comps = {comp.tag: comp for comp in doc.comps}

    assert [prop.name for prop in comps["Tab"].props] == ["text", "reverse"]
    assert "reverse决定颜色" in comps["Tab"].description
    assert {prop.name for prop in comps["Input"].props} == {"input_text", "default_text", "click", "input"}
    assert "input输入框" in comps["Input"].description
