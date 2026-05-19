-- Run these statements while connected to the figma database.

CREATE TABLE IF NOT EXISTS gen_docs (
    token text PRIMARY KEY,
    figma_key text NOT NULL,
    comps jsonb NOT NULL,
    pages jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS tok_docs (
    token text PRIMARY KEY REFERENCES gen_docs(token) ON DELETE CASCADE,
    colors jsonb NOT NULL,
    fonts jsonb NOT NULL,
    variables jsonb NOT NULL
);
