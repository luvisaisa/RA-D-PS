#!/usr/bin/env python3
"""
Test XMLKeywordExtractor

Validates extraction from LIDC-IDRI XML files:
1. Characteristic extraction (LIDC v1 and v2 formats)
2. Diagnostic text extraction (reason field)
3. Anatomical terms extraction
4. Metadata extraction
5. Batch processing with statistics

Requirements:
- PostgreSQL running with ra_d_ps database
- Sample XML files in XML-COMP/ directory
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ra_d_ps.xml_keyword_extractor import XMLKeywordExtractor
from src.ra_d_ps.database.keyword_repository import KeywordRepository


def print_section(title):
    """Print section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def test_single_xml_extraction():
    """Test extraction from a single XML file"""
    print_section("TEST 1: Single XML File Extraction")
    
    # Find a sample XML file
    xml_comp_dir = Path("/Users/isa/Desktop/python projects/XML PARSE/examples/XML-COMP")
    xml_files = list(xml_comp_dir.glob("**/*.xml"))
    
    if not xml_files:
        print("❌ No XML files found in XML-COMP directory")
        return False
    
    sample_xml = str(xml_files[0])
    print(f"Using: {Path(sample_xml).name}")
    
    # Create extractor (without database storage for testing)
    extractor = XMLKeywordExtractor()
    
    try:
        # Extract keywords (don't store in DB yet)
        keywords = extractor.extract_from_xml(sample_xml, store_in_db=False)
        
        print(f"\n✓ Extracted {len(keywords)} total keywords")
        
        # Group by category
        by_category = {}
        for kw in keywords:
            by_category.setdefault(kw.category, []).append(kw)
        
        # Display samples from each category
        for category, kws in by_category.items():
            print(f"\n  {category.upper()}: {len(kws)} keywords")
            for kw in kws[:3]:  # Show first 3
                print(f"    - {kw.text} (freq={kw.frequency})")
                print(f"      Context: {kw.context[:80]}...")
        
        extractor.close()
        print("\n✅ TEST 1 PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_characteristic_extraction():
    """Test extraction of LIDC characteristics"""
    print_section("TEST 2: Characteristic Field Extraction")
    
    xml_comp_dir = Path("/Users/isa/Desktop/python projects/XML PARSE/examples/XML-COMP")
    xml_files = list(xml_comp_dir.glob("**/*.xml"))[:5]  # Test 5 files
    
    if not xml_files:
        print("❌ No XML files found")
        return False
    
    extractor = XMLKeywordExtractor()
    
    try:
        all_characteristics = []
        
        for xml_file in xml_files:
            keywords = extractor.extract_from_xml(str(xml_file), store_in_db=False)
            
            # Filter characteristics
            chars = [kw for kw in keywords if kw.category == 'characteristic']
            all_characteristics.extend(chars)
        
        print(f"\n✓ Extracted {len(all_characteristics)} characteristic keywords from {len(xml_files)} files")
        
        # Group by characteristic name
        char_types = {}
        for kw in all_characteristics:
            char_name = kw.text.split(':')[0] if ':' in kw.text else kw.text
            char_types[char_name] = char_types.get(char_name, 0) + 1
        
        print(f"\n  Characteristic types found:")
        for char_name, count in sorted(char_types.items(), key=lambda x: x[1], reverse=True):
            print(f"    {char_name}: {count} occurrences")
        
        extractor.close()
        print("\n✅ TEST 2 PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_diagnostic_text_extraction():
    """Test extraction from diagnostic text (reason field)"""
    print_section("TEST 3: Diagnostic Text Extraction")
    
    xml_comp_dir = Path("/Users/isa/Desktop/python projects/XML PARSE/examples/XML-COMP")
    xml_files = list(xml_comp_dir.glob("**/*.xml"))[:10]  # Test 10 files
    
    if not xml_files:
        print("❌ No XML files found")
        return False
    
    extractor = XMLKeywordExtractor()
    
    try:
        all_diagnosis = []
        
        for xml_file in xml_files:
            keywords = extractor.extract_from_xml(str(xml_file), store_in_db=False)
            
            # Filter diagnostic keywords
            diagnosis = [kw for kw in keywords if kw.category == 'diagnosis']
            all_diagnosis.extend(diagnosis)
        
        print(f"\n✓ Extracted {len(all_diagnosis)} diagnostic keywords from {len(xml_files)} files")
        
        # Show top diagnostic terms
        diagnosis_freq = {}
        for kw in all_diagnosis:
            diagnosis_freq[kw.text] = diagnosis_freq.get(kw.text, 0) + 1
        
        top_terms = sorted(diagnosis_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        
        print(f"\n  Top 10 diagnostic terms:")
        for term, freq in top_terms:
            print(f"    {term}: {freq} occurrences")
        
        extractor.close()
        print("\n✅ TEST 3 PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_anatomical_terms_extraction():
    """Test anatomical term extraction"""
    print_section("TEST 4: Anatomical Terms Extraction")
    
    xml_comp_dir = Path("/Users/isa/Desktop/python projects/XML PARSE/examples/XML-COMP")
    xml_files = list(xml_comp_dir.glob("**/*.xml"))[:10]
    
    if not xml_files:
        print("❌ No XML files found")
        return False
    
    extractor = XMLKeywordExtractor()
    
    try:
        all_anatomy = []
        
        for xml_file in xml_files:
            keywords = extractor.extract_from_xml(str(xml_file), store_in_db=False)
            
            # Filter anatomical keywords
            anatomy = [kw for kw in keywords if kw.category == 'anatomy']
            all_anatomy.extend(anatomy)
        
        print(f"\n✓ Extracted {len(all_anatomy)} anatomical keywords from {len(xml_files)} files")
        
        # Count unique terms
        unique_terms = set(kw.text for kw in all_anatomy)
        
        print(f"\n  Unique anatomical terms: {len(unique_terms)}")
        print(f"  Terms found: {', '.join(sorted(unique_terms))}")
        
        extractor.close()
        print("\n✅ TEST 4 PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 4 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database_storage():
    """Test storing keywords in database"""
    print_section("TEST 5: Database Storage")
    
    xml_comp_dir = Path("/Users/isa/Desktop/python projects/XML PARSE/examples/XML-COMP")
    xml_files = list(xml_comp_dir.glob("**/*.xml"))[:3]  # Test 3 files only
    
    if not xml_files:
        print("❌ No XML files found")
        return False
    
    # Create repository and extractor
    repo = KeywordRepository()
    extractor = XMLKeywordExtractor(keyword_repo=repo)
    
    try:
        # Extract and store keywords
        print(f"\n  Processing {len(xml_files)} files...")
        
        for i, xml_file in enumerate(xml_files, 1):
            keywords = extractor.extract_from_xml(str(xml_file), store_in_db=True)
            print(f"    File {i}: {Path(xml_file).name} - {len(keywords)} keywords")
        
        # Verify database storage
        print(f"\n  Verifying database storage...")
        
        # Create a fresh repository for verification
        verification_repo = KeywordRepository()
        
        # Get total keywords
        all_keywords = verification_repo.get_all_keywords()
        print(f"    Total keywords in DB: {len(all_keywords)}")
        
        # Get keywords by category
        for category in ['characteristic', 'diagnosis', 'anatomy', 'metadata']:
            category_kws = verification_repo.get_keywords_by_category(category)
            print(f"    {category}: {len(category_kws)} keywords")
        
        # Get top keywords by frequency
        top_keywords = verification_repo.get_top_keywords(limit=5)
        print(f"\n  Top 5 keywords by frequency:")
        for keyword, kw_stat in top_keywords:
            print(f"    {keyword.keyword_text}: {kw_stat.total_frequency} occurrences in {kw_stat.document_count} documents")
        
        extractor.close()
        verification_repo.close()
        print("\n✅ TEST 5 PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 5 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_batch_processing():
    """Test batch processing with statistics"""
    print_section("TEST 6: Batch Processing with Statistics")
    
    xml_comp_dir = Path("/Users/isa/Desktop/python projects/XML PARSE/examples/XML-COMP")
    xml_files = [str(f) for f in list(xml_comp_dir.glob("**/*.xml"))[:10]]  # Test 10 files
    
    if not xml_files:
        print("❌ No XML files found")
        return False
    
    # Create extractor
    extractor = XMLKeywordExtractor()
    
    try:
        print(f"\n  Processing {len(xml_files)} files in batch...")
        
        # Extract from multiple files
        stats = extractor.extract_from_multiple(xml_files, show_progress=True)
        
        print(f"\n✓ Batch extraction completed")
        print(f"\n  Statistics:")
        print(f"    Files processed: {stats['files_processed']}")
        print(f"    Total keywords: {stats['total_keywords']}")
        print(f"    Unique keywords: {stats['unique_keywords']}")
        print(f"    Errors: {len(stats['errors'])}")
        
        print(f"\n  Keywords by category:")
        for category, count in stats['by_category'].items():
            print(f"    {category}: {count} keywords")
        
        if stats['errors']:
            print(f"\n  Errors encountered:")
            for error in stats['errors']:
                print(f"    {error['file']}: {error['error']}")
        
        extractor.close()
        print("\n✅ TEST 6 PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 6 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("  XMLKeywordExtractor Test Suite")
    print("="*60)
    
    tests = [
        ("Single XML Extraction", test_single_xml_extraction),
        ("Characteristic Extraction", test_characteristic_extraction),
        ("Diagnostic Text Extraction", test_diagnostic_text_extraction),
        ("Anatomical Terms Extraction", test_anatomical_terms_extraction),
        ("Database Storage", test_database_storage),
        ("Batch Processing", test_batch_processing)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} CRASHED: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("  TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\n  {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED")
        return 0
    else:
        print(f"\n❌ {total - passed} TESTS FAILED")
        return 1


if __name__ == '__main__':
    sys.exit(main())
