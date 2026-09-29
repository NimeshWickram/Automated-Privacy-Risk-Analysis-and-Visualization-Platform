# Phase 4 — Independent benchmark, blinded review and evaluation

Implemented 2026-09-29 (Asia/Colombo). **The Phase 4 software workflow is implemented; empirical validation is not complete.** No real-world benchmark, human ground truth or reviewer agreement has been manufactured. The recovered database's new benchmark tables are empty. Empirical Precision/Recall/F1 remain **N/A — benchmark dataset not yet evaluated**.

## Architecture and isolated records

Phase 1 provenance, Phase 2 normalization/fusion and Phase 3 graphs remain intact. The benchmark does not copy automated findings into truth and does not use the old seeded examples as verified applications.

New modules:

- `models_benchmark.py`: isolated datasets, applications/versions, raw ground-truth evidence, reviewers, assignments, submitted reviews, approved ground truth, evaluation snapshots, ablation manifests and audit events.
- `benchmark_schemas.py`: explicit input schemas; unexpected prediction fields are rejected.
- `benchmark_service.py`: independent review lifecycle, artifact admission, approval, dataset freezing, evaluation and export.
- `evaluation.py`: pure unit matching, confusion counts, micro/macro metrics and unweighted Cohen's kappa.
- `benchmark_api.py`: researcher-only API.
- `reviewer_api.py`: separate, always-blinded review service.
- `research_auth.py`: researcher credential checks and fail-closed protection of analysis routes.
- `migrations/phase4_benchmark.py`: backed-up additive migration.

The 11 new tables are `benchmark_datasets`, `benchmark_applications`, `benchmark_versions`, `ground_truth_evidence`, `ground_truth_reviewers`, `benchmark_review_assignments`, `reviewer_reviews`, `ground_truth_findings`, `benchmark_evaluation_runs`, `benchmark_ablation_experiments` and `benchmark_audit_events`.

Dataset and benchmark-version records explicitly identify SYNTHETIC or REAL_WORLD. Evaluation snapshots also retain that type. Synthetic evaluations are labeled IMPLEMENTATION_VALIDATION; eligible real-world evaluations are labeled EMPIRICAL_EVALUATION and are limited to the reviewed dataset. No API merges both dataset types.

## Independent ground-truth workflow

1. Create a named/versioned dataset protocol, selecting finding labels and data categories explicitly and recording scope/sampling rationale. The Cartesian product defines the fixed label universe for every benchmark version.
2. Register benchmark APK versions separately from automated analysis tables. Supply APK hash, package/version, source and eligibility notes. REAL_WORLD registration requires an actual retained APK beneath `backend/uploads` or `backend/benchmark_artifacts`, a matching SHA-256, valid APK/package/version parsed by Androguard, and researcher attestation of free educational eligibility. Eligibility is a documented human judgment, not inferred from permissions. Synthetic inputs cannot bypass this admission check by changing the requested evaluation type.
3. Add independent raw evidence, exact artifact references, artifact hashes and curator identity. The curator must attest that the packet is independent and prediction-free. There is no endpoint to copy analyzer annotations or predictions into a review packet. Curators must not paste automated interpretations into free-text raw evidence.
4. Register distinct reviewers with identity/qualification metadata. Assign each an opaque, randomly generated credential. Assignment locks the evidence packet; later evidence changes require a new dataset/version workflow rather than silently changing material already reviewed.
5. Reviewers independently label every protocol unit as POSITIVE, NEGATIVE or UNCERTAIN. Each decision requires separate observation and interpretation text, observation/access/transmission/disclosure statuses, and supporting evidence from that benchmark version. Missing coverage must not be marked negative automatically.
6. A researcher explicitly approves two independent completed reviews. If decisions disagree, a third, different reviewer must submit an independent adjudicator review. Approval retains the original submissions and audit trail; it does not modify a review. When the first two decisions agree, the first review's evidence-backed account is the explicitly approved account. Agreement on a label is not proof that every rationale is identical.
7. Freeze the dataset only when every registered version has approved ground truth. Evaluation requires the frozen dataset and exactly one matching analysis run per version.

