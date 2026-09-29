# PrivacyGuard recovery audit — Phase 0

Audit date: 2026-09-28 (Asia/Colombo). Audited commit: `63351d0ba3f39b96890936119226e5c3b796c974`, branch `main`.

## Conclusion and scope

The supplied status table is broadly correct about the missing research infrastructure, but **“working” is too strong for several recovered components**. This repository contains an application prototype, a populated database, a legacy evidence fusion engine, and partial provenance fields. It does not yet establish research readiness or empirical accuracy.

This is an audit only. No application implementation, dependencies, migrations, or original database contents were changed. The only new artifacts are this report, a separate SQLite backup, and database inspection JSON files. No application startup, seed script, APK analysis, external policy extraction, or LLM request was executed.

“Exists” below means source/schema evidence was found. It does not mean an end-to-end runtime test passed. Database integrity was checked directly; backend startup and frontend build remain unverified. Python, Node.js, npm, and sqlite3 executables were not available through the current shell's command discovery; the bundled-runtime lookup also reported no configured runtimes. Windows' built-in SQLite library was used for read-only database inspection and its online backup API.

The frontend is in **`src/` at the repository root**, not `frontend/src/`. No `AGENTS.md`, test suite, migration directory, Python dependency manifest, phase deliverables, or research-validation document was found in the recovered tree.

## Comparison with the supplied status table

| Component | Supplied status | Audited status and evidence |
|---|---|---|
| FastAPI backend | Working | Implemented in `backend/main.py`; six custom endpoints. Runtime/startup not verified. Importing it calls `Base.metadata.create_all`, so it was not imported against recovered data. |
| SQLite database | Working | Confirmed present and readable: `backend/privacy_analyzer.db`, 22 tables, 5 application rows. Integrity check passes; data validity is a separate issue. |
| SQLAlchemy | Working | Models, engine, sessions, and ORM queries exist. Installed package/version and ORM runtime behavior not verified. |
| APK upload | Working | Upload UI and `POST /api/analyze` exist; parses APK and writes results. No upload executed. The result construction introduces unsupported observations described below. |
| Androguard analysis | Working | APK/manifest parsing and DEX string scanning exist. This is not verified runtime collection, call-site analysis, taint tracking, or dynamic execution. Androguard version is unspecified. |
| Permission analysis | Working | Context profiles, necessity/risk scoring, SDK attribution heuristics, and nullable usage status exist. Upload does not establish actual permission usage. Downstream code incorrectly converts some declarations into collection records. |
| SDK intelligence | Working | Signature matching and a static SDK knowledge base exist. Generic SDK capabilities/domains are not per-APK observations. Upload also inserts undetected SDKs. |
| Privacy policy extraction | Working | Partial: HTML retrieval plus Gemini extraction path exists, but missing URL/key, fetch failure, or extraction failure silently switches to mock claims. No claim-to-quote validation. |
| EvidenceSource | Working | Model, table, upload persistence, detail response, and evidence UI exist. 89 saved records; incomplete source metadata and no durable finding relationship structure. |
| Disclosure mismatch | Partial | Confirmed partial. Legacy fusion creates mismatch descriptions, but uses unsupported collection assumptions; all 11 saved mismatches lack evidence links and explicit claim/technical statuses. UI contract also has gaps. |
| LLM report | Working | Partial: Gemini call, cache, report endpoint, and UI exist. Both saved reports are `mock-fallback`. Live generation not verified; output grounding is not enforced and fallback invents generic findings. |
| Chatbot | Working | Implemented keyword/decision-tree chatbot using database records; not a Gemini chatbot. Runtime not verified. It inherits unsupported claims in underlying records. |
| React/Vite dashboard | Working | Source, routes, API integration, package manifest, lockfile, and PDF action exist. Build and browser execution not verified in this environment. |
| Version analysis | Model only | Confirmed: `AppVersion` model/table exists but contains zero rows. No version-analysis endpoint, pipeline, version graph isolation, or regression UI. |
| Evidence provenance | Missing | **Partial scaffolding exists**, rather than completely absent: raw evidence/file/line fields, `confirmed_by`, mismatch evidence-ID JSON, and a nullable data-flow evidence FK. End-to-end finding provenance is missing. |
| Formal evidence fusion | Missing | **Legacy fusion already exists** as `EvidenceFusionEngine` and is called by upload. Required canonical normalization, formal ontology, safe semantics, configuration/version tracking, and determinism validation are missing. Preserve and adapt this module. |
| Privacy Evidence Graph | Missing | Correct for the required graph. Empty `DataFlow`/`DataFlowNode` tables are related scaffolding, not the requested typed evidence graph. |
| Benchmark | Missing | Confirmed: no benchmark models, tables, API, dataset registry, or UI. |
| Ground Truth | Missing | Confirmed: no independent evidence-backed reviewer workflow. `AppReview` is an app-store review model, not research ground truth. |
| Precision / Recall / F1 | Missing | Confirmed: no evaluation implementation or empirical results. No hardcoded Precision/Recall/F1 dashboard values found; other unsupported probability values do exist. |

