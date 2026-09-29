"""Isolated benchmark/review data. Automated findings are never ground truth."""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, ForeignKeyConstraint, UniqueConstraint, CheckConstraint
from database import Base


class BenchmarkDataset(Base):
    __tablename__ = 'benchmark_datasets'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    version = Column(String, nullable=False)
    dataset_type = Column(String, nullable=False)
    protocol_json = Column(Text, nullable=False)
    created_at = Column(String, nullable=False)
    frozen_at = Column(String)
    __table_args__ = (UniqueConstraint('name','version'), CheckConstraint("dataset_type IN ('SYNTHETIC','REAL_WORLD')"))


class BenchmarkApplication(Base):
    __tablename__ = 'benchmark_applications'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    package_name = Column(String, nullable=False)


class BenchmarkVersion(Base):
    __tablename__ = 'benchmark_versions'
    id = Column(Integer, primary_key=True)
    dataset_id = Column(Integer, ForeignKey('benchmark_datasets.id'), nullable=False)
    application_id = Column(Integer, ForeignKey('benchmark_applications.id'), nullable=False)
    dataset_type = Column(String, nullable=False)
    apk_sha256 = Column(String(64), nullable=False)
    application_version = Column(String, nullable=False)
    verification_json = Column(Text, nullable=False)
    created_at = Column(String, nullable=False)
    sealed_at = Column(String)
    truth_sha256 = Column(String(64))
    __table_args__ = (UniqueConstraint('dataset_id','apk_sha256'), CheckConstraint("dataset_type IN ('SYNTHETIC','REAL_WORLD')"))


class GroundTruthEvidence(Base):
    __tablename__ = 'ground_truth_evidence'
    id = Column(Integer, primary_key=True)
    version_id = Column(Integer, ForeignKey('benchmark_versions.id'), nullable=False)
    source = Column(String, nullable=False)
    raw_evidence = Column(Text, nullable=False)
    file_reference = Column(Text, nullable=False)
    artifact_sha256 = Column(String(64), nullable=False)
    curator = Column(String, nullable=False)
    created_at = Column(String, nullable=False)
    __table_args__ = (UniqueConstraint('id','version_id'),)


class GroundTruthReviewer(Base):
    __tablename__ = 'ground_truth_reviewers'
    id = Column(Integer, primary_key=True)
    identity = Column(String, unique=True, nullable=False)
    metadata_json = Column(Text, nullable=False)
    created_at = Column(String, nullable=False)


class ReviewAssignment(Base):
    __tablename__ = 'benchmark_review_assignments'
    id = Column(Integer, primary_key=True)
    version_id = Column(Integer, ForeignKey('benchmark_versions.id'), nullable=False)
    reviewer_id = Column(Integer, ForeignKey('ground_truth_reviewers.id'), nullable=False)
    token_sha256 = Column(String(64), unique=True, nullable=False)
    packet_sha256 = Column(String(64), nullable=False)
    created_at = Column(String, nullable=False)
    __table_args__ = (UniqueConstraint('version_id','reviewer_id'), UniqueConstraint('id','version_id'))


class ReviewerReview(Base):
    __tablename__ = 'reviewer_reviews'
    id = Column(Integer, primary_key=True)
    assignment_id = Column(Integer, unique=True, nullable=False)
    version_id = Column(Integer, nullable=False)
    decisions_json = Column(Text, nullable=False)
    submission_sha256 = Column(String(64), nullable=False)
    submitted_at = Column(String, nullable=False)
    __table_args__ = (ForeignKeyConstraint(['assignment_id','version_id'], ['benchmark_review_assignments.id','benchmark_review_assignments.version_id']), UniqueConstraint('id','version_id'))


class GroundTruthFinding(Base):
    __tablename__ = 'ground_truth_findings'
    id = Column(Integer, primary_key=True)
    version_id = Column(Integer, ForeignKey('benchmark_versions.id'), nullable=False)
    review_id = Column(Integer, nullable=False)
    first_evidence_id = Column(Integer, nullable=False)
    finding_category = Column(String, nullable=False)
    data_category = Column(String, nullable=False)
    decision_json = Column(Text, nullable=False)
    approved_by = Column(String, nullable=False)
    approval_reason = Column(Text, nullable=False)
    approved_at = Column(String, nullable=False)
    __table_args__ = (
        ForeignKeyConstraint(['review_id','version_id'], ['reviewer_reviews.id','reviewer_reviews.version_id']),
        ForeignKeyConstraint(['first_evidence_id','version_id'], ['ground_truth_evidence.id','ground_truth_evidence.version_id']),
        UniqueConstraint('version_id','finding_category','data_category'),)


class EvaluationRun(Base):
    __tablename__ = 'benchmark_evaluation_runs'
    id = Column(Integer, primary_key=True)
    dataset_id = Column(Integer, ForeignKey('benchmark_datasets.id'), nullable=False)
    dataset_type = Column(String, nullable=False)
    snapshot_json = Column(Text, nullable=False)
    snapshot_sha256 = Column(String(64), nullable=False)
    created_at = Column(String, nullable=False)


class AblationExperiment(Base):
    __tablename__ = 'benchmark_ablation_experiments'
    id = Column(Integer, primary_key=True)
    dataset_id = Column(Integer, ForeignKey('benchmark_datasets.id'), nullable=False)
    experiment_json = Column(Text, nullable=False)
    experiment_sha256 = Column(String(64), nullable=False)
    created_at = Column(String, nullable=False)


class BenchmarkAuditEvent(Base):
    __tablename__ = 'benchmark_audit_events'
    id = Column(Integer, primary_key=True)
    event = Column(String, nullable=False)
    actor = Column(String, nullable=False)
    detail_json = Column(Text, nullable=False)
    created_at = Column(String, nullable=False)


BENCHMARK_TABLES = [value.__table__ for value in (BenchmarkDataset, BenchmarkApplication, BenchmarkVersion, GroundTruthEvidence,
    GroundTruthReviewer, ReviewAssignment, ReviewerReview, GroundTruthFinding, EvaluationRun, AblationExperiment, BenchmarkAuditEvent)]
