# Recovery progress

## Step 5 — Phase 4 independent benchmark workflow (2026-09-29)

Implemented isolated benchmark tables, independent evidence-backed review and approval, a separate blinded reviewer API, researcher authentication across analysis/research endpoints, explicit SYNTHETIC/REAL_WORLD selection, frozen dataset evaluation, TP/FP/FN/TN, micro/macro metrics, kappa, A–E benchmark ablation, FP/FN cause notes, reproducibility snapshots and CSV/JSON exports. Ground truth never comes automatically from analysis. The frontend has Benchmark and standalone Review workflows.

The additive migration preserved all 33 prior schemas/rows and added 11 empty tables, bringing the database to 44 tables. Backup: `recovery_backups/phase4/before_phase4_20260928T191617287923Z.db`. Integrity and foreign-key checks pass; no synthetic benchmark records or generated research results were added to the recovered database.

Validation: 175 tests pass; frontend build/new module lint pass; actual two-service HTTP workflow passes on a disposable synthetic copy. See `phase4_deliverables.md` and `recovery_backups/phase4/final_validation.json` for setup, scope and evidence.

Empirical work stops here until verified real APKs and independent human reviews are supplied. Metrics remain N/A in the recovered dataset; no empirical accuracy or overall research-readiness claim is made. Earlier entries below remain historical snapshots.

## Step 4 — Phase 3 Privacy Evidence Graph (2026-09-29)

Implemented deterministic graph projection, central structural/semantic validation, version/run-scoped SQLite persistence and APIs, template explanations and the Privacy Evidence Graph tab. Every edge is traceable to same-run evidence. Static API references use REFERENCES_API_FOR; ACCESSES_DATA is reserved until actual access evidence is supported. Domain-only evidence does not create sensitive transmission. Unknown/unconnected observations remain in provenance with explicit graph omissions.

Reused `app_versions` identity without overwriting legacy metadata; uncomputed version metrics are NULL. The backed-up additive migration preserved all 30 previous table schemas/rows and added three empty graph tables. Backup: `recovery_backups/phase3/before_phase3_20260928T184456267031Z.db`. The database has 33 tables and passes integrity/foreign-key checks.

Validation: 126 tests pass, frontend build and graph component lint pass. Actual backend HTTP graph creation, scoped reads, app detail, index, idempotency and wrong-version rejection pass on an isolated copy with a synthetic fixture. No synthetic records were inserted into the recovered database. See `phase3_deliverables.md` and `recovery_backups/phase3/final_validation.json`.

Next is Phase 4 independent ground truth, blinded review, benchmark/evaluation and research exports. Empirical accuracy remains unavailable. Earlier entries below remain historical snapshots.

## Step 3 — Phase 2 deterministic fusion (2026-09-28)

Implemented a typed ontology, strict normalization of six source families, an adapter for existing analyzers, deterministic fusion, heuristic Evidence Strength Scores, configuration A–E replay and persistent run/configuration metadata. Permission/API/SDK/domain presence does not become proof of runtime collection or sensitive transmission. Network and disclosure annotations require explicit evidence anchors; acquisition limitations remain documented.

The additive migration inspected and backed up the database, preserved all 26 previous tables and rows, and added four empty tables. Backup: `recovery_backups/phase2/before_phase2_20260928T181852864662Z.db`. Database integrity and foreign-key checks pass. No synthetic records were added to the recovered database.

Validation: 84 tests pass, frontend build and changed standalone component lint pass, actual backend startup/HTTP reads pass on an isolated copy. Findings & Provenance selects a run and exposes normalized evidence, configuration, score meaning and ablation replay. Reports separate configurations. Empirical accuracy remains unavailable. See `phase2_deliverables.md` and `recovery_backups/phase2/final_validation.json`.

Next is Phase 3 graph semantics/validation, followed by Phase 4 independent evaluation. Earlier entries below are historical snapshots.

## Step 2 — Phase 1 provenance (2026-09-28)

Phase 1 is implemented and its additive migration has been applied with a verified backup. All 22 legacy table schemas and row contents were preserved; four new provenance tables were added. New analyses have linked observations and limited interpretations, an API and a Findings & Provenance view. Legacy results remain unverified. Upload no longer creates the fabricated SDK/collection/security/prediction records identified in the audit.