## Required component matrix

“Complete” is judged against this recovery request, not historical feature names.

| Component | Exists | Complete | Needs Recovery |
|------------|--------|----------|----------------|
| Provenance | Partial fields, evidence table and viewer | No | Yes: persistent findings, typed relationships, exact source traceability |
| Ontology | Legacy category dictionaries and enums | No | Yes: separate data, behavior, claim, finding concepts and versioned vocabulary |
| Normalization | Source-specific dictionary construction | No | Yes: canonical normalization for all six required sources and legacy adapters |
| Fusion | Legacy `EvidenceFusionEngine` | No | Yes: safe explicit rules, stable semantic output, Evidence Strength Score |
| Evidence Graph | Empty flow/node model scaffolding only | No | Yes: typed nodes/edges, graph persistence, queries, explanations and UI |
| Graph Validation | No | No | Yes: endpoint types, evidence requirements, orphan/version checks before persistence |
| Benchmark | No | No | Yes: isolated benchmark models, dataset types and workflows |
| Ground Truth | No | No | Yes: independent reviewed findings with mandatory evidence |
| Ablation | No | No | Yes: configurations A–E and per-run isolation |
| Evaluation | No | No | Yes: label definitions, matching, metrics, error analysis and exports |
| Tests | No test suite found | No | Yes: behavior-based tests for all requested integrity guarantees |

### Phase mapping

- **Requested Phase 1:** `EvidenceSource` is actively persisted, but there is no `RiskFinding` model/table or SUPPORTS/CORROBORATES/CONTRADICTS relationship table. Findings returned by fusion are transient dictionaries; only their mismatch descriptions are persisted separately. Provenance is partial.
- **Requested Phase 2:** the legacy engine accepts manifest, code, optional network, policy, and Data Safety dictionaries. SDK detection is bundled into manifest evidence. There are no `privacy_ontology.py`, `normalization.py`, `fusion_engine.py`, or `adapter.py` files, nor equivalents that enforce the requested canonical semantics. Absence of those filenames alone is not the basis for calling formal fusion incomplete; the behavior gaps are detailed below.
- **Requested Phase 3:** no Privacy Evidence Graph, graph edge model, central validator, graph endpoint, deterministic path explanation, or graph visualization. `DataFlow`/`DataFlowNode` are unused related models, not a completed graph.
- **Requested Phase 4:** benchmark, ground truth, independent review, blinding, agreement, ablation, evaluation metrics, empirical dataset isolation, error analysis, and research CSV/JSON export are missing.

## Repository/module inspection

