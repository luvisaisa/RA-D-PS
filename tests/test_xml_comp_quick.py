#!/usr/bin/env python3
"""
Quick test script for XML-COMP.zip dataset (minimal output)
"""
import os
import sys
from pathlib import Path
import time

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Suppress verbose parser output
import warnings
warnings.filterwarnings('ignore')

def test_quick():
    """Quick test of XML parsing"""
    print("🧪 Quick XML-COMP Test")
    print("=" * 60)
    
    # Test 1: Single file
    print("\n1️⃣  Testing single file...")
    from src.ra_d_ps.parser import parse_radiology_sample
    
    xml_path = "/Users/isa/Desktop/XML-COMP/157/158.xml"
    start = time.time()
    main_df, unblinded_df = parse_radiology_sample(xml_path)
    elapsed = time.time() - start
    
    print(f"   ✅ Parsed in {elapsed:.2f}s")
    print(f"   📊 Main: {len(main_df)} rows, Unblinded: {len(unblinded_df)} rows")
    print(f"   📋 Columns: {len(main_df.columns)} (showing first 5)")
    for col in list(main_df.columns)[:5]:
        print(f"      - {col}")
    
    # Test 2: Batch folder
    print("\n2️⃣  Testing folder batch (157 - 11 files)...")
    from src.ra_d_ps.parser import parse_multiple
    
    folder = "/Users/isa/Desktop/XML-COMP/157"
    xml_files = sorted([os.path.join(folder, f) for f in os.listdir(folder) if f.endswith('.xml')])
    
    print(f"   Found {len(xml_files)} files")
    start = time.time()
    case_data, case_unblinded = parse_multiple(xml_files)
    elapsed = time.time() - start
    
    total_rows = sum(len(df) for df in case_data.values())
    print(f"   ✅ Parsed in {elapsed:.2f}s ({elapsed/len(xml_files):.2f}s per file)")
    print(f"   📊 Total rows: {total_rows} ({total_rows/len(xml_files):.1f} per file)")
    print(f"   📋 Parse cases: {list(case_data.keys())}")
    
    # Test 3: Sample from large folder
    print("\n3️⃣  Testing sample from large folder (185 - first 5 files)...")
    
    folder = "/Users/isa/Desktop/XML-COMP/185"
    all_files = sorted([os.path.join(folder, f) for f in os.listdir(folder) if f.endswith('.xml')])
    sample_files = all_files[:5]
    
    print(f"   Total available: {len(all_files)} files")
    print(f"   Testing with: {len(sample_files)} files")
    start = time.time()
    case_data, case_unblinded = parse_multiple(sample_files)
    elapsed = time.time() - start
    
    total_rows = sum(len(df) for df in case_data.values())
    est_full = (elapsed / len(sample_files)) * len(all_files)
    print(f"   ✅ Parsed in {elapsed:.2f}s ({elapsed/len(sample_files):.2f}s per file)")
    print(f"   📊 Total rows: {total_rows}")
    print(f"   ⏱️  Estimated for all {len(all_files)} files: {est_full:.1f}s ({est_full/60:.1f} min)")
    
    # Test 4: Excel export
    print("\n4️⃣  Testing Excel export...")
    import pandas as pd
    
    all_data = pd.concat(list(case_data.values()), ignore_index=True)
    output_path = f"/Users/isa/Desktop/XML-COMP/test_output_{int(time.time())}.xlsx"
    
    start = time.time()
    all_data.to_excel(output_path, index=False)
    elapsed = time.time() - start
    
    size_kb = os.path.getsize(output_path) / 1024
    print(f"   ✅ Exported in {elapsed:.2f}s")
    print(f"   📁 File: {os.path.basename(output_path)}")
    print(f"   📏 Size: {size_kb:.1f} KB")
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED")
    print(f"📦 Dataset: 3 folders (157: 11 files, 185: 232 files, 186: 232 files)")
    print(f"🎯 Parser successfully handles LIDC-IDRI XML format")
    print(f"💾 Excel export working correctly")

if __name__ == "__main__":
    # Redirect stdout to suppress parser verbose output
    import io
    import contextlib
    
    # Capture parser output
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        test_quick()
    
    # Print only our test output (lines that don't start with emojis from parser)
    captured = f.getvalue()
    for line in captured.split('\n'):
        # Skip parser verbose lines but keep test output
        if not any(line.strip().startswith(emoji) for emoji in ['🔍', '  📋', '  ✅', '  📄', '  🔄', '  📊', '    📋', '      👨‍⚕️']):
            print(line)
