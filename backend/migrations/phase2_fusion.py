"""Add Phase 2 metadata with backup and full legacy-table preservation checks."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from migrations.phase1_provenance import migrate as additive_migration
from models_provenance import PROVENANCE_TABLES
from models_fusion import FUSION_TABLES


def migrate(database, backup_directory):
    return additive_migration(database, backup_directory, tables=FUSION_TABLES,
                              phase='phase2', required_tables=PROVENANCE_TABLES)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', required=True)
    parser.add_argument('--backup-directory', required=True)
    args = parser.parse_args()
    print(json.dumps(migrate(args.database, args.backup_directory), indent=2))
