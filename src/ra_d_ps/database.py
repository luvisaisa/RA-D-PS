#!/usr/bin/env python3
"""
SQLite Database Module for Radiology XML Data
Provides structured storage with relational design optimized for nodule-centric analysis
"""

import sqlite3
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd

class RadiologyDatabase:
    """
    SQLite database manager for radiology XML parsing results
    Implements normalized schema with nodule-centric design
    """
    
    def __init__(self, db_path: str):
        """Initialize database connection and create tables if needed"""
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Enable column access by name
        self._create_tables()
        self._create_indexes()
        
    def _create_tables(self):
        """Create optimized table structure for radiology data"""
        
        # Files table - one record per XML file
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS files (
            file_id TEXT PRIMARY KEY,
            file_path TEXT NOT NULL,
            parse_case TEXT NOT NULL,
            study_instance_uid TEXT,
            series_instance_uid TEXT,
            modality TEXT,
            date_service TEXT,
            time_service TEXT,
            parsed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            file_size INTEGER,
            parsing_duration_seconds REAL,
            UNIQUE(file_path)
        )
        """)
        
        # Nodules table - one record per unique nodule
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS nodules (
            nodule_key TEXT PRIMARY KEY,  -- file_id + nodule_id + z_coord
            file_id TEXT NOT NULL,
            nodule_id TEXT NOT NULL,
            z_coordinate REAL,
            x_coordinate REAL,
            y_coordinate REAL,
            coordinate_count INTEGER DEFAULT 0,
            session_type TEXT CHECK(session_type IN ('Standard', 'Detailed')) DEFAULT 'Standard',
            sop_uid TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (file_id) REFERENCES files(file_id) ON DELETE CASCADE
        )
        """)
        
        # Radiologist ratings table - one record per radiologist per nodule
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS radiologist_ratings (
            rating_id INTEGER PRIMARY KEY AUTOINCREMENT,
            nodule_key TEXT NOT NULL,
            file_id TEXT NOT NULL,
            radiologist_id TEXT NOT NULL,
            confidence REAL,
            subtlety REAL,
            obscuration REAL,
            reason TEXT,
            is_unblinded BOOLEAN DEFAULT FALSE,
            rating_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (nodule_key) REFERENCES nodules(nodule_key) ON DELETE CASCADE,
            FOREIGN KEY (file_id) REFERENCES files(file_id) ON DELETE CASCADE,
            UNIQUE(nodule_key, radiologist_id)  -- One rating per radiologist per nodule
        )
        """)
        
        # Parse statistics table - track parsing performance
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS parse_statistics (
            stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id TEXT NOT NULL,
            total_files INTEGER,
            successfully_parsed INTEGER,
            failed_files INTEGER,
            empty_files INTEGER,
            total_nodules INTEGER,
            total_ratings INTEGER,
            missing_data_percentage REAL,
            parse_duration_seconds REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Data quality issues table - track problems
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS quality_issues (
            issue_id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id TEXT,
            nodule_key TEXT,
            issue_type TEXT NOT NULL,  -- 'missing_data', 'parse_error', 'invalid_value', etc.
            issue_description TEXT,
            severity TEXT CHECK(severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')) DEFAULT 'MEDIUM',
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (file_id) REFERENCES files(file_id) ON DELETE CASCADE,
            FOREIGN KEY (nodule_key) REFERENCES nodules(nodule_key) ON DELETE CASCADE
        )
        """)
        
        self.conn.commit()
        
    def _create_indexes(self):
        """Create indexes for optimal query performance"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_nodules_file_id ON nodules(file_id)",
            "CREATE INDEX IF NOT EXISTS idx_nodules_session_type ON nodules(session_type)", 
            "CREATE INDEX IF NOT EXISTS idx_ratings_nodule ON radiologist_ratings(nodule_key)",
            "CREATE INDEX IF NOT EXISTS idx_ratings_radiologist ON radiologist_ratings(radiologist_id)",
            "CREATE INDEX IF NOT EXISTS idx_ratings_confidence ON radiologist_ratings(confidence)",
            "CREATE INDEX IF NOT EXISTS idx_files_parse_case ON files(parse_case)",
            "CREATE INDEX IF NOT EXISTS idx_files_date ON files(date_service)",
            "CREATE INDEX IF NOT EXISTS idx_quality_issues_type ON quality_issues(issue_type, severity)"
        ]
        
        for index_sql in indexes:
            self.conn.execute(index_sql)
        self.conn.commit()
        
    def insert_batch_data(self, parsed_data: List[Dict], batch_id: str = None) -> str:
        """
        Insert a batch of parsed XML data into the database
        Returns batch_id for tracking
        """
        if not batch_id:
            batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
        start_time = datetime.now()
        files_inserted = 0
        nodules_inserted = 0 
        ratings_inserted = 0
        quality_issues = []
        
        try:
            # Group data by file for efficient insertion
            file_groups = {}
            for row in parsed_data:
                file_id = row.get('FileID', 'unknown')
                if file_id not in file_groups:
                    file_groups[file_id] = []
                file_groups[file_id].append(row)
            
            for file_id, file_rows in file_groups.items():
                if not file_rows:
                    continue
                    
                # Insert file record (use first row for file-level data)
                first_row = file_rows[0]
                
                self.conn.execute("""
                INSERT OR REPLACE INTO files (
                    file_id, file_path, parse_case, study_instance_uid, 
                    series_instance_uid, modality, date_service, time_service
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    file_id,
                    first_row.get('FilePath', ''),
                    first_row.get('ParseCase', 'Unknown'),
                    first_row.get('StudyInstanceUID'),
                    first_row.get('SeriesInstanceUID'), 
                    first_row.get('Modality'),
                    first_row.get('DateService'),
                    first_row.get('TimeService')
                ))
                files_inserted += 1
                
                # Group file rows by nodule
                nodule_groups = {}
                for row in file_rows:
                    nodule_id = row.get('NoduleID', 'unknown')
                    z_coord = row.get('Z_coord', 'NoZ')
                    nodule_key = f"{file_id}_{nodule_id}_{z_coord}"
                    
                    if nodule_key not in nodule_groups:
                        nodule_groups[nodule_key] = []
                    nodule_groups[nodule_key].append(row)
                
                # Insert nodules and ratings
                for nodule_key, nodule_rows in nodule_groups.items():
                    if not nodule_rows:
                        continue
                        
                    # Use first row for nodule-level data
                    base_row = nodule_rows[0]
                    
                    # Safely convert coordinates
                    def safe_float(val):
                        if val in ['#N/A', 'MISSING', '', None]:
                            return None
                        try:
                            return float(val)
                        except (ValueError, TypeError):
                            return None
                    
                    def safe_int(val):
                        if val in ['#N/A', 'MISSING', '', None]:
                            return 0
                        try:
                            return int(val)
                        except (ValueError, TypeError):
                            return 0
                    
                    # Insert nodule
                    self.conn.execute("""
                    INSERT OR REPLACE INTO nodules (
                        nodule_key, file_id, nodule_id, z_coordinate,
                        x_coordinate, y_coordinate, coordinate_count,
                        session_type, sop_uid
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        nodule_key,
                        file_id,
                        base_row.get('NoduleID', 'unknown'),
                        safe_float(base_row.get('Z_coord')),
                        safe_float(base_row.get('X_coord')),
                        safe_float(base_row.get('Y_coord')),
                        safe_int(base_row.get('CoordCount')),
                        base_row.get('SessionType', 'Standard'),
                        base_row.get('SOP_UID')
                    ))
                    nodules_inserted += 1
                    
                    # Insert radiologist ratings
                    for row in nodule_rows:
                        radiologist = row.get('Radiologist', 'Unknown')
                        
                        # Check for data quality issues
                        missing_fields = []
                        for field in ['Confidence', 'Subtlety', 'X_coord', 'Y_coord']:
                            if row.get(field) == 'MISSING':
                                missing_fields.append(field)
                        
                        if missing_fields:
                            quality_issues.append({
                                'file_id': file_id,
                                'nodule_key': nodule_key,
                                'issue_type': 'missing_data',
                                'issue_description': f"Missing fields: {', '.join(missing_fields)}",
                                'severity': 'MEDIUM'
                            })
                        
                        self.conn.execute("""
                        INSERT OR REPLACE INTO radiologist_ratings (
                            nodule_key, file_id, radiologist_id, 
                            confidence, subtlety, obscuration, reason
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            nodule_key,
                            file_id,
                            radiologist,
                            safe_float(row.get('Confidence')),
                            safe_float(row.get('Subtlety')),
                            safe_float(row.get('Obscuration')),
                            row.get('Reason') if row.get('Reason') not in ['#N/A', 'MISSING'] else None
                        ))
                        ratings_inserted += 1
            
            # Insert quality issues
            for issue in quality_issues:
                self.conn.execute("""
                INSERT INTO quality_issues (
                    file_id, nodule_key, issue_type, issue_description, severity
                ) VALUES (?, ?, ?, ?, ?)
                """, (issue['file_id'], issue['nodule_key'], issue['issue_type'], 
                      issue['issue_description'], issue['severity']))
            
            # Insert batch statistics
            duration = (datetime.now() - start_time).total_seconds()
            missing_percentage = (len(quality_issues) / max(ratings_inserted, 1)) * 100
            
            self.conn.execute("""
            INSERT INTO parse_statistics (
                batch_id, total_files, successfully_parsed, total_nodules, 
                total_ratings, missing_data_percentage, parse_duration_seconds
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (batch_id, len(file_groups), files_inserted, nodules_inserted,
                  ratings_inserted, missing_percentage, duration))
            
            self.conn.commit()
            
            print(f"✅ Batch {batch_id} inserted successfully:")
            print(f"   📁 Files: {files_inserted}")
            print(f"   🎯 Nodules: {nodules_inserted}")  
            print(f"   👥 Ratings: {ratings_inserted}")
            print(f"   ⚠️  Quality issues: {len(quality_issues)}")
            print(f"   ⏱️  Duration: {duration:.2f}s")
            
            return batch_id
            
        except Exception as e:
            self.conn.rollback()
            raise Exception(f"Database insertion failed: {str(e)}")
    
    def get_nodule_analysis(self) -> pd.DataFrame:
        """Get comprehensive nodule analysis with radiologist agreement metrics"""
        query = """
        SELECT 
            n.file_id,
            n.nodule_id,
            n.z_coordinate,
            n.x_coordinate, 
            n.y_coordinate,
            n.coordinate_count,
            n.session_type,
            f.parse_case,
            f.modality,
            f.date_service,
            COUNT(r.radiologist_id) as radiologist_count,
            AVG(r.confidence) as avg_confidence,
            AVG(r.subtlety) as avg_subtlety,
            AVG(r.obscuration) as avg_obscuration,
            MIN(r.confidence) as min_confidence,
            MAX(r.confidence) as max_confidence,
            (MAX(r.confidence) - MIN(r.confidence)) as confidence_range,
            GROUP_CONCAT(r.radiologist_id) as radiologists,
            GROUP_CONCAT(r.confidence) as all_confidence_scores
        FROM nodules n
        JOIN files f ON n.file_id = f.file_id  
        LEFT JOIN radiologist_ratings r ON n.nodule_key = r.nodule_key
        GROUP BY n.nodule_key
        ORDER BY n.file_id, n.nodule_id
        """
        
        return pd.read_sql_query(query, self.conn)
    
    def get_radiologist_performance(self) -> pd.DataFrame:
        """Analyze individual radiologist performance patterns"""
        query = """
        SELECT 
            radiologist_id,
            COUNT(*) as total_ratings,
            AVG(confidence) as avg_confidence,
            AVG(subtlety) as avg_subtlety, 
            AVG(obscuration) as avg_obscuration,
            MIN(confidence) as min_confidence,
            MAX(confidence) as max_confidence,
            COUNT(CASE WHEN confidence >= 4 THEN 1 END) as high_confidence_count,
            COUNT(CASE WHEN confidence <= 2 THEN 1 END) as low_confidence_count,
            COUNT(DISTINCT file_id) as files_reviewed
        FROM radiologist_ratings
        WHERE confidence IS NOT NULL
        GROUP BY radiologist_id
        ORDER BY total_ratings DESC
        """
        
        return pd.read_sql_query(query, self.conn)
    
    def get_quality_report(self) -> Dict[str, Any]:
        """Generate comprehensive data quality report"""
        
        # Overall statistics
        stats = self.conn.execute("""
        SELECT 
            COUNT(DISTINCT f.file_id) as total_files,
            COUNT(DISTINCT n.nodule_key) as total_nodules,
            COUNT(r.rating_id) as total_ratings,
            AVG(r.confidence) as overall_avg_confidence
        FROM files f
        LEFT JOIN nodules n ON f.file_id = n.file_id
        LEFT JOIN radiologist_ratings r ON n.nodule_key = r.nodule_key
        """).fetchone()
        
        # Quality issues summary
        quality_issues = self.conn.execute("""
        SELECT 
            issue_type,
            severity,
            COUNT(*) as issue_count
        FROM quality_issues
        GROUP BY issue_type, severity
        ORDER BY issue_count DESC
        """).fetchall()
        
        # Parse case distribution
        parse_cases = self.conn.execute("""
        SELECT 
            parse_case,
            COUNT(*) as file_count,
            COUNT(DISTINCT n.nodule_key) as nodule_count
        FROM files f
        LEFT JOIN nodules n ON f.file_id = n.file_id  
        GROUP BY parse_case
        ORDER BY file_count DESC
        """).fetchall()
        
        return {
            'overall_stats': dict(stats),
            'quality_issues': [dict(row) for row in quality_issues],
            'parse_case_distribution': [dict(row) for row in parse_cases],
            'generated_at': datetime.now().isoformat()
        }
    
    def export_to_excel(self, output_path: str) -> str:
        """Export database contents to Excel for compatibility"""
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            
            # Nodule analysis (main sheet)
            nodule_df = self.get_nodule_analysis()
            nodule_df.to_excel(writer, sheet_name='Nodule Analysis', index=False)
            
            # Radiologist performance
            radiologist_df = self.get_radiologist_performance()
            radiologist_df.to_excel(writer, sheet_name='Radiologist Performance', index=False)
            
            # Raw data tables
            files_df = pd.read_sql_query("SELECT * FROM files ORDER BY file_id", self.conn)
            files_df.to_excel(writer, sheet_name='Files', index=False)
            
            nodules_df = pd.read_sql_query("SELECT * FROM nodules ORDER BY file_id, nodule_id", self.conn) 
            nodules_df.to_excel(writer, sheet_name='Nodules', index=False)
            
            ratings_df = pd.read_sql_query("""
                SELECT * FROM radiologist_ratings 
                ORDER BY file_id, nodule_key, radiologist_id
            """, self.conn)
            ratings_df.to_excel(writer, sheet_name='Radiologist Ratings', index=False)
            
            # Quality issues
            quality_df = pd.read_sql_query("SELECT * FROM quality_issues ORDER BY detected_at", self.conn)
            if not quality_df.empty:
                quality_df.to_excel(writer, sheet_name='Quality Issues', index=False)
        
        return f"Exported database to Excel: {output_path}"
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

# Example usage and testing
if __name__ == "__main__":
    # Test the database with sample data
    with RadiologyDatabase("test_radiology.db") as db:
        
        # Sample data structure (matches your current parsing output)
        sample_data = [
            {
                'FileID': 'file001',
                'ParseCase': 'Complete_Attributes',
                'NoduleID': 'nodule1',
                'Radiologist': 'rad_123_1',
                'Confidence': 4.0,
                'Subtlety': 3.0,
                'Obscuration': 2.0,
                'Reason': 'well defined',
                'X_coord': 123.5,
                'Y_coord': 456.7,
                'Z_coord': 1550.5,
                'CoordCount': 15,
                'SessionType': 'Detailed',
                'StudyInstanceUID': 'study123',
                'SeriesInstanceUID': 'series456',
                'Modality': 'CT'
            },
            {
                'FileID': 'file001', 
                'ParseCase': 'Complete_Attributes',
                'NoduleID': 'nodule1',
                'Radiologist': 'rad_456_1',
                'Confidence': 3.0,
                'Subtlety': 4.0, 
                'Obscuration': 1.0,
                'Reason': 'moderately defined',
                'X_coord': 123.5,
                'Y_coord': 456.7,
                'Z_coord': 1550.5,
                'CoordCount': 15,
                'SessionType': 'Detailed',
                'StudyInstanceUID': 'study123',
                'SeriesInstanceUID': 'series456',
                'Modality': 'CT'
            }
        ]
        
        # Insert test data
        batch_id = db.insert_batch_data(sample_data)
        print(f"Test batch inserted: {batch_id}")
        
        # Generate analysis
        nodule_analysis = db.get_nodule_analysis()
        print(f"Nodule analysis shape: {nodule_analysis.shape}")
        print(nodule_analysis.head())
        
        # Quality report
        quality_report = db.get_quality_report()
        print("Quality Report:", quality_report)
