import os
import re
from pathlib import Path
from doc.build import add_doc_json, mod_doc
from domain import GenDoc
import httpx
from gen.write import add_site


class Sercvice:
    def __init__(self, url: str) -> None:
        def get_key() -> str:
            hit = re.search(r"figma\.com/(?:file|design|proto|board)/([^/?#]+)", url)
            return hit.group(1) if hit else ""

        def get_file(key: str, token: str) -> dict:
            client = httpx.Client(follow_redirects=True)
            headers = {"X-Figma-Token": token, "Accept": "application/json"}
            url = f"https://api.figma.com/v1/files/{key}?geometry=paths"
            return client.get(url, headers=headers, timeout=30.0).json()

        self.key = get_key()
        self.file = get_file(self.key, os.environ.get("FIGMA_TOKEN", ""))

    def handle_svelte(self) -> str:
        def get_doc(key: str) -> GenDoc:
            doc = mod_doc(self.file)
            doc.key = key
            return doc

        doc = get_doc(self.key)
        add_doc_json(doc, Path("output/runs/doc.json"))
        add_site(doc, Path("output/runs/web"))
        return doc.name


if __name__ == "__main__":
    import json
    import sys

    def add_file(file: dict, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(file, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    url = sys.argv[1]
    add_file(Sercvice(url).file, Path("output/api_response.json"))
