#!/usr/bin/env python3
"""
Batch Processing Example

This example demonstrates how to process multiple XML files using the batch processor.
"""
import sys
from pathlib import Path

# Add the src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ra_d_ps import parse_multiple, convert_parsed_data_to_ra_d_ps_format, export_excel
from ra_d_ps.batch_processor import BatchProcessor


def batch_processing_example():
    """Example of batch processing workflow"""
    
    # Directory containing XML files
    xml_directory = "path/to/xml/files"
    
    # Output directory for results
    output_dir = "batch_output"
    
    try:
        # Get list of XML files
        xml_files = list(Path(xml_directory).glob("*.xml"))
        print(f"Found {len(xml_files)} XML files")
        
        if not xml_files:
            print("No XML files found in directory")
            return
        
        # Initialize batch processor
        batch_processor = BatchProcessor()
        
        # Analyze file structures
        print("Analyzing XML file structures...")
        structure_analysis = batch_processor.analyze_batch_structure(xml_files)
        
        print("Structure analysis results:")
        for structure_type, file_count in structure_analysis.items():
            print(f"  {structure_type}: {file_count} files")
        
        # Parse multiple files
        print("Parsing XML files...")
        case_data, case_unblinded_data = parse_multiple(xml_files)
        
        if not case_data and not case_unblinded_data:
            print("No data parsed from files")
            return
        
        # Combine all parsed data
        combined_data = {}
        combined_data.update(case_data)
        combined_data.update(case_unblinded_data)
        
        # Convert to RA-D-PS format
        print("Converting to RA-D-PS format...")
        ra_d_ps_records = convert_parsed_data_to_ra_d_ps_format(combined_data)
        
        print(f"Converted to {len(ra_d_ps_records)} RA-D-PS records")
        
        # Export to Excel
        if ra_d_ps_records:
            output_path = export_excel(ra_d_ps_records, output_dir)
            print(f"Batch Excel file created: {output_path}")
        else:
            print("No data to export")
            
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    batch_processing_example()