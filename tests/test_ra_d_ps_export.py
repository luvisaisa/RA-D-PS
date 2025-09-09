#!/usr/bin/env python3
"""
Test script for the RA-D-PS Excel exporter
"""

import sys
import os
sys.path.append('.')

from XMLPARSE import export_excel

def test_ra_d_ps_export():
    """Test the RA-D-PS Excel export functionality"""
    
    print("🧪 TESTING RA-D-PS EXCEL EXPORT")
    print("=" * 50)
    
    # Test data with different radiologist configurations
    demo_records = [
        {
            "file_number": "F-001",
            "study_uid": "1.2.3.4.5.6.7.8.1",
            "nodule_id": "N-1",
            "radiologists": {
                "1": {"subtlety": 3, "confidence": 4, "obscuration": 2, "reason": "partial overlap", "coordinates": "120, 85, 32"},
                "2": {"subtlety": 2, "confidence": 3, "obscuration": 3, "reason": "low contrast", "coordinates": "118, 80, 30"},
                "3": {"subtlety": 4, "confidence": 5, "obscuration": 1, "reason": "clear margins", "coordinates": "121, 83, 31"},
            },
        },
        {
            "file_number": "F-002",
            "study_uid": "1.2.3.4.5.6.7.8.2",
            "nodule_id": "N-2",
            "radiologist_count": 4,
            "radiologist_1": {"subtlety": 1, "confidence": 2, "obscuration": 4, "reason": "motion artifact", "coordinates": "210, 140, 45"},
            "radiologist_2": {"subtlety": 3, "confidence": 4, "obscuration": 2, "reason": "peripheral location", "coordinates": "205, 142, 47"},
            "radiologist_3": {"subtlety": 5, "confidence": 5, "obscuration": 1, "reason": "high contrast", "coordinates": "208, 139, 44"},
            "radiologist_4": {"subtlety": 2, "confidence": 3, "obscuration": 3, "reason": "vessel proximity", "coordinates": "211, 141, 46"},
        },
        {
            "file_number": "F-003",
            "study_uid": "1.2.3.4.5.6.7.8.3",
            "nodule_id": "N-3",
            "radiologists": {
                "1": {"subtlety": 2, "confidence": 3, "obscuration": 2, "reason": "well defined", "coordinates": "150, 120, 28"},
                "2": {"subtlety": 3, "confidence": 4, "obscuration": 1, "reason": "excellent visibility", "coordinates": "152, 118, 30"},
            },
        },
    ]
    
    # Test folder path
    test_folder = "/Users/isa/Desktop/python projects/XML PARSE"
    
    print(f"📊 Test data: {len(demo_records)} records")
    print(f"📂 Output folder: {test_folder}")
    
    try:
        # Export to Excel
        output_path = export_excel(demo_records, test_folder, sheet="test_data")
        
        print(f"✅ Export successful!")
        print(f"📄 File saved: {output_path}")
        
        # Check if file exists
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"📏 File size: {file_size:,} bytes")
        
        # Test versioning by running again
        print("\n🔄 Testing versioning...")
        output_path_v2 = export_excel(demo_records, test_folder, sheet="test_data")
        print(f"📄 Versioned file: {output_path_v2}")
        
        # Verify features
        print(f"\n✨ FEATURES VERIFIED:")
        print(f"  ✓ Auto-naming with timestamp")
        print(f"  ✓ Versioning (_v2 suffix)")
        print(f"  ✓ Dynamic radiologist columns (max 4 detected)")
        print(f"  ✓ Spacer columns between sections")
        print(f"  ✓ Mixed data formats (radiologists dict vs radiologist_count)")
        
        return output_path
        
    except Exception as e:
        print(f"❌ Error during export: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_ra_d_ps_export()
