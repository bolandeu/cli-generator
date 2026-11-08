"""This tool's tables, as SQLAlchemy Core — mirrors the latest migration (`migrations/versions/`).

A new package declares no table: add the tool's own to `metadata` and its views to `views`
as the tool needs them, together with the migration that creates them. `tests/test_db.py`
keeps a worked example — `items`, a data table pushed to production, and `responses`, a
cache — with every rule below applied.

Every name starts with `PREFIX` (`<tool>_`): the shared PostgreSQL holds every
tool's tables (and Directus') in one `public` schema. Change a table here *and* add
a migration by hand — tests/test_db.py fails when the migrated schema lacks a table or
column this metadata declares.

Every table has a single-column PRIMARY KEY — Directus can't show or edit a
table without one and doesn't support a composite one: a surrogate `id`, with the
natural key as a UNIQUE constraint (tests/test_db.py checks this metadata and the
migrated database).

Every table says what its rows are, `info={"kind": "data"}` or `"cache"` (tests/test_db.py
fails without it): `data` is the tool's result and lost when deleted; `cache` is a copy
of something it can fetch again. `describe --json` publishes it (x-rb-data).

A `cache` table lives in PostgreSQL schema `cache` — `schema=CACHE_SCHEMA` here (the test
checks kind and schema agree); `public` holds the data. On SQLite the schema is ignored
(core/db.py maps it away): the same file as before. The schema is created by the
infrastructure, not by the tool; `db upgrade` checks it exists and this role may CREATE in it.

`info={"push": {...}}` marks an append-only table for `<cli> db push` (local SQLite →
production PostgreSQL): rows are inserted without their ids and skipped when one
with the same natural key exists, so the table needs a unique constraint on that key
and no foreign keys (link by natural keys). `since` names the timestamp column that
`--since` filters on.
"""

from __future__ import annotations

import sqlalchemy as sa

from .._distribution import TOOL

PREFIX = f"{TOOL}_"
CACHE_SCHEMA = "cache"

# Deterministic constraint names: a later migration can drop or alter them by name
# on both PostgreSQL and SQLite (batch mode); they start with the (prefixed) table name.
metadata = sa.MetaData(
    naming_convention={
        "ix": "%(table_name)s_%(column_0_N_name)s_ix",
        "uq": "%(table_name)s_%(column_0_N_name)s_uq",
        "ck": "%(table_name)s_%(constraint_name)s_ck",
        "fk": "%(table_name)s_%(column_0_name)s_fk",
        "pk": "%(table_name)s_pk",
    }
)

# The `<tool>_v1_*` views other tools, Directus and the platform read instead of the
# tables — the tool's data contract, published by `describe --json` (x-rb-data.views).
# Declared here for that, created by a migration (`CREATE VIEW`); tests/test_db.py
# fails when a view below is missing from the migrated database or its columns differ.
# Columns never change: a different shape is a new `_v2_` view next to the old one.
# Kept out of `metadata`, which mirrors the tables only.
views = sa.MetaData()