| File/module | Existing behavior | Limitations relevant to restoration |
|---|---|---|
| `backend/database.py` | SQLite engine, session factory, declarative base, FastAPI session dependency | Relative URL `sqlite:///./privacy_analyzer.db` resolves against process working directory. Starting from repository root could create a different database. No explicit foreign-key-enforcement connection hook. |
| `backend/models.py` | App analysis, permissions, trackers, personal data, payment, incidents, mechanisms, predictions | App-centric schema; observation and interpretation are mixed. Several relationships use delete-orphan cascades. Preserve existing rows and do not recreate tables. |
| `backend/models_evidence.py` | Evidence, flow, policy, disclosure, network, ML, version and child-privacy models | Many are schema-only. No canonical finding, graph-edge, configuration, benchmark, ground-truth, reviewer, or evaluation models. |
| `backend/main.py` | Upload orchestration, persistence, lists/details, comparison, report and chatbot endpoints | Main compatibility boundary for existing engine/analyzers. Persists speculative fields as facts, loses provenance links, exposes predictions without a reviewer-specific payload. |
| `backend/analyzer.py` | Earlier standalone APK permission analyzer with SHA-256 calculation | Not imported by current `main.py`. Risk score direction differs from current upload logic (higher score means safer here). Do not replace the active pipeline with it without resolving this difference. |
| `backend/evidence_engine.py` | Category/indicator dictionaries, manifest extraction, DEX string scan, optional network matching, claim ingestion, fusion and consistency score | Coarse matching; no strict Layer A/B boundary or durable rule/configuration version. Active dependency of upload; preserve interface via adapters. |
| `backend/permission_analyzer.py` | Context profiles, permission necessity/risk weights, SDK attribution, child multipliers | Attribution and necessity are heuristics. `is_actually_used` remains unknown for the upload path; no runtime validation. Child multiplier defaults to an assumed child audience when age is unknown. |
| `backend/sdk_analyzer.py` | Static SDK catalog, data/domain associations, aliases, disclosure and risk heuristics | Catalog data is knowledge about SDKs, not proof of observed access. Missing declarations default to undisclosed. |
| `backend/policy_extractor.py` | Requests/BeautifulSoup text extraction and Gemini JSON extraction | Mock fallback is used as analysis input. Explicit denial and silence are collapsed into false. Full policy text and per-claim source spans are not retained by upload. |
| `backend/data_safety_scraper.py` | Returns a dictionary matching expected fields | Entirely mocked; does not scrape Google Play. Fixed timestamp and declarations manufacture a demonstration contradiction. |
| `backend/llm_report_generator.py` | Structured database inputs to Gemini, per-app cached Markdown, fallback | No validator tying generated claims to evidence IDs; no prohibition enforced on unsupported evidence. Fallback contains fixed location/analytics statements. |
| `backend/chatbot_engine.py` | Keyword intent matching and database-backed answer templates | No independent evidence validation; repeats application data and generic conclusions. |
| `backend/seed_data.py` | Hand-authored app examples and analyzer-enriched seed fields | Calls `drop_all` then `create_all` at module level. Never run/import against recovered data. Examples are not an independently reviewed benchmark. |
| `src/` | Dashboard, detail tabs, comparison, chatbot, upload and PDF reporting | No benchmark/evaluation/reviewer/graph routes. Existing viewer can be extended; broad rewrite is unnecessary. |

## Research-integrity findings

These are defects or limitations in the recovered system, not newly introduced changes.

