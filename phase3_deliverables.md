# Phase 3 — Privacy Evidence Graph

Implemented 2026-09-29 (Asia/Colombo). The graph is a deterministic projection of verified Phase 2 evidence and findings. It adds no new observations, LLM-generated evidence or empirical accuracy claims.

## Preserved architecture

The existing Phase 1/2 analyzers, normalized evidence, finding relationships and fusion results are reused. Legacy `data_flows` and `data_flow_nodes` are preserved; their contents are not promoted into canonical graph relations. The existing `app_versions` table is reused for identity rather than replaced. Inspection found 30 tables, no analysis runs and no version records in the recovered database before this migration.

- `backend/graph_engine.py`: graph ontology, deterministic projection, central validation and explanation templates.
- `backend/models_graph.py`: SQLite/SQLAlchemy graph snapshot, node and edge models.
- `backend/graph_service.py`: verified evidence adapter, application/version/run scoping, atomic persistence and read-time integrity checks.
- `backend/migrations/phase3_graph.py`: explicit backed-up additive migration.
- `src/components/PrivacyEvidenceGraph.jsx`: graph visualization, node/evidence inspection, relation details and payload explanation paths.
- `backend/tests/test_phase3_graph.py`: synthetic semantic, persistence, API and migration tests.

Graph creation is explicit and on demand through the graph API or the app's Privacy Evidence Graph tab. A previously built graph is verified and returned unchanged. There is no automatic graph backfill on startup, and no arbitrary client-supplied graph editor or destructive rebuild endpoint. New APK analysis still uses Phase 2; open its graph after analysis to materialize the snapshot.

## Node and edge semantics

Graph version: `privacy-graph-1.0`.

| Node | Layer | Meaning |
| --- | --- | --- |
| EVIDENCE_SOURCE | OBSERVED | Retained normalized source record, linked to its Phase 1 evidence ID |
| SDK | OBSERVED | SDK entity named by retained signature evidence |
| DOMAIN | OBSERVED | Hostname/IP from retained network evidence |
| DATA_CATEGORY | DERIVED | Ontology attribution, not an independently observed collection event |
| RISK_FINDING | DERIVED | Existing Phase 2 interpretation, including rule, strength score and evidence relationships |

OBSERVED labels the source/entity role in the evidence graph. It does not certify the authenticity of imported artifacts or turn a developer's claim into observed technical behavior. Relations carry explicit qualifications and supporting evidence IDs.

| Relation | Endpoints | Required basis |
| --- | --- | --- |
| INDICATES_CAPABILITY | EVIDENCE_SOURCE → DATA_CATEGORY | Manifest permission declaration; no access/collection assertion |
| REFERENCES_API_FOR | EVIDENCE_SOURCE → DATA_CATEGORY | Static API reference; execution and runtime access unverified |
| ACCESSES_DATA | EVIDENCE_SOURCE → DATA_CATEGORY | Reserved; rejected until a supported runtime/access evidence adapter exists |
| ATTRIBUTED_TO | EVIDENCE_SOURCE → SDK | Retained SDK signature match; no inferred SDK data access |
| CONTACTS | EVIDENCE_SOURCE → DOMAIN | Retained network observation; domain alone is insufficient for sensitive transmission |
| HAS_PAYLOAD_CATEGORY | EVIDENCE_SOURCE → DATA_CATEGORY | Explicit outbound payload/category annotation validated by Phase 2 |
| TRANSMITTED_TO | DATA_CATEGORY → DOMAIN | The same annotated outbound payload; qualified as potential transmission requiring review |
| CLAIMS_COLLECTION / DENIES_COLLECTION | EVIDENCE_SOURCE → DATA_CATEGORY | Explicit retained developer claim annotation; not technical collection behavior |
| SUPPORTED_BY | RISK_FINDING → EVIDENCE_SOURCE | Existing SUPPORTS or CORROBORATES finding link; original role retained in qualification |
| CONTRADICTED_BY | RISK_FINDING → EVIDENCE_SOURCE | Existing CONTRADICTS finding link |

### Static references versus actual access

The originally proposed `Code → ACCESSES_DATA → LOCATION` path would overstate this repository's current evidence: the analyzer records DEX string/API references, not runtime invocations. Therefore current code nodes use `REFERENCES_API_FOR`. `ACCESSES_DATA` is an explicitly reserved relation that validation rejects for current inputs. Implementing a runtime evidence adapter is required before emitting it. This preserves the stronger requirement that `API_REFERENCE` must never silently become actual runtime collection.

