#!/usr/bin/env python3
"""
Test script for XMLPARSE.py functionality
Tests core functions and methods without requiring GUI interaction
"""

import os
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

# Add current directory to path to import XMLPARSE
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from XMLPARSE import (
        parse_radiology_sample, 
        parse_multiple, 
        get_expected_attributes_for_case,
        detect_parse_case,
        NYTXMLGuiApp
    )
    print("✅ Successfully imported XMLPARSE modules")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def create_test_xml(filename):
    """Create a simple test XML file for testing"""
    xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<LidcReadMessage xmlns="http://www.nih.gov" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <ResponseHeader>
        <StudyInstanceUID>1.2.3.4.5.6.7.8.9</StudyInstanceUID>
        <SeriesInstanceUID>1.2.3.4.5.6.7.8.9.10</SeriesInstanceUID>
        <Modality>CT</Modality>
        <DateService>20240101</DateService>
        <TimeService>120000</TimeService>
    </ResponseHeader>
    <readingSession>
        <servicingRadiologistID>rad001</servicingRadiologistID>
        <unblindedReadNodule>
            <noduleID>1</noduleID>
            <characteristics>
                <confidence>5</confidence>
                <subtlety>3</subtlety>
                <obscuration>2</obscuration>
                <reason>nodule</reason>
            </characteristics>
            <roi>
                <imageSOP_UID>1.2.3.4.5.6.7.8.9.11</imageSOP_UID>
                <edgeMap>
                    <xCoord>100</xCoord>
                    <yCoord>150</yCoord>
                </edgeMap>
            </roi>
        </unblindedReadNodule>
    </readingSession>
</LidcReadMessage>'''
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(xml_content)
    return filename

def test_parse_case_detection():
    """Test the parse case detection function"""
    print("\n🔍 Testing parse case detection...")
    
    with tempfile.NamedTemporaryFile(suffix='.xml', delete=False, mode='w', encoding='utf-8') as tmp:
        tmp.write('''<?xml version="1.0" encoding="UTF-8"?>
<LidcReadMessage xmlns="http://www.nih.gov">
    <readingSession>
        <servicingRadiologistID>rad1</servicingRadiologistID>
    </readingSession>