1. **Permission declarations become collection/sharing assertions.** `backend/main.py:222` onward creates `PersonalDataCollection(is_collected=True)` for location and camera when their permission names occur. The location record further asserts cloud storage, third-party sharing and advertising purpose. Device-ID collection/sharing is inserted unconditionally. This directly violates PERMISSION_REQUESTED != DATA_COLLECTION.
2. **SDK presence is fabricated in the upload path.** `backend/main.py:188` onward appends Firebase Analytics even when absent from detected SDKs, and appends Facebook Ads when dangerous-permission count exceeds two. These entries then become stored trackers.
3. **Data Safety is a mock source.** `backend/data_safety_scraper.py:6` returns the same illustrative claims for every package. The actual upload pipeline consumes these as declarations without a synthetic-source flag.
4. **Policy failure silently supplies mock evidence.** `backend/policy_extractor.py:48` onward falls back to a fixed profile. The extraction prompt also treats “not mentioned” and explicit denial as the same boolean. That cannot establish a reliable contradiction.
5. **Fusion conflates capability with collection contradiction.** `backend/evidence_engine.py:540` onward treats manifest, code strings and network evidence alike as technical evidence for under-disclosure. Missing technical detection also becomes over-disclosure, despite unknown coverage. Claim state is inferred from English descriptions rather than typed claims.
6. **Corroboration is not semantically validated.** Fusion adds 0.1 per additional source to the largest confidence and sets `is_confirmed` whenever at least two source types exist. A contradicting claim can increase this score. Source sets are serialized unsorted and ties retain input order; reproducibility is not tested. Deterministic arithmetic alone does not establish deterministic, valid research inference.
7. **Code scanning is a reference heuristic.** `backend/evidence_engine.py:701` scans DEX strings, truncates context, labels every match `classes.dex`, and deduplicates by indicator/category. It does not establish execution, data access, or source-to-sink flow; exact multidex location can be lost. Broad exception handling can turn analyzer failure into an empty result.
8. **Network collection is not wired to upload.** `run_evidence_pipeline` accepts optional network data, but `main.py` never supplies it. No capture runner/import endpoint was found. URL/parameter substring matching exists, but raw evidence omits the matched parameter payload and cannot by itself prove sensitive data transmission. `network_captures` has zero rows.
9. **Analysis completion and security facts are overstated.** The app-detail API sets both `staticAnalysisComplete` and `dynamicAnalysisComplete` to true (`backend/main.py:402`). Upload asserts TLS detection/encryption, payment security, and a fixed-date incident without the necessary observations. The network API field is an empty legacy placeholder and the detail page initializes zero-valued network data.
10. **Unsupported probabilities are displayed.** Upload creates a fixed leakage prediction with probability 0.45 and confidence 0.7 (`backend/main.py:240`). `src/components/RiskPredictions.jsx:28` converts stored values to percentage gauges. Seed predictions are also hand-authored. These are not calibrated probabilities or benchmark metrics. Evidence UI uses confidence terminology rather than the requested Evidence Strength Score.
11. **Missing evidence becomes a reassuring conclusion.** The empty-mismatch UI says behavior is consistent with policy/Data Safety (`src/components/DisclosureMismatch.jsx:72`), and the LLM prompt similarly claims a complete match when mismatch rows are absent. Unknown/not analyzed must remain distinguishable from corroborated consistency.
12. **LLM grounding is not enforced.** The report generator saves unrestricted model text. Its mock fallback asserts location capability, Firebase-like tracking, device collection, and child-appropriate design without checking supporting evidence. Both recovered reports are mock fallbacks. No unsupported-evidence rejection tests exist.
13. **Provenance links are not populated.** `backend/main.py:138` stores evidence independently; its mismatch persistence at line 153 does not populate evidence IDs or claim details. All 11 database mismatch rows contain `evidence_source_ids=[]` and `unknown` for policy claim, Data Safety declaration, and technical evidence. All 89 evidence rows lack timestamps; 11 lack raw evidence and none have line numbers. The detail API also omits timestamps, confirmation relationships and line numbers.
14. **No version/configuration boundary.** App analyses carry version/hash metadata, but evidence is scoped only by `app_id`, not `app_version_id` or analysis configuration. There is no version/configuration graph to test. This is a missing guarantee, not evidence that an existing graph has already leaked versions.
15. **No dataset-origin separation.** Seed examples and uploaded analysis use the same tables. No SYNTHETIC/REAL_WORLD marker or evidence-backed benchmark eligibility exists. The first four database hashes exactly match literals in `seed_data.py`; all are 64 characters, so hash length alone cannot establish authenticity. The fifth record is Uptodown App Store, with all 89 evidence records; it is not an independently verified educational-app benchmark sample.
16. **Disclosure UI contract is incomplete.** `DisclosureMismatch.jsx` reads `data.overallMatch` and `item.explanation`; the API returns `total/list` and descriptions without those fields. Its score display cannot be treated as validated.