Manifest evidence can produce `INDICATES_CAPABILITY`; it cannot produce `ACCESSES_DATA`. SDK presence cannot produce access/transmission. Policy silence cannot become a denial. Domain-only evidence produces CONTACTS, without a sensitive category or transmission edge.

The implemented payload path is:

```text
[OBSERVED] Network payload evidence
  → HAS_PAYLOAD_CATEGORY
[DERIVED] LOCATION
  → TRANSMITTED_TO
[OBSERVED] analytics.example.com
```

Both path edges retain the same supporting payload evidence ID. The destination is taken from that payload's captured request. A separate static API reference may point to the same category, but shared categories do not establish a code-to-network data flow. Explanation templates state that limitation explicitly and do not construct a supposedly proven static-code-to-domain path.

## Central graph validation

Validation occurs before graph/version persistence and again on graph reads. It rejects unknown node types, incorrect observed/derived layers, unknown categories, duplicate nodes/edges, dangling endpoints, orphan nodes, invalid relation/type pairs, missing supporting evidence, unsupported access semantics, and domain-only transmission. It also requires exact agreement with the deterministic projection of independently checked Phase 2 inputs, preventing validly shaped but invented/missing relations.

For example, `EVIDENCE_SOURCE → TRANSMITTED_TO → DATA_CATEGORY` is rejected because the required endpoint pair is DATA_CATEGORY/DOMAIN. Reversing a transmission edge is rejected. Every graph edge must reference evidence from its own analysis run.

Observations without a justified graph relation are not given invented links merely to avoid orphans. Their IDs and exclusion reasons are retained as `omitted_evidence`; the full observations remain in Phase 2 provenance and its frontend explorer. An empty graph is valid and is not a finding that privacy risks are absent.

Graph nodes, edges and omissions have canonical ordering and a semantic SHA-256. Database IDs, timestamps, application/version/run IDs are outside this semantic hash, allowing equivalent analyses to yield the same graph hash while remaining separate stored graphs. The graph version is included. Read-time checks verify node/edge relational fields, evidence and finding IDs, graph hash, Phase 2 evidence snapshots and regenerated fusion/projection. No LLM is used in graph generation or explanations.

## Version and configuration isolation

The identity adapter matches the exact `(app_id, APK SHA-256, version_name)` in `app_versions`. It reuses one matching version, creates an identity if none exists, and stops on ambiguous duplicate identities. Existing version metadata is never overwritten. New identities leave uncomputed legacy metric/change columns NULL; graph creation does not invent version comparisons, risk deltas or zero counts.

Each graph belongs to one Phase 2 analysis run and one `app_version_id`. Nodes and edges carry both IDs. Composite foreign keys restrict node endpoints, evidence sources and findings to the same run/version. Service checks additionally verify ownership and the stored version's APK hash/version name against the immutable analysis run.

Every graph read requires app ID, version ID and run ID. The graph index checks ownership of both the version and analysis. Same version labels with different APK hashes are separate identities. Same APK hashes with different version labels are also separate identities. A and E ablations can share a version identity while remaining separate run-scoped graphs with distinct evidence row IDs. No query merges them into one graph.

Historical runs remain readable using their recorded version identity even if the application's current metadata changes. Different app records are intentionally not merged by package name or APK hash; cross-upload package/version comparison remains future work.

## Persistence and API

Three additive tables:

- `privacy_graph_runs`: run/version binding, graph version/hash, creation timestamp and omitted evidence.
- `privacy_graph_nodes`: version/run-scoped node identity and payload, observed/derived layer, source/finding foreign keys where appropriate.
- `privacy_graph_edges`: version/run-scoped endpoints, relation, evidence source foreign key and qualified semantic payload.

| Endpoint | Behavior |
| --- | --- |
| `GET /api/apps/{app_id}/graph-runs` | Lists saved graph scopes for that application |
| `POST /api/apps/{app_id}/runs/{run_id}/graph` | Verifies Phase 2 provenance, resolves version identity, validates and atomically materializes the graph; repeated calls verify/return the existing graph |
| `GET /api/apps/{app_id}/versions/{app_version_id}/runs/{run_id}/graph` | Reads and validates only the exact graph scope |

Wrong application/version/run scope returns 404. Missing migration, unsupported legacy input, ambiguous version identity or failed validation returns 409. The graph API does not accept predictions or graph edges supplied by the client. Creation uses an explicit outer SQLite transaction and a savepoint; failure during final validation rolls back new graph rows and any newly created version identity. Caller rollback is effective after a released savepoint.

