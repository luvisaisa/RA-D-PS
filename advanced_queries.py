#!/usr/bin/env python3
"""
Advanced SQLite Queries for Radiology Data Analysis
Examples of powerful queries you can run on your radiology database
"""

import sqlite3
import pandas as pd
from radiology_database import RadiologyDatabase

def demonstrate_advanced_queries(db_path: str):
    """Show advanced analysis queries for radiology data"""
    
    print(f"🔍 ADVANCED RADIOLOGY DATA ANALYSIS")
    print(f"Database: {db_path}")
    print("=" * 60)
    
    with RadiologyDatabase(db_path) as db:
        
        # 1. Find nodules with high radiologist disagreement
        print("\n1️⃣ NODULES WITH HIGH RADIOLOGIST DISAGREEMENT:")
        disagreement_query = """
        SELECT 
            n.file_id,
            n.nodule_id,
            n.z_coordinate,
            COUNT(r.radiologist_id) as radiologist_count,
            MIN(r.confidence) as min_confidence,
            MAX(r.confidence) as max_confidence,
            (MAX(r.confidence) - MIN(r.confidence)) as confidence_range,
            AVG(r.confidence) as avg_confidence,
            GROUP_CONCAT(r.radiologist_id || ':' || r.confidence) as individual_scores
        FROM nodules n
        JOIN radiologist_ratings r ON n.nodule_key = r.nodule_key
        WHERE r.confidence IS NOT NULL
        GROUP BY n.nodule_key
        HAVING COUNT(r.radiologist_id) >= 2  -- At least 2 radiologists
        AND (MAX(r.confidence) - MIN(r.confidence)) >= 2  -- High disagreement
        ORDER BY confidence_range DESC
        LIMIT 10
        """
        
        disagreement_df = pd.read_sql_query(disagreement_query, db.conn)
        if not disagreement_df.empty:
            print(disagreement_df.to_string(index=False))
        else:
            print("No high-disagreement nodules found")
        
        # 2. Radiologist consistency analysis
        print("\n\n2️⃣ RADIOLOGIST CONSISTENCY ANALYSIS:")
        consistency_query = """
        SELECT 
            radiologist_id,
            COUNT(*) as total_nodules_rated,
            AVG(confidence) as avg_confidence,
            ROUND(
                (COUNT(CASE WHEN confidence >= 4 THEN 1 END) * 100.0 / COUNT(*)), 2
            ) as high_confidence_percentage,
            MIN(confidence) as min_confidence,
            MAX(confidence) as max_confidence,
            ROUND(
                AVG(CASE 
                    WHEN subtlety IS NOT NULL AND confidence IS NOT NULL 
                    THEN ABS(subtlety - confidence) 
                END), 2
            ) as avg_confidence_subtlety_diff
        FROM radiologist_ratings
        WHERE confidence IS NOT NULL
        GROUP BY radiologist_id
        HAVING COUNT(*) >= 5  -- At least 5 ratings
        ORDER BY total_nodules_rated DESC
        """
        
        consistency_df = pd.read_sql_query(consistency_query, db.conn)
        if not consistency_df.empty:
            print(consistency_df.to_string(index=False))
        else:
            print("Not enough data for consistency analysis")
        
        # 3. Parse case quality comparison
        print("\n\n3️⃣ PARSE CASE QUALITY COMPARISON:")
        quality_comparison_query = """
        SELECT 
            f.parse_case,
            COUNT(DISTINCT f.file_id) as total_files,
            COUNT(DISTINCT n.nodule_key) as total_nodules,
            COUNT(r.rating_id) as total_ratings,
            ROUND(AVG(r.confidence), 2) as avg_confidence,
            COUNT(qi.issue_id) as quality_issues,
            ROUND(
                (COUNT(qi.issue_id) * 100.0 / COUNT(r.rating_id)), 2
            ) as issue_percentage
        FROM files f
        LEFT JOIN nodules n ON f.file_id = n.file_id
        LEFT JOIN radiologist_ratings r ON n.nodule_key = r.nodule_key
        LEFT JOIN quality_issues qi ON f.file_id = qi.file_id
        GROUP BY f.parse_case
        ORDER BY total_files DESC
        """
        
        quality_df = pd.read_sql_query(quality_comparison_query, db.conn)
        if not quality_df.empty:
            print(quality_df.to_string(index=False))
        else:
            print("No parse case data available")
        
        # 4. Coordinate-based analysis
        print("\n\n4️⃣ COORDINATE-BASED NODULE ANALYSIS:")
        coordinate_query = """
        SELECT 
            CASE 
                WHEN coordinate_count > 20 THEN 'High Detail (>20 coords)'
                WHEN coordinate_count > 10 THEN 'Medium Detail (11-20 coords)'
                WHEN coordinate_count > 0 THEN 'Low Detail (1-10 coords)'
                ELSE 'No Coordinates'
            END as detail_level,
            COUNT(DISTINCT nodule_key) as nodule_count,
            AVG(CASE WHEN x_coordinate IS NOT NULL THEN x_coordinate END) as avg_x,
            AVG(CASE WHEN y_coordinate IS NOT NULL THEN y_coordinate END) as avg_y,
            AVG(CASE WHEN z_coordinate IS NOT NULL THEN z_coordinate END) as avg_z,
            COUNT(CASE WHEN session_type = 'Detailed' THEN 1 END) as detailed_sessions
        FROM nodules
        GROUP BY 
            CASE 
                WHEN coordinate_count > 20 THEN 'High Detail (>20 coords)'
                WHEN coordinate_count > 10 THEN 'Medium Detail (11-20 coords)'
                WHEN coordinate_count > 0 THEN 'Low Detail (1-10 coords)'
                ELSE 'No Coordinates'
            END
        ORDER BY nodule_count DESC
        """
        
        coordinate_df = pd.read_sql_query(coordinate_query, db.conn)
        if not coordinate_df.empty:
            print(coordinate_df.to_string(index=False))
        else:
            print("No coordinate data available")
        
        # 5. Z-coordinate clustering analysis
        print("\n\n5️⃣ Z-COORDINATE DISTRIBUTION ANALYSIS:")
        z_distribution_query = """
        SELECT 
            CASE 
                WHEN z_coordinate IS NULL THEN 'No Z-Coordinate'
                WHEN z_coordinate < 1000 THEN 'Low Z (<1000)'
                WHEN z_coordinate < 1500 THEN 'Mid Z (1000-1500)'
                WHEN z_coordinate < 2000 THEN 'High Z (1500-2000)'
                ELSE 'Very High Z (>2000)'
            END as z_range,
            COUNT(*) as nodule_count,
            AVG(coordinate_count) as avg_coord_count,
            COUNT(CASE WHEN session_type = 'Detailed' THEN 1 END) as detailed_count
        FROM nodules
        GROUP BY 
            CASE 
                WHEN z_coordinate IS NULL THEN 'No Z-Coordinate'
                WHEN z_coordinate < 1000 THEN 'Low Z (<1000)'
                WHEN z_coordinate < 1500 THEN 'Mid Z (1000-1500)'
                WHEN z_coordinate < 2000 THEN 'High Z (1500-2000)'
                ELSE 'Very High Z (>2000)'
            END
        ORDER BY nodule_count DESC
        """
        
        z_dist_df = pd.read_sql_query(z_distribution_query, db.conn)
        if not z_dist_df.empty:
            print(z_dist_df.to_string(index=False))
        else:
            print("No Z-coordinate data available")

