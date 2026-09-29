# Phase 2 — Multi-source normalization and deterministic fusion

Implemented 2026-09-28. This phase adds implementation capability, not evidence of real-world accuracy. Phase 3 graph persistence/validation and Phase 4 independent benchmark evaluation are not implemented.

## Architecture and compatibility

The existing APK/DEX, permission and SDK analyzers remain. The new path is:

`legacy observations → adapter.py → normalization.py → canonical source records → fusion_engine.py → Phase 1 evidence/finding links + Phase 2 metadata`

- `privacy_ontology.py` separates sources, data categories, observed/static indicators, claims and interpreted findings. Versions: `privacy-ontology-1.0`, `privacy-fusion-1.0`, `phase2-fusion-1.0`.
- `adapter.py` maps manifest declarations, DEX indicators, SDK signatures and fetched policy documents. It does not promote legacy fused descriptions, confidence, mock claims or SDK-dependent permission explanations into canonical findings. Legacy heuristic views remain separate compatibility outputs.
- `normalization.py` validates evidence anchors, retains unknown categories, filters enabled sources, removes identical records and sorts canonical records.
- `fusion_engine.py` applies explicit rules without an LLM, network call, random decision or database lookup.
- `fusion_service.py` persists normalized observations and finding assessments through the existing Phase 1 provenance links. Reads verify the retained bundle, normalization, snapshots, configuration and recomputed semantic output. Replay uses the unchanged saved acquisition bundle.

Existing records are not backfilled as verified evidence. Phase 1 runs retain their original observations and score-unassigned interpretation. The four new tables are `analysis_configurations`, `fusion_runs`, `normalized_evidence` and `finding_assessments`; there are no replacements for legacy tables.

## Source semantics and acquisition limits

| Source | Accepted evidence | Interpretation boundary |
| --- | --- | --- |
| Manifest | XML permission declaration | Capability only; no collection assertion. Unknown permission mappings stay unknown. |
| Code | Static API indicator occurring in a retained DEX string | `API_REFERENCE`; potential access only. `API_ACCESS` is reserved and rejected for these static inputs. |
| SDK | Named SDK with a signature occurring in retained evidence | Presence only; no third-party access or transmission assertion. |
| Network | Structured domain observation, or an outbound captured payload with an explicit field/category annotation | Domain alone produces no sensitive-transmission finding. Payload attribution must retain JSON pointer, category basis, annotator, capture SHA-256 and timezone-aware capture timestamp. |
| Policy | Retained document or explicit evidence-backed claim annotation | Documents and silence do not establish denial. Affirmative/negative claims require a verbatim quote, explicit category, collection scope and manual annotation metadata. |
| Data Safety | Retained document or equivalent explicit claim annotation | Same conservative claim rules. No mock scraper output is accepted. |

APK upload currently acquires manifest declarations, manifest SDK signatures and static DEX references, plus an optional fetched policy document. The legacy engine's observation coverage remains a limitation: this phase does not add comprehensive decompilation or runtime instrumentation. Network capture and live Data Safety acquisition remain unavailable. Fetched policy text is not automatically interpreted as verified claims. Six-source normalization is available through explicit imports; this is not a claim that the upload pipeline acquires all six sources.

Import validation establishes internal evidence anchors, not external authenticity. A supplied capture hash is recorded but the API does not independently retrieve/authenticate its capture artifact; quotes do not prove the correctness or applicability of a manual claim interpretation. Category annotations and reviewer names are not independent ground truth or authenticated reviews. Imported evidence must be collected and checked by the researcher. Missing source coverage is not negative evidence.

## Deterministic rules and Evidence Strength Score

Scores are fixed rule-based evidence-strength heuristics, not calibrated probabilities, accuracy measurements or legal conclusions. Base points are Manifest 40, Code 60, SDK 50, Network 90, Policy 70 and Data Safety 80, divided by 100 for display.

| Rule | Preconditions and outcome | Score / severity |
| --- | --- | --- |
| Permission capability | Mapped permission with no corresponding code reference: Sensitive Permission Capability | 0.40 / low |
| Permission context | Explicit excessive/unnecessary context with a recorded basis and analyzer: Potentially Unnecessary Permission | 0.40 / moderate |
| Static access | Mapped API reference: Potential Sensitive Data Access; permission may corroborate capability only | 0.60; 0.70 with manifest / moderate |
| SDK presence | Retained SDK signature: Third-Party SDK Presence | 0.50 / low |
| Payload transmission | Outbound payload with anchored category attribution: Potential Data Transmission to its recorded domain | 0.90 / high |
| Payload versus denial | Category-attributed outbound payload plus explicit collection denial: Potential Disclosure Inconsistency | Minimum of network and denying-claim weights / high |
| Claim versus claim | Explicit positive and negative collection claims for the same category: Potential Disclosure Inconsistency | Minimum of claim weights / moderate |