The existing provenance service gained an optional run filter so graph validation reads only its target run. Other provenance API behavior remains unchanged. The Phase 2 migration-test fixture now explicitly creates its 26 predecessor tables, preventing imported Phase 3 models from contaminating pre-migration fixtures.

## Frontend usage

1. Analyze an APK with Phase 2, or use an existing verified Phase 2 run.
2. Open that application's **Privacy Evidence Graph** tab.
3. Select the version/run/configuration and choose **Open validated graph**.
4. Select a graph node or use the node dropdown to inspect raw evidence or the derived finding.
5. Expand relations to see their evidence ID, qualification and deterministic explanation. Inspect payload paths separately.

The SVG uses separate columns for findings, source records, categories and SDK/domain entities. Observed nodes are blue and derived nodes are purple. A relation list provides full labels and supporting evidence; node selection highlights adjacent edges. The view displays version/run/configuration, source coverage and graph/APK hashes. Unconnected observations are disclosed rather than silently discarded. Legacy analyses display an explicit Phase 2 prerequisite message.

This phase does not implement version-comparison statistics, privacy-regression inference, graph-based empirical accuracy, independent ground truth or the Phase 4 review/benchmark interface.

## Migration and data preservation

The migration checks schemas and integrity, creates and verifies an online backup, then applies CREATE TABLE statements inside a transaction. All 30 previous table schemas and row digests were compared and preserved. No existing table was dropped or rewritten. The database now has 33 tables; the three graph tables and existing `app_versions` remain empty until a graph is requested for a verified run. Five recovered application records remain present. No synthetic test records were inserted into the recovered database.

- Backup: `recovery_backups/phase3/before_phase3_20260928T184456267031Z.db` (UTC timestamp; local migration date 2026-09-29).
- Backup SHA-256: `f1b1d20527f276bd72ea7100ebd4bc036614be1e65ff0ead2ef6f9df7044229d`.
- Migration audit: matching `.json`, with pre-existing schemas, columns, foreign keys, counts, row digests and outcome.
- Before database SHA-256: `a73a431499a5d61b2b1dbe3f37c0a2227d78542b06029980cec2f8b5ca4a65a4`.
- After database SHA-256: `11d42d74b1990bda3efa080c578c1d7f924fcd0b780dcff9f71976c859d87d9d`.
- SQLite integrity check: `ok`; foreign-key violations: none.

Online backups can have a different file layout/hash while preserving the independently compared schemas and row contents. Earlier backups remain. Backup databases are local and ignored by Git; no off-device backup is claimed.

After applying Phase 1 and Phase 2 migrations, run from the repository root:

```powershell
python -B backend/migrations/phase3_graph.py --database backend/privacy_analyzer.db --backup-directory recovery_backups/phase3
```

Already applied in this workspace. Repeating the command against the matching schema returns `already_applied`. A conflicting/partial graph or prerequisite schema stops without mutation.

## Validation and remaining limits

**126 tests pass**: the previous 84 tests plus 42 Phase 3 tests. Coverage includes graph semantics, evidence-backed payload paths, domain-only restraint, static-reference restraint, explicit claim/contradiction roles, unknown-source omissions, deterministic permutation/duplicate behavior, node/edge/orphan validation, same-version and same-hash isolation, configuration isolation, foreign-key enforcement, tamper detection, version metadata preservation, atomic rollback, HTTP scope checks and backup/migration preservation with populated Phase 2 and legacy version fixtures.

```powershell
python -B -m unittest discover -s backend/tests -v
npm.cmd run build
npx.cmd eslint src/components/PrivacyEvidenceGraph.jsx
```

The frontend production build and graph-component lint pass. Actual Uvicorn HTTP startup, graph creation/read/index, application detail, wrong-version rejection and idempotent graph creation pass using a SYNTHETIC fixture in an isolated migrated database copy. The recovered source database remains unchanged by the smoke test. No interactive browser acceptance test or real-world APK experiment was performed. The existing Windows/CPython 3.12.10 and Node 22.16.0 dependency baseline is unchanged. Vite emits large-bundle/plugin-timing warnings; TestClient emits its existing HTTPX deprecation warning.

Machine-readable validation record: `recovery_backups/phase3/final_validation.json`.

Live network capture, authenticated artifact verification and runtime API access remain unavailable. Graph correctness demonstrates internal evidence/rule consistency, not the truth of all annotations. No independently reviewed REAL_WORLD benchmark has been evaluated. **Precision/Recall/F1: N/A — benchmark dataset not yet evaluated.** Phase 4 remains the next recovery phase.