def create_custom_views(db_path: str):
    """Create useful database views for common queries"""
    
    print(f"\n📋 CREATING CUSTOM DATABASE VIEWS")
    print("=" * 40)
    
    with sqlite3.connect(db_path) as conn:
        
        # View 1: Nodule summary with radiologist metrics
        conn.execute("""
        CREATE VIEW IF NOT EXISTS nodule_summary AS
        SELECT 
            n.file_id,
            n.nodule_id,
            n.z_coordinate,
            n.coordinate_count,
            n.session_type,
            f.parse_case,
            f.modality,
            COUNT(r.radiologist_id) as radiologist_count,
            AVG(r.confidence) as avg_confidence,
            MIN(r.confidence) as min_confidence,
            MAX(r.confidence) as max_confidence,
            (MAX(r.confidence) - MIN(r.confidence)) as confidence_range,
            GROUP_CONCAT(r.radiologist_id) as radiologists
        FROM nodules n
        JOIN files f ON n.file_id = f.file_id
        LEFT JOIN radiologist_ratings r ON n.nodule_key = r.nodule_key
        GROUP BY n.nodule_key
        """)
        
        # View 2: Radiologist performance summary
        conn.execute("""
        CREATE VIEW IF NOT EXISTS radiologist_summary AS
        SELECT 
            radiologist_id,
            COUNT(*) as total_ratings,
            AVG(confidence) as avg_confidence,
            COUNT(CASE WHEN confidence >= 4 THEN 1 END) as high_confidence_count,
            COUNT(CASE WHEN confidence <= 2 THEN 1 END) as low_confidence_count,
            COUNT(DISTINCT file_id) as unique_files,
            MIN(rating_timestamp) as first_rating,
            MAX(rating_timestamp) as last_rating
        FROM radiologist_ratings
        WHERE confidence IS NOT NULL
        GROUP BY radiologist_id
        """)
        
        # View 3: Quality issues summary  
        conn.execute("""
        CREATE VIEW IF NOT EXISTS quality_summary AS
        SELECT 
            f.parse_case,
            qi.issue_type,
            qi.severity,
            COUNT(*) as issue_count,
            COUNT(DISTINCT qi.file_id) as affected_files,
            ROUND(
                COUNT(*) * 100.0 / 
                (SELECT COUNT(*) FROM quality_issues), 2
            ) as percentage_of_all_issues
        FROM quality_issues qi
        JOIN files f ON qi.file_id = f.file_id
        GROUP BY f.parse_case, qi.issue_type, qi.severity
        """)
        
        conn.commit()
        print("✅ Custom views created:")
        print("   • nodule_summary - Comprehensive nodule analysis")
        print("   • radiologist_summary - Radiologist performance metrics")
        print("   • quality_summary - Quality issues by parse case")

