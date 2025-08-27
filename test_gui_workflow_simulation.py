#!/usr/bin/env python3
"""
Comprehensive test to simulate the actual GUI workflow with mock XML data
"""

import sys
import os
import tempfile
import pandas as pd

# Add the current directory to path to import XMLPARSE
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from XMLPARSE import parse_multiple, convert_parsed_data_to_ra_d_ps_format, export_excel

def create_mock_xml_file(file_path, radiologists_data):
    """Create a mock XML file with specified radiologist data"""
    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<LidcReadMessage>
  <ResponseHeader>
    <dateService>20231215</dateService>
    <timeService>143022.000000</timeService>
    <studyInstanceUID>1.2.840.113619.2.176.3596.3364818.7819.1234567890.123</studyInstanceUID>
    <seriesInstanceUID>1.2.840.113619.2.176.3596.3364818.7819.1234567890.456</seriesInstanceUID>
    <Modality>CT</Modality>
  </ResponseHeader>
"""
    
    # Add reading sessions with unblinded reads inside
    for i, rad_data in enumerate(radiologists_data[:2]):  # First 2 as main
        xml_content += f"""
  <readingSession>
    <annotationVersion>1.0</annotationVersion>
    <unblindedReadNodule>
      <nodule>
        <noduleID>nodule_001</noduleID>
        <characteristics>
          <subtlety>{rad_data['subtlety']}</subtlety>
          <internalStructure>1</internalStructure>
          <calcification>6</calcification>
          <sphericity>3</sphericity>
          <margin>1</margin>
          <lobulation>1</lobulation>
          <spiculation>1</spiculation>
          <texture>5</texture>
          <confidence>{rad_data['confidence']}</confidence>
          <obscuration>2</obscuration>
          <reason>Test reason for radiologist {i+1}</reason>
        </characteristics>
        <roi>
          <imageSOP_UID>1.2.840.113619.2.176.3596.3364818.7819.1234567890.789</imageSOP_UID>
          <imageZposition>-127.5</imageZposition>
          <inclusion>TRUE</inclusion>
          <edgeMap>
            <xCoord>{rad_data['x']}</xCoord>
            <yCoord>{rad_data['y']}</yCoord>
          </edgeMap>
        </roi>
      </nodule>
    </unblindedReadNodule>
  </readingSession>
"""
    
    # Add additional unblinded reads for remaining radiologists
    if len(radiologists_data) > 2:
        xml_content += f"""
  <readingSession>
    <annotationVersion>1.0</annotationVersion>
"""
        for i, rad_data in enumerate(radiologists_data[2:], 3):  # Additional as unblinded
            xml_content += f"""
    <unblindedReadNodule>
      <nodule>
        <noduleID>nodule_001</noduleID>
        <characteristics>
          <subtlety>{rad_data['subtlety']}</subtlety>
          <internalStructure>1</internalStructure>
          <calcification>6</calcification>
          <sphericity>3</sphericity>
          <margin>1</margin>
          <lobulation>1</lobulation>
          <spiculation>1</spiculation>
          <texture>5</texture>
          <confidence>{rad_data['confidence']}</confidence>
          <obscuration>1</obscuration>
          <reason>Test reason for unblinded radiologist {i}</reason>
        </characteristics>
        <roi>
          <imageSOP_UID>1.2.840.113619.2.176.3596.3364818.7819.1234567890.789</imageSOP_UID>
          <imageZposition>-127.5</imageZposition>
          <inclusion>TRUE</inclusion>
          <edgeMap>
            <xCoord>{rad_data['x']}</xCoord>
            <yCoord>{rad_data['y']}</yCoord>
          </edgeMap>
        </roi>
      </nodule>
    </unblindedReadNodule>
"""
        xml_content += """
  </readingSession>
"""
    
    xml_content += """
