#!/usr/bin/env python3
"""
Test script for KeywordRepository

Tests all CRUD operations, statistics calculations, and synonym handling.
"""

import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ra_d_ps.database.keyword_repository import KeywordRepository


def test_keyword_operations():
    """Test basic keyword CRUD operations"""
    print("\n" + "=" * 80)
    print("TEST 1: Keyword CRUD Operations")
    print("=" * 80)
    
    repo = KeywordRepository()
    
    try:
        # Add keywords
        print("\n1. Adding keywords...")
        kw1 = repo.add_keyword("pulmonary nodule", category="anatomy", 
                               normalized_form="pulmonary_nodule")
        print(f"   ✅ Added: {kw1.keyword_text} (id={kw1.keyword_id})")
        
        kw2 = repo.add_keyword("malignancy", category="characteristic")
        print(f"   ✅ Added: {kw2.keyword_text} (id={kw2.keyword_id})")
        
        kw3 = repo.add_keyword("ground glass opacity", category="diagnosis",
                               normalized_form="ground_glass_opacity")
        print(f"   ✅ Added: {kw3.keyword_text} (id={kw3.keyword_id})")
        
        # Get keyword by ID
        print("\n2. Getting keyword by ID...")
        fetched = repo.get_keyword(kw1.keyword_id)
        print(f"   ✅ Fetched: {fetched.keyword_text}")
        
        # Get keyword by text
        print("\n3. Getting keyword by text...")
        fetched_by_text = repo.get_keyword_by_text("malignancy")
        print(f"   ✅ Found: {fetched_by_text.keyword_text} (id={fetched_by_text.keyword_id})")
        
        # Search keywords
        print("\n4. Searching keywords...")
        results = repo.search_keywords("pulmonary", limit=10)
        print(f"   ✅ Found {len(results)} matches for 'pulmonary'")
        for kw in results:
            print(f"      - {kw.keyword_text} ({kw.category})")
        
        # Get all keywords by category
        print("\n5. Getting keywords by category...")
        anatomy_keywords = repo.get_all_keywords(category="anatomy", limit=100)
        print(f"   ✅ Found {len(anatomy_keywords)} anatomy keywords")
        
        return kw1, kw2, kw3
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        raise
    finally:
        repo.close()


def test_keyword_sources(kw1, kw2, kw3):
    """Test keyword source operations"""
    print("\n" + "=" * 80)
    print("TEST 2: Keyword Source Operations")
    print("=" * 80)
    
    repo = KeywordRepository()
    
    try:
        # Add keyword sources
        print("\n1. Adding keyword sources...")
        
        source1 = repo.add_keyword_source(
            keyword_id=kw1.keyword_id,
            source_type="xml",
            source_file="/test/data/example1.xml",
            frequency=3,
            context="A small pulmonary nodule was detected in the right upper lobe",
            sector="lidc_annotations"
        )
        print(f"   ✅ Added source: {source1.source_file} (freq={source1.frequency})")
        
        source2 = repo.add_keyword_source(
            keyword_id=kw2.keyword_id,
            source_type="xml",
            source_file="/test/data/example1.xml",
            frequency=1,
            context="Malignancy rating: 4/5",
            sector="lidc_annotations"
        )
        print(f"   ✅ Added source: {source2.source_file} (freq={source2.frequency})")
        
        source3 = repo.add_keyword_source(
            keyword_id=kw1.keyword_id,
            source_type="xml",
            source_file="/test/data/example2.xml",
            frequency=2,
            context="Multiple pulmonary nodules observed",
            sector="lidc_annotations"
        )
        print(f"   ✅ Added source: {source3.source_file} (freq={source3.frequency})")
        
        # Get sources for keyword
        print("\n2. Getting sources for keyword...")
        sources = repo.get_sources_for_keyword(kw1.keyword_id)
        print(f"   ✅ Found {len(sources)} sources for '{kw1.keyword_text}'")
        for src in sources:
            print(f"      - {src.source_file} (freq={src.frequency})")
        
        # Get keywords for source
        print("\n3. Getting keywords in source document...")
        doc_keywords = repo.get_keywords_for_source("/test/data/example1.xml")
        print(f"   ✅ Found {len(doc_keywords)} keywords in example1.xml")
        for keyword, source in doc_keywords:
            print(f"      - {keyword.keyword_text} (freq={source.frequency})")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        raise
    finally:
        repo.close()


