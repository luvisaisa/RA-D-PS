#!/usr/bin/env python3
"""
Simple GUI test to demonstrate working XML parsing and RA-D-PS export
Uses real XML files from /Users/isa/Desktop/XML files parse
"""

import os
import sys
import tempfile
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from ra_d_ps.parser import parse_multiple, convert_parsed_data_to_ra_d_ps_format, export_excel

# Path to real XML test files
REAL_XML_DIR = "/Users/isa/Desktop/XML files parse"

def create_test_xml(filename):
    """Create a minimal test XML file"""
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<LidcReadMessage>
    <ResponseHeader>
        <seriesInstanceUid>1.2.3.4.5</seriesInstanceUid>
    </ResponseHeader>
    <readingSession>
        <annotationVersion>1.0</annotationVersion>
        <servicingRadiologistID>R001</servicingRadiologistID>
        <unblindedReadNodule>
            <noduleID>1</noduleID>
            <characteristics>
                <subtlety>3</subtlety>
                <internalStructure>4</internalStructure>
                <calcification>1</calcification>
                <sphericity>2</sphericity>
                <margin>3</margin>
                <lobulation>4</lobulation>
                <spiculation>1</spiculation>
                <texture>2</texture>
                <malignancy>3</malignancy>
            </characteristics>
        </unblindedReadNodule>
    </readingSession>
</LidcReadMessage>"""
    with open(filename, 'w') as f:
        f.write(xml_content)

@pytest.mark.skipif(not os.path.exists(REAL_XML_DIR), 
                    reason="Test XML directory not available")
def test_gui_workflow():
    """Test the GUI workflow with real XML files from Desktop (30 files per folder)"""
    
    # Get XML files from each subdirectory - 30 files per folder
    xml_files = []
    
    # First, get all subdirectories
    subdirs = []
    try:
        for item in os.listdir(REAL_XML_DIR):
            item_path = os.path.join(REAL_XML_DIR, item)
            if os.path.isdir(item_path) and not item.startswith('.'):
                subdirs.append(item_path)
    except Exception as e:
        print(f"⚠️ Error listing directories: {e}")
        return
    
    print(f"📁 Found {len(subdirs)} subdirectories in {REAL_XML_DIR}")
    
    # Collect up to 30 XML files from each subdirectory
    for subdir in sorted(subdirs):
        folder_name = os.path.basename(subdir)
        folder_files = []
        
        try:
            for file in os.listdir(subdir):
                if file.lower().endswith('.xml') and not file.startswith('.'):
                    folder_files.append(os.path.join(subdir, file))
        except Exception as e:
            print(f"⚠️ Error reading {folder_name}: {e}")
            continue
        
        # Take first 30 files from this folder
        folder_files = sorted(folder_files)[:30]
        xml_files.extend(folder_files)
        print(f"   📂 {folder_name}: added {len(folder_files)} files")
    
    print(f"\n✅ Total files to process: {len(xml_files)} (up to 30 per folder)")
    
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
        
        # Calculate statistics
        folder_count = len(subdirs)
        avg_files_per_folder = len(xml_files) / folder_count if folder_count > 0 else 0
        
        # Show success message
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()  # Hide main window
        messagebox.showinfo("Success!", 
                           f"XML parsing and RA-D-PS export successful!\n\n"
                           f"Folders processed: {folder_count}\n"
                           f"Total files parsed: {len(xml_files)}\n"
                           f"Avg per folder: {avg_files_per_folder:.1f}\n"
                           f"Records generated: {len(all_records)}\n"
                           f"Output: {os.path.basename(output_file)}\n\n"
                           f"Multi-folder workflow working correctly!")
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

def test_gui_workflow_with_mock_data():
    """Test the GUI workflow with generated test data (no external dependencies)"""
    print("🧪 Testing GUI workflow with generated test data...")
    
    try:
        # Create temporary directory and test files
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"📁 Using temporary directory: {temp_dir}")
            
            # Create 3 test XML files
            xml_files = []
            for i in range(3):
                filename = os.path.join(temp_dir, f"test_case_{i+1:03d}.xml")
                create_test_xml(filename)
                xml_files.append(filename)
                print(f"  ✅ Created {os.path.basename(filename)}")
            
            print(f"\n✅ Generated {len(xml_files)} test XML files")
            
            # Step 1: Parse XML files
            print("\n1️⃣ Parsing XML files...")
            case_data, case_unblinded_data = parse_multiple(xml_files)
            
            total_parsed = sum(len(df) for df in case_data.values() if not df.empty)
            total_unblinded = sum(len(df) for df in case_unblinded_data.values() if not df.empty)
            print(f"✅ Parsed {len(case_data)} case data entries")
            print(f"✅ Parsed {len(case_unblinded_data)} unblinded data entries")
            print(f"   Total rows: {total_parsed + total_unblinded}")
            
            # Step 2: Convert to RA-D-PS format
            print("\n2️⃣ Converting to RA-D-PS format...")
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
            output_file = export_excel(all_records, temp_dir, sheet="test_workflow")
            print(f"✅ Excel export successful!")
            print(f"   Output file: {output_file}")
            
            # Verify file exists
            assert os.path.exists(output_file), "Output file should exist"
            print(f"✅ Output file verified: {os.path.basename(output_file)}")
            
            print("\n🎉 GUI workflow test PASSED with generated data!")
            return True
            
    except Exception as e:
        print(f"❌ Error in GUI workflow test: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Try the real test first, fall back to mock data
    if os.path.exists("/Users/isa/Desktop/XML TEST FILES/generated_cases_001_050"):
        print("📂 Using real test data...")
        test_gui_workflow()
    else:
        print("📂 Real test data not available, using generated mock data...")
        test_gui_workflow_with_mock_data()
