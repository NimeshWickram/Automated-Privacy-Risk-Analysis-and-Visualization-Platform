from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

DatasetType = Literal['SYNTHETIC','REAL_WORLD']
Decision = Literal['POSITIVE','NEGATIVE','UNCERTAIN']


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class DatasetInput(StrictModel):
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    dataset_type: DatasetType
    finding_categories: list[str] = Field(min_length=1)
    data_categories: list[str] = Field(min_length=1)
    protocol_rationale: str = Field(min_length=10)
    actor: str = Field(min_length=1)


class VersionInput(StrictModel):
    name: str = Field(min_length=1)
    package_name: str = Field(min_length=1)
    application_version: str = Field(min_length=1)
    apk_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    artifact_path: str | None = None
    android_tooling_version: str | None = None
    eligibility_source: str = Field(min_length=1)
    eligibility_notes: str = Field(min_length=10)
    free_educational_verified: bool
    actor: str = Field(min_length=1)


class EvidenceInput(StrictModel):
    source: Literal['MANIFEST','CODE','SDK','NETWORK','POLICY','DATA_SAFETY','RUNTIME','MANUAL_INSPECTION']
    raw_evidence: str = Field(min_length=1)
    file_reference: str = Field(min_length=1)
    artifact_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    independent_and_prediction_free: Literal[True]
    actor: str = Field(min_length=1)


class ReviewerInput(StrictModel):
    identity: str = Field(min_length=1)
    metadata: dict[str,str]
    actor: str = Field(min_length=1)


class AssignmentInput(StrictModel):
    reviewer_id: int
    actor: str = Field(min_length=1)


class ReviewUnit(StrictModel):
    finding_category: str
    data_category: str
    decision: Decision
    observation: str = Field(min_length=5)
    interpretation: str = Field(min_length=5)
    observation_status: Literal['OBSERVED','NOT_OBSERVED','UNKNOWN']
    access_status: Literal['CAPABILITY_ONLY','STATIC_REFERENCE','OBSERVED','NOT_OBSERVED','UNKNOWN','NOT_APPLICABLE']
    transmission_status: Literal['OBSERVED','NOT_OBSERVED','UNKNOWN','NOT_APPLICABLE']
    disclosure_status: Literal['CONSISTENT','INCONSISTENT','UNKNOWN','NOT_APPLICABLE']
    evidence_ids: list[int] = Field(min_length=1)


class ReviewInput(StrictModel):
    independent_review: Literal[True]
    predictions_not_seen: Literal[True]
    units: list[ReviewUnit] = Field(min_length=1)


class SealInput(StrictModel):
    review_ids: list[int] = Field(min_length=2, max_length=2)
    adjudicator_review_id: int | None = None
    approval_reason: str = Field(min_length=10)
    actor: str = Field(min_length=1)


class ActorInput(StrictModel):
    actor: str = Field(min_length=1)


class Selection(StrictModel):
    benchmark_version_id: int
    analysis_run_id: int


class EvaluationInput(StrictModel):
    dataset_type: DatasetType
    selections: list[Selection] = Field(min_length=1)
    actor: str = Field(min_length=1)


class AblationInput(EvaluationInput):
    configurations: list[Literal['A','B','C','D','E']] = Field(default_factory=lambda:list('ABCDE'), min_length=1)


class ErrorNoteInput(StrictModel):
    version_id: int
    finding_category: str
    data_category: str
    cause_analysis: str = Field(min_length=10)
    actor: str = Field(min_length=1)
