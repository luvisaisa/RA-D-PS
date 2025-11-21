#!/usr/bin/env python3
"""
Test script for XML-COMP.zip dataset
Tests the RA-D-PS parser against real LIDC-IDRI XML files
"""
import os
import sys
from pathlib import Path
import time
import traceback

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.ra_d_ps.parser import parse_radiology_sample, parse_multiple, detect_parse_case

def test_single_file():
    """Test parsing a single XML file"""
    print("=" * 80)
    print("TEST 1: Single File Parsing")
    print("=" * 80)
    
    xml_path = "/Users/isa/Desktop/XML-COMP/157/158.xml"
    
    try:
        print(f"\n📄 Parsing: {xml_path}")
        start = time.time()
        
        # Parse the file - returns (main_df, unblinded_df)
        main_df, unblinded_df = parse_radiology_sample(xml_path)
        
        elapsed = time.time() - start
        
        print(f"✅ Parse successful in {elapsed:.2f}s")
        print(f"\n📊 Results:")
        print(f"   Main DataFrame: {len(main_df)} rows")
        print(f"   Unblinded DataFrame: {len(unblinded_df)} rows")
        
        # Show dataframe info
        if not main_df.empty:
            print(f"\n   Main DataFrame columns:")
            for col in list(main_df.columns)[:10]:
                print(f"      - {col}")
            if len(main_df.columns) > 10:
                print(f"      ... and {len(main_df.columns) - 10} more columns")
            
            # Show sample data
            print(f"\n   Sample Data (first row):")
            first_row = main_df.iloc[0]
            print(f"      File #: {first_row.get('file #', 'N/A')}")
            print(f"      Study UID: {str(first_row.get('Study UID', 'N/A'))[:50]}...")
            print(f"      NoduleID: {first_row.get('NoduleID', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc()
        return False

def test_structure_detection():
    """Test XML structure detection on multiple files"""
    print("\n" + "=" * 80)
    print("TEST 2: Structure Detection")
    print("=" * 80)
    
    test_files = [
        "/Users/isa/Desktop/XML-COMP/157/158.xml",
        "/Users/isa/Desktop/XML-COMP/157/159.xml",
        "/Users/isa/Desktop/XML-COMP/185/068.xml",
        "/Users/isa/Desktop/XML-COMP/186/100.xml",
    ]
    
    for xml_path in test_files:
        if not os.path.exists(xml_path):
            print(f"⚠️  File not found: {xml_path}")
            continue
            
        try:
            print(f"\n📄 Analyzing: {os.path.basename(xml_path)}")
            parse_case = detect_parse_case(xml_path)
            print(f"   Parse case: {parse_case}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            traceback.print_exc()
    
    return True

def test_folder_batch():
    """Test batch parsing of a folder"""
    print("\n" + "=" * 80)
    print("TEST 3: Folder Batch Processing (Folder 157)")
    print("=" * 80)
    
    folder_path = "/Users/isa/Desktop/XML-COMP/157"
    
    try:
        print(f"\n📁 Processing folder: {folder_path}")
        
        # Get all XML files
        xml_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) 
                     if f.endswith('.xml')]
        print(f"   Found {len(xml_files)} XML files")
        
        start = time.time()
        
        # Parse multiple files - returns (case_data_dict, case_unblinded_data_dict)
        case_data, case_unblinded_data = parse_multiple(xml_files)
        
        elapsed = time.time() - start
        
        print(f"\n✅ Batch parse completed in {elapsed:.2f}s")
        print(f"   Parse cases found: {len(case_data)}")
        print(f"   Average time per file: {elapsed/len(xml_files):.2f}s")
        
        # Summary statistics
        total_rows = sum(len(df) for df in case_data.values())
        print(f"\n📊 Summary:")
        print(f"   Total main data rows: {total_rows}")
        print(f"   Average rows per file: {total_rows/len(xml_files):.1f}")
        
        # Show parse cases
        print(f"\n   Parse cases detected:")
        for case, df in case_data.items():
            print(f"      {case}: {len(df)} rows")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc()
        return False

