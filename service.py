import os
import re
from pathlib import Path
from doc.build import mod_doc
from domain import GenDoc
from store import add_doc
import httpx


class Service:
    def __init__(self, url: str, token_doc: dict[str, object] | None = None) -> None:
        def get_key(url: str) -> str:
            hit = re.search(r"figma\.com/(?:file|design|proto|board)/([^/?#]+)", url)
            return hit.group(1) if hit else ""

        def get_file(key: str, token: str) -> dict[str, object]:
            client = httpx.Client(follow_redirects=True)
            headers = {"X-Figma-Token": token, "Accept": "application/json"}
            url = f"https://api.figma.com/v1/files/{key}?geometry=paths"
            return client.get(url, headers=headers, timeout=30.0).json()

        self.key = get_key(url)
        self.token_doc = token_doc
        self.file = get_file(self.key, os.environ.get("FIGMA_TOKEN", ""))

    def get_doc(self) -> GenDoc:
        return mod_doc(self.file, self.token_doc)

    def add_doc(self) -> str:
        return add_doc(self.get_doc(), self.key)


if __name__ == "__main__":
    import json
    import sys

    def add_file(file: dict[str, object], path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(file, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    url = sys.argv[1]
    add_file(Service(url).file, Path("output/api_response.json"))
