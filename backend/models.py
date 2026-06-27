from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class AppAnalysis(Base):
    __tablename__ = "app_analyses"

    id = Column(Integer, primary_key=True, index=True)
    app_name = Column(String, index=True)
    package_name = Column(String, index=True)
    developer = Column(String)
    category = Column(String)
    version_name = Column(String)
    apk_size = Column(String)
    target_sdk = Column(Integer)
    apk_hash = Column(String)
    analyzed_at = Column(String)

    risk_score = Column(Integer)
    risk_grade = Column(String)
    risk_level = Column(String)

    permissions = relationship("AppPermission", back_populates="app", cascade="all, delete-orphan")
    trackers = relationship("AppTracker", back_populates="app", cascade="all, delete-orphan")

class AppPermission(Base):
    __tablename__ = "app_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(Integer, ForeignKey("app_analyses.id"))
    name = Column(String)
    status = Column(String) # 'normal' or 'dangerous'
    description = Column(String)
    justified = Column(Boolean, default=False)
    
    app = relationship("AppAnalysis", back_populates="permissions")

class AppTracker(Base):
    __tablename__ = "app_trackers"
    
    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(Integer, ForeignKey("app_analyses.id"))
    name = Column(String)
    risk = Column(String)
    description = Column(String)
    category = Column(String)
    
    app = relationship("AppAnalysis", back_populates="trackers")
