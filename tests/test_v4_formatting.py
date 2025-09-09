#!/usr/bin/env python3
"""
Test script for the updated v4 RA-D-PS formatting implementation
"""

import os
import sys
sys.path.append('/Users/isa/Desktop/python projects/XML PARSE')

from XMLPARSE import export_excel

def test_v4_formatting():
    """Test the updated v4 RA-D-PS formatting with improved features"""
    print("Testing v4 RA-D-PS formatting...")
    
    # Create test data with multiple radiologists
    test_records = [
        {
            "file_number": "001",
            "study_uid": "1.2.3.4.5.001",
            "nodule_id": "N001",
            "radiologists": {
                "1": {
                    "subtlety": 3,
                    "confidence": 4,
                    "obscuration": 1,
                    "reason": "Nodule clearly visible",
                    "coordinates": "(100,200,50)"
                },
                "2": {
                    "subtlety": 4,
                    "confidence": 5,
                    "obscuration": 2,
                    "reason": "Well-defined margins",
                    "coordinates": "(105,205,52)"
                }
            }
        },
        {
            "file_number": "002",
            "study_uid": "1.2.3.4.5.002",
            "nodule_id": "N002",
            "radiologists": {
                "1": {
                    "subtlety": 2,
                    "confidence": 3,
                    "obscuration": 3,
                    "reason": "Partially obscured",
                    "coordinates": "(150,250,60)"
                },
                "2": {
                    "subtlety": 3,
                    "confidence": 4,
                    "obscuration": 2,
                    "reason": "Good contrast",
                    "coordinates": "(155,255,62)"
                },
                "3": {
                    "subtlety": 5,
                    "confidence": 5,
                    "obscuration": 1,
                    "reason": "Excellent definition",
                    "coordinates": "(160,260,65)"
                }
            }
        }
    ]
    
    # Create test directory
    test_dir = "/Users/isa/Desktop/python projects/XML PARSE/test_v4_output"
    os.makedirs(test_dir, exist_ok=True)
    
    try:
        # Test basic export
        output_path = export_excel(test_records, test_dir, sheet="v4_test")
        print(f"✓ Basic export successful: {output_path}")
        
        # Test with force_blocks parameter
        output_path2 = export_excel(
            test_records, 
            test_dir, 
            sheet="v4_force_blocks",
            force_blocks=5  # Force 5 radiologist blocks even though we only have 3
        )
        print(f"✓ Force blocks export successful: {output_path2}")
        
        # Test with custom blue color
        output_path3 = export_excel(
            test_records,
            test_dir,
            sheet="v4_custom_blue",
            blue_argb="FF0066CC"  # Different blue shade
        )
        print(f"✓ Custom blue export successful: {output_path3}")
        
        print("\nAll v4 formatting tests passed!")
        print(f"Check the following files for proper formatting:")
        print(f"  - {output_path}")
        print(f"  - {output_path2}")
        print(f"  - {output_path3}")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_v4_formatting()
    sys.exit(0 if success else 1)