No hardcoded Precision/Recall/F1, confusion matrix, reviewer agreement, or benchmark-success result was found in the UI. This does **not** remove the separate unsupported prediction/observation issues above. There is no empirical-results UI displaying the required “N/A — benchmark dataset not yet evaluated” state yet.

## Database audit and backup

Original database:

`C:\Users\Shehan Nethuja\Downloads\Research\Automated-Privacy-Risk-Analysis-and-Visualization-Platform\backend\privacy_analyzer.db`

- Size: 389,120 bytes; tracked in Git despite the later `*.db` ignore rule.
- Opened using SQLite `SQLITE_OPEN_READONLY`; application modules were not imported.
- `sqlite_master`, every table's `PRAGMA table_info` and `PRAGMA foreign_key_list`, row counts, `PRAGMA integrity_check`, and `PRAGMA foreign_key_check` were inspected.
- Integrity: `ok`; foreign-key check: zero reported violations. This does not demonstrate that application connections enable FK enforcement or that logical evidence claims are correct.
- Table/column names match the 22 current ORM table declarations in a static comparison. No missing/extra table columns were found. Full ORM runtime compatibility, constraints, future migration compatibility, and planned schema coexistence are not proven by that comparison.
- No migration was needed or executed for the audit. No schema design for Phases 1–4 was applied.

| Existing table | Rows | Recovery interpretation |
|---|---:|---|
| app_analyses | 5 | Existing application records; includes seed examples |
| app_permissions | 74 | Legacy permission assessments |
| app_reviews | 0 | App-store review model only |
| app_trackers | 22 | Legacy SDK assessments |
| app_versions | 0 | Version scaffold |
| child_privacy_assessments | 0 | Child-privacy scaffold |
| dark_patterns | 0 | UI-pattern scaffold |
| data_flow_nodes | 0 | Flow-node scaffold |
| data_flows | 0 | Flow scaffold with optional evidence FK |
| data_safety_declarations | 0 | Structured declaration scaffold; upload does not persist these records |
| disclosure_mismatches | 11 | All evidence-ID lists empty |
| evidence_sources | 89 | All for app ID 5: manifest 9, code 63, policy 11, Data Safety 6 |
| hybrid_risk_scores | 0 | Scoring scaffold |
| llm_reports | 2 | Both provider `mock-fallback` |
| ml_risk_predictions | 0 | ML schema only; no trained model/evaluation found |
| network_captures | 0 | Capture scaffold |
| payment_gateways | 6 | Legacy payment claims |
| personal_data_collection | 36 | Legacy collection assertions requiring review |
| privacy_policy_extractions | 0 | Structured extraction scaffold; upload does not persist these records |
| risk_predictions | 14 | Legacy numeric predictions; no empirical calibration |
| security_incidents | 11 | Legacy incident claims requiring independent verification |
| security_mechanisms | 49 | Legacy security assertions |

The raw schema, indexes, column types/defaults/nullability, declared foreign keys, application metadata and inspection results are preserved in:

`recovery_backups/20260928_224818/database_audit.json`

Additional provenance queries are preserved in:

`recovery_backups/20260928_224818/provenance_audit.json`

**Verified backup path:**

`C:\Users\Shehan Nethuja\Downloads\Research\Automated-Privacy-Risk-Analysis-and-Visualization-Platform\recovery_backups\20260928_224818\privacy_analyzer.db`

The SQLite online backup API copied the read-only source into a new destination. Backup integrity check returned `ok`, and row counts match all 22 source tables. The backup is a logical SQLite snapshot, not a byte-identical filesystem copy; SQLite backup can change header metadata.

