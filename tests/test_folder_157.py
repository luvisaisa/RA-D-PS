#!/usr/bin/env python3

# Quick diagnostic script - save this as test_folder_157.py
# Then run: python3 test_folder_157.py /path/to/folder/157

import os
import sys
import xml.etree.ElementTree as ET

def quick_xml_diagnosis(folder_path):
    """Quickly diagnose XML structure issues in folder 157"""
    xml_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.xml')]
    
    if not xml_files:
        print("No XML files found!")
        return
    
    # Analyze first few files
    for i, filename in enumerate(xml_files[:3]):
        file_path = os.path.join(folder_path, filename)
        print(f"\n{'='*20} FILE {i+1}: {filename} {'='*20}")
        
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            print(f"Root tag: {root.tag}")
            
            # Check for key elements
            has_header = root.find('.//ResponseHeader') is not None
            sessions = root.findall('.//CXRreadingSession') + root.findall('.//readingSession')
            unblinded = root.findall('.//unblindedRead') + root.findall('.//unblindedReadNodule')
            characteristics = root.findall('.//characteristics')
            rois = root.findall('.//roi')
            
            print(f"Has ResponseHeader: {has_header}")
            print(f"Sessions found: {len(sessions)}")
            print(f"Unblinded reads: {len(unblinded)}")
            print(f"Characteristics: {len(characteristics)}")
            print(f"ROIs: {len(rois)}")
            
            # If no sessions, this explains the N/A problem
            if len(sessions) == 0:
                print("🚨 NO SESSIONS FOUND - This is why you get N/A values!")
                print("XML structure analysis needed...")
                
                # Show root children
                print("Root element children:")
                for child in root:
                    print(f"  - {child.tag}")
            
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        folder_path = sys.argv[1]
        if os.path.exists(folder_path):
            quick_xml_diagnosis(folder_path)
        else:
            print(f"Folder not found: {folder_path}")
    else:
        print("Usage: python3 test_folder_157.py /path/to/folder/157")
