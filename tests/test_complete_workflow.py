#!/usr/bin/env python3
"""
Test the complete workflow: parse XML and export to RA-D-PS Excel
"""

import os
import sys
sys.path.append('/Users/isa/Desktop/python projects/XML PARSE')

from XMLPARSE import parse_radiology_sample, convert_parsed_data_to_ra_d_ps_format, export_excel

def test_complete_workflow():
    """Test the complete workflow from XML parsing to RA-D-PS Excel export"""
    xml_file = "/Users/isa/Desktop/XML TEST FILES/generated_cases_001_050/001.xml"
    output_dir = "/Users/isa/Desktop/python projects/XML PARSE/test_complete_workflow"
    
    print(f"🚀 Testing complete workflow...")
    print(f"📄 Input: {xml_file}")
    print(f"📁 Output: {output_dir}")
    
    try:
        # Step 1: Parse XML
        print("\n1️⃣ Parsing XML...")
        main_df, unblinded_df = parse_radiology_sample(xml_file)
        print(f"✅ Parsed successfully!")
        print(f"   Main: {len(main_df)} rows, Unblinded: {len(unblinded_df)} rows")
        
        # Step 2: Convert to RA-D-PS format
        print("\n2️⃣ Converting to RA-D-PS format...")
        # The convert function expects the tuple format from parse_radiology_sample
        ra_d_ps_records = convert_parsed_data_to_ra_d_ps_format((main_df, unblinded_df))
        print(f"✅ Converted successfully!")
        print(f"   Generated {len(ra_d_ps_records)} records")
        
        # Display the records structure
        for i, record in enumerate(ra_d_ps_records):
            print(f"\n📋 Record {i+1}:")
            print(f"   File: {record['file_number']}")
            print(f"   Study UID: {record['study_uid']}")
            print(f"   Nodule ID: {record['nodule_id']}")
            print(f"   Radiologists: {len(record['radiologists'])}")
            for rad_id, rad_data in record['radiologists'].items():
                print(f"     Radiologist {rad_id}: Subtlety={rad_data['subtlety']}, Confidence={rad_data['confidence']}")
        
        # Step 3: Export to Excel
        print("\n3️⃣ Exporting to RA-D-PS Excel...")
        os.makedirs(output_dir, exist_ok=True)
        
        output_file = export_excel(ra_d_ps_records, output_dir, sheet="workflow_test")
        print(f"✅ Excel export successful!")
        print(f"   Output file: {output_file}")
        
        # Verify file was created
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            print(f"   File size: {file_size} bytes")
            print(f"✅ Workflow completed successfully!")
        else:
            print(f"❌ Output file not found!")
            
    except Exception as e:
        print(f"❌ Error in workflow: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_complete_workflow()
