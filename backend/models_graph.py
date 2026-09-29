"""Additive version-scoped graph tables; reuse the existing app_versions table."""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, ForeignKeyConstraint, UniqueConstraint, CheckConstraint
from database import Base


class GraphRun(Base):
    __tablename__ = 'privacy_graph_runs'
    run_id = Column(Integer, ForeignKey('fusion_runs.run_id'), primary_key=True)
    app_version_id = Column(Integer, ForeignKey('app_versions.id'), nullable=False)
    graph_version = Column(String, nullable=False)
    graph_sha256 = Column(String(64), nullable=False)
    created_at = Column(String, nullable=False)
    omitted_evidence_json = Column(Text, nullable=False)
    __table_args__ = (UniqueConstraint('run_id', 'app_version_id'),)


class GraphNode(Base):
    __tablename__ = 'privacy_graph_nodes'
    run_id = Column(Integer, primary_key=True)
    app_version_id = Column(Integer, primary_key=True)
    node_id = Column(String, primary_key=True)
    node_type = Column(String, nullable=False)
    layer = Column(String, nullable=False)
    data_json = Column(Text, nullable=False)
    evidence_source_id = Column(Integer, nullable=True)
    finding_id = Column(Integer, nullable=True)
    __table_args__ = (
        ForeignKeyConstraint(['run_id','app_version_id'], ['privacy_graph_runs.run_id','privacy_graph_runs.app_version_id']),
        ForeignKeyConstraint(['evidence_source_id','run_id'], ['evidence_provenance.evidence_source_id','evidence_provenance.run_id']),
        ForeignKeyConstraint(['finding_id','run_id'], ['risk_findings.id','risk_findings.run_id']),
        CheckConstraint("(node_type IN ('EVIDENCE_SOURCE','SDK','DOMAIN') AND layer = 'OBSERVED') OR (node_type IN ('DATA_CATEGORY','RISK_FINDING') AND layer = 'DERIVED')"),
        CheckConstraint("(node_type = 'EVIDENCE_SOURCE' AND evidence_source_id IS NOT NULL AND finding_id IS NULL) OR (node_type = 'RISK_FINDING' AND finding_id IS NOT NULL AND evidence_source_id IS NULL) OR (node_type IN ('SDK','DOMAIN','DATA_CATEGORY') AND evidence_source_id IS NULL AND finding_id IS NULL)"),
    )


class GraphEdge(Base):
    __tablename__ = 'privacy_graph_edges'
    run_id = Column(Integer, primary_key=True)
    app_version_id = Column(Integer, primary_key=True)
    edge_id = Column(String(64), primary_key=True)
    source_node_id = Column(String, nullable=False)
    target_node_id = Column(String, nullable=False)
    relation = Column(String, nullable=False)
    evidence_source_id = Column(Integer, nullable=False)
    data_json = Column(Text, nullable=False)
    __table_args__ = (
        ForeignKeyConstraint(['run_id','app_version_id','source_node_id'], ['privacy_graph_nodes.run_id','privacy_graph_nodes.app_version_id','privacy_graph_nodes.node_id']),
        ForeignKeyConstraint(['run_id','app_version_id','target_node_id'], ['privacy_graph_nodes.run_id','privacy_graph_nodes.app_version_id','privacy_graph_nodes.node_id']),
        ForeignKeyConstraint(['evidence_source_id','run_id'], ['evidence_provenance.evidence_source_id','evidence_provenance.run_id']),
        CheckConstraint("relation IN ('INDICATES_CAPABILITY','REFERENCES_API_FOR','ACCESSES_DATA','ATTRIBUTED_TO','CONTACTS','HAS_PAYLOAD_CATEGORY','TRANSMITTED_TO','CLAIMS_COLLECTION','DENIES_COLLECTION','SUPPORTED_BY','CONTRADICTED_BY')"),
    )


GRAPH_TABLES = [GraphRun.__table__, GraphNode.__table__, GraphEdge.__table__]
