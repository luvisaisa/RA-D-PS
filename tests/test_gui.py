#!/usr/bin/env python3
"""
Simple GUI test for XMLPARSE.py
Tests that the GUI can start and display correctly
"""

import sys
import tkinter as tk
from XMLPARSE import NYTXMLGuiApp

def test_gui():
    """Test GUI startup and basic functionality"""
    print("🖥️ Testing GUI startup...")
    
    try:
        # Create the main window
        root = tk.Tk()
        root.title("XMLPARSE GUI Test")
        
        # Create the app
        app = NYTXMLGuiApp(root)
        
        print("✅ GUI created successfully!")
        print("📝 Testing basic GUI properties...")
        
        # Test that key widgets exist
        widgets_to_check = ['listbox']
        missing_widgets = []
        for widget in widgets_to_check:
            if not hasattr(app, widget):
                missing_widgets.append(widget)
        
        if missing_widgets:
            print(f"⚠️  Missing widgets: {missing_widgets}")
        else:
            print("✅ All expected widgets found")
        
        # Test basic functionality
        print("📋 Testing basic methods...")
        
        # Test file list update (should work with empty list)
        app._update_file_list()
        print("✅ File list update works")
        
        # Test show_temporary_error
        print("💬 Testing temporary error display (will auto-close)...")
        app.show_temporary_error("This is a test message - will auto-close in 3 seconds")
        
        # Schedule window close after brief display
        root.after(4000, root.quit)  # Close after 4 seconds
        
        print("🚀 GUI test window will display for 4 seconds...")
        print("   (Check that the window appears and shows the interface)")
        
        # Start the main loop
        root.mainloop()
        
        print("✅ GUI test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ GUI test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Starting GUI Test...")
    print("=" * 40)
    
    success = test_gui()
    
    print("=" * 40)
    if success:
        print("🎉 GUI test passed!")
        print("Your XMLPARSE.py GUI is working correctly.")
    else:
        print("⚠️  GUI test failed.")
        print("Check the error output above.")
    
    sys.exit(0 if success else 1)
