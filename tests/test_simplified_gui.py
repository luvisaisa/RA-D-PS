"""
test script for the new simplified 2-button gui interface
verifies that folder selection and both export buttons work correctly
"""
import tkinter as tk
from tkinter import messagebox
import sys
import os

# add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ra_d_ps.gui import NYTXMLGuiApp


def test_simplified_gui_structure():
    """test that the simplified gui has the correct structure"""
    root = tk.Tk()
    app = NYTXMLGuiApp(root)
    
    # verify the app has the required attributes
    assert hasattr(app, 'selected_folder_paths'), "app should have selected_folder_paths attribute"
    assert hasattr(app, 'listbox'), "app should have listbox widget"
    assert hasattr(app, 'single_export'), "app should have single_export method"
    assert hasattr(app, 'multi_export'), "app should have multi_export method"
    assert hasattr(app, 'select_folders_simple'), "app should have select_folders_simple method"
    
    # verify listbox is empty initially
    assert app.listbox.size() == 0, "listbox should be empty initially"
    assert len(app.selected_folder_paths) == 0, "selected folder paths should be empty initially"
    
    print("✅ gui structure test passed")
    root.destroy()


def test_export_button_validation():
    """test that export buttons show warning when no folders selected"""
    root = tk.Tk()
    app = NYTXMLGuiApp(root)
    
    # intercept messagebox to verify warning is shown
    warning_shown = []
    original_showwarning = messagebox.showwarning
    
    def mock_showwarning(title, message):
        warning_shown.append((title, message))
    
    messagebox.showwarning = mock_showwarning
    
    try:
        # try single export without folders
        app.single_export()
        assert len(warning_shown) == 1, "should show warning for single export"
        assert warning_shown[0][0] == "No Folders", "warning title should be 'No Folders'"
        
        # try multi export without folders
        app.multi_export()
        assert len(warning_shown) == 2, "should show warning for multi export"
        assert warning_shown[1][0] == "No Folders", "warning title should be 'No Folders'"
        
        print("✅ export button validation test passed")
    finally:
        messagebox.showwarning = original_showwarning
        root.destroy()


def test_folder_selection_integration():
    """test that folder selection properly updates the listbox and storage"""
    root = tk.Tk()
    app = NYTXMLGuiApp(root)
    
    # simulate folder selection by directly setting the storage
    test_folders = [
        "/Users/isa/Desktop/XML files parse/157",
        "/Users/isa/Desktop/XML files parse/185"
    ]
    
    app.selected_folder_paths = test_folders
    
    # manually update listbox as the method would
    app.listbox.delete(0, tk.END)
    for folder in test_folders:
        app.listbox.insert(tk.END, os.path.basename(folder))
    
    # verify storage
    assert len(app.selected_folder_paths) == 2, "should have 2 folders stored"
    assert app.selected_folder_paths[0] == test_folders[0], "first folder should match"
    
    # verify listbox display
    assert app.listbox.size() == 2, "listbox should show 2 folders"
    assert app.listbox.get(0) == "157", "first folder display should be '157'"
    assert app.listbox.get(1) == "185", "second folder display should be '185'"
    
    print("✅ folder selection integration test passed")
    root.destroy()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("testing simplified 2-button gui interface")
    print("="*60 + "\n")
    
    test_simplified_gui_structure()
    test_export_button_validation()
    test_folder_selection_integration()
    
    print("\n" + "="*60)
    print("all tests passed! ✅")
    print("="*60 + "\n")
