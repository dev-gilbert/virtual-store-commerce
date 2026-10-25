import sqlite3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.backup_database import backup_sqlite, sha256


def test_sqlite_backup_is_integrity_checked_and_restorable(tmp_path: Path):
    source = tmp_path / "source.sqlite3"
    backup = tmp_path / "backup.sqlite3"
    restored = tmp_path / "restored.sqlite3"
    with sqlite3.connect(source) as db:
        db.execute("CREATE TABLE sample (id INTEGER PRIMARY KEY, value TEXT NOT NULL)")
        db.execute("INSERT INTO sample(value) VALUES ('before-backup')")
        db.commit()

    backup_sqlite(source, backup)
    assert sha256(backup)
    with sqlite3.connect(source) as db:
        db.execute("UPDATE sample SET value='changed-after-backup'")
        db.commit()

    backup_sqlite(backup, restored)
    with sqlite3.connect(restored) as db:
        assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert db.execute("SELECT value FROM sample").fetchone()[0] == "before-backup"