</LidcReadMessage>"""
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(xml_content)

def test_complete_gui_workflow():
    """Test the complete GUI workflow simulation"""
    
    print("🧪 Testing complete GUI workflow simulation...")
    
    # Create temporary directory and XML files
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 Created temporary directory: {temp_dir}")
        
        # Create mock XML files with different radiologist configurations
        xml_files = []
        
        # File 1: 3 radiologists (2 main + 1 unblinded)
        file1_path = os.path.join(temp_dir, "test_file_1.xml")
        radiologists_1 = [
            {'subtlety': 3, 'confidence': 4, 'x': 100, 'y': 200},  # Main rad 1
            {'subtlety': 4, 'confidence': 3, 'x': 150, 'y': 250},  # Main rad 2
            {'subtlety': 2, 'confidence': 5, 'x': 110, 'y': 210},  # Unblinded rad 1
        ]
        create_mock_xml_file(file1_path, radiologists_1)
        xml_files.append(file1_path)
        
        # File 2: 4 radiologists (2 main + 2 unblinded)
        file2_path = os.path.join(temp_dir, "test_file_2.xml")
        radiologists_2 = [
            {'subtlety': 5, 'confidence': 2, 'x': 300, 'y': 400},  # Main rad 1
            {'subtlety': 1, 'confidence': 4, 'x': 320, 'y': 420},  # Main rad 2
            {'subtlety': 3, 'confidence': 3, 'x': 310, 'y': 410},  # Unblinded rad 1
            {'subtlety': 4, 'confidence': 1, 'x': 330, 'y': 430},  # Unblinded rad 2
        ]
        create_mock_xml_file(file2_path, radiologists_2)
        xml_files.append(file2_path)
        
        print(f"📋 Created {len(xml_files)} test XML files")
        
        try:
            # Step 1: Parse multiple files (like GUI does)
            print("\n🔄 Step 1: Parsing multiple files...")
            case_data, case_unblinded_data = parse_multiple(xml_files)
            
            print(f"📊 Parse results:")
            print(f"  Main data cases: {list(case_data.keys())}")
            print(f"  Unblinded data cases: {list(case_unblinded_data.keys())}")
            
            if not case_data and not case_unblinded_data:
                print("❌ No data parsed!")
                return False
                
            # Step 2: Combine data per case (like GUI should do)
            print("\n🔄 Step 2: Combining data per case...")
            combined_case_data = {}
            all_cases = set(case_data.keys()) | set(case_unblinded_data.keys())
            
            print(f"📋 Found parse cases: {list(all_cases)}")
            
            for case in all_cases:
                main_df = case_data.get(case, pd.DataFrame())
                unblinded_df = case_unblinded_data.get(case, pd.DataFrame())
                
                print(f"  📊 Case '{case}':")
                print(f"    Main: {len(main_df)} rows")
                if not main_df.empty and 'Radiologist' in main_df.columns:
                    main_rads = main_df['Radiologist'].unique()
                    print(f"      Radiologists: {main_rads}")
                
                print(f"    Unblinded: {len(unblinded_df)} rows")
                if not unblinded_df.empty and 'Radiologist' in unblinded_df.columns:
                    unblinded_rads = unblinded_df['Radiologist'].unique()
                    print(f"      Radiologists: {unblinded_rads}")
                
                combined_case_data[case] = (main_df, unblinded_df)
            
            # Step 3: Convert to RA-D-PS format
            print("\n🔄 Step 3: Converting to RA-D-PS format...")
            all_ra_d_ps_records = []
            for case, (main_df, unblinded_df) in combined_case_data.items():
                print(f"🔄 Converting case '{case}' to RA-D-PS...")
                case_records = convert_parsed_data_to_ra_d_ps_format((main_df, unblinded_df))
                all_ra_d_ps_records.extend(case_records)
                print(f"  ✅ Generated {len(case_records)} records for case '{case}'")
            
            ra_d_ps_records = all_ra_d_ps_records
            
            if not ra_d_ps_records:
                print("❌ No RA-D-PS records generated!")
                return False
                
            print(f"\n📋 Total RA-D-PS records: {len(ra_d_ps_records)}")
            
            # Show radiologist counts
            for i, record in enumerate(ra_d_ps_records, 1):
                file_id = record.get('file_number', 'unknown')
                nodule_id = record.get('nodule_id', 'unknown')
                rad_count = len(record.get('radiologists', {}))
                rad_keys = list(record.get('radiologists', {}).keys())
                print(f"  📄 Record {i}: {file_id}-{nodule_id} → {rad_count} radiologists {rad_keys}")
            
            # Step 4: Export to Excel
            print("\n🔄 Step 4: Exporting to Excel...")
            output_file = "test_gui_workflow_output.xlsx"
            
            export_excel(ra_d_ps_records, output_file, force_blocks=True)
            
            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                print(f"✅ Excel export successful!")
                print(f"  📋 File: {output_file}")
                print(f"  📏 Size: {file_size:,} bytes")
                print("\n🎉 Complete GUI workflow test successful!")
                return True
            else:
                print("❌ Excel file was not created!")
                return False
                
        except Exception as e:
            print(f"❌ Workflow test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_complete_gui_workflow()
    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Tests failed!")
        sys.exit(1)
