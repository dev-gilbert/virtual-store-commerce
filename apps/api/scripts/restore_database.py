"""Restore a verified backup. Destructive restores require explicit --confirm."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy.engine import make_url
from backup_database import backup_sqlite, sha256


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("backup", type=Path)
    parser.add_argument("--confirm", action="store_true", help="Required to overwrite the configured database.")
    args = parser.parse_args()
    if not args.confirm:
        raise SystemExit("Restore not run. Re-run with --confirm after checking the target database.")
    artifact = args.backup.resolve()
    if not artifact.is_file():
        raise SystemExit(f"Backup file not found: {artifact}")
    manifest_path = artifact.with_suffix(artifact.suffix + ".manifest.json")
    if not manifest_path.is_file():
        raise SystemExit("Backup manifest is missing; refusing an unverified restore.")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if sha256(artifact) != manifest.get("sha256"):
        raise SystemExit("Backup checksum does not match its manifest.")
    database_url = os.getenv("DATABASE_URL", "sqlite:///./virtual_store.db")
    url = make_url(database_url)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    if manifest.get("database_type") == "sqlite" and url.drivername.startswith("sqlite"):
        if not url.database or url.database == ":memory:":
            raise SystemExit("A file-backed SQLite DATABASE_URL is required for restore.")
        target = Path(url.database)
        if not target.is_absolute():
            target = Path.cwd() / target
        if target.resolve() == artifact:
            raise SystemExit("Backup and target database paths must differ.")
        if target.exists():
            safety = target.with_name(target.name + f".pre-restore-{stamp}.sqlite3")
            backup_sqlite(target, safety)
            print(f"Safety backup created: {safety}")
        backup_sqlite(artifact, target)
        print(f"Restored SQLite database: {target}")
    elif manifest.get("database_type") == "postgresql" and url.drivername.startswith("postgresql"):
        subprocess.run(["pg_restore", "--clean", "--if-exists", "--no-owner", "--dbname", database_url, str(artifact)], check=True)
        print("Restored PostgreSQL database. Run migrations and application smoke tests before reopening traffic.")
    else:
        raise SystemExit("Backup database type does not match DATABASE_URL.")


if __name__ == "__main__":
    main()