Positive capability decisions require manifest evidence and CAPABILITY_ONLY status. Static references support POTENTIAL_ACCESS; they cannot establish ACTUAL_ACCESS, which requires RUNTIME evidence and OBSERVED access status. Transmission requires reviewed network evidence and a transmission observation. Disclosure inconsistency requires explicit conflicting claim sources or a claim plus behavioral evidence. Negative access/transmission decisions need an explicit NOT_OBSERVED review status; negative disclosure decisions need CONSISTENT. Unknown status is not an implicit negative label.

Every submitted decision, including negative and uncertain decisions, requires supporting evidence and a written interpretation of review scope. The service validates references/status consistency, but a human can still misinterpret an artifact. Two credentials do not prove two different humans, and two agreeing reviewers do not make ground truth infallible. Reviewer recruitment, independence, training and adjudication remain research responsibilities.

Submitted reviews are immutable through the API, with server timestamps, packet hashes, submission hashes, reviewer metadata and audit events. Ground-truth rows require a review and same-version evidence foreign key; there is no automated-finding foreign key. Approved truth is hashed and rechecked against its manual review before evaluation.

## Blinding is enforced by the servers

The reviewer service exposes only `GET /api/review` and `POST /api/review`. It has no analysis, graph, benchmark-results, chatbot, report, OpenAPI or unblinding route. Reviewer payloads are constructed with an allowlist from independent benchmark tables: application identity, fixed protocol units, raw evidence/reference/hash, the assigned reviewer's name and submission status. Automated predictions, severity, confidence/strength, scores, analysis IDs and TP/FP/FN classifications are absent. Passing `blinded=false` cannot enable them. Even after submission, this service remains blinded.

The researcher service requires `X-Research-Key` for **all `/api/` routes** when `PRIVACYGUARD_RESEARCH_KEY` is configured, including the pre-existing analysis, graph, comparison, chatbot and report routes. A review token is not a researcher key. If a database already contains review assignments and the researcher key is later missing, analysis access fails closed. Phase 4 administrative operations and the reviewer service require a configured researcher key before use; a missing/short key cannot enable a review study.

The old application can still operate without research credentials when no assignments exist. This preserves the earlier analysis workflow, but no Phase 4 reviewer assignments can be issued in that mode. Run both services against the same configured database. Review participants must use separate browser profiles/devices and receive only their assignment token, never the researcher key. Existing knowledge of predictions cannot be erased: each review requires explicit attestations of independent work and that predictions were not seen.

Assignment tokens are hashed in SQLite and shown once at assignment. The frontend uses a URL fragment to open a reviewer page, sends the token as an Authorization header, and removes the fragment after loading. The standalone reviewer page does not load researcher navigation or use the research-key API helper. Researcher credentials are kept in the current tab's session storage, with a clear-credential control. This is a local research workflow, not a fully audited multi-tenant identity system; database/host administrators can access the stored data.

## Evaluation unit and prediction matching

One unit is:

`benchmark APK version × finding category × data category`, evaluated for **one analysis configuration**.

Available labels are CAPABILITY, POTENTIAL_ACCESS, ACTUAL_ACCESS, POTENTIAL_TRANSMISSION, DISCLOSURE_INCONSISTENCY and UNNECESSARY_PERMISSION. Every dataset version is reviewed against the complete protocol label/category universe. Multiple findings for the same unit produce one positive prediction, not multiple true positives.

CAPABILITY predictions come from normalized permission declarations, because Phase 2 can suppress a separate capability finding when code is present. Other supported labels map to their corresponding Phase 2 finding categories. ACTUAL_ACCESS is never predicted by the current static analyzer. It can be included deliberately to document that limitation, but must not be conflated with potential access. SDK presence is not an access prediction.

