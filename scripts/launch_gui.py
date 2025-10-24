#!/usr/bin/env python3
"""
quick visual test to launch the simplified gui
allows manual inspection of the new 2-button interface
"""
import sys
import os

# add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import tkinter as tk
from ra_d_ps.gui import NYTXMLGuiApp


def main():
    """launch the simplified gui for visual inspection"""
    print("\n" + "="*60)
    print("launching simplified 2-button gui")
    print("="*60)
    print("\nvisual checklist:")
    print("✓ single 'select folders' button visible")
    print("✓ listbox for showing selected folders")
    print("✓ large green '1️⃣ single export' button")
    print("✓ large blue '2️⃣ multi export' button")
    print("✓ key/legend section at bottom")
    print("✓ clear and help buttons")
    print("\nclose the gui window when done inspecting")
    print("="*60 + "\n")
    
    root = tk.Tk()
    app = NYTXMLGuiApp(root)
    root.mainloop()
    
    print("\ngui closed successfully ✅")


if __name__ == "__main__":
    main()
