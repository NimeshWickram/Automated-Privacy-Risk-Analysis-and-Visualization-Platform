"""Additive Phase 1 tables. Existing evidence and application tables are retained."""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, ForeignKeyConstraint, UniqueConstraint, CheckConstraint
from database import Base


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"
    id = Column(Integer, primary_key=True)
    app_id = Column(Integer, ForeignKey("app_analyses.id"), nullable=False)
    apk_sha256 = Column(String(64), nullable=False)
    application_version = Column(String, nullable=False)
    analysis_version = Column(String, nullable=False)
    started_at = Column(String, nullable=False)
    source_status_json = Column(Text, nullable=False)
    environment_json = Column(Text, nullable=False)


class EvidenceProvenance(Base):
    __tablename__ = "evidence_provenance"
    evidence_source_id = Column(Integer, ForeignKey("evidence_sources.id"), primary_key=True)
    run_id = Column(Integer, ForeignKey("analysis_runs.id"), nullable=False)
    observation_kind = Column(String, nullable=False)
    analyzer = Column(String, nullable=False)
    captured_at = Column(String, nullable=False)
    snapshot_json = Column(Text, nullable=False)
    snapshot_sha256 = Column(String(64), nullable=False)
    __table_args__ = (UniqueConstraint("evidence_source_id", "run_id"),)


class RiskFinding(Base):
    __tablename__ = "risk_findings"
    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("analysis_runs.id"), nullable=False)
    finding_category = Column(String, nullable=False)
    data_category = Column(String, nullable=False)
    interpretation = Column(Text, nullable=False)
    rule_id = Column(String, nullable=False)
    created_at = Column(String, nullable=False)
    __table_args__ = (UniqueConstraint("id", "run_id"),)


class FindingEvidence(Base):
    __tablename__ = "finding_evidence"
    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, nullable=False)
    finding_id = Column(Integer, nullable=False)
    evidence_source_id = Column(Integer, nullable=False)
    relationship = Column(String, nullable=False)
    rationale = Column(Text, nullable=False)
    __table_args__ = (
        ForeignKeyConstraint(["finding_id", "run_id"], ["risk_findings.id", "risk_findings.run_id"]),
        ForeignKeyConstraint(["evidence_source_id", "run_id"], ["evidence_provenance.evidence_source_id", "evidence_provenance.run_id"]),
        CheckConstraint("relationship IN ('SUPPORTS', 'CORROBORATES', 'CONTRADICTS')"),
        UniqueConstraint("finding_id", "evidence_source_id", "relationship"),
    )


PROVENANCE_TABLES = [AnalysisRun.__table__, EvidenceProvenance.__table__, RiskFinding.__table__, FindingEvidence.__table__]