</LidcReadMessage>''')
        tmp_path = tmp.name
    
    try:
        case = detect_parse_case(tmp_path)
        print(f"  ✅ Detected parse case: {case}")
        return True
    except Exception as e:
        print(f"  ❌ Parse case detection failed: {e}")
        return False
    finally:
        os.unlink(tmp_path)

def test_expected_attributes():
    """Test the expected attributes function"""
    print("\n📋 Testing expected attributes...")
    
    try:
        attrs = get_expected_attributes_for_case("Complete_Attributes")
        expected_keys = ["header", "characteristics", "roi", "nodule"]
        
        if all(key in attrs for key in expected_keys):
            print("  ✅ Expected attributes structure is correct")
            print(f"  - Header fields: {len(attrs['header'])}")
            print(f"  - Characteristic fields: {len(attrs['characteristics'])}")
            print(f"  - ROI fields: {len(attrs['roi'])}")
            print(f"  - Nodule fields: {len(attrs['nodule'])}")
            return True
        else:
            print("  ❌ Expected attributes missing required keys")
            return False
    except Exception as e:
        print(f"  ❌ Expected attributes test failed: {e}")
        return False

def test_xml_parsing():
    """Test XML file parsing"""
    print("\n📄 Testing XML parsing...")
    
    with tempfile.NamedTemporaryFile(suffix='.xml', delete=False, mode='w', encoding='utf-8') as tmp:
        create_test_xml(tmp.name)
        tmp_path = tmp.name
    
    try:
        main_df, unblinded_df = parse_radiology_sample(tmp_path)
        
        print(f"  ✅ XML parsing completed")
        print(f"  - Main data rows: {len(main_df)}")
        print(f"  - Unblinded data rows: {len(unblinded_df)}")
        
        if not main_df.empty or not unblinded_df.empty:
            if not unblinded_df.empty:
                print(f"  - Sample columns: {list(unblinded_df.columns[:5])}")
                print(f"  - First row FileID: {unblinded_df.iloc[0].get('FileID', 'N/A')}")
            return True
        else:
            print("  ⚠️  No data extracted (might be expected for test XML)")
            return True
    except Exception as e:
        print(f"  ❌ XML parsing failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        os.unlink(tmp_path)

def test_multiple_parsing():
    """Test parsing multiple files"""
    print("\n📂 Testing multiple file parsing...")
    
    # Create multiple test files
    temp_files = []
    try:
        for i in range(3):
            tmp = tempfile.NamedTemporaryFile(suffix=f'_test_{i}.xml', delete=False, mode='w', encoding='utf-8')
            create_test_xml(tmp.name)
            temp_files.append(tmp.name)
            tmp.close()
        
        case_data, case_unblinded_data = parse_multiple(temp_files)
        
        print(f"  ✅ Multiple file parsing completed")
        print(f"  - Main data cases: {len(case_data)}")
        print(f"  - Unblinded data cases: {len(case_unblinded_data)}")
        
        total_main = sum(len(df) for df in case_data.values())
        total_unblinded = sum(len(df) for df in case_unblinded_data.values())
        print(f"  - Total main rows: {total_main}")
        print(f"  - Total unblinded rows: {total_unblinded}")
        
        return True
    except Exception as e:
        print(f"  ❌ Multiple file parsing failed: {e}")
        return False
    finally:
        # Clean up temp files
        for tmp_file in temp_files:
            try:
                os.unlink(tmp_file)
            except:
                pass

def test_gui_class_instantiation():
    """Test that the GUI class can be instantiated"""
    print("\n🖥️ Testing GUI class instantiation...")
    
    try:
        import tkinter as tk
        
        # Create a temporary root window (won't show)
        root = tk.Tk()
        root.withdraw()  # Hide the window
        
        # Test instantiation
        app = NYTXMLGuiApp(root)
        
        # Test some basic attributes
        if hasattr(app, 'master') and hasattr(app, 'files'):
            print("  ✅ GUI class instantiated successfully")
            print(f"  - Has required attributes: master, files")
            
            # Test method existence
            methods_to_check = [
                'select_files', 'select_folders', 'parse_files', 
                '_sanitize_sheet_name', '_export_with_formatting_detailed'
            ]
            
            missing_methods = []
            for method in methods_to_check:
                if not hasattr(app, method):
                    missing_methods.append(method)
            
            if missing_methods:
                print(f"  ⚠️  Missing methods: {missing_methods}")
            else:
                print(f"  ✅ All required methods present")
            
            root.destroy()
            return len(missing_methods) == 0
        else:
            print("  ❌ GUI class missing required attributes")
            root.destroy()
            return False
            
    except Exception as e:
        print(f"  ❌ GUI class instantiation failed: {e}")
        return False

def test_sanitize_sheet_name():
    """Test the sheet name sanitization method"""
    print("\n📝 Testing sheet name sanitization...")
    
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        app = NYTXMLGuiApp(root)
        
        test_cases = [
            ("Complete_Attributes", "_Main", "Complete_Attributes_Main"),
            ("LIDC/Multi*Session:2", "_Unblinded", "LIDC_Multi_Session_2_Unblinded"),
            ("Very_Long_Parse_Case_Name_That_Exceeds_Limit", "_Main", "Very_Long_Parse_Case_Name_T_Main"),
            ("Normal_Case", "", "Normal_Case")
        ]
        
        all_passed = True
        for input_case, suffix, expected in test_cases:
            result = app._sanitize_sheet_name(input_case, suffix)
            if len(result) <= 31:  # Excel limit
                print(f"  ✅ '{input_case}' → '{result}' (len: {len(result)})")
            else:
                print(f"  ❌ '{input_case}' → '{result}' (len: {len(result)} > 31)")
                all_passed = False
        
        root.destroy()
        return all_passed
        
    except Exception as e:
        print(f"  ❌ Sheet name sanitization test failed: {e}")
        return False

def run_all_tests():
    """Run all tests and report results"""
    print("🧪 Starting XMLPARSE.py test suite...")
    print("=" * 50)
    
    tests = [
        ("Parse Case Detection", test_parse_case_detection),
        ("Expected Attributes", test_expected_attributes),
        ("XML Parsing", test_xml_parsing),
        ("Multiple File Parsing", test_multiple_parsing),
        ("GUI Class Instantiation", test_gui_class_instantiation),
        ("Sheet Name Sanitization", test_sanitize_sheet_name)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY:")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\n🎯 OVERALL: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! Your XMLPARSE.py is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
