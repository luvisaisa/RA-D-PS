#!/usr/bin/env python3
"""
RA-D-PS Entry Point

Simple launcher for the RA-D-PS XML parsing application.
"""
import sys
from pathlib import Path

# Add the scripts directory to path
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

def main():
    """Launch the appropriate interface based on arguments"""
    if len(sys.argv) > 1 and sys.argv[1] in ['--cli', 'cli', 'parse']:
        # Launch CLI interface
        from scripts.cli import main as cli_main
        # Remove our argument and pass the rest
        if sys.argv[1] in ['--cli', 'cli']:
            sys.argv.pop(1)
        sys.argv[0] = 'ra-d-ps'  # Clean up the command name
        cli_main()
    else:
        # Launch GUI interface
        from scripts.main import main as gui_main
        gui_main()

if __name__ == "__main__":
    main()