Permission-only evidence does not establish that a permission is unnecessary; the context rule needs additional explicit justification. Automatic legacy necessity explanations are excluded because they can include SDK assumptions and an unverified educational category. Context annotations supplied in an import are held fixed during ablation and must be disclosed as researcher-supplied context.

Static API references, SDKs and permissions alone cannot contradict a collection denial. Absence of detection does not create an over-disclosure finding. `UNKNOWN` and `NOT_MENTIONED` are not denials. Repeated observations do not increase scores. Positive collection claims are not proof that collection occurred. Disclosure rules require review of category attribution, policy applicability and collection scope; the engine makes no legal determination.

Determinism means identical normalized input and configuration produce identical semantic JSON and its SHA-256, including across input order and tested Python hash seeds. Persistence IDs and timestamps differ between runs and are excluded from semantic hashes. Exact duplicate records are removed. Canonical JSON sorts keys and rejects non-finite numbers. Configuration IDs hash the complete versioned definition, source selection and weights. Changes to mappings, rules or scoring must advance their versions; historical rule execution will require retaining the corresponding implementation, not silently reinterpreting old runs with new rules.

## Ablation and run isolation

| Configuration | Admitted sources |
| --- | --- |
| A | Manifest |
| B | Manifest + Code |
| C | Manifest + Code + SDK |
| D | Manifest + Code + SDK + Network |
| E | Manifest + Code + SDK + Network + Policy + Data Safety |

These are evidence-admission/fusion ablations over a retained acquisition bundle. They do not disable acquisition instrumentation, measure analysis cost, or establish detector accuracy. Excluded raw observations remain in the saved bundle for replay but are not admitted to normalization/findings for that run. For an APK with no captured traffic or validated claims, later configurations may legitimately add no findings.

Each run records application identity, APK SHA-256, application version, analysis version, content-addressed configuration, enabled sources and coverage, ontology/rule versions, original bundle/hash, normalized input/hash, semantic output/hash, environment/tool versions, timestamp and optional source-run ID. Findings and normalized observations have same-run composite foreign keys. Import envelopes must match the application's hash/version; another application's run cannot be replayed even if its APK hash is the same. Version-aware graph queries and the dedicated application-version architecture belong to Phase 3.

Runs are append-only through these APIs. Atomic writes use nested transactions with an explicit outer SQLite transaction, so a failed write or failed response validation cannot leave a partial or unintentionally committed run. A multi-configuration ablation is atomic. No arbitrary rule weights or client-generated findings are accepted.

## API and frontend

- `GET /api/analysis-configurations`: full canonical definitions of A–E, score meaning and ablation scope.
- `POST /api/analyze`: existing multipart upload, with optional `analysis_configuration` (`A`–`E`, default `E`). Retains the existing `app_id` response and adds run/configuration IDs.
- `POST /api/apps/{app_id}/fusion`: explicitly import `apk_sha256`, `application_version`, `records`, `source_status` and optional `configuration`. Returns the new run ID and provenance. Unsupported fields at the envelope level are rejected.
- `POST /api/apps/{app_id}/ablation`: `{"source_run_id": 123, "configurations": ["A", "B", "C", "D", "E"]}`. Requires an existing Phase 2 run for this application. Returns new run IDs and provenance.
- `GET /api/apps/{app_id}/provenance`: enriched per-run configuration, normalized observations, scores, hashes and linked findings. Legacy status remains explicit.

An example individual manifest record for the import API is:

```json
{
  "source": "MANIFEST",
  "kind": "permission",
  "raw_evidence": "<uses-permission android:name=\"android.permission.ACCESS_FINE_LOCATION\"/>",
  "file_reference": "AndroidManifest.xml",
  "description": "Declared location permission"
}
```

Wrap real records in an envelope with the exact stored APK hash/version and honest source coverage, such as `{"MANIFEST": "observed", "NETWORK": "not_performed"}`. Do not submit this illustrative record as a real observation without inspecting that APK. Synthetic examples of all six input shapes live in `backend/tests/test_phase2_fusion.py`, explicitly designated implementation fixtures.

