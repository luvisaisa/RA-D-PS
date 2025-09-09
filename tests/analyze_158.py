#!/usr/bin/env python3

# Test script for analyzing XML file from folder 157
import sys
import os

# Add current directory to path so we can import XMLPARSE
sys.path.append('/Users/isa/Desktop/python projects/XML PARSE')

try:
    from XMLPARSE import parse_radiology_sample, detect_parse_case, get_expected_attributes_for_case
    import xml.etree.ElementTree as ET
    
    def analyze_158_xml():
        """Analyze the 158.xml file structure"""
        xml_path = "/Volumes/LUCKY/tcia-lidc-xml/157/158.xml"
        
        if not os.path.exists(xml_path):
            print(f"❌ File not found: {xml_path}")
            return
            
        print(f"📁 Analyzing: {xml_path}")
        print("="*60)
        
        try:
            # Parse the XML to understand structure
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            print(f"Root tag: {root.tag}")
            
            # Check namespace
            import re
            m = re.match(r'\{(.*)\}', root.tag)
            ns_uri = m.group(1) if m else ''
            print(f"Namespace: {ns_uri}")
            
            def tag(name):
                return f"{{{ns_uri}}}{name}" if ns_uri else name
            
            # Check for ResponseHeader
            header = root.find(tag('ResponseHeader'))
            print(f"Has ResponseHeader: {header is not None}")
            
            # Check sessions
            root_tag_name = root.tag.split('}')[-1] if '}' in root.tag else root.tag
            is_lidc_format = root_tag_name == 'LidcReadMessage'
            session_tag = 'readingSession' if is_lidc_format else 'CXRreadingSession'
            
            print(f"Format: {'LIDC' if is_lidc_format else 'CXR'}")
            print(f"Looking for sessions: {session_tag}")
            
            sessions = root.findall(tag(session_tag))
            print(f"Sessions found: {len(sessions)}")
            
            # Analyze each session
            for i, session in enumerate(sessions):
                print(f"\n📋 Session {i+1}:")
                
                # Get radiologist
                rad_elem = session.find(tag('servicingRadiologistID'))
                rad_id = rad_elem.text if rad_elem is not None else "unknown"
                print(f"  Radiologist: {rad_id}")
                
                # Check unblinded reads
                unblinded_tag = 'unblindedReadNodule' if is_lidc_format else 'unblindedRead'
                unblinded_reads = session.findall(tag(unblinded_tag))
                print(f"  Unblinded reads: {len(unblinded_reads)}")
                
                # Analyze first few reads
                for j, read in enumerate(unblinded_reads[:3]):  # Look at first 3 reads
                    print(f"    📖 Read {j+1}:")
                    
                    # Nodule ID
                    nodule_elem = read.find(tag('noduleID'))
                    nodule_id = nodule_elem.text if nodule_elem is not None else "N/A"
                    print(f"      NoduleID: {nodule_id}")
                    
                    # Characteristics
                    char_elem = read.find(tag('characteristics'))
                    if char_elem is not None:
                        print(f"      Has characteristics: Yes")
                        for attr in ['confidence', 'subtlety', 'obscuration', 'reason']:
                            attr_elem = char_elem.find(tag(attr))
                            value = attr_elem.text if attr_elem is not None else "missing"
                            print(f"        {attr}: {value}")
                    else:
                        print(f"      Has characteristics: No")
                    
                    # ROIs and coordinates
                    rois = read.findall(tag('roi'))
                    print(f"      ROIs: {len(rois)}")
                    
                    total_coords = 0
                    for k, roi in enumerate(rois):
                        sop_elem = roi.find(tag('imageSOP_UID'))
                        sop_uid = sop_elem.text if sop_elem is not None else "N/A"
                        
                        # Count coordinates
                        edge_maps = roi.findall(tag('edgeMap'))
                        coord_count = len(edge_maps)
                        total_coords += coord_count
                        
                        if k == 0:  # Show details for first ROI
                            print(f"        ROI 1 - SOP_UID: {sop_uid[:20]}... Coordinates: {coord_count}")
                            
                            if coord_count > 0:
                                first_edge = edge_maps[0]
                                x_elem = first_edge.find(tag('xCoord'))
                                y_elem = first_edge.find(tag('yCoord'))
                                x_val = x_elem.text if x_elem is not None else "N/A"
                                y_val = y_elem.text if y_elem is not None else "N/A"
                                print(f"          First coordinate: ({x_val}, {y_val})")
                    
                    print(f"      Total coordinates this read: {total_coords}")
                    
                    if j < len(unblinded_reads) - 1:  # Don't add separator after last read
                        print()
                
                if len(unblinded_reads) > 3:
                    print(f"    ... and {len(unblinded_reads) - 3} more reads")
            
            print("\n" + "="*60)
            
            # Now test our parser
            print("🔬 TESTING OUR PARSER:")
            print("="*60)
            
            # Detect parse case
            parse_case = detect_parse_case(xml_path)
            print(f"Detected parse case: {parse_case}")
            
            # Get expected attributes
            expected = get_expected_attributes_for_case(parse_case)
            print(f"Expected attributes:")
            print(f"  Header: {expected['header']}")
            print(f"  Characteristics: {expected['characteristics']}")  
            print(f"  ROI: {expected['roi']}")
            
            # Parse the file
            print(f"\nParsing file...")
            df, unblinded_df = parse_radiology_sample(xml_path)
            
            print(f"✅ Main DataFrame: {len(df)} rows")
            print(f"✅ Unblinded DataFrame: {len(unblinded_df)} rows")
            
            if len(df) > 0:
                print(f"\nMain data sample (first 2 rows):")
                print(df.head(2).to_string())
                
                # Count MISSING vs N/A
                missing_count = (df == "MISSING").sum().sum()
                na_count = (df == "#N/A").sum().sum()
                print(f"\nMISSING values: {missing_count}")
                print(f"N/A values: {na_count}")
                
            if len(unblinded_df) > 0:
                print(f"\nUnblinded data sample (first 2 rows):")
                print(unblinded_df.head(2).to_string())
                
                # Count MISSING vs N/A
                missing_count = (unblinded_df == "MISSING").sum().sum()
                na_count = (unblinded_df == "#N/A").sum().sum()
                print(f"\nUnblinded MISSING values: {missing_count}")
                print(f"Unblinded N/A values: {na_count}")
            
        except Exception as e:
            print(f"❌ Error analyzing XML: {e}")
            import traceback
            traceback.print_exc()
    
    if __name__ == "__main__":
        analyze_158_xml()

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure XMLPARSE.py is in the current directory")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
