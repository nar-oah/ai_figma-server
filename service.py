import os
import re
from pathlib import Path
from typing import Any
from doc.build import add_doc_json, mod_doc
from domain import GenDoc
from figma import get_file
from gen.write import add_site


def get_gen_res(url: str) -> str:
    def get_key() -> str:
        hit = re.search(r"figma\.com/(?:file|design|proto|board)/([^/?#]+)", url)
        return hit.group(1) if hit else ""

    def get_raw_data(key: str) -> dict[str, Any]:
        token = os.environ.get("FIGMA_TOKEN", "")
        file_doc = get_file(key, token)
        return file_doc

    def get_doc(key: str, file_doc: dict[str, Any]) -> GenDoc:
        doc = mod_doc(file_doc)
        doc.key = key
        return doc

    key = get_key()
    file_doc = get_raw_data(key)
    doc = get_doc(key, file_doc)
    add_doc_json(doc, Path("output/runs/doc.json"))
    add_site(doc, Path("output/runs/web"))
    return doc.name


if __name__ == "__main__":
    import sys

    url = sys.argv[1]
    print(get_gen_res(url))
