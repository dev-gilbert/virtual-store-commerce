"""Create verified database backups for SQLite or PostgreSQL deployments."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy.engine import make_url


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def backup_sqlite(source: Path, destination: Path) -> None:
    import sqlite3
    destination.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(f"file:{source.resolve()}?mode=ro", uri=True) as src:
        with sqlite3.connect(destination) as dst:
            src.backup(dst)
            check = dst.execute("PRAGMA integrity_check").fetchone()[0]
            if check != "ok":
                raise RuntimeError(f"SQLite integrity check failed: {check}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default=os.getenv("BACKUP_DIR", "./backups"))
    args = parser.parse_args()
    database_url = os.getenv("DATABASE_URL", "sqlite:///./virtual_store.db")
    url = make_url(database_url)
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    if url.drivername.startswith("sqlite"):
        if not url.database or url.database == ":memory:":
            raise SystemExit("A file-backed SQLite DATABASE_URL is required for backups.")
        source = Path(url.database)
        if not source.is_absolute():
            source = Path.cwd() / source
        if not source.exists():
            raise SystemExit(f"Database file not found: {source}")
        artifact = output_dir / f"virtual-store-{stamp}.sqlite3"
        backup_sqlite(source, artifact)
        kind = "sqlite"
    elif url.drivername.startswith("postgresql"):
        artifact = output_dir / f"virtual-store-{stamp}.dump"
        command = ["pg_dump", "--format=custom", "--no-owner", "--file", str(artifact), database_url]
        subprocess.run(command, check=True)
        kind = "postgresql"
    else:
        raise SystemExit(f"Unsupported database driver: {url.drivername}")
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "database_type": kind,
        "artifact": artifact.name,
        "size_bytes": artifact.stat().st_size,
        "sha256": sha256(artifact),
    }
    manifest_path = artifact.with_suffix(artifact.suffix + ".manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"backup": str(artifact), "manifest": str(manifest_path), **manifest}, indent=2))


if __name__ == "__main__":
    main()
