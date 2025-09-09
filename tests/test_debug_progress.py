#!/usr/bin/env python3
"""
Test the debug progress information
"""

import os
import sys
sys.path.append('/Users/isa/Desktop/python projects/XML PARSE')

from XMLPARSE import parse_radiology_sample, parse_multiple

def test_debug_progress():
    """Test the debug progress information"""
    print("🧪 Testing debug progress information...")
    
    # Test single file parsing
    xml_file = "/Users/isa/Desktop/XML TEST FILES/generated_cases_001_050/001.xml"
    
    print("\n" + "="*60)
    print("Testing single file parsing with debug info:")
    print("="*60)
    
    main_df, unblinded_df = parse_radiology_sample(xml_file)
    
    print("\n" + "="*60)
    print("Testing multiple file parsing with debug info:")
    print("="*60)
    
    # Test multiple file parsing
    test_files = []
    test_dir = "/Users/isa/Desktop/XML TEST FILES/generated_cases_001_050"
    
    for file in os.listdir(test_dir):
        if file.lower().endswith('.xml'):
            test_files.append(os.path.join(test_dir, file))
    
    test_files = sorted(test_files)[:3]  # Use first 3 files
    
    case_data, case_unblinded_data = parse_multiple(test_files)
    
    print("\n🎉 Debug testing complete!")

if __name__ == "__main__":
    test_debug_progress()
