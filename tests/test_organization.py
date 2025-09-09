#!/usr/bin/env python3
"""
Test basic functionality of the reorganized RA-D-PS package
"""

import sys
import os
from pathlib import Path

# Add both old and new paths for compatibility
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.dirname(__file__) + '/..')

def test_package_import():
    """Test that we can import the package"""
    try:
        import ra_d_ps
        print("✅ ra_d_ps package imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import ra_d_ps: {e}")
        return False

def test_parser_import():
    """Test that we can import parser functions"""
    try:
        from ra_d_ps import parse_radiology_sample, NYTXMLGuiApp
        print("✅ Parser functions imported successfully from ra_d_ps")
        return True
    except ImportError as e:
        print(f"❌ Failed to import parser functions: {e}")
        return False

def test_backward_compatibility():
    """Test that old imports still work"""
    try:
        from XMLPARSE import parse_radiology_sample, NYTXMLGuiApp
        print("✅ Backward compatibility maintained")
        return True
    except ImportError as e:
        print(f"❌ Backward compatibility broken: {e}")
        return False

def test_cli_functionality():
    """Test CLI can be imported"""
    try:
        # Import CLI module
        sys.path.insert(0, Path(__file__).parent.parent)
        import cli
        print("✅ CLI module imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import CLI: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Running RA-D-PS organization tests...\n")
    
    tests = [
        test_package_import,
        test_parser_import, 
        test_backward_compatibility,
        test_cli_functionality
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All organization tests passed!")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed - see details above")
        sys.exit(1)