This is category-level detection evaluation, not exact destination-domain or source-to-sink correctness. A transmission prediction means at least one potential transmission finding for that category. The full underlying findings and evidence remain in the export for auditing the finer interpretation. Predictions outside the selected protocol are retained in the snapshot but are not included in its metrics. Researchers must specify an appropriate protocol before viewing results and report its scope.

APK hash, version string and package identity must match the benchmark version. A run from another version cannot be substituted. One evaluation rejects mixed configurations. All versions in the frozen dataset must be selected, preventing silent selection of only favorable records. Changing cohort or protocol requires a new dataset version.

| Independent decision | Prediction | Classification |
| --- | --- | --- |
| POSITIVE | Present | TP |
| NEGATIVE | Present | FP |
| POSITIVE | Absent | FN |
| NEGATIVE | Absent | TN |
| UNCERTAIN | Either | EXCLUDED_UNCERTAIN |

No unlabeled records become TN. If no determinate units remain, evaluation stops without creating a result. Source coverage remains attached to the run; lack of detection is never promoted to independent truth.

Precision = TP/(TP+FP), Recall = TP/(TP+FN), F1 = 2TP/(2TP+FP+FN), FPR = FP/(FP+TN), FNR = FN/(FN+TP). Micro metrics use summed counts. Macro metrics average each defined label/category metric; macro F1 is the mean of per-label F1 values. The aggregation follows the distinction documented in [scikit-learn's metric reference](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.precision_recall_fscore_support.html).

Zero denominators produce null/N/A, rather than fabricated zero or perfect values. Each macro metric reports its number of defined labels and total protocol labels. Uncertain-unit counts are explicit. This policy matters when comparing small/sparse datasets and must be reported with thesis results.

Cohen's kappa is computed on two independent reviews of the same version and complete unit universe, treating POSITIVE/NEGATIVE/UNCERTAIN as three nominal categories. It uses `(observed agreement − expected agreement)/(1 − expected agreement)`. Fewer than two paired units or degenerate marginals return N/A with a reason. This is the unweighted statistic described by the [official Cohen's kappa reference](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.cohen_kappa_score.html). Two paired units are a mathematical minimum, not a claim of statistical adequacy. No agreement value has been generated for real reviewers in this workspace.

## Ablation, error analysis and exports

Benchmark ablation reuses the Phase 2 A–E configurations over a fixed acquisition bundle for each benchmark APK. Each configuration gets a separate evaluation against the same frozen ground truth; the experiment records source selections and evaluation IDs. It does not measure acquisition-time performance. A failure rolls back new analysis runs and evaluations for the experiment.

The Benchmark UI can reload saved ablation experiments and compare dynamically computed micro metrics/counts. Read-time checks require linked evaluations to share the same dataset fingerprint and correct configuration. No synthetic result is combined with a real-world result.

Error Analysis filters actual FP/FN units and exposes their independent decision, evidence IDs, version and prediction. A researcher can append an evidence-backed cause hypothesis to a specific error. Notes are separate audit events and do not alter ground truth, predictions or the original evaluation snapshot. The audit API provides those later notes; immutable evaluation exports do not silently change to include later annotations.

JSON exports contain the complete hashed evaluation snapshot. CSV exports contain one row per protocol unit, including truth, prediction, TP/FP/FN/TN or exclusion status, dataset type/version/fingerprint, APK hash, application/run/configuration identity, ground-truth JSON, metrics JSON and a reproducibility/observation snapshot. Spreadsheet-formula-leading string cells are escaped. Both formats are generated from the stored evaluation, not current UI calculations.

