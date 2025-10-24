"""
SQLAlchemy Models for Parse Case Management
Declarative ORM models for PostgreSQL tables
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import uuid4

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, JSON, 
    ForeignKey, CheckConstraint, Index, ARRAY, Numeric, Date
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class ParseCase(Base):
    """
    Parse case definitions with detection criteria
    """
    __tablename__ = 'parse_cases'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text)
    version = Column(String(20), nullable=False, default='1.0')
    
    # Detection criteria as JSONB
    detection_criteria = Column(JSONB, nullable=False)
    field_mappings = Column(JSONB, default=[])
    characteristic_fields = Column(ARRAY(String), default=[])
    
    # Structural requirements
    requires_header = Column(Boolean, default=False)
    requires_modality = Column(Boolean, default=False)
    min_session_count = Column(Integer, default=0)
    max_session_count = Column(Integer, nullable=True)
    
    # Detection priority (0-100)
    detection_priority = Column(
        Integer, 
        default=50,
        nullable=False
    )
    
    # Status and metadata
    is_active = Column(Boolean, default=True, index=True)
    is_legacy_format = Column(Boolean, default=True)
    format_type = Column(String(50), default='LIDC', index=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(String(100))
    notes = Column(Text)
    
    # Relationships
    profiles = relationship("ParseCaseProfile", back_populates="parse_case", cascade="all, delete-orphan")
    detection_history = relationship("ParseCaseDetectionHistory", back_populates="parse_case")
    statistics = relationship("ParseCaseStatistics", back_populates="parse_case", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('detection_priority >= 0 AND detection_priority <= 100', name='valid_priority'),
        Index('idx_parse_cases_detection_criteria', 'detection_criteria', postgresql_using='gin'),
    )
    
    def __repr__(self):
        return f"<ParseCase(name='{self.name}', version='{self.version}', format='{self.format_type}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'detection_criteria': self.detection_criteria,
            'field_mappings': self.field_mappings,
            'characteristic_fields': self.characteristic_fields,
            'requires_header': self.requires_header,
            'requires_modality': self.requires_modality,
            'min_session_count': self.min_session_count,
            'max_session_count': self.max_session_count,
            'detection_priority': self.detection_priority,
            'is_active': self.is_active,
            'is_legacy_format': self.is_legacy_format,
            'format_type': self.format_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by,
            'notes': self.notes
        }


class ParseCaseProfile(Base):
    """
    Profile configurations linked to parse cases
    """
    __tablename__ = 'parse_case_profiles'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    parse_case_id = Column(UUID(as_uuid=True), ForeignKey('parse_cases.id', ondelete='CASCADE'), nullable=False)
    profile_name = Column(String(100), nullable=False)
    profile_config = Column(JSONB, nullable=False)
    is_default = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    parse_case = relationship("ParseCase", back_populates="profiles")
    
    # Constraints
    __table_args__ = (
        Index('idx_parse_case_profiles_parse_case', 'parse_case_id'),
        Index('idx_parse_case_profiles_default', 'is_default', postgresql_where='is_default = true'),
    )
    
    def __repr__(self):
        return f"<ParseCaseProfile(name='{self.profile_name}', is_default={self.is_default})>"


class ParseCaseDetectionHistory(Base):
    """
    Audit trail of parse case detections
    """
    __tablename__ = 'parse_case_detection_history'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    file_path = Column(Text, nullable=False, index=True)
    file_checksum = Column(String(64))
    parse_case_id = Column(UUID(as_uuid=True), ForeignKey('parse_cases.id', ondelete='SET NULL'))
    parse_case_name = Column(String(100), nullable=False)
    detection_metadata = Column(JSONB)
    
    detected_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    detection_duration_ms = Column(Integer)
    
    # Relationships
    parse_case = relationship("ParseCase", back_populates="detection_history")
    
    # Indexes
    __table_args__ = (
        Index('idx_detection_history_file', 'file_path'),
        Index('idx_detection_history_detected_at', 'detected_at', postgresql_ops={'detected_at': 'DESC'}),
    )
    
    def __repr__(self):
        return f"<DetectionHistory(file='{self.file_path[:50]}...', case='{self.parse_case_name}')>"


class ParseCaseStatistics(Base):
    """
    Aggregated statistics for parse case usage
    """
    __tablename__ = 'parse_case_statistics'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    parse_case_id = Column(UUID(as_uuid=True), ForeignKey('parse_cases.id', ondelete='CASCADE'), nullable=False)
    date = Column(Date, nullable=False, default=func.current_date())
    
    detection_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    avg_detection_time_ms = Column(Numeric(10, 2))
    
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    parse_case = relationship("ParseCase", back_populates="statistics")
    
    # Constraints and indexes
    __table_args__ = (
        Index('idx_statistics_parse_case', 'parse_case_id'),
        Index('idx_statistics_date', 'date', postgresql_ops={'date': 'DESC'}),
    )
    
    def __repr__(self):
        return f"<Statistics(date={self.date}, detections={self.detection_count})>"
