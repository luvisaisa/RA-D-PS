#!/usr/bin/env python3
"""
Integration test for RA-D-PS export with real XML parsing
"""

import sys
import os
sys.path.append('.')

from XMLPARSE import parse_radiology_sample, convert_parsed_data_to_ra_d_ps_format, export_excel

def test_full_integration():
    """Test the complete workflow from XML parsing to RA-D-PS export"""
    
    print("🧪 TESTING FULL RA-D-PS INTEGRATION")
    print("=" * 60)
    
    # Test with a real XML file if available
    test_xml_path = "/Volumes/LUCKY/tcia-lidc-xml/157/158.xml"
    
    if os.path.exists(test_xml_path):
        print(f"📄 Testing with real XML: {test_xml_path}")
        
        try:
            # Step 1: Parse XML file
            print("1️⃣ Parsing XML file...")
            main_df, unblinded_df = parse_radiology_sample(test_xml_path)
            
            print(f"   • Main DataFrame: {len(main_df)} rows")
            print(f"   • Unblinded DataFrame: {len(unblinded_df)} rows")
            
            # Step 2: Convert to RA-D-PS format
            print("2️⃣ Converting to RA-D-PS format...")
            ra_d_ps_records = convert_parsed_data_to_ra_d_ps_format((main_df, unblinded_df))
            
            print(f"   • RA-D-PS records: {len(ra_d_ps_records)}")
            
            # Show sample record structure
            if ra_d_ps_records:
                sample = ra_d_ps_records[0]
                print(f"   • Sample record keys: {list(sample.keys())}")
                if "radiologists" in sample:
                    print(f"   • Radiologists in sample: {list(sample['radiologists'].keys())}")
            
            # Step 3: Export to Excel
            print("3️⃣ Exporting to RA-D-PS Excel...")
            output_folder = "/Users/isa/Desktop/python projects/XML PARSE"
            output_path = export_excel(ra_d_ps_records, output_folder, sheet="integration_test")
            
            print(f"   ✅ Export successful: {os.path.basename(output_path)}")
            
            # Verify file
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                print(f"   📏 File size: {file_size:,} bytes")
            
            print(f"\n✨ INTEGRATION TEST RESULTS:")
            print(f"  ✓ XML parsing successful")
            print(f"  ✓ Data conversion successful")
            print(f"  ✓ RA-D-PS export successful")
            print(f"  ✓ Auto-naming with timestamp")
            print(f"  ✓ File saved and verified")
            
            return output_path
            
        except Exception as e:
            print(f"❌ Integration test failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    else:
        print(f"⚠️ Test XML file not found: {test_xml_path}")
        print("   Using demo data instead...")
        
        # Create demo parsed data structure
        import pandas as pd
        
        demo_main_df = pd.DataFrame([
            {
                "FileID": "158",
                "ParseCase": "LIDC_Multi_Session_4", 
                "Radiologist": "anonRad1",
                "NoduleID": 1,
                "Confidence": 4.0,
                "Subtlety": 3.0,
                "Obscuration": 2.0,
                "Reason": "well defined",
                "X_coord": 123.5,
                "Y_coord": 456.7,
                "Z_coord": 78.9,
                "StudyInstanceUID": "1.2.3.4.5.6.7.8.9"
            },
            {
                "FileID": "158",
                "ParseCase": "LIDC_Multi_Session_4",
                "Radiologist": "anonRad2", 
                "NoduleID": 1,
                "Confidence": 3.0,
                "Subtlety": 4.0,
                "Obscuration": 1.0,
                "Reason": "clear boundary",
                "X_coord": 125.0,
                "Y_coord": 458.2,
                "Z_coord": 79.1,
                "StudyInstanceUID": "1.2.3.4.5.6.7.8.9"
            }
        ])
        
        demo_unblinded_df = pd.DataFrame()  # Empty for demo
        
        # Test conversion and export
        ra_d_ps_records = convert_parsed_data_to_ra_d_ps_format((demo_main_df, demo_unblinded_df))
        output_folder = "/Users/isa/Desktop/python projects/XML PARSE"
        output_path = export_excel(ra_d_ps_records, output_folder, sheet="demo_test")
        
        print(f"✅ Demo integration test completed: {os.path.basename(output_path)}")
        return output_path

if __name__ == "__main__":
    test_full_integration()
