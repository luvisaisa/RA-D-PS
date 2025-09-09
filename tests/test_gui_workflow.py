#!/usr/bin/env python3
"""
Simple GUI test to demonstrate working XML parsing and RA-D-PS export
"""

import os
import sys
sys.path.append('/Users/isa/Desktop/python projects/XML PARSE')

import tkinter as tk
from tkinter import messagebox
from XMLPARSE import parse_multiple, convert_parsed_data_to_ra_d_ps_format, export_excel

def test_gui_workflow():
    """Test the GUI workflow with known working XML files"""
    
    # Get XML files from the test directory
    test_dir = "/Users/isa/Desktop/XML TEST FILES/generated_cases_001_050"
    xml_files = []
    
    for file in os.listdir(test_dir):
        if file.lower().endswith('.xml'):
            xml_files.append(os.path.join(test_dir, file))
    
    xml_files = sorted(xml_files)[:5]  # Use first 5 files for testing
    
    if not xml_files:
        print("❌ No XML files found for testing")
        return
    
    print(f"🧪 Testing GUI workflow with {len(xml_files)} files...")
    for f in xml_files:
        print(f"   - {os.path.basename(f)}")
    
    try:
        # Step 1: Parse multiple files (like the GUI does)
        print("\n1️⃣ Parsing multiple XML files...")
        case_data, case_unblinded_data = parse_multiple(xml_files)
        
        print(f"✅ Parsing completed!")
        print(f"   Case data keys: {list(case_data.keys())}")
        print(f"   Case unblinded data keys: {list(case_unblinded_data.keys())}")
        
        # Check if we have data
        total_main_rows = sum(len(df) for df in case_data.values())
        total_unblinded_rows = sum(len(df) for df in case_unblinded_data.values())
        
        print(f"   Total main rows: {total_main_rows}")
        print(f"   Total unblinded rows: {total_unblinded_rows}")
        
        if total_main_rows == 0 and total_unblinded_rows == 0:
            print("⚠️  No data extracted from any files")
            return
        
        # Step 2: Convert to RA-D-PS format
        print("\n2️⃣ Converting to RA-D-PS format...")
        
        # Combine all data
        all_records = []
        for parse_case, df in case_data.items():
            if not df.empty:
                records = convert_parsed_data_to_ra_d_ps_format(df)
                all_records.extend(records)
        
        for parse_case, df in case_unblinded_data.items():
            if not df.empty:
                records = convert_parsed_data_to_ra_d_ps_format(df)
                all_records.extend(records)
        
        print(f"✅ Converted {len(all_records)} records to RA-D-PS format")
        
        # Step 3: Export to Excel
        print("\n3️⃣ Exporting to RA-D-PS Excel...")
        output_dir = "/Users/isa/Desktop/python projects/XML PARSE/test_gui_workflow"
        os.makedirs(output_dir, exist_ok=True)
        
        output_file = export_excel(all_records, output_dir, sheet="gui_test")
        print(f"✅ Excel export successful!")
        print(f"   Output file: {output_file}")
        
        # Show success message
        root = tk.Tk()
        root.withdraw()  # Hide main window
        messagebox.showinfo("Success!", 
                           f"XML parsing and RA-D-PS export successful!\n\n"
                           f"Parsed {len(xml_files)} files\n"
                           f"Generated {len(all_records)} records\n"
                           f"Output: {os.path.basename(output_file)}\n\n"
                           f"The parsing is working correctly!")
        root.destroy()
        
    except Exception as e:
        print(f"❌ Error in GUI workflow test: {e}")
        import traceback
        traceback.print_exc()
        
        # Show error message
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Error", f"Error in workflow: {e}")
        root.destroy()

if __name__ == "__main__":
    test_gui_workflow()
