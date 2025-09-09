"""
GUI components for the radiology data processing application
"""
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import platform
import subprocess
import os
from typing import Optional


def open_file_cross_platform(file_path):
    """Open a file using the default system application across different platforms"""
    try:
        if platform.system() == "Darwin":  # macOS
            subprocess.run(["open", file_path], check=True)
        elif platform.system() == "Windows":  # Windows
            os.startfile(file_path)
        else:  # Linux and others
            subprocess.run(["xdg-open", file_path], check=True)
    except Exception as e:
        print(f"Could not open file {file_path}: {e}")


class NYTXMLGuiApp:
    """Main GUI application for XML parsing"""
    
    def __init__(self, root):
        # ... (move implementation from parser.py)
        pass
