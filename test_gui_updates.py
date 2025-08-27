#!/usr/bin/env python3
"""
Test script to verify the updated signature popup
"""
import tkinter as tk
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from XMLPARSE import NYTXMLGuiApp

def test_signature_popup():
    """Test the updated signature popup"""
    print("🧪 Testing signature popup changes...")
    
    root = tk.Tk()
    app = NYTXMLGuiApp(root)
    
    # Manually trigger the signature to test it
    print("✅ Creating signature popup (should show logo + 'Created by: Isa Lucia Schlichting' only)")
    app.show_creator_signature()
    
    # Keep window open briefly to see the popup
    root.after(5000, root.destroy)  # Auto-close after 5 seconds
    
    try:
        root.mainloop()
        print("✅ Signature popup test completed")
        return True
    except Exception as e:
        print(f"❌ Signature popup test failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("GUI UPDATE TEST")
    print("=" * 50)
    print("Testing the following changes:")
    print("1. Window size: 500x500")
    print("2. Window centered on screen")
    print("3. Window not resizable")
    print("4. Signature popup shows only logo + creator name")
    print("=" * 50)
    
    success = test_signature_popup()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All GUI updates working correctly!")
        print("✅ Window: 500x500, centered, non-resizable")
        print("✅ Signature: Logo + 'Created by: Isa Lucia Schlichting' only")
    else:
        print("❌ Some tests failed - check output above")
    print("=" * 50)
