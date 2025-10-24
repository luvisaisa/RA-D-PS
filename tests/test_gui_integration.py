#!/usr/bin/env python3
"""
GUI Integration Test for RA-D-PS Parser
"""

import tkinter as tk
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from ra_d_ps.gui import NYTXMLGuiApp

def test_gui_buttons():
    """Test that the GUI has the new RA-D-PS export button"""
    
    print("🧪 TESTING GUI INTEGRATION")
    print("=" * 40)
    
    try:
        # Create a test window
        root = tk.Tk()
        root.withdraw()  # Hide the window
        
        # Create the app
        app = NYTXMLGuiApp(root)
        
        print("✅ GUI app created successfully")
        
        # Get all children widgets from the app
        widgets = app.master.winfo_children()
        print(f"📋 Found {len(widgets)} top-level widgets")
        
        # Check if the app has the expected buttons
        has_export_button = False
        has_sqlite_button = False
        
        def check_widgets(widget):
            nonlocal has_export_button, has_sqlite_button
            if isinstance(widget, tk.Button):
                text = widget.cget('text')
                if 'Export to Excel' in text:
                    has_export_button = True
                    print(f"✅ Found export button: '{text}'")
                elif 'SQLite' in text:
                    has_sqlite_button = True
                    print(f"✅ Found SQLite button: '{text}'")
            
            # Recursively check children
            for child in widget.winfo_children():
                check_widgets(child)
        
        # Check all widgets in the main frame
        for widget in widgets:
            check_widgets(widget)
        
        # Try importing the export functions to verify they exist
        try:
            from ra_d_ps.parser import convert_parsed_data_to_ra_d_ps_format, export_excel
            print("✅ Export functions imported successfully")
        except ImportError as e:
            print(f"❌ Failed to import export functions: {e}")
        
        print("=" * 40)
        print(f"Export button found: {'✅' if has_export_button else '❌'}")
        print(f"SQLite button found: {'✅' if has_sqlite_button else '❌'}")
        
        # Clean up
        root.destroy()
        
        return has_export_button
        
    except Exception as e:
        print(f"❌ Error during GUI test: {e}")
        return False

if __name__ == "__main__":
    success = test_gui_buttons()
    if success:
        print("\n🎉 GUI integration test PASSED")
    else:
        print("\n💥 GUI integration test FAILED")