"""Phase 2 additive metadata; Phase 1 sources, runs and finding links are reused."""
from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, ForeignKeyConstraint, UniqueConstraint, CheckConstraint
from database import Base


class AnalysisConfiguration(Base):
    __tablename__ = 'analysis_configurations'
    id = Column(String(64), primary_key=True)
    preset = Column(String, nullable=False)
    definition_json = Column(Text, nullable=False)


class FusionRun(Base):
    __tablename__ = 'fusion_runs'
    run_id = Column(Integer, ForeignKey('analysis_runs.id'), primary_key=True)
    analysis_configuration_id = Column(String(64), ForeignKey('analysis_configurations.id'), nullable=False)
    ontology_version = Column(String, nullable=False)
    rule_version = Column(String, nullable=False)
    bundle_json = Column(Text, nullable=False)
    bundle_sha256 = Column(String(64), nullable=False)
    normalized_input_sha256 = Column(String(64), nullable=False)
    semantic_output_sha256 = Column(String(64), nullable=False)
    replay_of_run_id = Column(Integer, ForeignKey('fusion_runs.run_id'), nullable=True)


class NormalizedEvidence(Base):
    __tablename__ = 'normalized_evidence'
    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey('fusion_runs.run_id'), nullable=False)
    evidence_source_id = Column(Integer, nullable=False)
    semantic_id = Column(String(64), nullable=False)
    normalized_json = Column(Text, nullable=False)
    __table_args__ = (
        ForeignKeyConstraint(['evidence_source_id', 'run_id'], ['evidence_provenance.evidence_source_id', 'evidence_provenance.run_id']),
        UniqueConstraint('run_id', 'semantic_id'),
        UniqueConstraint('run_id', 'evidence_source_id'),
    )


class FindingAssessment(Base):
    __tablename__ = 'finding_assessments'
    finding_id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey('fusion_runs.run_id'), nullable=False)
    semantic_id = Column(String(64), nullable=False)
    evidence_strength_score = Column(Float, nullable=False)
    severity = Column(String, nullable=False)
    semantic_json = Column(Text, nullable=False)
    __table_args__ = (
        ForeignKeyConstraint(['finding_id', 'run_id'], ['risk_findings.id', 'risk_findings.run_id']),
        UniqueConstraint('run_id', 'semantic_id'),
        CheckConstraint('evidence_strength_score >= 0 AND evidence_strength_score <= 1'),
    )


FUSION_TABLES = [AnalysisConfiguration.__table__, FusionRun.__table__, NormalizedEvidence.__table__, FindingAssessment.__table__]