def export_analysis_reports(db_path: str, output_dir: str = "."):
    """Export various analysis reports as CSV files"""
    
    print(f"\n📊 EXPORTING ANALYSIS REPORTS")
    print("=" * 40)
    
    with RadiologyDatabase(db_path) as db:
        
        # Export nodule analysis
        nodule_df = db.get_nodule_analysis()
        if not nodule_df.empty:
            nodule_path = os.path.join(output_dir, "nodule_analysis.csv")
            nodule_df.to_csv(nodule_path, index=False)
            print(f"✅ Nodule analysis: {nodule_path}")
        
        # Export radiologist performance
        radiologist_df = db.get_radiologist_performance()
        if not radiologist_df.empty:
            rad_path = os.path.join(output_dir, "radiologist_performance.csv")
            radiologist_df.to_csv(rad_path, index=False)
            print(f"✅ Radiologist performance: {rad_path}")
        
        # Export custom queries
        queries = {
            "high_disagreement_nodules": """
                SELECT * FROM nodule_summary 
                WHERE radiologist_count >= 2 AND confidence_range >= 2
                ORDER BY confidence_range DESC
            """,
            "detailed_session_analysis": """
                SELECT 
                    parse_case,
                    session_type,
                    COUNT(*) as nodule_count,
                    AVG(coordinate_count) as avg_coords,
                    AVG(avg_confidence) as avg_confidence
                FROM nodule_summary
                GROUP BY parse_case, session_type
                ORDER BY nodule_count DESC
            """
        }
        
        for name, query in queries.items():
            try:
                df = pd.read_sql_query(query, db.conn)
                if not df.empty:
                    csv_path = os.path.join(output_dir, f"{name}.csv")
                    df.to_csv(csv_path, index=False)
                    print(f"✅ {name.replace('_', ' ').title()}: {csv_path}")
            except Exception as e:
                print(f"⚠️ Could not export {name}: {e}")

