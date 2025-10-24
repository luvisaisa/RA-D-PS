"""
Keyword Repository

Repository pattern for keyword extraction, normalization, and search operations.
Provides CRUD operations for keywords, sources, statistics, and synonyms.

Database: PostgreSQL (ra_d_ps)
"""

import logging
from typing import List, Optional, Dict, Tuple, Any
from datetime import datetime
import math

from sqlalchemy import create_engine, func, desc, or_, and_
from sqlalchemy.orm import sessionmaker, Session, joinedload
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from .keyword_models import (
    Keyword, KeywordSource, KeywordStatistics, 
    KeywordSynonym, KeywordCooccurrence, KeywordSearchHistory
)
from .models import Base

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KeywordRepository:
    """
    Repository for keyword extraction and search operations.
    
    Provides comprehensive CRUD operations for:
    - Keywords (core keyword management)
    - Keyword sources (document tracking)
    - Statistics (frequency, IDF, TF-IDF)
    - Synonyms (normalization)
    - Co-occurrence (semantic relationships)
    - Search history (analytics)
    """
    
    def __init__(self, database: str = "ra_d_ps", 
                 host: str = "localhost", 
                 port: int = 5432,
                 user: str = None, 
                 password: str = None):
        """
        Initialize keyword repository with database connection.
        
        Args:
            database: Database name (default: ra_d_ps)
            host: Database host (default: localhost)
            port: Database port (default: 5432)
            user: Database user (optional, uses env if not provided)
                # -------------------------------------------------------------------------
                # TEXT STORAGE SECTOR (PDF/Paper/Text Clip Feature)
                # -------------------------------------------------------------------------
                # The 'text_storage' sector is used to store arbitrary text blocks, such as
                # extracted snippets from PDFs, research papers, or manual text clips. This
                # enables downstream search, retrieval, and annotation workflows for research.

            password: Database password (optional, uses env if not provided)
        """
        # Build connection string
        if user and password:
            conn_string = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        else:
            # Use default postgres user (assumes peer authentication)
            conn_string = f"postgresql://{host}:{port}/{database}"
        
        try:
            self.engine = create_engine(conn_string, echo=False)
            self.SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False)
            logger.info(f"KeywordRepository initialized with database: {database}")
        except Exception as e:
            logger.error(f"Failed to initialize KeywordRepository: {e}")
            raise
    
    def _get_session(self) -> Session:
        """Create a new database session"""
        return self.SessionLocal()
    
    # =========================================================================
    # KEYWORD CRUD OPERATIONS
    # =========================================================================
    
    def add_keyword(self, keyword_text: str, category: str = None, 
                   normalized_form: str = None, description: str = None) -> Keyword:
        """
        Add a new keyword to the database.
        
        Args:
            keyword_text: The keyword text (unique)
            category: Category ('anatomy', 'characteristic', 'diagnosis', 'metadata', 'research')
            normalized_form: Canonical/normalized version
            description: Optional description
            
        Returns:
            Keyword object
            
        Raises:
            IntegrityError: If keyword already exists (duplicate keyword_text)
            SQLAlchemyError: If database operation fails
        """
        session = self._get_session()
        try:
            keyword = Keyword(
                keyword_text=keyword_text,
                category=category,
                normalized_form=normalized_form or keyword_text.lower(),
                description=description
            )
            session.add(keyword)
            session.commit()
            session.refresh(keyword)
            
            # Initialize statistics entry
            stats = KeywordStatistics(keyword_id=keyword.keyword_id)
            session.add(stats)
            session.commit()
            
            logger.debug(f"Added keyword: {keyword_text} (id={keyword.keyword_id})")
            return keyword
        except IntegrityError:
            session.rollback()
            # Keyword already exists, fetch and return it
            keyword = session.query(Keyword).filter_by(keyword_text=keyword_text).first()
            logger.debug(f"Keyword already exists: {keyword_text} (id={keyword.keyword_id})")
            return keyword
        except Exception as e:
            session.rollback()
            logger.error(f"Error adding keyword '{keyword_text}': {e}")
            raise
        finally:
            session.close()
    
    def add_text_block(self, keyword_id: int, text: str, source_file: str = "text_block", sector: str = "text_storage") -> KeywordSource:
        """
        Store an arbitrary text block in the 'text_storage' sector.
        This is the main entry point for the PDF/paper/text clip feature.
        Args:
            keyword_id: The associated keyword (or create a generic one for clips)
            text: The text snippet to store
            source_file: Logical name for the clip (default 'text_block')
            sector: Should always be 'text_storage' for this feature
        Returns:
            KeywordSource object
        """
        return self.add_keyword_source(
            keyword_id=keyword_id,
            source_type="text",
            source_file=source_file,
            frequency=1,
            context=text,
            sector=sector
        )

    def get_text_blocks(self, keyword_id: int, sector: str = "text_storage") -> list:
        """
        Retrieve all text blocks for a keyword in the 'text_storage' sector.
        This is used to fetch all PDF/paper/text clips for downstream analysis.
        Args:
            keyword_id: The associated keyword
            sector: Should be 'text_storage'
        Returns:
            List of text snippets (strings)
        """
        session = self._get_session()
        try:
            sources = session.query(KeywordSource).filter_by(
                keyword_id=keyword_id,
                sector=sector,
                source_type="text"
            ).all()
            return [src.context for src in sources]
        finally:
            session.close()
    
    def get_keyword(self, keyword_id: int) -> Optional[Keyword]:
        """
        Get keyword by ID.
        
        Args:
            keyword_id: Keyword ID
            
        Returns:
            Keyword object or None if not found
        """
        session = self._get_session()
        try:
            keyword = session.query(Keyword).filter_by(keyword_id=keyword_id).first()
            if keyword:
                session.expunge(keyword)  # Detach from session
            return keyword
        finally:
            session.close()
    
    def get_keyword_by_text(self, keyword_text: str) -> Optional[Keyword]:
        """
        Get keyword by exact text match.
        
        Args:
            keyword_text: Keyword text
            
        Returns:
            Keyword object or None if not found
        """
        session = self._get_session()
        try:
            keyword = session.query(Keyword).filter_by(keyword_text=keyword_text).first()
            if keyword:
                session.expunge(keyword)  # Detach from session
            return keyword
        finally:
            session.close()
    
    def search_keywords(self, query: str, category: str = None, 
                       limit: int = 50) -> List[Keyword]:
        """
        Search keywords by text pattern.
        
        Args:
            query: Search query (uses ILIKE for case-insensitive match)
            category: Filter by category (optional)
            limit: Maximum results (default: 50)
            
        Returns:
            List of matching Keyword objects
        """
        session = self._get_session()
        try:
            q = session.query(Keyword).filter(
                Keyword.keyword_text.ilike(f'%{query}%')
            )
            
            if category:
                q = q.filter(Keyword.category == category)
            
            keywords = q.limit(limit).all()
            
            # Detach from session
            for keyword in keywords:
                session.expunge(keyword)
            
            return keywords
        finally:
            session.close()
    
    def get_all_keywords(self, limit: int = None) -> List[Keyword]:
        """
        Get all keywords with eagerly loaded relationships.
        
        Args:
            limit: Maximum number of keywords to return
            
        Returns:
            List of Keyword objects with statistics and sources loaded
        """
        session = self._get_session()
        try:
            query = session.query(Keyword).options(
                joinedload(Keyword.statistics),
                joinedload(Keyword.sources)
            )
            
            if limit:
                query = query.limit(limit)
            
            result = query.all()
            session.close()
            return result
        except Exception as e:
            session.close()
            logger.error(f"Error getting all keywords: {e}")
            raise
    
    def get_keywords_by_category(self, category: str) -> List[Keyword]:
        """
        Get all keywords in a specific category with eagerly loaded relationships.
        
        Args:
            category: Category name (e.g., 'characteristic', 'diagnosis', 'anatomy', 'metadata')
            
        Returns:
            List of Keyword objects in the specified category with statistics and sources loaded
        """
        session = self._get_session()
        try:
            query = session.query(Keyword).options(
                joinedload(Keyword.statistics),
                joinedload(Keyword.sources)
            ).filter(Keyword.category == category)
            result = query.all()
            session.close()
            return result
        except Exception as e:
            session.close()
            logger.error(f"Error getting keywords by category: {e}")
            raise
    
    # =========================================================================
    # KEYWORD SOURCE OPERATIONS
    # =========================================================================
    
    def add_keyword_source(self, keyword_id: int, source_type: str, 
                          source_file: str, frequency: int = 1,
                          context: str = None, sector: str = None,
                          page_number: int = None,
                          position_start: int = None,
                          position_end: int = None) -> KeywordSource:
        """
        Add a keyword source (links keyword to document).
        
        Args:
            keyword_id: Keyword ID
            source_type: Type ('xml', 'pdf', 'research_paper', 'annotation')
            source_file: File path or identifier
            frequency: Occurrences in this document (default: 1)
            context: Surrounding text snippet (max 500 chars)
            sector: Sector ('lidc_annotations', 'research_papers', 'metadata')
            page_number: Page number for PDFs
            position_start: Character position start
            position_end: Character position end
            
        Returns:
            KeywordSource object
        """
        session = self._get_session()
        try:
            source = KeywordSource(
                keyword_id=keyword_id,
                source_type=source_type,
                source_file=source_file,
                frequency=frequency,
                context=context[:500] if context else None,  # Truncate to 500 chars
                sector=sector,
                page_number=page_number,
                position_start=position_start,
                position_end=position_end
            )
            session.add(source)
            session.commit()
            session.refresh(source)
            
            logger.debug(f"Added keyword source: keyword_id={keyword_id}, file={source_file}")
            return source
        except IntegrityError:
            session.rollback()
            # Source already exists, update frequency
            source = session.query(KeywordSource).filter_by(
                keyword_id=keyword_id,
                source_type=source_type,
                source_file=source_file,
                page_number=page_number
            ).first()
            
            if source:
                source.frequency += frequency
                session.commit()
                session.refresh(source)
                logger.debug(f"Updated keyword source frequency: {source.source_id}")
            
            return source
        except Exception as e:
            session.rollback()
            logger.error(f"Error adding keyword source: {e}")
            raise
        finally:
            session.close()
    
    def get_sources_for_keyword(self, keyword_id: int, 
                               source_type: str = None,
                               sector: str = None) -> List[KeywordSource]:
        """
        Get all sources for a keyword.
        
        Args:
            keyword_id: Keyword ID
            source_type: Filter by source type (optional)
            sector: Filter by sector (optional)
            
        Returns:
            List of KeywordSource objects
        """
        session = self._get_session()
        try:
            q = session.query(KeywordSource).filter(KeywordSource.keyword_id == keyword_id)
            
            if source_type:
                q = q.filter(KeywordSource.source_type == source_type)
            if sector:
                q = q.filter(KeywordSource.sector == sector)
            
            sources = q.all()
            
            # Detach from session
            for source in sources:
                session.expunge(source)
            
            return sources
        finally:
            session.close()
    
    def get_keywords_for_source(self, source_file: str, 
                               source_type: str = None) -> List[Tuple[Keyword, KeywordSource]]:
        """
        Get all keywords in a source document.
        
        Args:
            source_file: File path or identifier
            source_type: Filter by source type (optional)
            
        Returns:
            List of (Keyword, KeywordSource) tuples
        """
        session = self._get_session()
        try:
            q = session.query(Keyword, KeywordSource).join(
                KeywordSource, Keyword.keyword_id == KeywordSource.keyword_id
            ).filter(KeywordSource.source_file == source_file)
            
            if source_type:
                q = q.filter(KeywordSource.source_type == source_type)
            
            results = q.all()
            
            # Detach from session
            for keyword, source in results:
                session.expunge(keyword)
                session.expunge(source)
            
            return results
        finally:
            session.close()
    
    # =========================================================================
    # STATISTICS OPERATIONS
    # =========================================================================
    
    def get_keyword_statistics(self, keyword_id: int) -> Optional[KeywordStatistics]:
        """
        Get statistics for a keyword.
        
        Args:
            keyword_id: Keyword ID
            
        Returns:
            KeywordStatistics object or None
        """
        session = self._get_session()
        try:
            stats = session.query(KeywordStatistics).filter_by(keyword_id=keyword_id).first()
            if stats:
                session.expunge(stats)
            return stats
        finally:
            session.close()
    
    def update_keyword_statistics(self, keyword_id: int) -> KeywordStatistics:
        """
        Recalculate statistics for a keyword.
        
        Calculates:
        - total_frequency: Sum of frequencies across all documents
        - document_count: Number of unique documents
        - idf_score: log(N / (1 + df))
        - avg_tf_idf: Average TF-IDF score across documents
        
        Args:
            keyword_id: Keyword ID
            
        Returns:
            Updated KeywordStatistics object
        """
        session = self._get_session()
        try:
            # Get statistics
            stats = session.query(KeywordStatistics).filter_by(keyword_id=keyword_id).first()
            
            if not stats:
                stats = KeywordStatistics(keyword_id=keyword_id)
                session.add(stats)
            
            # Calculate total frequency and document count
            result = session.query(
                func.sum(KeywordSource.frequency).label('total_freq'),
                func.count(KeywordSource.source_id).label('doc_count')
            ).filter(KeywordSource.keyword_id == keyword_id).first()
            
            stats.total_frequency = result.total_freq or 0
            stats.document_count = result.doc_count or 0
            
            # Calculate IDF score
            total_documents = session.query(
                func.count(func.distinct(KeywordSource.source_file))
            ).scalar() or 1
            
            if stats.document_count > 0:
                stats.idf_score = math.log(total_documents / (1 + stats.document_count))
            else:
                stats.idf_score = 0.0
            
            # Calculate average TF-IDF
            avg_tfidf = session.query(
                func.avg(KeywordSource.tf_idf_score)
            ).filter(KeywordSource.keyword_id == keyword_id).scalar()
            
            stats.avg_tf_idf = avg_tfidf or 0.0
            stats.last_calculated = datetime.utcnow()
            stats.last_updated = datetime.utcnow()
            
            session.commit()
            session.refresh(stats)
            session.expunge(stats)
            
            logger.debug(f"Updated statistics for keyword_id={keyword_id}: "
                        f"freq={stats.total_frequency}, docs={stats.document_count}, idf={stats.idf_score:.4f}")
            
            return stats
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating keyword statistics: {e}")
            raise
        finally:
            session.close()
    
    def calculate_tfidf_for_document(self, source_file: str) -> None:
        """
        Calculate TF-IDF scores for all keywords in a document.
        
        TF-IDF = term_frequency * idf_score
        
        Args:
            source_file: File path or identifier
        """
        session = self._get_session()
        try:
            # Get all keyword sources for this document
            sources = session.query(KeywordSource).filter_by(source_file=source_file).all()
            
            for source in sources:
                # Get IDF score from statistics
                stats = session.query(KeywordStatistics).filter_by(
                    keyword_id=source.keyword_id
                ).first()
                
                if stats and stats.idf_score > 0:
                    # Calculate TF-IDF
                    source.tf_idf_score = source.frequency * stats.idf_score
                else:
                    source.tf_idf_score = 0.0
            
            session.commit()
            logger.debug(f"Calculated TF-IDF for {len(sources)} keywords in {source_file}")
        except Exception as e:
            session.rollback()
            logger.error(f"Error calculating TF-IDF: {e}")
            raise
        finally:
            session.close()
    
    def get_top_keywords(self, limit: int = 100, 
                        category: str = None,
                        sector: str = None) -> List[Tuple[Keyword, KeywordStatistics]]:
        """
        Get top keywords by frequency.
        
        Args:
            limit: Maximum results (default: 100)
            category: Filter by category (optional)
            sector: Filter by sector (optional)
            
        Returns:
            List of (Keyword, KeywordStatistics) tuples, sorted by frequency
        """
        session = self._get_session()
        try:
            q = session.query(Keyword, KeywordStatistics).join(
                KeywordStatistics, Keyword.keyword_id == KeywordStatistics.keyword_id
            )
            
            if category:
                q = q.filter(Keyword.category == category)
            
            if sector:
                q = q.join(
                    KeywordSource, Keyword.keyword_id == KeywordSource.keyword_id
                ).filter(KeywordSource.sector == sector)
            
            results = q.order_by(desc(KeywordStatistics.total_frequency)).limit(limit).all()
            
            # Detach from session
            for keyword, stats in results:
                session.expunge(keyword)
                session.expunge(stats)
            
            return results
        finally:
            session.close()
    
    # =========================================================================
    # SYNONYM OPERATIONS
    # =========================================================================
    
    def add_synonym(self, synonym_text: str, canonical_keyword_id: int,
                   synonym_type: str = 'manual', confidence_score: float = 1.0,
                   source: str = 'manual') -> KeywordSynonym:
        """
        Add a synonym mapping.
        
        Args:
            synonym_text: Synonym text
            canonical_keyword_id: ID of canonical keyword
            synonym_type: Type ('abbreviation', 'medical_term', 'alternate_spelling', 'acronym')
            confidence_score: Confidence (0-1, default: 1.0)
            source: Source ('umls', 'manual', 'auto_detected')
            
        Returns:
            KeywordSynonym object
        """
        session = self._get_session()
        try:
            synonym = KeywordSynonym(
                synonym_text=synonym_text,
                canonical_keyword_id=canonical_keyword_id,
                synonym_type=synonym_type,
                confidence_score=confidence_score,
                source=source
            )
            session.add(synonym)
            session.commit()
            session.refresh(synonym)
            
            logger.debug(f"Added synonym: '{synonym_text}' -> keyword_id={canonical_keyword_id}")
            return synonym
        except IntegrityError:
            session.rollback()
            # Synonym already exists
            synonym = session.query(KeywordSynonym).filter_by(
                synonym_text=synonym_text,
                canonical_keyword_id=canonical_keyword_id
            ).first()
            return synonym
        except Exception as e:
            session.rollback()
            logger.error(f"Error adding synonym: {e}")
            raise
        finally:
            session.close()
    
    def get_canonical_keyword(self, text: str) -> Optional[Keyword]:
        """
        Get canonical keyword for a text (exact match or synonym lookup).
        
        Args:
            text: Search text
            
        Returns:
            Keyword object or None
        """
        session = self._get_session()
        try:
            # Try exact match first
            keyword = session.query(Keyword).filter_by(keyword_text=text).first()
            
            if keyword:
                session.expunge(keyword)
                return keyword
            
            # Try synonym lookup
            synonym = session.query(KeywordSynonym).filter_by(synonym_text=text).first()
            
            if synonym:
                keyword = session.query(Keyword).filter_by(
                    keyword_id=synonym.canonical_keyword_id
                ).first()
                
                if keyword:
                    session.expunge(keyword)
                return keyword
            
            return None
        finally:
            session.close()
    
    def get_synonyms_for_keyword(self, keyword_id: int) -> List[KeywordSynonym]:
        """
        Get all synonyms for a keyword.
        
        Args:
            keyword_id: Keyword ID
            
        Returns:
            List of KeywordSynonym objects
        """
        session = self._get_session()
        try:
            synonyms = session.query(KeywordSynonym).filter_by(
                canonical_keyword_id=keyword_id
            ).all()
            
            # Detach from session
            for synonym in synonyms:
                session.expunge(synonym)
            
            return synonyms
        finally:
            session.close()
    
    # =========================================================================
    # SEARCH & ANALYTICS
    # =========================================================================
    
    def record_search(self, query_text: str, result_count: int,
                     execution_time_ms: float = None,
                     user_sector: str = None) -> KeywordSearchHistory:
        """
        Record a search query for analytics.
        
        Args:
            query_text: Search query
            result_count: Number of results returned
            execution_time_ms: Query execution time in milliseconds
            user_sector: Sector searched
            
        Returns:
            KeywordSearchHistory object
        """
        session = self._get_session()
        try:
            search_record = KeywordSearchHistory(
                query_text=query_text,
                result_count=result_count,
                execution_time_ms=execution_time_ms,
                user_sector=user_sector
            )
            session.add(search_record)
            session.commit()
            session.refresh(search_record)
            
            return search_record
        except Exception as e:
            session.rollback()
            logger.error(f"Error recording search: {e}")
            raise
        finally:
            session.close()
    
    def get_search_analytics(self, limit: int = 100) -> List[Dict]:
        """
        Get recent search analytics.
        
        Args:
            limit: Maximum results (default: 100)
            
        Returns:
            List of search history dictionaries
        """
        session = self._get_session()
        try:
            searches = session.query(KeywordSearchHistory).order_by(
                desc(KeywordSearchHistory.search_timestamp)
            ).limit(limit).all()
            
            return [s.to_dict() for s in searches]
        finally:
            session.close()
    
    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    
    def close(self):
        """Close database connection"""
        if self.engine:
            self.engine.dispose()
            logger.info("KeywordRepository connection closed")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
