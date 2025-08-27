#!/usr/bin/env python3
"""
Test to verify all essential attributes are being extracted correctly:
1. Characteristics: confidence, subtlety, obscuration, reason
2. Coordinates: X, Y, Z
3. Study UID
"""

import os
import sys
sys.path.append('/Users/isa/Desktop/python projects/XML PARSE')

from XMLPARSE import parse_radiology_sample, convert_parsed_data_to_ra_d_ps_format

def test_essential_attributes():
    """Test that all essential attributes are being extracted"""
    print("🧪 Testing Essential Attributes Extraction...")
    print("✅ Target attributes:")
    print("   📊 Characteristics: confidence, subtlety, obscuration, reason")
    print("   📍 Coordinates: X, Y, Z")
    print("   🆔 Study UID")
    print()
    
    xml_file = "/Users/isa/Desktop/XML TEST FILES/generated_cases_001_050/001.xml"
    
    # Step 1: Parse the XML
    print("1️⃣ Parsing XML file...")
    main_df, unblinded_df = parse_radiology_sample(xml_file)
    
    print(f"\n2️⃣ Analyzing extracted data...")
    print(f"📊 Main DataFrame: {len(main_df)} rows")
    print(f"📊 Unblinded DataFrame: {len(unblinded_df)} rows")
    
    # Step 2: Check what columns we have
    if not main_df.empty:
        print(f"\n📋 Main DataFrame columns:")
        for col in main_df.columns:
            print(f"   - {col}")
        
        print(f"\n📋 First few rows of main data:")
        for idx, row in main_df.head().iterrows():
            print(f"   Row {idx+1}:")
            print(f"     Radiologist: {row.get('Radiologist', 'N/A')}")
            print(f"     Confidence: {row.get('Confidence', 'N/A')}")
            print(f"     Subtlety: {row.get('Subtlety', 'N/A')}")
            print(f"     Obscuration: {row.get('Obscuration', 'N/A')}")
            print(f"     Reason: {row.get('Reason', 'N/A')}")
            print(f"     X_coord: {row.get('X_coord', 'N/A')}")
            print(f"     Y_coord: {row.get('Y_coord', 'N/A')}")
            print(f"     Z_coord: {row.get('Z_coord', 'N/A')}")
            print(f"     StudyInstanceUID: {str(row.get('StudyInstanceUID', 'N/A'))[:30]}...")
            print()
    
    # Step 3: Test RA-D-PS conversion
    print("3️⃣ Testing RA-D-PS conversion...")
    records = convert_parsed_data_to_ra_d_ps_format((main_df, unblinded_df))
    
    print(f"📊 Generated {len(records)} RA-D-PS records")
    
    for i, record in enumerate(records):
        print(f"\n📋 Record {i+1}:")
        print(f"   File: {record['file_number']}")
        print(f"   Study UID: {record['study_uid'][:30]}...")
        print(f"   Nodule ID: {record['nodule_id']}")
        print(f"   Radiologists: {len(record['radiologists'])}")
        
        for rad_id, rad_data in record['radiologists'].items():
            print(f"     Radiologist {rad_id}:")
            print(f"       ✅ Subtlety: {rad_data.get('subtlety', 'MISSING')}")
            print(f"       ✅ Confidence: {rad_data.get('confidence', 'MISSING')}")
            print(f"       ✅ Obscuration: {rad_data.get('obscuration', 'MISSING')}")
            print(f"       ✅ Reason: {rad_data.get('reason', 'MISSING')}")
            print(f"       ✅ Coordinates: {rad_data.get('coordinates', 'MISSING')}")
    
    # Step 4: Verify all essential attributes are present
    print("\n4️⃣ Verification Summary...")
    
    all_good = True
    
    # Check if we have radiologist data
    if records and len(records) > 0 and 'radiologists' in records[0]:
        radiologists = records[0]['radiologists']
        
        print(f"✅ Found {len(radiologists)} radiologists")
        
        # Check each radiologist has all essential attributes
        for rad_id, rad_data in radiologists.items():
            print(f"   Radiologist {rad_id}:")
            
            # Check characteristics
            for attr in ['subtlety', 'confidence', 'obscuration', 'reason']:
                if attr in rad_data and rad_data[attr] not in ['', None]:
                    print(f"     ✅ {attr}: {rad_data[attr]}")
                else:
                    print(f"     ❌ {attr}: MISSING")
                    all_good = False
            
            # Check coordinates
            coords = rad_data.get('coordinates', '')
            if coords and coords.strip():
                print(f"     ✅ coordinates: {coords}")
            else:
                print(f"     ❌ coordinates: MISSING")
                all_good = False
        
        # Check Study UID
        study_uid = records[0].get('study_uid', '')
        if study_uid and study_uid not in ['#N/A', 'MISSING', '']:
            print(f"   ✅ Study UID: {study_uid[:30]}...")
        else:
            print(f"   ❌ Study UID: MISSING")
            all_good = False
    else:
        print("❌ No radiologist data found!")
        all_good = False
    
    print(f"\n🎯 Overall Result: {'✅ ALL ESSENTIAL ATTRIBUTES EXTRACTED' if all_good else '❌ SOME ATTRIBUTES MISSING'}")
    
    return all_good

if __name__ == "__main__":
    success = test_essential_attributes()
    sys.exit(0 if success else 1)
