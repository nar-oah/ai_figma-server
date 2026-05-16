from typing import Any
from doc.names import get_pascal
from doc.props import get_prop_list
from doc.walk import get_walk
from domain import PropDoc


def get_comp_node_list(file_doc: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        node
        for node in get_walk(file_doc.get("document", {}))
        if node.get("type") == "COMPONENT_SET"
    ]


def get_prop_by_tag(comp_nodes: list[dict[str, Any]]) -> dict[str, list[PropDoc]]:
    return {
        get_pascal(node.get("name", "Component")): get_prop_list(node)
        for node in comp_nodes
    }
