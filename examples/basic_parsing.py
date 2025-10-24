#!/usr/bin/env python3
"""
Basic XML Parsing Example

This example demonstrates how to parse a single XML file and export to Excel.
"""
import sys
from pathlib import Path

# Add the src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ra_d_ps import parse_radiology_sample, convert_parsed_data_to_ra_d_ps_format, export_excel


def basic_parsing_example():
    """Example of basic XML parsing workflow"""
    
    # Path to your XML file
    xml_file = "path/to/your/sample.xml"
    
    # Output directory for results
    output_dir = "output"
    
    try:
        print(f"Parsing XML file: {xml_file}")
        
        # Parse the XML file
        main_df, unblinded_df = parse_radiology_sample(xml_file)
        
        print(f"Parsed {len(main_df)} main records and {len(unblinded_df)} unblinded records")
        
        # Convert to RA-D-PS format
        ra_d_ps_records = convert_parsed_data_to_ra_d_ps_format((main_df, unblinded_df))
        
        print(f"Converted to {len(ra_d_ps_records)} RA-D-PS records")
        
        # Export to Excel
        if ra_d_ps_records:
            output_path = export_excel(ra_d_ps_records, output_dir)
            print(f"Excel file created: {output_path}")
        else:
            print("No data to export")
            
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    basic_parsing_example()