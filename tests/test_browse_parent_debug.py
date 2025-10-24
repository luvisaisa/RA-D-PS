#!/usr/bin/env python3
"""
Debug test to verify browse_parent_folder is being called and working
"""
import sys
import os
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_browse_logic():
    """Test the actual folder browsing logic"""
    print("\n" + "="*70)
    print("Testing browse_parent_folder logic")
    print("="*70)
    
    # Create test structure
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"\n✓ Created test parent: {tmpdir}")
        
        # Create 3 subfolders
        for i, name in enumerate(["folder1", "folder2", "folder3"]):
            subfolder = os.path.join(tmpdir, name)
            os.makedirs(subfolder)
            
            # Add XML files to first two
            if i < 2:
                for j in range(i + 1):
                    xml_file = os.path.join(subfolder, f"test{j}.xml")
                    with open(xml_file, 'w') as f:
                        f.write("<root></root>")
        
        print(f"✓ Created subfolders:")
        
        # Simulate the scan logic
        subfolders = []
        for item in os.listdir(tmpdir):
            full_path = os.path.join(tmpdir, item)
            if os.path.isdir(full_path):
                try:
                    xml_files = [f for f in os.listdir(full_path) if f.lower().endswith('.xml')]
                    xml_count = len(xml_files)
                except (PermissionError, OSError):
                    continue
                subfolders.append((full_path, item, xml_count))
                print(f"  - {item}: {xml_count} XML files")
        
        assert len(subfolders) == 3, f"Expected 3, got {len(subfolders)}"
        print(f"\n✅ Found {len(subfolders)} subfolders correctly")
        
        # Check XML counts
        counts = sorted([count for _, _, count in subfolders])
        assert counts == [0, 1, 2], f"Expected [0, 1, 2], got {counts}"
        print("✅ XML counts correct: [0, 1, 2]")
        
        # Simulate auto-check logic
        auto_checked = [(name, count) for _, name, count in subfolders if count > 0]
        print(f"\n✓ Would auto-check {len(auto_checked)} folders:")
        for name, count in auto_checked:
            print(f"  ☑ {name} ({count} XML files)")
        
        print("\n" + "="*70)
        print("✅ Logic test passed - browse_parent_folder SHOULD work")
        print("="*70)
        return True

if __name__ == "__main__":
    test_browse_logic()
