"""Database locations and safeguards; no database connections on import."""

from pathlib import Path
import os


DATABASE_PATH = Path(__file__).resolve().with_name("privacy_analyzer.db")


def configured_database_path():
    override = os.environ.get("PRIVACYGUARD_DATABASE_PATH")
    if not override:
        return DATABASE_PATH
    path = Path(override).expanduser()
    if not path.is_absolute():
        raise ValueError("PRIVACYGUARD_DATABASE_PATH must be an absolute path.")
    return path.resolve()


def validate_seed_destination(destination):
    """Accept only a new demo database, never the recovered application database."""
    requested = Path(destination).expanduser()
    target = requested.resolve()
    if target == DATABASE_PATH.resolve():
        raise ValueError("Refusing to seed the recovered application database.")
    # is_symlink also catches dangling links, which exists() does not.
    if requested.is_symlink() or target.exists():
        raise ValueError("Seed destination already exists; it will not be modified.")
    if not target.parent.is_dir():
        raise ValueError("Seed destination parent directory must already exist.")
    for suffix in ("-wal", "-shm", "-journal"):
        sidecar = Path(str(target) + suffix)
        if sidecar.exists() or sidecar.is_symlink():
            raise ValueError("SQLite recovery files exist for this destination; choose a new path.")
    return target


def reserve_seed_destination(destination):
    """Exclusively create a fresh file; never truncate a file created meanwhile."""
    target = validate_seed_destination(destination)
    with target.open("xb"):
        pass
    return target
