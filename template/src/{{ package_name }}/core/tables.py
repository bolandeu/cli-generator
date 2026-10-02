"""This tool's tables, as SQLAlchemy Core — mirrors the latest migration (`migrations/versions/`).

Every name starts with `PREFIX` (`<tool>_`): the shared PostgreSQL holds every
tool's tables (and Directus') in one `public` schema. Change a table here *and* add
a migration by hand (copy the example in `migrations/versions/`) — tests/test_db.py
fails when the migrated schema and this metadata disagree.

Every table has a single-column PRIMARY KEY — Directus can't show or edit a
table without one and doesn't support a composite one: a surrogate `id`, with the
natural key as a UNIQUE constraint (tests/test_db.py checks this metadata and the
migrated database).

`items` below is the template's example: replace it with the tool's own tables.

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

items = sa.Table(
    f"{PREFIX}items",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("phrase", sa.Text, nullable=False),  # as the user typed it
    sa.Column("phrase_key", sa.Text, nullable=False),  # core.normalize.norm_phrase(phrase)
    sa.Column("region", sa.Integer, nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    sa.UniqueConstraint("phrase_key", "region"),  # the natural key
    info={"kind": "data", "push": {"since": "created_at"}},
)

# The template's example of a cache table: one stored API response per phrase and region.
responses = sa.Table(
    f"{PREFIX}responses",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("phrase_key", sa.Text, nullable=False),
    sa.Column("region", sa.Integer, nullable=False),
    sa.Column("body", sa.Text, nullable=False),
    sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    sa.UniqueConstraint("phrase_key", "region"),
    schema=CACHE_SCHEMA,
    info={"kind": "cache"},
)

# The `<tool>_v1_*` views other tools, Directus and the platform read instead of the
# tables — the tool's data contract, published by `describe --json` (x-rb-data.views).
# Declared here for that, created by a migration (`CREATE VIEW`); tests/test_db.py
# fails when a view below is missing from the migrated database or its columns differ.
# Columns never change: a different shape is a new `_v2_` view next to the old one.
# Kept out of `metadata`, which mirrors the tables only.
views = sa.MetaData()

v1_items = sa.Table(
    f"{PREFIX}v1_items",
    views,
    sa.Column("phrase", sa.Text, comment="The phrase as the user typed it"),
    sa.Column("phrase_key", sa.Text, comment="The normalized phrase: the key to join on"),
    sa.Column("region", sa.Integer, comment="Region id"),
    sa.Column("created_at", sa.DateTime(timezone=True), comment="When the row was added"),
    comment="The template's example: one row per stored phrase and region",
)

v1_responses = sa.Table(
    f"{PREFIX}v1_responses",
    views,
    sa.Column("phrase_key", sa.Text, comment="The normalized phrase: the key to join on"),
    sa.Column("region", sa.Integer, comment="Region id"),
    sa.Column("body", sa.Text, comment="The provider's response, as received"),
    sa.Column("fetched_at", sa.DateTime(timezone=True), comment="When it was fetched"),
    comment="The template's example of a view over a cache table (in schema `cache`; the view stays in public)",
)
