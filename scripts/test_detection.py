#!/usr/bin/env python3
"""
Test script for database-driven parse case detection
"""

import sys
import logging
from pathlib import Path
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ra_d_ps.structure_detector import XMLStructureDetector

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_database_connection():
    """Test 1: Database connection and initialization"""
    print("\n" + "=" * 70)
    print("Test 1: Database Connection")
    print("=" * 70)
    
    try:
        detector = XMLStructureDetector(use_database=True)
        
        if detector.use_database:
            print("✅ Database connection successful")
            print(f"   Repository: {detector._repository}")
            print(f"   Cache TTL: {detector.cache_ttl}s")
        else:
            print("⚠️  Database not available, using fallback")
        
        detector.close()
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def test_parse_case_loading():
    """Test 2: Load parse cases from database"""
    print("\n" + "=" * 70)
    print("Test 2: Parse Case Loading")
    print("=" * 70)
    
    try:
        detector = XMLStructureDetector(use_database=True)
        
        if not detector.use_database:
            print("⚠️  Skipping (database not available)")
            return True
        
        # Load parse cases
        parse_cases = detector._get_parse_cases_from_db()
        
        print(f"\n✅ Loaded {len(parse_cases)} parse cases from database")
        print("\n   Parse Cases (by priority):")
        print("   " + "-" * 66)
        
        for case in parse_cases[:5]:  # Show first 5
            print(f"   {case.name:30s} | Priority: {case.detection_priority:3d} | {case.format_type}")
        
        if len(parse_cases) > 5:
            print(f"   ... and {len(parse_cases) - 5} more")
        
        # Test cache
        print("\n   Testing cache...")
        start = time.time()
        parse_cases_cached = detector._get_parse_cases_from_db()
        cache_time = (time.time() - start) * 1000
        
        print(f"   ✅ Cache working (retrieval time: {cache_time:.2f}ms)")
        
        detector.close()
        return True
        
    except Exception as e:
        print(f"❌ Parse case loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_detection_with_xml(xml_path: str = None):
    """Test 3: Detect structure type for XML file"""
    print("\n" + "=" * 70)
    print("Test 3: XML Structure Detection")
    print("=" * 70)
    
    # Find a test XML file
    if xml_path is None:
        # Try to find examples/XML-COMP/157/158.xml (LIDC v2 format)
        workspace_path = Path("/Users/isa/Desktop/python projects/XML PARSE")
        test_paths = [
            workspace_path / "examples" / "XML-COMP" / "157" / "158.xml",
            workspace_path / "examples" / "sample.xml"
        ]
        for path in test_paths:
            if path.exists():
                xml_path = str(path)
                break
    
    if xml_path is None or not Path(xml_path).exists():
        print("⚠️  No test XML file found, skipping")
        return True
    
    print(f"\n📄 Testing with: {Path(xml_path).name}")
    
    try:
        # Test with database
        print("\n   With database:")
        detector_db = XMLStructureDetector(use_database=True)
        
        start = time.time()
        parse_case_db = detector_db.detect_structure_type(xml_path, record_detection=True)
        detection_time_db = (time.time() - start) * 1000
        
        print(f"   ✅ Parse case: {parse_case_db}")
        print(f"   ⏱️  Detection time: {detection_time_db:.2f}ms")
        
        # Get case info from database
        case_info = detector_db.get_parse_case_info(parse_case_db)
        print(f"   📋 Description: {case_info.get('description', 'N/A')}")
        print(f"   🏷️  Format type: {case_info.get('format_type', 'N/A')}")
        print(f"   🔢 Priority: {case_info.get('detection_priority', 'N/A')}")
        
        # Test cache hit
        print("\n   Testing cache (2nd detection):")
        start = time.time()
        parse_case_cached = detector_db.detect_structure_type(xml_path, record_detection=False)
        cache_time = (time.time() - start) * 1000
        
        print(f"   ✅ Parse case: {parse_case_cached}")
        print(f"   ⚡ Cache hit time: {cache_time:.2f}ms (speedup: {detection_time_db/cache_time:.1f}x)")
        
        detector_db.close()
        
        # Test without database (fallback)
        print("\n   Without database (fallback):")
        detector_fallback = XMLStructureDetector(use_database=False)
        
        start = time.time()
        parse_case_fallback = detector_fallback.detect_structure_type(xml_path)
        fallback_time = (time.time() - start) * 1000
        
        print(f"   ✅ Parse case: {parse_case_fallback}")
        print(f"   ⏱️  Detection time: {fallback_time:.2f}ms")
        
        # Compare results
        if parse_case_db == parse_case_fallback:
            print("\n   ✅ Database and fallback results match!")
        else:
            print(f"\n   ⚠️  Results differ: DB={parse_case_db}, Fallback={parse_case_fallback}")
        
        detector_fallback.close()
        return True
        
    except Exception as e:
        print(f"❌ Detection failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_lidc_v2_detection():
    """Test 4: Specifically test LIDC v2 detection"""
    print("\n" + "=" * 70)
    print("Test 4: LIDC v2 Format Detection")
    print("=" * 70)
    
    # Look for XML-COMP files
    workspace_path = Path("/Users/isa/Desktop/python projects/XML PARSE")
    xml_comp_path = workspace_path / "examples" / "XML-COMP"
    if not xml_comp_path.exists():
        print("⚠️  examples/XML-COMP directory not found, skipping")
        return True
    # Find XML files in examples/XML-COMP
    xml_files = list(xml_comp_path.rglob("*.xml"))[:5]  # Test first 5 files
    
    if not xml_files:
        print("⚠️  No XML files found in XML-COMP, skipping")
        return True
    
    print(f"\n📂 Testing {len(xml_files)} files from XML-COMP:")
    
    try:
        detector = XMLStructureDetector(use_database=True)
        
        v2_count = 0
        for xml_file in xml_files:
            parse_case = detector.detect_structure_type(str(xml_file))
            marker = "🆕" if parse_case == "LIDC_v2_Standard" else "  "
            print(f"   {marker} {xml_file.name:20s} -> {parse_case}")
            
            if parse_case == "LIDC_v2_Standard":
                v2_count += 1
        
        print(f"\n   📊 LIDC v2 files detected: {v2_count}/{len(xml_files)}")
        
        if v2_count > 0:
            print("   ✅ LIDC v2 detection working!")
        else:
            print("   ℹ️  No LIDC v2 files found in sample")
        
        detector.close()
        return True
        
    except Exception as e:
        print(f"❌ LIDC v2 detection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("Database-Driven Parse Case Detection Tests")
    print("=" * 70)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Parse Case Loading", test_parse_case_loading),
        ("XML Structure Detection", test_detection_with_xml),
        ("LIDC v2 Detection", test_lidc_v2_detection)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            logger.error(f"Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status:10s} {test_name}")
    
    print("\n" + "-" * 70)
    print(f"   Total: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    print("=" * 70)
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