| Artifact | SHA-256 |
|---|---|
| Original before inspection/backup | `2B67609F70376CA1D78B4BFAC18CD00173D2DA1B4D77DAA786FB199EE2B3F7B5` |
| Original after inspection/backup | `2B67609F70376CA1D78B4BFAC18CD00173D2DA1B4D77DAA786FB199EE2B3F7B5` |
| New SQLite backup | `1293DA7C4B9E14A44387071EA35D81A3B9614304D52E4150499226C2A65B8128` |

The new `.db` backup is ignored by the existing Git ignore rule. It exists locally; a commit of this audit alone would not preserve that binary elsewhere. No backup upload or database replacement was performed.

**Data-loss hazard:** `backend/seed_data.py:79` invokes `Base.metadata.drop_all(bind=engine)` at module scope. Do not run or import that script against recovered data. `main.py:20` also creates tables at import time; startup checks must first use an isolated disposable database after dependency recovery. New migrations must be separate, reviewed, additive scripts with backups and explicit handling of populated legacy rows.

## Existing API endpoints

Six custom routes were found in `backend/main.py`:

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/analyze` | APK multipart upload with optional policy URL; analysis and persistence |
| GET | `/api/apps` | Dashboard aggregate data and app list |
| GET | `/api/apps/{app_id}` | Detailed observations/assessments, evidence, mismatches and cached report |
| POST | `/api/apps/{app_id}/generate-report` | Generate/cache LLM or mock report |
| GET | `/api/compare` | Compare all app-analysis records |
| POST | `/api/chatbot` | Rule-based chatbot response |

FastAPI's default documentation/schema routes are not counted as research endpoints. No graph, version drift, benchmark, review, blinded-review, ablation, evaluation, error-analysis, reproducibility, or research export endpoint exists. The current detail endpoint deliberately exposes predictions and severity; it must not be reused as a blinded reviewer payload.

## Existing frontend routes and views

Routes in `src/App.jsx`:

| Route | View |
|---|---|
| `/` | Dashboard |
| `/analyze` | Redirect to `/analyze/1` |
| `/analyze/:appId` | App detail |
| `/compare` | Cross-app comparison |
| `/chatbot` | Chatbot |

App detail tabs: Overview, AI Educator Brief, Permissions Context, Evidence Sources, SDK Intelligence, Personal Data, Payment Security, Security Mechanisms, Incidents, Risk Predictions. Upload is a modal, not a separate analysis-workflow route. Dashboard totals are queried from existing records; they are not empirical accuracy measurements.

PDF generation exists in `AppDetailView.jsx` using `html-to-image` and `jsPDF` on a hidden summary. A separate `PrintableReport.jsx` component exists but is not imported by the current detail page. This is not the requested research CSV/JSON export. `vite.config.js` proxies `/api` to port 8000; upload separately hardcodes `http://localhost:8000/api/analyze`.

Missing requested dedicated views: typed graph and explanations, formal findings/provenance navigation, child-privacy assessment workflow, version comparison, privacy regression, benchmark, ablation, evaluation, FP/FN analysis, reproducibility, and independent/blinded review. Existing app comparison does not implement version-aware evaluation. Reports and evidence browsing provide useful partial UI to retain.

## Git recovery findings

