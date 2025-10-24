"""
Parse Case Repository - Data Access Layer
Implements repository pattern with caching for parse case management
"""

import logging
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional
from functools import lru_cache
from contextlib import contextmanager

from sqlalchemy import create_engine, and_, or_, desc
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from .models import Base, ParseCase, ParseCaseProfile, ParseCaseDetectionHistory, ParseCaseStatistics
from .db_config import db_config

logger = logging.getLogger(__name__)


class ParseCaseRepository:
    """
    Repository for parse case database operations
    Implements caching and connection pooling
    """
    
    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize repository with database connection
        
        Args:
            connection_string: Optional custom connection string
        """
        if connection_string is None:
            connection_string = db_config.postgresql.get_connection_string()
        
        # Determine if using SQLite (for testing) or PostgreSQL
        is_sqlite = connection_string.startswith('sqlite')
        
        # Create engine with appropriate options
        if is_sqlite:
            # SQLite doesn't support pooling options
            self.engine = create_engine(
                connection_string,
                echo=db_config.postgresql.echo_sql
            )
        else:
            # PostgreSQL with full pooling configuration
            self.engine = create_engine(
                connection_string,
                **db_config.postgresql.get_engine_kwargs()
            )
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        # Cache settings
        self.cache_enabled = db_config.enable_cache
        self.cache_ttl = db_config.cache_ttl
        
        logger.info(f"ParseCaseRepository initialized with database: {db_config.postgresql.database}")
    
    @contextmanager
    def get_session(self):
        """
        Context manager for database sessions
        Ensures proper session cleanup
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Session error: {e}")
            raise
        finally:
            session.close()
    
    def create_tables(self):
        """Create all tables in the database"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except SQLAlchemyError as e:
            logger.error(f"Failed to create tables: {e}")
            raise
    
    def drop_tables(self):
        """Drop all tables (use with caution!)"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.warning("All database tables dropped")
        except SQLAlchemyError as e:
            logger.error(f"Failed to drop tables: {e}")
            raise
    
    # ===== Parse Case CRUD Operations =====
    
    def create_parse_case(
        self,
        name: str,
        description: str,
        detection_criteria: Dict[str, Any],
        field_mappings: List[Dict[str, Any]] = None,
        characteristic_fields: List[str] = None,
        requires_header: bool = False,
        requires_modality: bool = False,
        min_session_count: int = 0,
        max_session_count: Optional[int] = None,
        detection_priority: int = 50,
        format_type: str = "LIDC",
        is_legacy_format: bool = True,
        version: str = "1.0",
        created_by: Optional[str] = None,
        notes: Optional[str] = None
    ) -> ParseCase:
        """
        Create a new parse case
        
        Args:
            name: Unique name for the parse case
            description: Human-readable description
            detection_criteria: JSON detection criteria
            field_mappings: Optional field mapping list
            characteristic_fields: List of characteristic field names
            requires_header: Whether header is required
            requires_modality: Whether modality is required
            min_session_count: Minimum number of sessions
            max_session_count: Maximum number of sessions
            detection_priority: Priority (0-100, higher = check first)
            format_type: Format category (LIDC, LIDC_v2, CXR, etc.)
            is_legacy_format: Whether this is a legacy format
            version: Version string
            created_by: Creator identifier
            notes: Additional notes
            
        Returns:
            Created ParseCase object
        """
        with self.get_session() as session:
            parse_case = ParseCase(
                name=name,
                description=description,
                detection_criteria=detection_criteria,
                field_mappings=field_mappings or [],
                characteristic_fields=characteristic_fields or [],
                requires_header=requires_header,
                requires_modality=requires_modality,
                min_session_count=min_session_count,
                max_session_count=max_session_count,
                detection_priority=detection_priority,
                format_type=format_type,
                is_legacy_format=is_legacy_format,
                version=version,
                created_by=created_by,
                notes=notes
            )
            
            session.add(parse_case)
            session.flush()
            
            logger.info(f"Created parse case: {name} (v{version})")
            return parse_case
    
    def get_parse_case_by_name(self, name: str) -> Optional[ParseCase]:
        """
        Get parse case by name
        
        Args:
            name: Parse case name
            
        Returns:
            ParseCase object or None with all attributes loaded
        """
        with self.get_session() as session:
            result = session.query(ParseCase).filter(
                ParseCase.name == name,
                ParseCase.is_active == True
            ).first()
            
            if result:
                # Trigger loading of all attributes
                _ = result.name
                _ = result.description
                _ = result.version
                _ = result.detection_criteria
                _ = result.field_mappings
                _ = result.characteristic_fields
                _ = result.detection_priority
                _ = result.format_type
                _ = result.is_active
                _ = result.is_legacy_format
                _ = result.id
                
                # Expunge to make independent of session
                session.expunge(result)
            
            return result
    
    def get_parse_case_by_id(self, parse_case_id: str) -> Optional[ParseCase]:
        """Get parse case by UUID"""
        with self.get_session() as session:
            return session.query(ParseCase).filter(
                ParseCase.id == parse_case_id
            ).first()
    
    def get_all_parse_cases(self, active_only: bool = True) -> List[ParseCase]:
        """
        Get all parse cases, optionally filtered by active status
        
        Args:
            active_only: Only return active parse cases
            
        Returns:
            List of ParseCase objects with all attributes loaded
        """
        with self.get_session() as session:
            query = session.query(ParseCase)
            
            if active_only:
                query = query.filter(ParseCase.is_active == True)
            
            # Fetch all results
            results = query.order_by(desc(ParseCase.detection_priority)).all()
            
            # Trigger loading of all attributes before session closes
            for case in results:
                # Access all lazy-loaded attributes to load them
                _ = case.name
                _ = case.description
                _ = case.version
                _ = case.detection_criteria
                _ = case.field_mappings
                _ = case.characteristic_fields
                _ = case.detection_priority
                _ = case.format_type
                _ = case.is_active
                _ = case.is_legacy_format
            
            # Make objects independent of session (expunge)
            for case in results:
                session.expunge(case)
            
            return results
    
    def get_parse_cases_by_format(self, format_type: str, active_only: bool = True) -> List[ParseCase]:
        """
        Get parse cases by format type
        
        Args:
            format_type: Format type (LIDC, LIDC_v2, CXR, etc.)
            active_only: Only return active parse cases
            
        Returns:
            List of ParseCase objects
        """
        with self.get_session() as session:
            query = session.query(ParseCase).filter(ParseCase.format_type == format_type)
            
            if active_only:
                query = query.filter(ParseCase.is_active == True)
            
            return query.order_by(desc(ParseCase.detection_priority)).all()
    
    def update_parse_case(
        self,
        name: str,
        **kwargs
    ) -> Optional[ParseCase]:
        """
        Update parse case by name
        
        Args:
            name: Parse case name
            **kwargs: Fields to update
            
        Returns:
            Updated ParseCase or None
        """
        with self.get_session() as session:
            parse_case = session.query(ParseCase).filter(ParseCase.name == name).first()
            
            if not parse_case:
                logger.warning(f"Parse case not found: {name}")
                return None
            
            for key, value in kwargs.items():
                if hasattr(parse_case, key):
                    setattr(parse_case, key, value)
            
            session.flush()
            logger.info(f"Updated parse case: {name}")
            return parse_case
    
    def deactivate_parse_case(self, name: str) -> bool:
        """
        Deactivate parse case (soft delete)
        
        Args:
            name: Parse case name
            
        Returns:
            True if deactivated, False if not found
        """
        with self.get_session() as session:
            parse_case = session.query(ParseCase).filter(ParseCase.name == name).first()
            
            if not parse_case:
                return False
            
            parse_case.is_active = False
            session.flush()
            logger.info(f"Deactivated parse case: {name}")
            return True
    
    # ===== Detection History Operations =====
    
    def record_detection(
        self,
        file_path: str,
        parse_case_name: str,
        parse_case_id: Optional[str] = None,
        file_checksum: Optional[str] = None,
        detection_metadata: Optional[Dict[str, Any]] = None,
        detection_duration_ms: Optional[int] = None
    ) -> ParseCaseDetectionHistory:
        """
        Record a parse case detection in history
        
        Args:
            file_path: Path to the file
            parse_case_name: Name of detected parse case
            parse_case_id: UUID of parse case
            file_checksum: File checksum
            detection_metadata: Detection metadata JSON
            detection_duration_ms: Detection time in milliseconds
            
        Returns:
            Created DetectionHistory object
        """
        with self.get_session() as session:
            history = ParseCaseDetectionHistory(
                file_path=file_path,
                parse_case_name=parse_case_name,
                parse_case_id=parse_case_id,
                file_checksum=file_checksum,
                detection_metadata=detection_metadata,
                detection_duration_ms=detection_duration_ms
            )
            
            session.add(history)
            session.flush()
            return history
    
    def get_detection_history(
        self,
        file_path: Optional[str] = None,
        parse_case_name: Optional[str] = None,
        limit: int = 100
    ) -> List[ParseCaseDetectionHistory]:
        """
        Query detection history
        
        Args:
            file_path: Filter by file path
            parse_case_name: Filter by parse case name
            limit: Maximum results
            
        Returns:
            List of detection history records
        """
        with self.get_session() as session:
            query = session.query(ParseCaseDetectionHistory)
            
            if file_path:
                query = query.filter(ParseCaseDetectionHistory.file_path == file_path)
            
            if parse_case_name:
                query = query.filter(ParseCaseDetectionHistory.parse_case_name == parse_case_name)
            
            return query.order_by(desc(ParseCaseDetectionHistory.detected_at)).limit(limit).all()
    
    # ===== Statistics Operations =====
    
    def update_statistics(
        self,
        parse_case_id: str,
        detection_count: int = 1,
        success: bool = True,
        detection_time_ms: Optional[int] = None,
        stat_date: Optional[date] = None
    ):
        """
        Update statistics for a parse case
        
        Args:
            parse_case_id: UUID of parse case
            detection_count: Number of detections
            success: Whether detection was successful
            detection_time_ms: Detection time in milliseconds
            stat_date: Date for statistics (defaults to today)
        """
        if stat_date is None:
            stat_date = date.today()
        
        with self.get_session() as session:
            stats = session.query(ParseCaseStatistics).filter(
                ParseCaseStatistics.parse_case_id == parse_case_id,
                ParseCaseStatistics.date == stat_date
            ).first()
            
            if not stats:
                stats = ParseCaseStatistics(
                    parse_case_id=parse_case_id,
                    date=stat_date
                )
                session.add(stats)
            
            stats.detection_count += detection_count
            if success:
                stats.success_count += 1
            else:
                stats.failure_count += 1
            
            if detection_time_ms is not None:
                # Update running average
                if stats.avg_detection_time_ms:
                    total = stats.avg_detection_time_ms * (stats.detection_count - 1) + detection_time_ms
                    stats.avg_detection_time_ms = total / stats.detection_count
                else:
                    stats.avg_detection_time_ms = detection_time_ms
            
            session.flush()
    
    def get_statistics(
        self,
        parse_case_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[ParseCaseStatistics]:
        """
        Query statistics
        
        Args:
            parse_case_id: Filter by parse case
            start_date: Start date filter
            end_date: End date filter
            
        Returns:
            List of statistics records
        """
        with self.get_session() as session:
            query = session.query(ParseCaseStatistics)
            
            if parse_case_id:
                query = query.filter(ParseCaseStatistics.parse_case_id == parse_case_id)
            
            if start_date:
                query = query.filter(ParseCaseStatistics.date >= start_date)
            
            if end_date:
                query = query.filter(ParseCaseStatistics.date <= end_date)
            
            return query.order_by(desc(ParseCaseStatistics.date)).all()
    
    def close(self):
        """Close database connections"""
        self.engine.dispose()
        logger.info("Database connections closed")
