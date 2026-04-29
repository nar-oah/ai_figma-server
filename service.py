import json
import os
import re
from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field
from doc import add_doc_json, mod_doc
from domain import GenDoc
from figma import get_file
from gen import add_site


class GenRes(BaseModel):
    file_key: str
    file_name: str
    out_dir: str
    pages: list[str]
    components: list[str]
    files: list[str]
    warnings: list[str] = Field(default_factory=list)


def get_gen_res(url: str) -> GenRes:
    def get_key() -> str:
        hit = re.search(r"figma\.com/(?:file|design|proto|board)/([^/?#]+)", url)
        return hit.group(1) if hit else ""

    def get_raw_data() -> tuple[str, dict[str, Any]]:
        key = get_key()
        token = os.environ.get("FIGMA_TOKEN", "")
        file_doc = get_file(key, token)
        return key, file_doc

    def get_doc(key: str, file_doc: dict[str, Any]) -> GenDoc:
        doc = mod_doc(file_doc)
        doc.key = key
        return doc

    def get_out_root(key: str) -> Path:
        return Path("output/runs").expanduser().resolve() / key

    def add_json(path: Path, data: dict[str, Any]) -> str:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        return str(path.relative_to(root))

    key, file_doc = get_raw_data()
    doc = get_doc(key, file_doc)
    root = get_out_root(key)
    files = [add_json(root / "raw" / "api_response.json", file_doc)]
    add_doc_json(doc, root / "doc.json")
    files.append("doc.json")
    files.extend(f"web/{path}" for path in add_site(doc, root / "web"))
    return GenRes(
        file_key=key,
        file_name=doc.name,
        out_dir=str(root),
        pages=[item.route for item in doc.pages],
        components=[item.tag for item in doc.comps],
        files=files,
        warnings=doc.warns,
    )


def get_test_gen_res(tmp_path: Path, monkeypatch: Any) -> None:
    def get_sample() -> dict[str, object]:
        path = (
            Path(__file__).resolve().parent / "output" / "samples" / "api_response.json"
        )
        return json.loads(path.read_text(encoding="utf-8"))

    monkeypatch.setenv("FIGMA_TOKEN", "demo-token")
    monkeypatch.setattr("service.get_file", lambda _key, _token: get_sample())
    monkeypatch.chdir(tmp_path)
    url = "https://www.figma.com/design/AbCdEf123456/Test?node-id=1-2"
    res = get_gen_res(url)
    root = Path(res.out_dir)
    assert root == tmp_path.resolve() / "output" / "runs" / "AbCdEf123456"
    assert (root / "raw" / "api_response.json").exists()
    assert (root / "doc.json").exists()
    assert (root / "web" / "src" / "lib" / "generated" / "meta.json").exists()
    assert "raw/api_response.json" in res.files
    assert "raw/variables_response.json" not in res.files
    assert "doc.json" in res.files
    assert any(path.startswith("web/") for path in res.files)
    assert res.warnings == []
