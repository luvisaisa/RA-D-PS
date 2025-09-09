#!/usr/bin/env python3
"""
Test parsing with a specific XML file
"""

import os
import sys
sys.path.append('/Users/isa/Desktop/python projects/XML PARSE')

import traceback
from XMLPARSE import parse_radiology_sample, detect_parse_case

def test_specific_xml():
    """Test parsing with a specific XML file"""
    xml_file = "/Users/isa/Desktop/XML TEST FILES/generated_cases_001_050/001.xml"
    
    print(f"🧪 Testing XML file: {xml_file}")
    
    try:
        # Test parse case detection
        print("🔍 Detecting parse case...")
        parse_case = detect_parse_case(xml_file)
        print(f"✅ Parse case: {parse_case}")
        
        # Test parsing
        print("🔄 Parsing XML...")
        main_df, unblinded_df = parse_radiology_sample(xml_file)
        
        print(f"📊 Results:")
        print(f"  Main DataFrame: {len(main_df)} rows")
        print(f"  Unblinded DataFrame: {len(unblinded_df)} rows")
        
        if main_df.empty and unblinded_df.empty:
            print("⚠️  No data extracted. Let's examine the XML structure...")
            
            # Read and display XML content
            with open(xml_file, 'r', encoding='utf-8') as f:
                content = f.read()
                print("📄 XML Content:")
                print(content)
                
        else:
            print("✅ Data successfully extracted!")
            if not main_df.empty:
                print("\n📋 Main DataFrame:")
                print(main_df.to_string())
            if not unblinded_df.empty:
                print("\n📋 Unblinded DataFrame:")
                print(unblinded_df.to_string())
    
    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_specific_xml()