Validation: 34 tests pass, dependency consistency passes, frontend build passes, and actual backend startup/HTTP reads pass against an isolated migrated database copy. A Windows/Python 3.12 dependency baseline is now locked. The application no longer creates tables at import time.

See `phase1_deliverables.md` for implementation, migration backup, setup and scope; see `RESEARCH_VALIDATION.md` for the separation between software tests and empirical validation. Formal Phase 2 fusion and all benchmark metrics remain incomplete. The Step 1 notes below describe the earlier state and are retained as history.

## Step 1 — database preservation safeguards (2026-09-28)

The Phase 0 audit is preserved in `RECOVERY_AUDIT.md` as a snapshot of the recovered commit. This document records subsequent changes.

### Completed

- Removed the destructive `drop_all` call from `backend/seed_data.py`.
- Seeding requires an explicit `--database` destination and rejects every existing destination, including empty files, the recovered application database, and destinations with SQLite recovery sidecars.
- A new destination is reserved with exclusive file creation, so a file created between validation and reservation cannot be truncated.
- Importing the seed script is rejected before loading database modules or executing seed operations.
- The seeder uses its own engine for the new demo file; it no longer uses the application's session factory.
- The application database path now resolves to `backend/privacy_analyzer.db` relative to the Python module, independent of the shell's working directory. This matches the database inspected during the audit.
- Seed-script documentation and output identify its hand-authored records as synthetic demonstration data, not verified research ground truth. This is not a substitute for the dataset-type fields required in Phase 4.

No original records or database schemas were modified. No migration was necessary for these code changes.

### Usage

Once the project's backend dependencies are explicitly established, demo data can be generated separately:

```powershell
python backend/seed_data.py --database ./privacyguard_demo.db
```

The destination's parent directory must already exist. Existing destinations are always refused; there is no force/reset option. If a seed run fails after reservation, the new file is retained and subsequent attempts refuse to overwrite it. Inspect it and choose another new destination. The application continues to use its recovered database, not this demo file.

### Validation

Run the standard-library preservation tests from the repository root:

```powershell
python -B -m unittest discover -s backend/tests -v
```

**11 tests passed** under a temporary official CPython 3.14.0 embedded runtime. The runtime was downloaded into the system temporary directory; no project dependencies were installed, pinned, or upgraded. This test runtime does not establish the supported backend runtime or SQLAlchemy/Androguard versions.

The tests exercise startup-folder independence, protection of the recovered path even when absent, preservation of a real SQLite table and its rows/bytes, refusal of empty existing files, sidecar preservation, one-time file reservation, competing file creation, missing-parent refusal, CLI destination requirements, CLI refusal before dependency loading, and import-time protection.

The first test run exposed an unclosed SQLite test connection during Windows temporary-file cleanup. The test now closes its connections explicitly; the complete rerun passed.

Additional checks:

- All four new/changed Python files parsed successfully.
- Recovered database opened read-only: `PRAGMA integrity_check` returned `ok`; `PRAGMA foreign_key_check` returned no violations.
- Application row count remains 5.
- Original SHA-256 remains `2B67609F70376CA1D78B4BFAC18CD00173D2DA1B4D77DAA786FB199EE2B3F7B5`, identical to the audit baseline.
- Existing verified backup: `recovery_backups/20260928_224818/privacy_analyzer.db`.

Successful demo population and full backend startup were not executed because backend dependency versions remain unresolved. Tests used disposable files, not mutations of the recovered database. These results validate preservation behavior; they are not empirical privacy-detection accuracy.

### Remaining work

Phase 1 provenance has not been implemented. Resolve and document compatible backend dependency versions, then introduce additive provenance migrations and persistent finding-to-evidence relationships with behavior tests.

The audit's unsupported collection/SDK claims, mock policy/Data Safety inputs, and LLM grounding issues remain open. `main.py` still contains its pre-existing startup `create_all` call and upload writes; these safeguards specifically remove destructive seeding and database-path ambiguity. Future startup/migration tests must use an isolated database after introducing an explicit safe configuration path. No claim of overall research readiness is made.