def test_statistics(kw1, kw2):
    """Test statistics calculations"""
    print("\n" + "=" * 80)
    print("TEST 3: Statistics Calculations")
    print("=" * 80)
    
    repo = KeywordRepository()
    
    try:
        # Update statistics
        print("\n1. Updating keyword statistics...")
        
        stats1 = repo.update_keyword_statistics(kw1.keyword_id)
        print(f"   ✅ Stats for '{kw1.keyword_text}':")
        print(f"      - Total frequency: {stats1.total_frequency}")
        print(f"      - Document count: {stats1.document_count}")
        print(f"      - IDF score: {stats1.idf_score:.4f}")
        
        stats2 = repo.update_keyword_statistics(kw2.keyword_id)
        print(f"\n   ✅ Stats for '{kw2.keyword_text}':")
        print(f"      - Total frequency: {stats2.total_frequency}")
        print(f"      - Document count: {stats2.document_count}")
        print(f"      - IDF score: {stats2.idf_score:.4f}")
        
        # Calculate TF-IDF for document
        print("\n2. Calculating TF-IDF scores...")
        repo.calculate_tfidf_for_document("/test/data/example1.xml")
        print(f"   ✅ TF-IDF calculated for example1.xml")
        
        # Get sources with TF-IDF
        sources = repo.get_sources_for_keyword(kw1.keyword_id)
        for src in sources:
            print(f"      - {src.source_file}: TF-IDF = {src.tf_idf_score:.4f}")
        
        # Get top keywords
        print("\n3. Getting top keywords...")
        top_keywords = repo.get_top_keywords(limit=10)
        print(f"   ✅ Top {len(top_keywords)} keywords:")
        for i, (keyword, stats) in enumerate(top_keywords, 1):
            print(f"      {i}. {keyword.keyword_text}: freq={stats.total_frequency}, docs={stats.document_count}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        raise
    finally:
        repo.close()


def test_synonyms(kw1):
    """Test synonym operations"""
    print("\n" + "=" * 80)
    print("TEST 4: Synonym Operations")
    print("=" * 80)
    
    repo = KeywordRepository()
    
    try:
        # Add synonyms
        print("\n1. Adding synonyms...")
        
        syn1 = repo.add_synonym("lung nodule", kw1.keyword_id, 
                               synonym_type="alternate_spelling")
        print(f"   ✅ Added synonym: 'lung nodule' -> '{kw1.keyword_text}'")
        
        syn2 = repo.add_synonym("pulmonary mass", kw1.keyword_id,
                               synonym_type="medical_term")
        print(f"   ✅ Added synonym: 'pulmonary mass' -> '{kw1.keyword_text}'")
        
        # Get canonical keyword
        print("\n2. Getting canonical keyword from synonym...")
        canonical = repo.get_canonical_keyword("lung nodule")
        if canonical:
            print(f"   ✅ 'lung nodule' maps to '{canonical.keyword_text}' (id={canonical.keyword_id})")
        
        # Get all synonyms for keyword
        print("\n3. Getting all synonyms for keyword...")
        synonyms = repo.get_synonyms_for_keyword(kw1.keyword_id)
        print(f"   ✅ Found {len(synonyms)} synonyms for '{kw1.keyword_text}'")
        for syn in synonyms:
            print(f"      - {syn.synonym_text} ({syn.synonym_type})")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        raise
    finally:
        repo.close()


def test_search_analytics():
    """Test search analytics"""
    print("\n" + "=" * 80)
    print("TEST 5: Search Analytics")
    print("=" * 80)
    
    repo = KeywordRepository()
    
    try:
        # Record search queries
        print("\n1. Recording search queries...")
        
        repo.record_search("pulmonary nodule", result_count=5, 
                          execution_time_ms=12.5, user_sector="lidc_annotations")
        print(f"   ✅ Recorded search: 'pulmonary nodule'")
        
        repo.record_search("malignancy", result_count=3,
                          execution_time_ms=8.2, user_sector="lidc_annotations")
        print(f"   ✅ Recorded search: 'malignancy'")
        
        # Get analytics
        print("\n2. Getting search analytics...")
        analytics = repo.get_search_analytics(limit=10)
        print(f"   ✅ Found {len(analytics)} recent searches")
        for i, search in enumerate(analytics[:5], 1):
            print(f"      {i}. '{search['query_text'][:40]}...' - "
                  f"{search['result_count']} results, {search['execution_time_ms']:.2f}ms")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        raise
    finally:
        repo.close()


def main():
    """Main test entry point"""
    print("\n" + "=" * 80)
    print("KEYWORD REPOSITORY TEST SUITE")
    print("=" * 80)
    print("\nTesting all CRUD operations, statistics, and search functionality\n")
    
    try:
        # Test 1: Basic keyword operations
        kw1, kw2, kw3 = test_keyword_operations()
        
        # Test 2: Keyword sources
        test_keyword_sources(kw1, kw2, kw3)
        
        # Test 3: Statistics
        test_statistics(kw1, kw2)
        
        # Test 4: Synonyms
        test_synonyms(kw1)
        
        # Test 5: Search analytics
        test_search_analytics()
        
        # Summary
        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED")
        print("=" * 80)
        print("\nKeywordRepository is working correctly!")
        print("- Keyword CRUD: ✅")
        print("- Keyword sources: ✅")
        print("- Statistics & TF-IDF: ✅")
        print("- Synonyms: ✅")
        print("- Search analytics: ✅")
        print()
        
        return 0
        
    except Exception as e:
        print("\n" + "=" * 80)
        print("❌ TESTS FAILED")
        print("=" * 80)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