Reproducibility records include APK hash/version, configuration definition and enabled sources, rule/ontology/analysis/evaluation versions, normalized observations, original prediction links, source coverage, Python/OS/analyzer versions, timestamps, dataset/protocol/truth hashes, reviewer metadata/submissions and approval metadata. Android tooling version can be provided when registering a benchmark version; otherwise it is explicitly recorded as unavailable. Real-world evaluation rechecks retained APK bytes/package/version. Hashes support consistency checking, not authentication against a privileged database administrator.

## API surface

Researcher routes under `/api/benchmark` require the researcher header:

- `GET /api/benchmark`: datasets, versions, submitted reviews, reviewers, evaluations, ablations and actual empirical status.
- `POST /datasets`: create an explicit protocol/type/version.
- `POST /datasets/{id}/versions`: independently register an APK version.
- `POST /versions/{id}/evidence`: curate independent evidence before assignment.
- `POST /reviewers`: register reviewer identity/metadata.
- `POST /versions/{id}/assignments`: create a blinded assignment; token returned once.
- `GET /versions/{id}/agreement?first_review_id=…&second_review_id=…`: calculate paired agreement.
- `POST /versions/{id}/seal`: approve two reviews, with a third review when needed.
- `POST /datasets/{id}/freeze`: freeze the fully reviewed cohort.
- `POST /datasets/{id}/evaluate`: explicit dataset_type plus benchmark-version/analysis-run selections.
- `POST /datasets/{id}/ablation`: same explicit cohort, with selected A–E configurations.
- `GET /evaluations/{id}` and `/ablations/{id}`: verified stored results/manifests.
- `GET /evaluations/{id}/export?format=json|csv`: authenticated research export.
- `POST /evaluations/{id}/error-notes`: append FP/FN cause analysis.
- `GET /audit`: reviewer/approval/evaluation/error-analysis audit trail.

Separate reviewer service: `GET /api/review` and `POST /api/review`, with `Authorization: Bearer <assignment-token>`. These are not mounted on the researcher service. Full request schemas are available from the researcher API's OpenAPI document; reviewer OpenAPI is disabled.

## Startup and UI

Use the Windows/Python 3.12 setup and dependency lock in `phase1_deliverables.md`. No dependencies were added for Phase 4. Configure the **same private key of at least 32 characters** in both backend shells and use the same database path. A key can be generated locally with Python's `secrets.token_urlsafe(32)`; do not put it in Git or give it to reviewers.

Researcher service, from the repository root:

```powershell
$env:PRIVACYGUARD_RESEARCH_KEY = Read-Host 'Enter your private researcher key (at least 32 characters)'
python -m uvicorn main:app --app-dir backend --host 127.0.0.1 --port 8000
```

Reviewer service, in another shell with the same environment settings:

```powershell
$env:PRIVACYGUARD_RESEARCH_KEY = Read-Host 'Enter the same private researcher key'
python -m uvicorn reviewer_api:app --app-dir backend --host 127.0.0.1 --port 8001
```

Frontend: `npm.cmd run dev`. Open **Benchmark**, connect using the researcher key, and follow protocol → version → evidence → reviewer assignment → independent submissions → approval → dataset freeze → evaluation/ablation. Existing analysis views also use the session's researcher credential. The default frontend is configured for the local analysis API/Vite proxy. `VITE_REVIEW_API` may configure a different reviewer-service base URL when deliberately deploying a review environment; remote hosting/authentication infrastructure has not been tested here.

Review assignments return a reviewer-page link under `/review#<token>`. Hand that credential to its assigned reviewer through your chosen private channel; this implementation has not sent invitations. Use a separate reviewer browser profile/device without the researcher key. The raw-evidence form and independent review form are functional; no study records are prefilled in the real database.

The Benchmark page separates Implementation Validation and Empirical Evaluation, and includes protocol/evidence setup, reviewer workflow, evaluation results, A–E comparisons, error analysis, reproducibility and CSV/JSON export. Existing APK analysis/evidence/graph/report views remain. Full child-privacy and privacy-regression research workflows are not newly implemented by Phase 4.

## Backup and migration

