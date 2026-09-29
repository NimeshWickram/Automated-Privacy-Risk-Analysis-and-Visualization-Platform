# Phase 1 — evidence provenance

Implemented 2026-09-28, following `RECOVERY_AUDIT.md` and the database-preservation safeguards. This is a new, tested recovery implementation; it is not a claim to have recovered the lost laptop's original Phase 1.

## Delivered behavior

New APK analyses persist this explanation chain:

```text
RiskFinding (interpretation, rule ID)
  -> FindingEvidence (SUPPORTS / CORROBORATES / CONTRADICTS, rationale)
  -> EvidenceSource + EvidenceProvenance (observation, source locator, snapshot)
  -> AnalysisRun (application ID, APK SHA-256, app version, analyzer environment)
```

The initial adapter generates only limited interpretations:

| Observation | Finding | Explicit limitation |
|---|---|---|
| Manifest permission declaration | Sensitive Permission Capability | Does not establish access, collection, transmission or unnecessary use |
| DEX string/API indicator | Potential Sensitive Data Access | Does not establish an invocation or runtime collection |
| Manifest SDK signature | Third-Party SDK Presence | Does not establish SDK data access or transmission |
| Fetched policy text | Source document retained, no risk finding | Claims and contradictions are not validated yet |

Permission-only findings deliberately do not say “unnecessary”: that requires additional context. Formal fusion and its finding categories are Phase 2 work.

`models_provenance.py` adds `analysis_runs`, `evidence_provenance`, `risk_findings`, and `finding_evidence`. Existing source/application/model fields are not repurposed. Each finding created by the service requires at least one SUPPORTS link; all links must reference evidence in the same analysis run. Composite foreign keys also reject cross-run links at database level when foreign keys are enabled. Application engine connections now explicitly enable SQLite foreign keys.

Evidence snapshots contain the observed text, source type, observation kind, category, description and source locator. They have a SHA-256 digest and collection timestamp. The API checks snapshot digests and application/run ownership before returning linked findings. This detects snapshot corruption; it is not a signed, adversary-proof audit log. There is no public mutation endpoint for findings or links.

Manifest raw evidence is a serialized declaration extracted by Androguard, not the APK's original XML byte formatting. DEX scanning retains the complete matched string and correct multidex filename, but provides no call-site line number or taint path. Scanner failures are recorded as failed/partial/unavailable rather than silently reported as successful completion.

All six required source families can have exact raw observations recorded by the provenance adapter, including separately supplied SDK, network and Data Safety records. There is no new network capture or real Data Safety ingestion implementation in Phase 1. A network observation alone creates no transmission finding.

## Integration and research-integrity corrections

- Existing `evidence_engine.py` and permission/SDK analyzers remain in use. The provenance adapter consumes raw evidence records; it does not promote the legacy fused dictionaries into validated findings.
- Upload no longer consumes mock Data Safety or mock/LLM policy claims. Supplied policy URLs can produce retained extracted text only. Missing sources remain unavailable.
- Upload no longer invents Firebase/Facebook SDK presence, personal data collection, storage/sharing, payment security, incidents, leakage probabilities or TLS observations.
- SDK catalog capabilities/domains are not written as observed access or communications. SDK disclosure status is unknown without declaration evidence.
- New run metadata contains Python/OS/analyzer versions, APK SHA-256, app version, analysis version, source coverage and timestamp. Formal configuration IDs, ontology/rule configuration manifests and ablation are deferred to Phase 2.
- Evidence Strength Score is explicitly unassigned (`null`) in Phase 1. Legacy confidence values are not presented as calibrated probabilities or renamed into an invented score.
- App detail includes provenance; `GET /api/apps/{app_id}/provenance` returns the linked explanation. Missing apps return 404, corrupted provenance fails closed, and uploads return 503 before analysis when migration tables are absent.
- The Findings & Provenance tab separates observation from interpretation, displays raw source evidence, run metadata and snapshot hashes. Legacy analyses display an unverified-data banner; no old findings were backfilled or labeled verified.
- Report generation now renders a deterministic summary from linked findings. Live LLM generation and mock fallback output are bypassed until grounding is validated. Existing stored reports remain preserved and subject to the legacy banner. Legacy helper functions remain in the module, but the report endpoint does not call them.
- Empty disclosure lists no longer claim policy consistency. Dynamic analysis is not reported complete without capture evidence.

## Migration and preservation

`backend/migrations/phase1_provenance.py` performs read-only schema/table/row inspection, rejects conflicting/partial provenance schemas, checks integrity and foreign keys, locks out writers, creates and verifies a separate SQLite backup, and then creates only the four new tables in a transaction. Before commit, it compares every legacy schema, row count and row-content digest. Injected post-DDL failures are tested to roll back. Reapplying the matching migration is a no-op.

Applied successfully to the recovered database on 2026-09-28. Existing 22 tables, including all 5 application records, 89 evidence records, 11 disclosure mismatches and 2 saved reports, were preserved. Four new tables are empty until a new APK is analyzed; no synthetic test data was inserted into the recovered database. The database now has 26 tables.

