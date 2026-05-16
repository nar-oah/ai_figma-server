import os
import re
from pathlib import Path
from typing import Any
from doc.build import mod_doc
from domain import GenDoc
import httpx
from gen.write import add_site


class Service:
    def __init__(self, url: str, token_doc: dict[str, Any] | None = None) -> None:
        self.key = get_key(url)
        self.token_doc = token_doc
        self.file = get_file(self.key, os.environ.get("FIGMA_TOKEN", ""))

    def handle_svelte(self) -> str:
        doc = self.handle_doc()
        add_site(doc, Path("output"))
        return doc.name

    def handle_doc(self) -> GenDoc:
        doc = mod_doc(self.file, self.token_doc)
        doc.key = self.key
        return doc


Sercvice = Service


def get_key(url: str) -> str:
    hit = re.search(r"figma\.com/(?:file|design|proto|board)/([^/?#]+)", url)
    return hit.group(1) if hit else ""


def get_file(key: str, token: str) -> dict[str, Any]:
    client = httpx.Client(follow_redirects=True)
    headers = {"X-Figma-Token": token, "Accept": "application/json"}
    url = f"https://api.figma.com/v1/files/{key}?geometry=paths"
    return client.get(url, headers=headers, timeout=30.0).json()


if __name__ == "__main__":
    import json
    import sys

    def add_file(file: dict[str, Any], path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(file, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    url = sys.argv[1]
    add_file(Service(url).file, Path("output/api_response.json"))
