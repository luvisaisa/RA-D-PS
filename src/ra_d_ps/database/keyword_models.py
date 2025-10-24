"""
Keyword Extraction SQLAlchemy Models

Models for keyword extraction, normalization, search, and analytics.
Database: PostgreSQL (ra_d_ps)
"""

from sqlalchemy import (
    Column, Integer, String, Text, Float, ForeignKey, 
    DateTime, UniqueConstraint, CheckConstraint, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional

from .models import Base


class Keyword(Base):
    """Core keyword model"""
    __tablename__ = 'keywords'
    
    keyword_id = Column(Integer, primary_key=True, autoincrement=True)
    keyword_text = Column(String(255), nullable=False, unique=True)
    normalized_form = Column(String(255))
    category = Column(String(100))  # 'anatomy', 'characteristic', 'diagnosis', 'metadata', 'research'
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sources = relationship("KeywordSource", back_populates="keyword", cascade="all, delete-orphan")
    statistics = relationship("KeywordStatistics", back_populates="keyword", uselist=False, cascade="all, delete-orphan")
    synonyms = relationship("KeywordSynonym", back_populates="canonical_keyword", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Keyword(id={self.keyword_id}, text='{self.keyword_text}', category='{self.category}')>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'keyword_id': self.keyword_id,
            'keyword_text': self.keyword_text,
            'normalized_form': self.normalized_form,
            'category': self.category,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class KeywordSource(Base):
    """Links keywords to source documents"""
    __tablename__ = 'keyword_sources'
    
    source_id = Column(Integer, primary_key=True, autoincrement=True)
    keyword_id = Column(Integer, ForeignKey('keywords.keyword_id', ondelete='CASCADE'), nullable=False)
    source_type = Column(String(50), nullable=False)  # 'xml', 'pdf', 'research_paper', 'annotation'
    source_file = Column(String(500), nullable=False)
    sector = Column(String(100))  # 'lidc_annotations', 'research_papers', 'metadata'
    frequency = Column(Integer, default=1)
    tf_idf_score = Column(Float, default=0.0)
    context = Column(Text)  # Surrounding text for snippet (max 500 chars)
    page_number = Column(Integer)
    position_start = Column(Integer)  # Character position in source
    position_end = Column(Integer)  # Character position end
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Unique constraint: one keyword per source file (per page for PDFs)
    __table_args__ = (
        UniqueConstraint('keyword_id', 'source_type', 'source_file', 'page_number', 
                        name='uq_keyword_source'),
        Index('idx_keyword_sources_keyword', 'keyword_id'),
        Index('idx_keyword_sources_file', 'source_file'),
        Index('idx_keyword_sources_sector', 'sector'),
        Index('idx_keyword_sources_type', 'source_type'),
        Index('idx_keyword_sources_tfidf', 'tf_idf_score'),
    )
    
    # Relationships
    keyword = relationship("Keyword", back_populates="sources")
    
    def __repr__(self):
        return f"<KeywordSource(id={self.source_id}, keyword_id={self.keyword_id}, file='{self.source_file}')>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'source_id': self.source_id,
            'keyword_id': self.keyword_id,
            'source_type': self.source_type,
            'source_file': self.source_file,
            'sector': self.sector,
            'frequency': self.frequency,
            'tf_idf_score': self.tf_idf_score,
            'context': self.context,
            'page_number': self.page_number,
            'position_start': self.position_start,
            'position_end': self.position_end,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class KeywordStatistics(Base):
    """Cached statistics for keywords"""
    __tablename__ = 'keyword_statistics'
    
    keyword_id = Column(Integer, ForeignKey('keywords.keyword_id', ondelete='CASCADE'), primary_key=True)
    total_frequency = Column(Integer, default=0)
    document_count = Column(Integer, default=0)
    idf_score = Column(Float, default=0.0)
    avg_tf_idf = Column(Float, default=0.0)
    last_calculated = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_keyword_statistics_freq', 'total_frequency'),
        Index('idx_keyword_statistics_idf', 'idf_score'),
        Index('idx_keyword_statistics_doc_count', 'document_count'),
    )
    
    # Relationships
    keyword = relationship("Keyword", back_populates="statistics")
    
    def __repr__(self):
        return f"<KeywordStatistics(keyword_id={self.keyword_id}, freq={self.total_frequency}, docs={self.document_count})>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'keyword_id': self.keyword_id,
            'total_frequency': self.total_frequency,
            'document_count': self.document_count,
            'idf_score': self.idf_score,
            'avg_tf_idf': self.avg_tf_idf,
            'last_calculated': self.last_calculated.isoformat() if self.last_calculated else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }


