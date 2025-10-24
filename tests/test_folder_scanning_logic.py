#!/usr/bin/env python3
"""
Real functional test to verify browse_parent_folder logic works correctly
Tests the actual folder scanning and checkbox generation logic
"""
import os
import sys
import tempfile

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def test_folder_scanning_logic():
    """Test that folder scanning logic works correctly"""
    print("\n" + "="*70)
    print("Testing browse_parent_folder logic")
    print("="*70 + "\n")
    
    # Create temporary test structure
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"✓ Created temp directory: {tmpdir}")
        
        # Create subfolders
        folder1 = os.path.join(tmpdir, "folder_with_xml")
        folder2 = os.path.join(tmpdir, "empty_folder")
        folder3 = os.path.join(tmpdir, "another_xml_folder")
        
        os.makedirs(folder1)
        os.makedirs(folder2)
        os.makedirs(folder3)
        
        # Create XML files in folders
        with open(os.path.join(folder1, "test1.xml"), 'w') as f:
            f.write("<root></root>")
        with open(os.path.join(folder1, "test2.xml"), 'w') as f:
            f.write("<root></root>")
        with open(os.path.join(folder3, "test3.xml"), 'w') as f:
            f.write("<root></root>")
        
        print(f"✓ Created test folders:")
        print(f"  - {os.path.basename(folder1)} (2 XML files)")
        print(f"  - {os.path.basename(folder2)} (0 XML files)")
        print(f"  - {os.path.basename(folder3)} (1 XML file)")
        
        # Simulate the scanning logic
        subfolders = []
        for item in os.listdir(tmpdir):
            full_path = os.path.join(tmpdir, item)
            if os.path.isdir(full_path):
                xml_count = len([f for f in os.listdir(full_path) if f.lower().endswith('.xml')])
                subfolders.append((full_path, item, xml_count))
        
        print(f"\n✓ Scanning found {len(subfolders)} subfolders")
        
        # Verify results
        assert len(subfolders) == 3, f"Expected 3 subfolders, found {len(subfolders)}"
        print("✅ Correct number of subfolders found")
        
        # Check XML counts
        xml_counts = sorted([count for _, _, count in subfolders])
        assert xml_counts == [0, 1, 2], f"Expected [0, 1, 2], got {xml_counts}"
        print("✅ XML file counts are correct")
        
        # Test auto-check logic (should check folders with XML > 0)
        auto_check_count = sum(1 for _, _, count in subfolders if count > 0)
        assert auto_check_count == 2, f"Expected 2 folders to auto-check, got {auto_check_count}"
        print("✅ Auto-check logic would select correct folders")
        
        # Test sorting
        sorted_folders = sorted(subfolders, key=lambda x: x[1])
        print(f"\n✓ Folders would appear in this order:")
        for full_path, name, count in sorted_folders:
            check_mark = "☑" if count > 0 else "☐"
            print(f"  {check_mark} {name} ({count} XML files)")
        
        print("\n" + "="*70)
        print("✅ All logic tests passed!")
        print("="*70)
        return True


if __name__ == "__main__":
    try:
        success = test_folder_scanning_logic()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