The source database was inspected, backed up and verified before adding tables. All 33 existing schemas and rows were compared and preserved, including the five recovered applications. Eleven empty benchmark tables were added; there are now 44 tables. No seeded benchmark, automatic ground truth, reviews or evaluation results were inserted into the recovered database.

- Backup: `recovery_backups/phase4/before_phase4_20260928T191617287923Z.db` (UTC timestamp, local date 2026-09-29).
- Backup SHA-256: `0ac74c34ad21e4f99be0900eae90f425f3dd65c2e683248932a4ec7ab4a37193`.
- Matching `.json` records the original schema/columns/foreign keys, row counts/digests and migration outcome.
- Before database SHA-256: `11d42d74b1990bda3efa080c578c1d7f924fcd0b780dcff9f71976c859d87d9d`.
- After database SHA-256: `a2942b17f3233527e83581378ce7f44e6bad678d4dfdb56b4a5780a700792baf`.
- Integrity: `ok`; foreign-key violations: none. Earlier backups remain. Backup `.db` files are local and ignored by Git.

Migration is already applied in this workspace:

```powershell
python -B backend/migrations/phase4_benchmark.py --database backend/privacy_analyzer.db --backup-directory recovery_backups/phase4
```

It requires compatible Phase 1–3 schemas, refuses partial/conflicting tables and is idempotent for the matching schema. No destructive migration or downgrade is supplied.

## Implementation validation

**175 tests pass**, including the previous 126 tests and 49 Phase 4 tests. Tests cover counts/rates, macro/micro differences, undefined denominators, uncertainty exclusion, kappa limits, evidence requirements, truth independence, actual-versus-potential access, immutable reviews, packet integrity, adjudication, dataset/type/version isolation, explicit selection, frozen cohorts, reproducibility, exports, CSV formula escaping, audit trails, ablation rollback and blind API access control. Migration tests preserve populated legacy graphs and all preceding data.

```powershell
python -B -m unittest discover -s backend/tests -v
npm.cmd run build
npx.cmd eslint src/pages/BenchmarkPage.jsx src/pages/ReviewerPage.jsx src/api.js
python -B backend/tests/smoke_phase4.py --database backend/privacy_analyzer.db
```

The frontend build and new-page/API-helper lint pass. Vite retains its large-bundle warning; TestClient retains an HTTPX deprecation warning. Actual Uvicorn startup and a complete two-service HTTP workflow pass: dataset/evidence registration, separate blinded reviews, protected analysis routes, manual approval, freeze, evaluation and exports. That test creates SYNTHETIC fixtures only in a temporary copy and verifies the source database hash remains unchanged. Its first launch exposed an embedded-Python test-module path issue; the smoke script now resolves its test directory explicitly and passed after correction.

Validation records: `recovery_backups/phase4/http_validation.json` and `recovery_backups/phase4/final_validation.json`. No interactive browser acceptance test was performed. No real-world APK study was performed. Temporary runtimes used for validation are the existing CPython 3.12.10/Node 22.16.0 baseline and should not be treated as a durable installation.

## Empirical stop condition and remaining research work

There is no supplied, independently reviewed REAL_WORLD benchmark. Therefore actual empirical evaluation remains blocked on researcher work: define the sampling protocol; retain and verify eligible APKs and evidence; recruit independent reviewers; complete blinded reviews/adjudication; freeze the dataset; then evaluate the recorded configurations. Synthetic fixture results validate implementation only and must not appear as thesis empirical results.

Threats remain from manual annotation/eligibility error, selection bias, reviewer dependence or prior exposure, sparse/imbalanced labels, uncertain-case exclusion, category-level matching, static-analysis limitations and version/artifact coverage. Network capture and runtime access instrumentation are still unavailable in the automated analyzer. Software completion does not establish research readiness or real-world accuracy. See `RESEARCH_VALIDATION.md` for the current overall assessment.