Backup:

`recovery_backups/phase1/before_phase1_20260928T174904640177Z.db`

Backup SHA-256:

`e66e3d4d5f2b8abe247934de74473afced31282016b797701afb27467eae04eb`

The matching `.json` audit records the original schemas, counts, row hashes, backup and migration outcome. As with the Phase 0 backup, `.db` backups are ignored by Git and exist locally. They have not been uploaded elsewhere.

Post-migration database SHA-256:

`8aa618a415accd6024e419b35cb296b0c8e37b49e924759039d7d4d643abe2b4`

The file hash changed because tables were added; every pre-existing table schema and row was compared and preserved. The original Phase 0 backup is also retained. Startup no longer invokes automatic `create_all` against the application database.

## Reproducible setup

Tested recovery baseline: Windows x64, CPython 3.12.10, Node 22.16.0, npm 10.9.2. This explicitly replaces the previously unspecified environment; it does not establish what the failed laptop used.

Exact Python packages, including transitive dependencies, are recorded in `backend/requirements-lock-windows-py312.txt`, referenced by `backend/requirements.txt`. Key versions: SQLAlchemy 2.0.54, FastAPI 0.141.1, Pydantic 2.13.5, Androguard 4.1.3, Requests 2.34.2, BeautifulSoup 4.15.0, google-generativeai 0.8.5, Uvicorn 0.54.0, python-multipart 0.0.32 and HTTPX 0.28.1. `pip check` passes. The lock is environment-specific, not a cross-platform guarantee or a hash-locked supply-chain manifest. The [Androguard release](https://pypi.org/project/androguard/4.1.3/) retains the `core.apk`/`core.dex` APIs used by this project.

Commands from repository root with a normal Python 3.12 installation:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
.\.venv\Scripts\python.exe -B -m unittest discover -s backend/tests -v
.\.venv\Scripts\python.exe backend/migrations/phase1_provenance.py --database backend/privacy_analyzer.db --backup-directory recovery_backups/phase1
.\.venv\Scripts\python.exe -m uvicorn main:app --app-dir backend
```

The migration command above is for the recovered legacy database and is already applied in this workspace. It deliberately refuses missing databases and incompatible legacy schemas rather than creating an ambiguous replacement. `PRIVACYGUARD_DATABASE_PATH` may point to an absolute path for an isolated copy; relative overrides are rejected. This is separate from the protected default path used by the seed safeguards.

Frontend:

```powershell
npm ci
npm run build
npm run dev
```

Validation used temporary portable Python and Node runtimes rather than installing system-wide tools or creating `.venv`. Those temporary runtimes may be removed by OS cleanup; use the setup commands above for a durable development environment.

## Validation results

- **34 automated tests pass:** 11 database-preservation tests and 23 Phase 1 tests. Coverage includes exact source links, static capability/reference distinction, no network transmission inference, metadata/digests, mandatory support, relationship types, cross-run/app isolation, corruption rejection, legacy non-backfill, mock/LLM exclusion, HTTP provenance route, synthetic upload behavior, scanner failure, full multidex string retention, readiness transaction safety, migration refusal/backup/idempotence and rollback.
- A failing early test exposed engine-level schema inspection rolling back a pending transaction with a single-connection SQLite pool. Inspection now uses the current session connection, with a regression test.
- `pip check`: passed.
- Frontend production build: passed, with an existing large-chunk warning (main bundle exceeds 500 kB).
- Real Uvicorn startup and HTTP requests passed on an isolated copy of the migrated database: app listing, app detail, provenance, comparison and OpenAPI. All 5 legacy apps remained readable. The verification server was stopped afterward.
- SQLite integrity and foreign-key checks passed during migration; every legacy schema and row digest matched before/after.
- `git diff --check`: passed.
- The test client emits an HTTPX deprecation warning from Starlette; tests pass. No test-client migration was included in this phase.

## Limits and next phase

These are **synthetic implementation tests**, not empirical validation. No real APK was re-analyzed during this phase, no live Gemini call was made, and no benchmark accuracy was calculated. The upload integration test supplies a synthetic APK parser fixture while running the actual pipeline adapter, ORM and API persistence.

Formal normalization, deterministic multi-source fusion, corroboration/contradiction rules, evidence-strength weights, graph semantics, version/configuration graph isolation, ablation, independent ground truth, blinded review, evaluation metrics and research exports remain future phases. Run isolation implemented here is not proof of the full Phase 3 version graph requirement.

Legacy risk scores, permissions/SDK heuristics, chatbot templates and stored demo claims remain research limitations. The new finding service is the only supported write path for linked findings; direct arbitrary SQL can still create an orphan finding, which the reader rejects. DB-level deferred support constraints, immutable audit enforcement, reviewer workflows and full pipeline semantic validation are not claimed complete.

Next: Phase 2 ontology and source normalization, then explicit deterministic fusion rules and ablation traceability, keeping these provenance links intact.