Upload now offers A–E. Findings & Provenance selects one run, displays source coverage and normalized evidence, labels scores and supports A–E replay. Deterministic reports group findings by run/configuration and retain source links. Upload status no longer claims MobSF, emulator execution or network capture, and does not invent percentage progress.

Legacy dashboard risk scores, cached reports and old evidence views are not Phase 2 evaluation results; use the run-selected Findings & Provenance view for configuration comparisons. The legacy dashboard has not been redesigned into the full Phase 4 research interface.

## Safe migration and backup

Applied `backend/migrations/phase2_fusion.py` after inspecting the existing database and passing migration tests. It reuses the backed-up additive migration machinery, validates Phase 1 prerequisites and refuses partial/conflicting schemas. Every pre-existing table schema and row digest is compared before/after.

- Before: 26 tables; database SHA-256 `8aa618a415accd6024e419b35cb296b0c8e37b49e924759039d7d4d643abe2b4`.
- Backup: `recovery_backups/phase2/before_phase2_20260928T181852864662Z.db`.
- Backup SHA-256: `93e36182edb4ce27d11b7de96f003a7430b4173faea753bb1367e87804649a58`.
- Matching `.json`: schemas, columns, foreign keys, row counts/digests and migration outcome.
- After: 30 tables; database SHA-256 `a73a431499a5d61b2b1dbe3f37c0a2227d78542b06029980cec2f8b5ca4a65a4`.
- All previous schemas/rows preserved, including five applications; four new tables empty. No fixtures were inserted into the recovered database.
- SQLite integrity is `ok`; no foreign-key violations. Online backup can change file layout/hash while preserving the compared schemas and rows. Backups are local and `.db` files are ignored by Git; earlier backups remain present.

After the Phase 1 setup, the repeatable migration command is:

```powershell
python -B backend/migrations/phase2_fusion.py --database backend/privacy_analyzer.db --backup-directory recovery_backups/phase2
```

The migration is already applied in this workspace; a matching existing schema returns `already_applied`. No destructive downgrade/reset is supplied.

## Validation

84 automated tests pass, comprising the previous 34 tests and 50 Phase 2 tests. They exercise six-source normalization, conservative mappings, malformed anchors, explicit denial versus silence, static versus runtime distinctions, domain versus payload evidence, deterministic order/hash-seed behavior, duplicate invariance, configuration isolation, same-bundle replay, cross-application/hash/version rejection, persistence integrity, rollback, API import/ablation, report scoping and preservation of populated Phase 1 tables during migration.

The existing Phase 1 test fixture was restricted to legacy tables so importing Phase 2 models cannot accidentally add dependent tables to a pre-migration test database. Its report-provider expectation was advanced to deterministic template v2; assertions against LLM/mock evidence remain.

Validation environment is the Phase 1 Windows/CPython 3.12.10 and Node 22.16.0 baseline, with unchanged dependency locks. Commands:

```powershell
python -B -m unittest discover -s backend/tests -v
npm.cmd run build
npx.cmd eslint src/components/ProvenanceFindings.jsx src/components/UploadModal.jsx
```

The frontend builds and the changed standalone components pass ESLint. Vite still warns about a large bundle; TestClient emits an upstream HTTPX deprecation warning. Actual Uvicorn startup and HTTP reads for applications, app details, provenance, configurations and OpenAPI passed on an isolated migrated database copy. Both copy and source remained unchanged by the read smoke test. Its first assertion incorrectly assumed the app endpoint returned a list; it was corrected to the existing `totalAppsAnalyzed`/`recentApps` response contract and rerun successfully. No real APK runtime experiment or interactive browser acceptance test was conducted for this phase.

Machine-readable result: `recovery_backups/phase2/final_validation.json`.

## Remaining research work

Phase 3 must add graph semantics, central graph validation and version isolation. Phase 4 must add independent evidence-backed ground truth, server-side blinded review, dataset separation, evaluation units, TP/FP/FN/TN, valid metrics, reviewer agreement and research exports. This phase's ablation runs are not an `AblationExperiment` benchmark or an empirical evaluation. No Precision/Recall/F1 values are available: **N/A — benchmark dataset not yet evaluated**. See `RESEARCH_VALIDATION.md` for threats to validity.