- Initial working tree was clean; current branch `main` and cached `origin/main` both pointed to `63351d0`.
- Remote: `https://github.com/NimeshWickram/Automated-Privacy-Risk-Analysis-and-Visualization-Platform.git`.
- Live `git ls-remote --heads --tags origin` confirmed only `refs/heads/main`, at the same full SHA. No advertised remote tags or other branches.
- Seven reachable commits; no local tags. Reflogs contain only clone records. `git fsck --full --no-reflogs` reported no errors or dangling recovery candidates.
- Historical filename enumeration and content searches covered all seven reachable commits for phase names, fusion, ontology, normalization, graph, benchmark, ground truth, ablation, provenance, `EvidenceEdge`, `GraphEdge`, and `RiskFinding`. No hidden implementation of the requested four-phase research architecture was found.
- `b510b08` introduced the legacy evidence engine and evidence models already present at HEAD. Its message **“complete Phase 3” means Privacy Policy NLP Analyser integration**, not this request's Phase 3 evidence graph.
- Deleted files: `backend/mock_data.py` and `src/data/mockData.js` in `75167bf`. No renamed/deleted required phase implementation was identified. Old mock files are recoverable from Git but are not research infrastructure.
- Historical `.pyc` files exist in Git and indicate a CPython 3.14 compilation at some point; they do not establish dependency versions or a reproducible environment.
- Scope limit: this cannot establish whether work existed only on the failed laptop, an unpushed branch, another repository, or an unavailable external backup. None was assumed recovered.

| Commit | Date | Actual feature history |
|---|---|---|
| `63351d0` | 2026-08-06 | Light theme and seed changes |
| `b510b08` | 2026-07-22 | Policy NLP, legacy multimodal evidence, mismatch and LLM integration |
| `a5b18a5` | 2026-07-21 | Chatbot and dashboard components |
| `a8c09f9` | 2026-07-04 | PDF reporting |
| `75167bf` | 2026-06-28 | FastAPI/SQLite/Androguard integration; mock-file deletion |
| `4f4c466` | 2026-06-27 | UI redesign and API mapping |
| `3f6ae9c` | 2026-06-26 | Initial project |

## Dependencies, tests, migrations and documentation

Frontend dependency declarations and `package-lock.json` exist. Lockfile examples: React 19.2.6, Vite 8.0.11, React Router DOM 7.15.0, Tailwind CSS 4.3.0, ESLint 10.3.0. Scripts are `dev`, `build`, `lint`, and `preview`; there is no test script. Installed `node_modules` was not present. No dependency installation or lockfile update was performed.

No `requirements.txt`, `pyproject.toml`, Pipfile, Poetry/uv lock, or other Python dependency/version specification was found in the working tree or reachable historical filenames. Imports identify FastAPI, SQLAlchemy, Pydantic, Androguard, Requests, BeautifulSoup and `google.generativeai`; exact compatible versions and an ASGI server setup are unresolved. Multipart uploads also need the corresponding FastAPI multipart dependency. Versions must be established explicitly before restoration; do not infer them from bytecode or silently install latest packages.

No automated backend/frontend tests, pytest configuration, test fixtures, CI workflow, or migration scripts were found. `create_all` and destructive seeding are not a migration system. All 24 requested test categories remain unverified, including normalization, determinism, capability/access/transmission separation, graph validation, version/ablation isolation, reproducibility, independent mandatory-evidence ground truth, confusion counts, macro/micro metrics, dataset exclusion/isolation, blinded sanitization, reviewer audit trail, exports and LLM grounding. No meaningless placeholder tests were created.

`README.md` is the only pre-existing Markdown documentation found. It overstates dynamic analysis and comparison against “actual behavior,” omits backend setup, and still lists upload/PDF as future work despite their source implementations. `phase1_deliverables.md` through `phase4_deliverables.md` and `RESEARCH_VALIDATION.md` are absent. They were not fabricated during this audit and should be written against verified future deliverables.

### Validation actually performed

| Check | Result |
|---|---|
| Repository, route, model, dependency and history inspection | Completed |
| Live remote heads/tags check | Completed; main only |
| SQLite schema/table/count inspection | Completed, 22 tables |
| Source and backup SQLite integrity checks | Both `ok` |
| Source foreign-key check | Zero reported violations |
| Backup/source row-count comparison | All 22 tables match |
| Original database SHA-256 before/after backup | Identical |
| Backend startup / HTTP endpoint tests | Not run; environment/dependency versions unresolved; import has DB side effects |
| APK/Androguard runtime analysis | Not run; no retained APK fixture found |
| Live policy or Gemini behavior | Not run; code inspection only |
| Frontend lint / build / browser test | Not run; required runtime/dependencies unavailable in current shell |
| Requested implementation test suite | Missing |
| Empirical benchmark evaluation | Missing; **N/A — benchmark dataset not yet evaluated** |