class KeywordSynonym(Base):
    """Maps synonyms to canonical keyword forms"""
    __tablename__ = 'keyword_synonyms'
    
    synonym_id = Column(Integer, primary_key=True, autoincrement=True)
    synonym_text = Column(String(255), nullable=False)
    canonical_keyword_id = Column(Integer, ForeignKey('keywords.keyword_id', ondelete='CASCADE'), nullable=False)
    synonym_type = Column(String(50))  # 'abbreviation', 'medical_term', 'alternate_spelling', 'acronym'
    confidence_score = Column(Float, default=1.0)
    source = Column(String(100))  # 'umls', 'manual', 'auto_detected'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('synonym_text', 'canonical_keyword_id', name='uq_synonym_canonical'),
        Index('idx_keyword_synonyms_text', 'synonym_text'),
        Index('idx_keyword_synonyms_canonical', 'canonical_keyword_id'),
        Index('idx_keyword_synonyms_type', 'synonym_type'),
    )
    
    # Relationships
    canonical_keyword = relationship("Keyword", back_populates="synonyms")
    
    def __repr__(self):
        return f"<KeywordSynonym(id={self.synonym_id}, text='{self.synonym_text}', canonical_id={self.canonical_keyword_id})>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'synonym_id': self.synonym_id,
            'synonym_text': self.synonym_text,
            'canonical_keyword_id': self.canonical_keyword_id,
            'synonym_type': self.synonym_type,
            'confidence_score': self.confidence_score,
            'source': self.source,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class KeywordCooccurrence(Base):
    """Tracks which keywords appear together"""
    __tablename__ = 'keyword_cooccurrence'
    
    cooccurrence_id = Column(Integer, primary_key=True, autoincrement=True)
    keyword_id_1 = Column(Integer, ForeignKey('keywords.keyword_id', ondelete='CASCADE'), nullable=False)
    keyword_id_2 = Column(Integer, ForeignKey('keywords.keyword_id', ondelete='CASCADE'), nullable=False)
    cooccurrence_count = Column(Integer, default=1)
    correlation_score = Column(Float, default=0.0)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint('keyword_id_1 < keyword_id_2', name='ck_keyword_order'),
        UniqueConstraint('keyword_id_1', 'keyword_id_2', name='uq_keyword_pair'),
        Index('idx_keyword_cooccurrence_kw1', 'keyword_id_1'),
        Index('idx_keyword_cooccurrence_kw2', 'keyword_id_2'),
        Index('idx_keyword_cooccurrence_count', 'cooccurrence_count'),
    )
    
    def __repr__(self):
        return f"<KeywordCooccurrence(kw1={self.keyword_id_1}, kw2={self.keyword_id_2}, count={self.cooccurrence_count})>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'cooccurrence_id': self.cooccurrence_id,
            'keyword_id_1': self.keyword_id_1,
            'keyword_id_2': self.keyword_id_2,
            'cooccurrence_count': self.cooccurrence_count,
            'correlation_score': self.correlation_score,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }


class KeywordSearchHistory(Base):
    """Analytics for search queries"""
    __tablename__ = 'keyword_search_history'
    
    search_id = Column(Integer, primary_key=True, autoincrement=True)
    query_text = Column(Text, nullable=False)
    result_count = Column(Integer, default=0)
    execution_time_ms = Column(Float)
    user_sector = Column(String(100))
    search_timestamp = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_search_history_timestamp', 'search_timestamp'),
        Index('idx_search_history_query', 'query_text'),
    )
    
    def __repr__(self):
        return f"<KeywordSearchHistory(id={self.search_id}, query='{self.query_text[:50]}...', count={self.result_count})>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'search_id': self.search_id,
            'query_text': self.query_text,
            'result_count': self.result_count,
            'execution_time_ms': self.execution_time_ms,
            'user_sector': self.user_sector,
            'search_timestamp': self.search_timestamp.isoformat() if self.search_timestamp else None
        }
