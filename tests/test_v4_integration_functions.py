#!/usr/bin/env python3
"""
Test script for v4 RA-D-PS formatting integration functions
"""

import os
import sys
sys.path.append('/Users/isa/Desktop/python projects/XML PARSE')

# Import the functions directly
from XMLPARSE import export_excel, convert_parsed_data_to_ra_d_ps_format

def test_integration_functions():
    """Test the integration functions that the GUI uses"""
    print("Testing v4 RA-D-PS integration functions...")
    
    try:
        # Test convert_parsed_data_to_ra_d_ps_format function
        test_parsed_data = {
            "test1.xml": {
                "file_number": "test1",
                "study_uid": "1.2.3.4.5.6.001",
                "nodule_id": "nodule_001",
                "radiologist_1": {
                    "subtlety": 3,
                    "confidence": 4,
                    "obscuration": 2,
                    "reason": "Test nodule",
                    "coordinates": "(256,256,-145)"
                }
            },
            "test2.xml": {
                "file_number": "test2", 
                "study_uid": "1.2.3.4.5.6.002",
                "nodule_id": "nodule_002",
                "radiologist_1": {
                    "subtlety": 5,
                    "confidence": 5,
                    "obscuration": 1,
                    "reason": "Clear nodule",
                    "coordinates": "(300,300,-150)"
                },
                "radiologist_2": {
                    "subtlety": 4,
                    "confidence": 4,
                    "obscuration": 2,
                    "reason": "Good visibility",
                    "coordinates": "(305,305,-152)"
                }
            }
        }
        
        ra_d_ps_records = convert_parsed_data_to_ra_d_ps_format(test_parsed_data)
        print(f"✓ Data conversion successful: {len(ra_d_ps_records)} records")
        
        # Verify the conversion worked correctly
        assert len(ra_d_ps_records) == 2, f"Expected 2 records, got {len(ra_d_ps_records)}"
        
        # Check first record
        rec1 = ra_d_ps_records[0]
        assert rec1["file_number"] == "test1"
        assert rec1["study_uid"] == "1.2.3.4.5.6.001" 
        assert rec1["nodule_id"] == "nodule_001"
        assert "radiologists" in rec1
        assert "1" in rec1["radiologists"]
        assert rec1["radiologists"]["1"]["subtlety"] == 3
        print("✓ First record conversion verified")
        
        # Check second record (should have 2 radiologists)
        rec2 = ra_d_ps_records[1]
        assert rec2["file_number"] == "test2"
        assert len(rec2["radiologists"]) == 2
        assert "1" in rec2["radiologists"] and "2" in rec2["radiologists"]
        print("✓ Second record conversion verified")
        
        # Test the export function with the converted data
        test_dir = "/Users/isa/Desktop/python projects/XML PARSE/test_integration_v4"
        os.makedirs(test_dir, exist_ok=True)
        
        output_path = export_excel(ra_d_ps_records, test_dir, sheet="integration_test")
        print(f"✓ Integration export successful: {output_path}")
        
        # Verify the file was created
        assert os.path.exists(output_path), f"Output file not found: {output_path}"
        print("✓ Output file exists")
        
        print("\nAll integration function tests passed!")
        print("The v4 formatting is properly integrated and ready for GUI use.")
        
        return True
        
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_integration_functions()
    sys.exit(0 if success else 1)
