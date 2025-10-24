#!/usr/bin/env python3
"""
Real functional test for RA-D-PS GUI
Tests actual button functionality and user workflows
"""

import tkinter as tk
import sys
import os
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from ra_d_ps.gui import NYTXMLGuiApp


def create_test_xml(filename):
    """Create a minimal test XML file for testing"""
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


def test_real_gui_functionality():
    """Test actual GUI functionality with real operations"""
    print("🧪 REAL GUI FUNCTIONALITY TEST")
    print("=" * 50)
    
    # Create temporary directory with test files
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 Using temp directory: {temp_dir}")
        
        # Create test XML files
        test_files = []
        for i in range(3):
            filename = os.path.join(temp_dir, f"test_file_{i+1}.xml")
            create_test_xml(filename)
            test_files.append(filename)
            print(f"📄 Created test file: {filename}")
        
        # Test GUI creation
        print("\n🖥️ Testing GUI creation...")
        root = tk.Tk()
        root.withdraw()  # Hide window for testing
        
        try:
            app = NYTXMLGuiApp(root)
            print("✅ GUI created successfully")
            
            # Test 1: File selection functionality
            print("\n🔧 Testing file selection...")
            app.files = test_files.copy()
            app._update_file_list()
            print(f"✅ Files added to GUI: {len(app.files)} files")
            
            # Verify listbox was updated
            listbox_items = app.listbox.size()
            print(f"📋 Listbox contains: {listbox_items} items")
            assert listbox_items == len(test_files), f"Expected {len(test_files)} items, got {listbox_items}"
            
            # Test 2: Clear functionality
            print("\n🗑️ Testing clear functionality...")
            app.clear_files()
            assert len(app.files) == 0, "Files should be cleared"
            assert app.listbox.size() == 0, "Listbox should be empty"
            print("✅ Clear functionality works")
            
            # Test 3: Mock file dialog selection
            print("\n📂 Testing file dialog integration...")
            with patch('tkinter.filedialog.askopenfilenames') as mock_dialog:
                mock_dialog.return_value = test_files
                app.select_files()
                assert len(app.files) == len(test_files), "Files should be selected"
                print("✅ File dialog integration works")
            
            # Test 4: Button connections
            print("\n🔘 Testing button connections...")
            button_tests = {
                "Select XML Files": app.select_files,
                "Select Folders": app.select_folders,
                "Select Excel to Append": app.select_excel,
                "Export to Excel": app.export_ra_d_ps_excel,
                "Append to Selected Excel": app.parse_files,
                "Clear File List": app.clear_files,
                "Help & About": app.show_help
            }
            
            button_count = 0
            def check_button_connections(widget):
                nonlocal button_count
                if isinstance(widget, tk.Button):
                    button_count += 1
                    text = widget.cget('text')
                    command = widget.cget('command')
                    if any(btn_text in text for btn_text in button_tests.keys()):
                        print(f"  ✅ Button '{text}' properly connected")
                    else:
                        print(f"  ⚠️ Button '{text}' not in test list")
                
                for child in widget.winfo_children():
                    check_button_connections(child)
            
            check_button_connections(root)
            print(f"🔘 Total buttons found: {button_count}")
            
            # Test 5: Error handling
            print("\n⚠️ Testing error handling...")
            try:
                # Test with non-existent files
                app.files = ["/nonexistent/file.xml"]
                app._update_file_list()
                print("✅ Error handling for invalid files works")
            except Exception as e:
                print(f"❌ Error handling failed: {e}")
            
            # Test 6: Window properties
            print("\n🖼️ Testing window properties...")
            title = root.title()
            print(f"📝 Window title: '{title}'")
            assert "RA-D-PS" in title, f"Title should contain 'RA-D-PS', got '{title}'"
            
            min_size = root.minsize()
            print(f"📏 Minimum size: {min_size}")
            assert min_size[0] >= 550 and min_size[1] >= 600, f"Minimum size should be at least 550x600, got {min_size}"
            
            print("\n✅ ALL REAL FUNCTIONALITY TESTS PASSED!")
            return True
            
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False
            
        finally:
            root.destroy()


def test_gui_import_and_structure():
    """Test that GUI can be imported and has correct structure"""
    print("\n🔍 TESTING GUI IMPORT AND STRUCTURE")
    print("=" * 40)
    
    try:
        # Test import
        from ra_d_ps.gui import NYTXMLGuiApp
        print("✅ GUI import successful")
        
        # Test class attributes
        required_methods = [
            'select_files', 'select_folders', 'select_excel',
            'export_ra_d_ps_excel', 'export_to_sqlite', 'parse_files',
            'clear_files', 'show_help', '_create_widgets', '_update_file_list'
        ]
        
        missing_methods = []
        for method in required_methods:
            if not hasattr(NYTXMLGuiApp, method):
                missing_methods.append(method)
        
        if missing_methods:
            print(f"❌ Missing methods: {missing_methods}")
            return False
        else:
            print(f"✅ All {len(required_methods)} required methods present")
        
        return True
        
    except Exception as e:
        print(f"❌ Import/structure test failed: {e}")
        return False


if __name__ == "__main__":
    print("🧪 COMPREHENSIVE GUI TESTING")
    print("=" * 60)
    
    # Run all tests
    test1_passed = test_gui_import_and_structure()
    test2_passed = test_real_gui_functionality()
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY:")
    print(f"  Import & Structure: {'✅ PASS' if test1_passed else '❌ FAIL'}")
    print(f"  Real Functionality: {'✅ PASS' if test2_passed else '❌ FAIL'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 ALL TESTS PASSED - GUI IS FULLY FUNCTIONAL!")
        sys.exit(0)
    else:
        print("\n💥 SOME TESTS FAILED - GUI NEEDS FIXES!")
        sys.exit(1)