#!/usr/bin/env python3
"""
Test to verify that both main and unblinded radiologist data 
are properly preserved in RA-D-PS conversion
"""

import sys
import os
import pandas as pd

# Add the current directory to path to import XMLPARSE
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from XMLPARSE import convert_parsed_data_to_ra_d_ps_format

def test_data_combination():
    """Test that both main and unblinded data are preserved"""
    
    print("🧪 Testing RA-D-PS data combination...")
    
    # Create mock main DataFrame (normal radiologists)
    main_data = {
        'FileID': ['file1', 'file1', 'file2'],
        'NoduleID': ['nodule1', 'nodule1', 'nodule1'],
        'StudyInstanceUID': ['study1', 'study1', 'study2'],
        'Radiologist': ['anonRad1', 'anonRad2', 'anonRad1'],
        'Confidence': [4, 3, 5],
        'Subtlety': [2, 4, 3],
        'Obscuration': [1, 2, 1],
        'Reason': ['reason1', 'reason2', 'reason3'],
        'X_coord': [100, 150, 200],
        'Y_coord': [200, 250, 300],
        'Z_coord': [50, 75, 100]
    }
    main_df = pd.DataFrame(main_data)
    
    # Create mock unblinded DataFrame (additional radiologists)
    unblinded_data = {
        'FileID': ['file1', 'file2', 'file2'],
        'NoduleID': ['nodule1', 'nodule1', 'nodule1'],
        'StudyInstanceUID': ['study1', 'study2', 'study2'],
        'Radiologist': ['anonRad3', 'anonRad2', 'anonRad3'],
        'Confidence': [2, 4, 3],
        'Subtlety': [5, 1, 2],
        'Obscuration': [3, 4, 2],
        'Reason': ['reason4', 'reason5', 'reason6'],
        'X_coord': [110, 210, 220],
        'Y_coord': [210, 310, 320],
        'Z_coord': [60, 110, 120]
    }
    unblinded_df = pd.DataFrame(unblinded_data)
    
    print("📊 Input data:")
    print(f"  Main DataFrame: {len(main_df)} rows")
    print(f"    Radiologists: {main_df['Radiologist'].unique()}")
    print(f"  Unblinded DataFrame: {len(unblinded_df)} rows")
    print(f"    Radiologists: {unblinded_df['Radiologist'].unique()}")
    
    # Test conversion with tuple format (main, unblinded)
    print("\n🔄 Testing RA-D-PS conversion...")
    dataframes = (main_df, unblinded_df)
    
    try:
        records = convert_parsed_data_to_ra_d_ps_format(dataframes)
        
        print(f"\n✅ Conversion successful! Generated {len(records)} records")
        
        # Analyze results
        for i, record in enumerate(records, 1):
            file_id = record['file_number']
            nodule_id = record['nodule_id']
            rads = record['radiologists']
            
            print(f"\n📋 Record {i}: {file_id}-{nodule_id}")
            print(f"  👥 Radiologists: {list(rads.keys())}")
            
            for rad_num, data in rads.items():
                conf = data['confidence']
                coords = data['coordinates']
                print(f"    👨‍⚕️ Rad {rad_num}: confidence={conf}, coords={coords}")
        
        # Verify expected results
        print("\n🔍 Verification:")
        
        # Check file1-nodule1 should have 3 radiologists (anonRad1, anonRad2, anonRad3)
        file1_record = next((r for r in records if r['file_number'] == 'file1'), None)
        if file1_record:
            rad_count = len(file1_record['radiologists'])
            expected_count = 3  # anonRad1, anonRad2 from main + anonRad3 from unblinded
            print(f"  File1-nodule1: {rad_count} radiologists (expected {expected_count})")
            if rad_count == expected_count:
                print("  ✅ PASS: All radiologists preserved")
            else:
                print("  ❌ FAIL: Missing radiologists")
                return False
        
        # Check file2-nodule1 should have 3 radiologists (anonRad1 from main, anonRad2+anonRad3 from unblinded)
        file2_record = next((r for r in records if r['file_number'] == 'file2'), None)
        if file2_record:
            rad_count = len(file2_record['radiologists'])
            expected_count = 3  # anonRad1 from main + anonRad2, anonRad3 from unblinded
            print(f"  File2-nodule1: {rad_count} radiologists (expected {expected_count})")
            if rad_count == expected_count:
                print("  ✅ PASS: All radiologists preserved")
            else:
                print("  ❌ FAIL: Missing radiologists")
                return False
        
        print("\n🎉 All tests passed! Both main and unblinded data are preserved.")
        return True
        
    except Exception as e:
        print(f"\n❌ Conversion failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_data_combination()
    if success:
        print("\n✅ Test completed successfully")
    else:
        print("\n❌ Test failed")
        sys.exit(1)