# Example usage
if __name__ == "__main__":
    import os
    
    # Look for existing database files
    db_files = [f for f in os.listdir('.') if f.endswith('.db')]
    
    if db_files:
        print(f"Found database files: {db_files}")
        
        # Use the first database file found
        db_path = db_files[0]
        print(f"Analyzing: {db_path}")
        
        # Run demonstrations
        demonstrate_advanced_queries(db_path)
        create_custom_views(db_path)
        export_analysis_reports(db_path)
        
    else:
        print("No database files found. Please run the XML parser with SQLite export first.")
        print("Example: Create some sample data to demonstrate...")
        
        # Create sample database for demonstration
        sample_db = "sample_radiology_demo.db"
        with RadiologyDatabase(sample_db) as db:
            # Insert comprehensive sample data
            sample_data = [
                # File 1 - Multiple radiologists, high agreement
                {'FileID': 'file001', 'ParseCase': 'Complete_Attributes', 'NoduleID': 'nodule1', 
                 'Radiologist': 'rad_001', 'Confidence': 4.0, 'Subtlety': 3.0, 'Obscuration': 2.0,
                 'X_coord': 123.5, 'Y_coord': 456.7, 'Z_coord': 1550.5, 'CoordCount': 15, 
                 'SessionType': 'Detailed', 'StudyInstanceUID': 'study123'},
                 
                {'FileID': 'file001', 'ParseCase': 'Complete_Attributes', 'NoduleID': 'nodule1',
                 'Radiologist': 'rad_002', 'Confidence': 4.0, 'Subtlety': 4.0, 'Obscuration': 2.0,
                 'X_coord': 123.5, 'Y_coord': 456.7, 'Z_coord': 1550.5, 'CoordCount': 15,
                 'SessionType': 'Detailed', 'StudyInstanceUID': 'study123'},
                 
                # File 1 - Same nodule, third radiologist with disagreement
                {'FileID': 'file001', 'ParseCase': 'Complete_Attributes', 'NoduleID': 'nodule1',
                 'Radiologist': 'rad_003', 'Confidence': 2.0, 'Subtlety': 2.0, 'Obscuration': 4.0,
                 'X_coord': 123.5, 'Y_coord': 456.7, 'Z_coord': 1550.5, 'CoordCount': 15,
                 'SessionType': 'Detailed', 'StudyInstanceUID': 'study123'},
                 
                # File 2 - Different nodule, standard session
                {'FileID': 'file002', 'ParseCase': 'Core_Attributes_Only', 'NoduleID': 'nodule2',
                 'Radiologist': 'rad_001', 'Confidence': 3.0, 'Subtlety': 3.0, 'Obscuration': 1.0,
                 'X_coord': 200.1, 'Y_coord': 300.2, 'Z_coord': 1200.0, 'CoordCount': 5,
                 'SessionType': 'Standard', 'StudyInstanceUID': 'study456'},
                 
                {'FileID': 'file002', 'ParseCase': 'Core_Attributes_Only', 'NoduleID': 'nodule2',
                 'Radiologist': 'rad_004', 'Confidence': 3.0, 'Subtlety': 2.0, 'Obscuration': 1.0,
                 'X_coord': 200.1, 'Y_coord': 300.2, 'Z_coord': 1200.0, 'CoordCount': 5,
                 'SessionType': 'Standard', 'StudyInstanceUID': 'study456'},
            ]
            
            batch_id = db.insert_batch_data(sample_data)
            print(f"Created sample database: {sample_db} (batch: {batch_id})")
        
        # Now demonstrate with sample data
        demonstrate_advanced_queries(sample_db)
        create_custom_views(sample_db)
        export_analysis_reports(sample_db)
