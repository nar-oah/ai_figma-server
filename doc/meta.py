import json
import re
from typing import Any


def get_comp_note(file_doc: dict[str, Any], node: dict[str, Any]) -> tuple[str, dict[str, object]]:
    comp_sets = file_doc.get("componentSets", {})
    item = comp_sets.get(str(node.get("id", "")), {}) if isinstance(comp_sets, dict) else {}
    desc = str(item.get("description", "")) if isinstance(item, dict) else ""
    return desc, get_code_meta(desc)


def get_code_meta(text: str) -> dict[str, object]:
    for raw in get_meta_candidates(text):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            return data
    return {}


def get_meta_candidates(text: str) -> list[str]:
    stripped = text.strip()
    out = [stripped] if stripped.startswith("{") else []
    out.extend(re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.S))
    hit = re.search(r"@code\s*(\{.*\})", text, flags=re.S)
    if hit:
        out.append(hit.group(1))
    return out
