"""Explicit, additive migration. Inspect and back up before any DDL; never backfill claims."""

import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import models  # Register referenced legacy tables; no database connection.
import models_evidence
from models_provenance import PROVENANCE_TABLES
from sqlalchemy.dialects.sqlite import dialect
from sqlalchemy.schema import CreateTable


def table_snapshot(connection):
    schema = connection.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name").fetchall()
    result = {}
    for name, sql in schema:
        quoted = '"' + name.replace('"', '""') + '"'
        rows = connection.execute("SELECT * FROM " + quoted + " ORDER BY rowid").fetchall()
        result[name] = {"schema": sql, "count": len(rows), "rows_sha256": hashlib.sha256(repr(rows).encode()).hexdigest(),
                        "columns": connection.execute("PRAGMA table_info(" + quoted + ")").fetchall(),
                        "foreign_keys": connection.execute("PRAGMA foreign_key_list(" + quoted + ")").fetchall()}
    return result


def migrate(database, backup_directory, *, tables=None, phase="phase1", required_tables=()):
    database = Path(database).resolve(strict=True)
    expected = {table.name: str(CreateTable(table).compile(dialect=dialect())).strip() for table in (PROVENANCE_TABLES if tables is None else tables)}
    normalize = lambda value: " ".join(value.split())
    # Read-only inspection, before making even a backup directory.
    with closing(sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)) as reader:
        before = table_snapshot(reader)
        if reader.execute("PRAGMA integrity_check").fetchall() != [("ok",)] or reader.execute("PRAGMA foreign_key_check").fetchall():
            raise ValueError("Existing database integrity failure; migration stopped.")
    for table, columns in {"app_analyses": {"id", "apk_hash", "version_name"}, "evidence_sources": {"id", "app_id", "raw_evidence", "file_reference"}}.items():
        if table not in before or not columns.issubset({column[1] for column in before[table]["columns"]}):
            raise ValueError("Legacy schema conflict; migration stopped: " + table)
    for table in required_tables:
        expected_schema = str(CreateTable(table).compile(dialect=dialect())).strip()
        if table.name not in before or normalize(before[table.name]['schema']) != normalize(expected_schema):
            raise ValueError("Prerequisite schema conflict; migration stopped: " + table.name)
    existing = set(expected).intersection(before)
    if existing and (existing != set(expected) or any(normalize(before[name]["schema"]) != normalize(expected[name]) for name in existing)):
        raise ValueError("Partial or conflicting provenance schema; migration stopped without changes.")
    if existing:
        return {"status": "already_applied", "database": str(database)}
    backup_directory = Path(backup_directory).resolve()
    backup_directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup = backup_directory / ("before_" + phase + "_" + stamp + ".db")
    audit_path = backup.with_suffix(".json")
    with closing(sqlite3.connect(database.as_uri() + "?mode=rw", uri=True)) as writer:
        writer.execute("PRAGMA foreign_keys=ON")
        writer.execute("BEGIN IMMEDIATE")
        try:
            if table_snapshot(writer) != before:
                raise ValueError("Database changed after inspection; retry after stopping writers.")
            with backup.open("xb"):
                pass
            with closing(sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)) as reader, closing(sqlite3.connect(backup)) as dest:
                reader.backup(dest)
                if table_snapshot(dest) != before or dest.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
                    raise ValueError("Backup verification failed; migration stopped.")
            report = {"status": "backed_up", "database": str(database), "backup": str(backup),
                      "backup_sha256": hashlib.sha256(backup.read_bytes()).hexdigest(), "before": before}
            audit_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
            for sql in expected.values():
                writer.execute(sql)
            after = table_snapshot(writer)
            if any(after[name] != snapshot for name, snapshot in before.items()):
                raise ValueError("Legacy data or schema changed; rolling back migration.")
            if writer.execute("PRAGMA integrity_check").fetchall() != [("ok",)] or writer.execute("PRAGMA foreign_key_check").fetchall():
                raise ValueError("Post-migration integrity check failed.")
            writer.commit()
            report.update(status="applied", added_tables=list(expected), legacy_rows_preserved=True)
            audit_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
            return {key: value for key, value in report.items() if key != "before"}
        except Exception:
            writer.rollback()
            raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", required=True)
    parser.add_argument("--backup-directory", required=True)
    args = parser.parse_args()
    print(json.dumps(migrate(args.database, args.backup_directory), indent=2))