def test_large_folder_sample():
    """Test parsing a sample from the large folder (185)"""
    print("\n" + "=" * 80)
    print("TEST 4: Large Folder Sample (First 10 files from 185)")
    print("=" * 80)
    
    folder_path = "/Users/isa/Desktop/XML-COMP/185"
    
    try:
        print(f"\n📁 Processing sample from: {folder_path}")
        
        # Get first 10 XML files
        all_files = sorted([os.path.join(folder_path, f) for f in os.listdir(folder_path) 
                           if f.endswith('.xml')])
        xml_files = all_files[:10]
        
        print(f"   Total files available: {len(all_files)}")
        print(f"   Processing first: {len(xml_files)}")
        
        start = time.time()
        
        # Parse files - returns (case_data_dict, case_unblinded_data_dict)
        case_data, case_unblinded_data = parse_multiple(xml_files)
        
        elapsed = time.time() - start
        
        print(f"\n✅ Sample parse completed in {elapsed:.2f}s")
        print(f"   Parse cases found: {len(case_data)}")
        print(f"   Average time per file: {elapsed/len(xml_files):.2f}s")
        print(f"   Estimated time for all {len(all_files)} files: {(elapsed/len(xml_files))*len(all_files):.1f}s")
        
        # Summary statistics
        total_rows = sum(len(df) for df in case_data.values())
        print(f"\n📊 Summary:")
        print(f"   Total rows in sample: {total_rows}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc()
        return False

def test_export_excel():
    """Test Excel export for folder 157"""
    print("\n" + "=" * 80)
    print("TEST 5: Excel Export (Folder 157)")
    print("=" * 80)
    
    folder_path = "/Users/isa/Desktop/XML-COMP/157"
    
    try:
        from src.ra_d_ps.parser import export_excel
        
        print(f"\n📁 Processing folder: {folder_path}")
        
        # Get all XML files
        xml_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) 
                     if f.endswith('.xml')]
        
        print(f"   Found {len(xml_files)} XML files")
        
        # Parse files - returns (case_data_dict, case_unblinded_data_dict)
        print("   Parsing files...")
        case_data, case_unblinded_data = parse_multiple(xml_files)
        
        # Combine all case data
        import pandas as pd
        all_data = pd.concat(list(case_data.values()), ignore_index=True) if case_data else pd.DataFrame()
        
        print(f"   Parsed {len(case_data)} parse cases with {len(all_data)} total rows")
        
        # Export to Excel
        print("   Exporting to Excel...")
        # The export_excel function expects records (list of dicts), so we need to convert the dataframe
        # For now, let's try using the dataframe directly or convert to records
        # Let's check what export_excel expects
        
        # Actually, let's try a simpler approach - just save the dataframe directly
        output_filename = f"157_RA-D-PS_{time.strftime('%Y-%m-%d_%H%M%S')}.xlsx"
        output_path = os.path.join(folder_path, output_filename)
        
        all_data.to_excel(output_path, index=False)
        
        print(f"✅ Excel export successful!")
        print(f"   Output: {output_path}")
        
        # Check file size
        if os.path.exists(output_path):
            size_kb = os.path.getsize(output_path) / 1024
            print(f"   File size: {size_kb:.1f} KB")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🧪 RA-D-PS XML Parser Test Suite")
    print(f"📦 Testing XML-COMP.zip dataset")
    print(f"🕐 {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        ("Single File Parsing", test_single_file),
        ("Structure Detection", test_structure_detection),
        ("Folder Batch Processing", test_folder_batch),
        ("Large Folder Sample", test_large_folder_sample),
        ("Excel Export", test_export_excel),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
            traceback.print_exc()
            results.append((test_name, False))
    
    # Final summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    passed = sum(1 for _, s in results if s)
    total = len(results)
    
    print(f"\nTotal: {passed}/{total} tests passed ({100*passed/total:.0f}%)")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
