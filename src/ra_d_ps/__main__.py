#!/usr/bin/env python3
"""
entry point for running ra_d_ps gui as a module
usage: python -m src.ra_d_ps
"""
import tkinter as tk
from .gui import NYTXMLGuiApp


def main():
    """launch the gui application"""
    root = tk.Tk()
    app = NYTXMLGuiApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
