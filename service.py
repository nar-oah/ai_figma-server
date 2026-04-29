import json
import os
import re
from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field
from doc.build import add_doc_json, mod_doc
from domain import GenDoc
from figma import get_file
from gen.write import add_site


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


def add_run() -> None:
    import sys

    url = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("FIGMA_URL", "")
    if not url:
        raise SystemExit("用法: FIGMA_TOKEN=... python service.py <figma_url>")
    res = get_gen_res(url)
    print(json.dumps(res.dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    add_run()
