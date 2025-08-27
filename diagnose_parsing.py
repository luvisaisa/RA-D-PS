#!/usr/bin/env python3
"""
Diagnostic script to test XML parsing and identify why no information is being parsed
"""

import os
import sys
sys.path.append('/Users/isa/Desktop/python projects/XML PARSE')

import traceback
from XMLPARSE import parse_radiology_sample, detect_parse_case

def diagnose_parsing_issue():
    """Test parsing with various files to identify the issue"""
    print("🔍 Diagnosing XML parsing issue...")
    
    # Check current directory for XML files
    xml_files = []
    current_dir = "/Users/isa/Desktop/python projects/XML PARSE"
    
    for file in os.listdir(current_dir):
        if file.lower().endswith('.xml'):
            xml_files.append(os.path.join(current_dir, file))
    
    if not xml_files:
        print("❌ No XML files found in the current directory")
        print("Please provide the path to an XML file to test:")
        test_file = input("Enter XML file path: ").strip()
        if test_file and os.path.exists(test_file):
            xml_files = [test_file]
        else:
            print("❌ Invalid file path or file doesn't exist")
            return False
    
    print(f"📁 Found {len(xml_files)} XML files to test")
    
    for i, xml_file in enumerate(xml_files[:3], 1):  # Test first 3 files
        print(f"\n{'='*60}")
        print(f"🧪 Testing file {i}: {os.path.basename(xml_file)}")
        print(f"{'='*60}")
        
        try:
            # Test 1: Check if file exists and is readable
            if not os.path.exists(xml_file):
                print(f"❌ File doesn't exist: {xml_file}")
                continue
                
            if not os.access(xml_file, os.R_OK):
                print(f"❌ File is not readable: {xml_file}")
                continue
                
            print(f"✅ File exists and is readable")
            
            # Test 2: Check file size
            file_size = os.path.getsize(xml_file)
            print(f"📏 File size: {file_size} bytes")
            
            if file_size == 0:
                print("❌ File is empty")
                continue
            
            # Test 3: Test parse case detection
            print("🔍 Testing parse case detection...")
            try:
                parse_case = detect_parse_case(xml_file)
                print(f"✅ Parse case detected: {parse_case}")
            except Exception as e:
                print(f"❌ Parse case detection failed: {e}")
                traceback.print_exc()
                continue
            
            # Test 4: Test actual parsing
            print("🔄 Testing XML parsing...")
            try:
                main_df, unblinded_df = parse_radiology_sample(xml_file)
                print(f"✅ Parsing completed!")
                print(f"📊 Main DataFrame: {len(main_df)} rows, {len(main_df.columns) if not main_df.empty else 0} columns")
                print(f"📊 Unblinded DataFrame: {len(unblinded_df)} rows, {len(unblinded_df.columns) if not unblinded_df.empty else 0} columns")
                
                if main_df.empty and unblinded_df.empty:
                    print("⚠️  Both DataFrames are empty - no data was extracted")
                    
                    # Additional debugging: peek at file content
                    print("🔍 File content preview (first 500 characters):")
                    with open(xml_file, 'r', encoding='utf-8') as f:
                        content = f.read(500)
                        print(content)
                        print("...")
                else:
                    print("✅ Data successfully extracted!")
                    if not main_df.empty:
                        print("📋 Main DataFrame columns:", list(main_df.columns))
                        print("📋 First few rows:")
                        print(main_df.head())
                    
                    if not unblinded_df.empty:
                        print("📋 Unblinded DataFrame columns:", list(unblinded_df.columns))
                        print("📋 First few rows:")
                        print(unblinded_df.head())
                
            except Exception as e:
                print(f"❌ Parsing failed with error: {e}")
                traceback.print_exc()
                
                # Try to provide more detailed error information
                print("\n🔍 Additional debugging information:")
                try:
                    import xml.etree.ElementTree as ET
                    tree = ET.parse(xml_file)
                    root = tree.getroot()
                    print(f"✅ XML is valid. Root element: {root.tag}")
                    print(f"📝 Root children: {[child.tag for child in root]}")
                except Exception as xml_error:
                    print(f"❌ XML parsing error: {xml_error}")
        
        except Exception as e:
            print(f"❌ Unexpected error testing file: {e}")
            traceback.print_exc()
    
    print(f"\n{'='*60}")
    print("🏁 Diagnosis complete!")
    print("If all files show empty DataFrames, the issue might be:")
    print("1. XML files have a different structure than expected")
    print("2. The parsing logic needs adjustment for your specific XML format")
    print("3. There might be encoding or namespace issues")
    print("Please check the file content preview above to see the XML structure.")

if __name__ == "__main__":
    diagnose_parsing_issue()
