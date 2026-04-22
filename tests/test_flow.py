from __future__ import annotations
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from app.doc import mod_doc
from app.figma import get_key, get_token
from app.gen import add_front


class FlowTest(unittest.TestCase):
    def get_sample(self) -> dict:
        path = Path(__file__).resolve().parents[1] / "api_response.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def test_get_key(self) -> None:
        url = "https://www.figma.com/design/AbCdEf123456/Test?node-id=1-2"
        self.assertEqual(get_key(url), "AbCdEf123456")

    def test_get_token(self) -> None:
        with patch.dict(os.environ, {"FIGMA_TOKEN": " demo-token "}, clear=False):
            self.assertEqual(get_token(), "demo-token")

    def test_get_token_missing(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, "FIGMA_TOKEN"):
                get_token()

    def test_mod_doc(self) -> None:
        doc = mod_doc(self.get_sample(), None)
        self.assertEqual(len(doc.comps), 3)
        self.assertEqual(len(doc.pages), 1)
        self.assertIn("Tab", list(map(lambda item: item.tag, doc.comps)))
        self.assertTrue(any(name.startswith("--figma-color-") for name in doc.tokens.root))
        self.assertTrue(any(name.startswith("--figma-var-") for name in doc.tokens.root))

    def test_add_front(self) -> None:
        doc = mod_doc(self.get_sample(), None)
        with tempfile.TemporaryDirectory() as tmp:
            files = add_front(doc, Path(tmp))
            self.assertIn("uno.config.ts", files)
            self.assertIn("src/lib/generated/components/Tab.svelte", files)
            self.assertIn(f"src/routes/generated/{doc.pages[0].route}/+page.svelte", files)
            code = (Path(tmp) / "src/lib/generated/components/Tab.svelte").read_text(encoding="utf-8")
            self.assertIn("export let text", code)
            self.assertIn("class_name", code)


if __name__ == "__main__":
    unittest.main()
