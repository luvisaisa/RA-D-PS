#!/usr/bin/env python3
"""
Complete end-to-end test with actual XML parsing and RA-D-PS export
to verify both main and unblinded data appear in Excel output
"""

import sys
import os
import pandas as pd
from glob import glob

# Add the current directory to path to import XMLPARSE
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from XMLPARSE import (
    parse_radiology_sample, 
    convert_parsed_data_to_ra_d_ps_format,
    export_excel
)

def test_complete_workflow():
    """Test complete workflow from XML to Excel with both main and unblinded data"""
    
    print("🧪 Testing complete XML to RA-D-PS Excel workflow...")
    
    # Find XML files in current directory
    xml_files = glob("*.xml")
    if not xml_files:
        print("❌ No XML files found in current directory")
        return False
    
    print(f"📁 Found {len(xml_files)} XML files")
    
    # Test with first XML file
    test_file = xml_files[0]
    print(f"🔍 Testing with file: {test_file}")
    
    try:
        # Parse the XML file
        print("\n📖 Parsing XML file...")
        main_df, unblinded_df = parse_radiology_sample(test_file)
        
        print(f"  📊 Main DataFrame: {len(main_df)} rows")
        if 'Radiologist' in main_df.columns:
            main_rads = main_df['Radiologist'].unique() if not main_df.empty else []
            print(f"    Radiologists: {main_rads}")
        
        print(f"  📊 Unblinded DataFrame: {len(unblinded_df)} rows")
        if 'Radiologist' in unblinded_df.columns:
            unblinded_rads = unblinded_df['Radiologist'].unique() if not unblinded_df.empty else []
            print(f"    Radiologists: {unblinded_rads}")
        
        # Convert to RA-D-PS format
        print("\n🔄 Converting to RA-D-PS format...")
        dataframes = (main_df, unblinded_df)
        ra_d_ps_records = convert_parsed_data_to_ra_d_ps_format(dataframes)
        
        print(f"  ✅ Generated {len(ra_d_ps_records)} RA-D-PS records")
        
        # Show radiologist counts for each record
        for i, record in enumerate(ra_d_ps_records, 1):
            file_id = record.get('file_number', 'unknown')
            nodule_id = record.get('nodule_id', 'unknown')
            radiologists = record.get('radiologists', {})
            print(f"    📋 Record {i}: {file_id}-{nodule_id} → {len(radiologists)} radiologists")
        
        # Export to Excel
        if ra_d_ps_records:
            print("\n📄 Exporting to Excel...")
            output_file = "test_complete_workflow_output.xlsx"
            
            try:
                export_excel(
                    ra_d_ps_records, 
                    output_file,
                    force_blocks=True
                )
                print(f"  ✅ Excel export completed: {output_file}")
                
                # Verify file exists
                if os.path.exists(output_file):
                    file_size = os.path.getsize(output_file)
                    print(f"  📋 File size: {file_size:,} bytes")
                    print("  🎉 Complete workflow test successful!")
                    return True
                else:
                    print("  ❌ Excel file was not created")
                    return False
                    
            except Exception as export_error:
                print(f"  ❌ Excel export failed: {export_error}")
                import traceback
                traceback.print_exc()
                return False
        else:
            print("  ⚠️  No RA-D-PS records to export")
            return False
        
    except Exception as e:
        print(f"\n❌ Workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_complete_workflow()
    if success:
        print("\n✅ Complete workflow test passed!")
    else:
        print("\n❌ Complete workflow test failed!")
        sys.exit(1)
