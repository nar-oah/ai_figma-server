from dataclasses import asdict
from secrets import token_urlsafe

import psycopg
from psycopg.types.json import Jsonb

from domain import GenDoc


def add_doc(doc: GenDoc, figma_key: str) -> str:
    token = token_urlsafe(32)
    data = asdict(doc)
    tokens = data["tokens"]
    with psycopg.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO gen_docs (token, figma_key, comps, pages)
                VALUES (%s, %s, %s, %s)
                """,
                (token, figma_key, Jsonb(data["comps"]), Jsonb(data["pages"])),
            )
            cur.execute(
                """
                INSERT INTO tok_docs (token, colors, fonts, variables)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    token,
                    Jsonb(tokens["colors"]),
                    Jsonb(tokens["fonts"]),
                    Jsonb(tokens["variables"]),
                ),
            )
    return token
