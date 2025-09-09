#!/usr/bin/env python3
"""
Command-line interface for RA-D-PS
"""
import argparse
import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from ra_d_ps import parse_multiple, export_excel, convert_parsed_data_to_ra_d_ps_format, NYTXMLGuiApp
except ImportError:
    # Fallback to original modules
    from XMLPARSE import parse_multiple, export_excel, convert_parsed_data_to_ra_d_ps_format, NYTXMLGuiApp
import tkinter as tk


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="RA-D-PS: Radiology XML Data Processing System")
    parser.add_argument("--version", action="version", version="RA-D-PS 1.0.0")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # GUI command
    gui_parser = subparsers.add_parser("gui", help="Launch GUI interface")
    
    # Parse command
    parse_parser = subparsers.add_parser("parse", help="Parse XML files")
    parse_parser.add_argument("input_dir", help="Directory containing XML files")
    parse_parser.add_argument("--output", "-o", help="Output Excel file", default="output.xlsx")
    parse_parser.add_argument("--format", choices=["ra-d-ps", "standard"], default="ra-d-ps", 
                             help="Output format")
    
    args = parser.parse_args()
    
    if args.command == "gui" or args.command is None:
        # Launch GUI
        root = tk.Tk()
        app = NYTXMLGuiApp(root)
        root.mainloop()
    
    elif args.command == "parse":
        # CLI parsing
        try:
            print(f"Parsing XML files from {args.input_dir}...")
            data = parse_multiple(args.input_dir)
            
            if args.format == "ra-d-ps":
                formatted_data = convert_parsed_data_to_ra_d_ps_format(data)
            else:
                formatted_data = data
                
            export_excel(formatted_data, args.output)
            print(f"Output saved to {args.output}")
            
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
