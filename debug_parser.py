#!/usr/bin/env python3
"""
Debug script to analyze XML parsing and identify why many cells show #N/A
"""
import os
import sys
import xml.etree.ElementTree as ET
import re
from collections import defaultdict

# Add the current directory to path to import XMLPARSE functions
sys.path.append('.')
from XMLPARSE import detect_parse_case, get_expected_attributes_for_case, parse_radiology_sample

def analyze_xml_structure(file_path):
    """Analyze the structure of an XML file to understand attribute availability"""
    print(f"\n{'='*60}")
    print(f"ANALYZING: {os.path.basename(file_path)}")
    print(f"{'='*60}")
    
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Get namespace
        m = re.match(r'\{(.*)\}', root.tag)
        ns_uri = m.group(1) if m else ''
        def tag(name):
            return f"{{{ns_uri}}}{name}" if ns_uri else name
        
        print(f"Root element: {root.tag}")
        print(f"Namespace: {ns_uri if ns_uri else 'None'}")
        
        # Analyze header
        print(f"\n📋 HEADER ANALYSIS:")
        header = root.find(tag('ResponseHeader'))
        if header is not None:
            print("✅ ResponseHeader found")
            header_fields = ["StudyInstanceUID", "SeriesInstanceUID", "SeriesInstanceUid", "Modality", "DateService", "TimeService"]
            for field in header_fields:
                elem = header.find(tag(field))
                if elem is not None and elem.text:
                    print(f"  ✅ {field}: {elem.text[:50]}...")
                elif elem is not None:
                    print(f"  ⚠️  {field}: <empty>")
                else:
                    print(f"  ❌ {field}: NOT FOUND")
        else:
            print("❌ ResponseHeader NOT FOUND")
        
        # Analyze sessions
        print(f"\n🔍 SESSION ANALYSIS:")
        sessions = root.findall(tag('readingSession')) or root.findall(tag('CXRreadingSession'))
        print(f"Sessions found: {len(sessions)}")
        
        if not sessions:
            print("❌ No sessions found!")
            return
        
        for i, session in enumerate(sessions[:2]):  # Analyze first 2 sessions
            print(f"\n  Session {i+1}:")
            rad_elem = session.find(tag('servicingRadiologistID'))
            rad_id = rad_elem.text if rad_elem is not None else "NOT_FOUND"
            print(f"    Radiologist: {rad_id}")
            
            # Analyze unblinded reads
            unblinded_reads = session.findall(tag('unblindedReadNodule')) or session.findall(tag('unblindedRead'))
            print(f"    Unblinded reads: {len(unblinded_reads)}")
            
            for j, read in enumerate(unblinded_reads[:2]):  # Analyze first 2 reads
                print(f"\n    Read {j+1}:")
                nodule_elem = read.find(tag('noduleID'))
                nodule_id = nodule_elem.text if nodule_elem is not None else "NOT_FOUND"
                print(f"      Nodule ID: {nodule_id}")
                
                # Analyze characteristics
                characteristics = read.find(tag('characteristics'))
                if characteristics is not None:
                    print(f"      ✅ Characteristics found:")
                    char_fields = ['confidence', 'subtlety', 'obscuration', 'reason']
                    for field in char_fields:
                        elem = characteristics.find(tag(field))
                        if elem is not None and elem.text:
                            print(f"        ✅ {field}: {elem.text}")
                        elif elem is not None:
                            print(f"        ⚠️  {field}: <empty>")
                        else:
                            print(f"        ❌ {field}: NOT FOUND")
                else:
                    print(f"      ❌ Characteristics NOT FOUND")
                
                # Analyze ROI
                rois = read.findall(tag('roi'))
                print(f"      ROIs found: {len(rois)}")
                
                if rois:
                    roi = rois[0]  # Analyze first ROI
                    sop_elem = roi.find(tag('imageSOP_UID'))
                    sop_uid = sop_elem.text if sop_elem is not None else "NOT_FOUND"
                    print(f"        SOP UID: {sop_uid[:30]}..." if len(sop_uid) > 30 else f"        SOP UID: {sop_uid}")
                    
                    # Check edge maps
                    edge_maps = roi.findall(tag('edgeMap'))
                    edge_single = roi.find(tag('edgeMap'))
                    
                    if edge_maps:
                        print(f"        Edge maps (multiple): {len(edge_maps)}")
                        first_edge = edge_maps[0]
                    elif edge_single is not None:
                        print(f"        Edge map (single): found")
                        first_edge = edge_single
                    else:
                        print(f"        Edge maps: NOT FOUND")
                        continue
                    
                    # Check coordinates
                    x_elem = first_edge.find(tag('xCoord'))
                    y_elem = first_edge.find(tag('yCoord'))
                    z_elem = first_edge.find(tag('imageZposition'))
                    
                    x_val = x_elem.text if x_elem is not None else "NOT_FOUND"
                    y_val = y_elem.text if y_elem is not None else "NOT_FOUND"
                    z_val = z_elem.text if z_elem is not None else "NOT_FOUND"
                    
                    print(f"        X coord: {x_val}")
                    print(f"        Y coord: {y_val}")
                    print(f"        Z coord: {z_val}")
        
        # Get parse case and expected attributes
        print(f"\n🎯 PARSE CASE ANALYSIS:")
        parse_case = detect_parse_case(file_path)
        print(f"Detected parse case: {parse_case}")
        
        expected_attrs = get_expected_attributes_for_case(parse_case)
        print(f"Expected attributes:")
        for category, attrs in expected_attrs.items():
            print(f"  {category}: {attrs}")
        
    except Exception as e:
        print(f"❌ Error analyzing {file_path}: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main function to run XML analysis"""
    print("XML Parser Debug Tool")
    print("This tool analyzes XML file structure to identify parsing issues")
    
    # Check for XML files in current directory first
    xml_files = [f for f in os.listdir('.') if f.endswith('.xml')]
    
    if not xml_files:
        # Ask user for folder path
        print("No XML files found in current directory")
        folder_path = input("Please enter the path to folder containing XML files: ").strip()
        
        if not folder_path or not os.path.exists(folder_path):
            print("Invalid folder path")
            return
            
        try:
            xml_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith('.xml')]
        except Exception as e:
            print(f"Error accessing folder: {e}")
            return
    else:
        # Use files from current directory
        xml_files = [os.path.join('.', f) for f in xml_files]
    
    if not xml_files:
        print("No XML files found in specified location")
        return
    
    print(f"\nFound {len(xml_files)} XML files")
    
    # Analyze first few files
    for file_path in xml_files[:3]:  # Limit to 3 files for now
        analyze_xml_structure(file_path)
    
    # Test parsing with actual parser
    print(f"\n{'='*60}")
    print("TESTING ACTUAL PARSER OUTPUT")
    print(f"{'='*60}")
    
    test_file = xml_files[0]
    print(f"Testing parser on: {test_file}")
    
    try:
        df, unblinded_df = parse_radiology_sample(test_file)
        print(f"\nParser results:")
        print(f"  Main DataFrame: {len(df)} rows")
        print(f"  Unblinded DataFrame: {len(unblinded_df)} rows")
        
        if len(df) > 0:
            print(f"\nFirst few rows of main data:")
            pd_available = True
            try:
                import pandas as pd
                print(df.head())
                
                # Count #N/A values
                na_count = (df == '#N/A').sum().sum()
                missing_count = (df == 'MISSING').sum().sum()
                total_cells = df.shape[0] * df.shape[1]
                
                print(f"\nData quality summary:")
                print(f"  Total cells: {total_cells}")
                print(f"  #N/A values: {na_count} ({na_count/total_cells*100:.1f}%)")
                print(f"  MISSING values: {missing_count} ({missing_count/total_cells*100:.1f}%)")
                
            except ImportError:
                print("pandas not available for detailed analysis")
        
    except Exception as e:
        print(f"❌ Error testing parser: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
