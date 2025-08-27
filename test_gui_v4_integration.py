#!/usr/bin/env python3
"""
Test script for GUI integration with v4 RA-D-PS formatting
"""

import os
import sys
sys.path.append('/Users/isa/Desktop/python projects/XML PARSE')

from XMLPARSE import NYTXMLGuiApp

def test_gui_integration():
    """Test that the GUI integration still works with v4 formatting"""
    print("Testing GUI integration with v4 formatting...")
    
    # Create a test parser instance
    parser = NYTXMLGuiApp()
    
    # Create test data directory structure
    test_base = "/Users/isa/Desktop/python projects/XML PARSE/test_gui_v4"
    test_folder1 = os.path.join(test_base, "folder1")
    test_folder2 = os.path.join(test_base, "folder2")
    
    os.makedirs(test_folder1, exist_ok=True)
    os.makedirs(test_folder2, exist_ok=True)
    
    # Create some test XML files
    test_xml_content = '''<?xml version="1.0" encoding="utf-8"?>
<LidcReadMessage>
    <ResponseHeader>
        <seriesInstanceUid>1.2.3.4.5.6.001</seriesInstanceUid>
    </ResponseHeader>
    <readingSession>
        <annotationVersion>1.0</annotationVersion>
        <servicingRadiologistID>R001</servicingRadiologistID>
        <unblindedReadNodule>
            <noduleID>nodule_001</noduleID>
            <characteristics>
                <subtlety>3</subtlety>
                <internalStructure>4</internalStructure>
                <calcification>2</calcification>
                <sphericity>5</sphericity>
                <margin>3</margin>
                <lobulation>2</lobulation>
                <spiculation>1</spiculation>
                <texture>4</texture>
                <malignancy>3</malignancy>
            </characteristics>
            <roi>
                <imageZposition>-145.0</imageZposition>
                <imageSOP_UID>1.2.3.4.5.6.7.001</imageSOP_UID>
                <inclusion>TRUE</inclusion>
                <edgeMap>
                    <xCoord>256</xCoord>
                    <yCoord>256</yCoord>
                </edgeMap>
            </roi>
        </unblindedReadNodule>
    </readingSession>
</LidcReadMessage>'''
    
    # Write test XML files
    with open(os.path.join(test_folder1, "test1.xml"), "w") as f:
        f.write(test_xml_content)
    
    with open(os.path.join(test_folder2, "test2.xml"), "w") as f:
        f.write(test_xml_content.replace("R001", "R002").replace("nodule_001", "nodule_002"))
    
    try:
        # Test convert_parsed_data_to_ra_d_ps_format function
        test_parsed_data = {
            "test1.xml": {
                "file_number": "test1",
                "study_uid": "1.2.3.4.5.6.001",
                "nodule_id": "nodule_001",
                "radiologist_1": {
                    "subtlety": 3,
                    "confidence": 4,
                    "obscuration": 2,
                    "reason": "Test nodule",
                    "coordinates": "(256,256,-145)"
                }
            }
        }
        
        ra_d_ps_records = parser.convert_parsed_data_to_ra_d_ps_format(test_parsed_data)
        print(f"✓ Data conversion successful: {len(ra_d_ps_records)} records")
        
        # Test export_ra_d_ps_excel with single folder
        parser.processing_mode.set("single")
        output_paths = parser.export_ra_d_ps_excel([test_folder1], test_base)
        print(f"✓ Single folder export successful: {len(output_paths)} files created")
        
        # Test export_ra_d_ps_excel with multiple folders (separate files)
        parser.processing_mode.set("separate")
        output_paths = parser.export_ra_d_ps_excel([test_folder1, test_folder2], test_base)
        print(f"✓ Separate folders export successful: {len(output_paths)} files created")
        
        # Test export_ra_d_ps_excel with multiple folders (combined file)
        parser.processing_mode.set("combined")
        output_paths = parser.export_ra_d_ps_excel([test_folder1, test_folder2], test_base)
        print(f"✓ Combined folders export successful: {len(output_paths)} files created")
        
        print("\nAll GUI integration tests passed!")
        print("The Export to Excel button should work properly with v4 formatting.")
        
        return True
        
    except Exception as e:
        print(f"✗ GUI integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_gui_integration()
    sys.exit(0 if success else 1)