Database integrity and source inspection are implementation-level audit evidence. They establish neither detection accuracy nor real-world privacy violations. Stored sample app names, hand-authored predictions, and existing evidence counts are not independent ground truth. No Precision, Recall, F1, TP/FP/FN/TN, agreement, or success rate was calculated or invented.

## Recommended restoration order — not executed

1. Retain this database and verified backup. Resolve Python/runtime versions, intended legacy phase semantics, and any additional external recovery sources before implementation. Keep original records as legacy/unverified; do not relabel them as reviewed real-world ground truth.
2. Restore **Phase 1 provenance** through additive migrations: canonical source records, separate interpreted findings, typed support/corroboration/contradiction relationships, exact source snapshots/locators, and explicit unknown states. Preserve the current analyzer APIs using adapters. Avoid producing further fabricated SDK, collection, policy or Data Safety observations. Add Phase 1 provenance and unsupported-inference tests before progressing.
3. Restore **Phase 2 ontology, normalization and deterministic fusion**: separate capability, API reference/potential access, transmission evidence, claim states and findings. Add six-source normalization, documented rule-based Evidence Strength Scores, stable ordering, analysis configurations and rule/ontology versions. Implement A–E ablation traceability against the same APK/version; test behavior and isolation.
4. Restore **Phase 3 graph** in SQLite/SQLAlchemy: typed observed/derived nodes, valid directed relations, pre-persistence validation, version/configuration scoping, supported transmission paths and deterministic explanations. Add graph/semantic/version tests. Existing flow tables may need compatibility mappings; do not repurpose populated legacy data by assumption.
5. Restore **Phase 4 benchmark** in isolated tables: explicit SYNTHETIC/REAL_WORLD datasets, independently reviewed evidence-backed truth, separate observation/interpretation/access/transmission/disclosure fields, reviewer audit trails, genuine API-level blinding and multiple reviewers. Define the evaluation unit and negative-label universe before computing TN or FPR. Implement explicit-dataset evaluation, appropriate micro/macro metrics, FP/FN analysis, agreement when defined, reproducibility metadata, and CSV/JSON exports. Add the required evaluation/integrity tests.
6. Complete research-integrity hardening across API, UI, chatbot and reports. Missing evidence must not become a finding or reassurance. Validate LLM statements against structured sources. Distinguish implementation tests from empirical evaluation; display unavailable metrics honestly.
7. Run the complete meaningful test suite, frontend build, isolated backend startup/API tests, and final database integrity/data-preservation checks. Then produce phase deliverables and `RESEARCH_VALIDATION.md`, including threats from static coverage, string matching, policy ambiguity/LLM extraction, app/version selection, reviewer disagreement, dataset contamination and incomplete runtime observation.

### Stop conditions and unresolved decisions

- **Audit-only stop honored:** no Phase 1–4 implementation started.
- **Dependencies ambiguous:** backend versions are not recoverable from a manifest in this repository. Runtime success is not asserted.
- **Partial legacy phases:** historical “Phase 3,” flow/ML/child models and unused provenance fields do not define the new requested semantics. Reconcile their intended role before changing persistence contracts.
- **Populated data is at risk from current seeding:** preserve it; no destructive script or migration was run. No specific future schema conflict is claimed before a migration design exists.
- **Ground truth/evaluation insufficient:** no empirical metric is defensible from the recovered data. No metrics were computed.
- **Blinding unavailable:** the existing API exposes automated predictions. A new sanitized reviewer API and tests are required before a review can be described as blinded.
- No recoverable older implementation of the requested phase architecture was identified in accessible Git history. If another backup/repository appears, inspect it before rebuilding equivalent modules.

The immediate outcome is a documented recovery baseline with preserved data. Research readiness remains unverified and incomplete.
