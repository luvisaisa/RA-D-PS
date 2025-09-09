#!/usr/bin/env python3

import os
import sys
import xml.etree.ElementTree as ET
import pandas as pd
from collections import defaultdict

# Import our parsing functions
from XMLPARSE import parse_radiology_sample, detect_parse_case

def analyze_xml_structure(file_path):
    """Analyze the structure of an XML file to understand why we get N/A values"""
    print(f"\n{'='*50}")
    print(f"ANALYZING: {os.path.basename(file_path)}")
    print(f"{'='*50}")
    
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Show basic info
        print(f"Root tag: {root.tag}")
        
        # Get namespace
        import re
        m = re.match(r'\{(.*)\}', root.tag)
        ns_uri = m.group(1) if m else ''
        print(f"Namespace: {ns_uri}")
        
        def tag(name):
            return f"{{{ns_uri}}}{name}" if ns_uri else name
        
        # Check for ResponseHeader
        header = root.find(tag('ResponseHeader'))
        print(f"ResponseHeader found: {header is not None}")
        
        if header is not None:
            for field in ['StudyInstanceUID', 'SeriesInstanceUID', 'SeriesInstanceUid', 'Modality', 'DateService', 'TimeService']:
                elem = header.find(tag(field))
                print(f"  {field}: {'✓' if elem is not None else '✗'} {elem.text if elem is not None else 'MISSING'}")
        
        # Check session structure
        root_tag_name = root.tag.split('}')[-1] if '}' in root.tag else root.tag
        is_lidc_format = root_tag_name == 'LidcReadMessage'
        session_tag = 'readingSession' if is_lidc_format else 'CXRreadingSession'
        unblinded_tag = 'unblindedReadNodule' if is_lidc_format else 'unblindedRead'
        
        print(f"Format: {'LIDC' if is_lidc_format else 'CXR'}")
        print(f"Looking for: {session_tag}")
        
        sessions = root.findall(tag(session_tag))
        print(f"Sessions found: {len(sessions)}")
        
        if sessions:
            for i, session in enumerate(sessions):
                print(f"\n  Session {i+1}:")
                rad_elem = session.find(tag('servicingRadiologistID'))
                print(f"    Radiologist: {'✓' if rad_elem is not None else '✗'} {rad_elem.text if rad_elem is not None else 'MISSING'}")
                
                unblinded_reads = session.findall(tag(unblinded_tag))
                print(f"    Unblinded reads: {len(unblinded_reads)}")
                
                for j, read in enumerate(unblinded_reads):
                    print(f"      Read {j+1}:")
                    nodule_elem = read.find(tag('noduleID'))
                    print(f"        NoduleID: {'✓' if nodule_elem is not None else '✗'} {nodule_elem.text if nodule_elem is not None else 'MISSING'}")
                    
                    char_elem = read.find(tag('characteristics'))
                    print(f"        Characteristics: {'✓' if char_elem is not None else '✗'}")
                    
                    if char_elem is not None:
                        for attr in ['confidence', 'subtlety', 'obscuration', 'reason']:
                            attr_elem = char_elem.find(tag(attr))
                            print(f"          {attr}: {'✓' if attr_elem is not None else '✗'} {attr_elem.text if attr_elem is not None else 'MISSING'}")
                    
                    roi_elems = read.findall(tag('roi'))
                    print(f"        ROIs: {len(roi_elems)}")
                    
                    if roi_elems:
                        roi = roi_elems[0]  # Check first ROI
                        sop_elem = roi.find(tag('imageSOP_UID'))
                        print(f"          SOP_UID: {'✓' if sop_elem is not None else '✗'} {sop_elem.text if sop_elem is not None else 'MISSING'}")
                        
                        edge_maps = roi.findall(tag('edgeMap'))
                        print(f"          EdgeMaps: {len(edge_maps)}")
                        
                        if edge_maps:
                            edge = edge_maps[0]
                            x_elem = edge.find(tag('xCoord'))
                            y_elem = edge.find(tag('yCoord'))
                            print(f"            X: {'✓' if x_elem is not None else '✗'} {x_elem.text if x_elem is not None else 'MISSING'}")
                            print(f"            Y: {'✓' if y_elem is not None else '✗'} {y_elem.text if y_elem is not None else 'MISSING'}")
                        else:
                            # Try single edgeMap
                            edge = roi.find(tag('edgeMap'))
                            if edge is not None:
                                x_elem = edge.find(tag('xCoord'))
                                y_elem = edge.find(tag('yCoord'))
                                print(f"            X (single): {'✓' if x_elem is not None else '✗'} {x_elem.text if x_elem is not None else 'MISSING'}")
                                print(f"            Y (single): {'✓' if y_elem is not None else '✗'} {y_elem.text if y_elem is not None else 'MISSING'}")
                            else:
                                print("            No coordinate data found")
        
    except ET.ParseError as e:
        print(f"XML Parse Error: {e}")
    except Exception as e:
        print(f"Analysis Error: {e}")

def test_parser_on_file(file_path):
    """Test our parser on a specific file and show results"""
    print(f"\n{'='*30}")
    print(f"PARSING TEST")
    print(f"{'='*30}")
    
    try:
        # Get parse case
        parse_case = detect_parse_case(file_path)
        print(f"Parse case: {parse_case}")
        
        # Parse the file
        df, unblinded_df = parse_radiology_sample(file_path)
        
        print(f"Main DataFrame rows: {len(df)}")
        print(f"Unblinded DataFrame rows: {len(unblinded_df)}")
        
        if len(df) > 0:
            print("\nMain DataFrame sample:")
            print(df.head(3).to_string())
            
            # Count N/A values
            na_counts = {}
            for col in df.columns:
                na_count = (df[col] == "#N/A").sum()
                if na_count > 0:
                    na_counts[col] = na_count
            
            if na_counts:
                print(f"\nN/A counts in main data:")
                for col, count in na_counts.items():
                    print(f"  {col}: {count}/{len(df)} ({100*count/len(df):.1f}%)")
            else:
                print("\nNo N/A values found in main data!")
        
        if len(unblinded_df) > 0:
            print(f"\nUnblinded DataFrame sample:")
            print(unblinded_df.head(3).to_string())
            
            # Count N/A values
            na_counts = {}
            for col in unblinded_df.columns:
                na_count = (unblinded_df[col] == "#N/A").sum()
                if na_count > 0:
                    na_counts[col] = na_count
            
            if na_counts:
                print(f"\nN/A counts in unblinded data:")
                for col, count in na_counts.items():
                    print(f"  {col}: {count}/{len(unblinded_df)} ({100*count/len(unblinded_df):.1f}%)")
            else:
                print("\nNo N/A values found in unblinded data!")
        
    except Exception as e:
        print(f"Parser Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    # Check if a file path was provided as argument
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        if os.path.exists(file_path):
            analyze_xml_structure(file_path)
            test_parser_on_file(file_path)
        else:
            print(f"File not found: {file_path}")
    else:
        print("Usage: python diagnostic_test.py <xml_file_path>")
        print("\nOr provide the path to folder 157 and we'll analyze the first XML file")

if __name__ == "__main__":
    main()
