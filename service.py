import os
import re
from pathlib import Path
from doc.build import add_doc_json, mod_doc
from domain import GenDoc
from figma import get_file
from gen.write import add_site


def get_svelte(url: str) -> str:
    def get_key() -> str:
        hit = re.search(r"figma\.com/(?:file|design|proto|board)/([^/?#]+)", url)
        return hit.group(1) if hit else ""

    def get_doc(key: str) -> GenDoc:
        token = os.environ.get("FIGMA_TOKEN", "")
        doc = mod_doc(get_file(key, token))
        doc.key = key
        return doc

    doc = get_doc(get_key())
    add_doc_json(doc, Path("output/runs/doc.json"))
    add_site(doc, Path("output/runs/web"))
    return doc.name


if __name__ == "__main__":
    import sys

    url = sys.argv[1]
    print(get_svelte(url))
