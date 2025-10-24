#!/usr/bin/env python3
"""
test the new multi-folder selection and preview functionality
tests both the native folder selection and tree view display
"""
import sys
import os

# add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import tkinter as tk
from ra_d_ps.gui import NYTXMLGuiApp


def test_new_folder_selection():
    """test the new folder selection dialog"""
    print("\n" + "="*70)
    print("testing new folder selection with preview")
    print("="*70)
    
    print("\n✓ features to test:")
    print("  1. multiple folder selection at once (cmd+click or shift+click)")
    print("  2. collapsible tree view showing folders and xml files")
    print("  3. xml file count displayed for each folder")
    print("  4. add another folder button")
    print("  5. clear all button")
    print("  6. confirm selection button")
    
    print("\n✓ updated help window:")
    print("  1. clear description of single export (1 file, multiple sheets)")
    print("  2. clear description of multi export (multiple files)")
    print("  3. examples showing the difference")
    
    print("\n🚀 launching gui - test these features:")
    print("  → click 'select folders' button")
    print("  → use cmd+click to select multiple folders in finder")
    print("  → verify tree view shows folders with xml file counts")
    print("  → expand/collapse folder nodes to see xml files")
    print("  → click help button to verify export descriptions")
    print("  → close gui when done testing")
    print("="*70 + "\n")
    
    root = tk.Tk()
    app = NYTXMLGuiApp(root)
    root.mainloop()
    
    print("\n✅ testing complete")


if __name__ == "__main__":
    test_new_folder_selection()
