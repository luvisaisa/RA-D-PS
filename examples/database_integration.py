#!/usr/bin/env python3
"""
Database Integration Example

This example demonstrates how to use the SQLite database functionality.
"""
import sys
from pathlib import Path

# Add the src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ra_d_ps import parse_multiple
from ra_d_ps.radiology_database import RadiologyDatabase


def database_example():
    """Example of database integration workflow"""
    
    # Directory containing XML files
    xml_directory = "path/to/xml/files"
    
    # Database file path
    db_path = "radiology_analysis.db"
    
    try:
        # Get list of XML files
        xml_files = list(Path(xml_directory).glob("*.xml"))
        print(f"Found {len(xml_files)} XML files")
        
        if not xml_files:
            print("No XML files found in directory")
            return
        
        # Parse multiple files
        print("Parsing XML files...")
        case_data, case_unblinded_data = parse_multiple(xml_files)
        
        if not case_data and not case_unblinded_data:
            print("No data parsed from files")
            return
        
        # Combine all data for database insertion
        all_parsed_data = []
        for df in case_data.values():
            all_parsed_data.extend(df.to_dict('records'))
        for df in case_unblinded_data.values():
            unblinded_records = df.to_dict('records')
            # Mark unblinded data
            for record in unblinded_records:
                record['is_unblinded'] = True
            all_parsed_data.extend(unblinded_records)
        
        print(f"Total records to insert: {len(all_parsed_data)}")
        
        # Create database and insert data
        print("Creating database and inserting data...")
        with RadiologyDatabase(db_path) as db:
            batch_id = db.insert_batch_data(all_parsed_data)
            print(f"Data inserted with batch ID: {batch_id}")
            
            # Generate quality report
            print("Generating quality report...")
            quality_report = db.get_quality_report()
            
            # Print summary statistics
            stats = quality_report['overall_stats']
            print(f"Database Summary:")
            print(f"  Total Files: {stats.get('total_files', 0)}")
            print(f"  Total Nodules: {stats.get('total_nodules', 0)}")
            print(f"  Total Ratings: {stats.get('total_ratings', 0)}")
            
            # Export to Excel for analysis
            excel_path = db_path.replace('.db', '_analysis.xlsx')
            export_msg = db.export_to_excel(excel_path)
            print(f"Analysis Excel exported: {excel_path}")
            
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    database_example()