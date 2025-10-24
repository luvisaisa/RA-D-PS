#!/usr/bin/env python3
"""
KeywordNormalizer Usage Examples

Quick reference for medical keyword normalization in RA-D-PS.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ra_d_ps.keyword_normalizer import KeywordNormalizer
from src.ra_d_ps.database.keyword_repository import KeywordRepository


def example_1_basic_normalization():
    """Example 1: Basic synonym and abbreviation normalization"""
    print("="*60)
    print("Example 1: Basic Normalization")
    print("="*60)
    
    normalizer = KeywordNormalizer()
    
    # Test various medical terms
    terms = [
        "lung", "lesion", "mass", "CT", "GGO", 
        "cancer", "density", "MRI", "tumor"
    ]
    
    print("\nNormalizing medical terms:")
    for term in terms:
        normalized = normalizer.normalize(term)
        print(f"  {term:15} → {normalized}")
    
    normalizer.close()


def example_2_synonym_expansion():
    """Example 2: Expand synonyms for search queries"""
    print("\n" + "="*60)
    print("Example 2: Synonym Expansion for Search")
    print("="*60)
    
    normalizer = KeywordNormalizer()
    
    # Get all synonym forms
    search_terms = ["pulmonary", "nodule", "opacity"]
    
    print("\nExpanding search terms:")
    for term in search_terms:
        forms = normalizer.get_all_forms(term)
        print(f"  {term}:")
        print(f"    → {', '.join(forms)}")
    
    normalizer.close()


def example_3_multi_word_detection():
    """Example 3: Detect multi-word medical terms"""
    print("\n" + "="*60)
    print("Example 3: Multi-Word Term Detection")
    print("="*60)
    
    normalizer = KeywordNormalizer()
    
    # Sample radiology report text
    texts = [
        "Patient has ground glass opacity in right upper lobe",
        "Pleural effusion noted with pulmonary nodule",
        "Small cell carcinoma with lymph node involvement"
    ]
    
    print("\nDetecting multi-word terms:")
    for text in texts:
        print(f"\n  Text: {text}")
        detected = normalizer.detect_multi_word_terms(text)
        print(f"  Found {len(detected)} terms:")
        for term, start, end in detected:
            print(f"    - '{term}' at position {start}-{end}")
    
    normalizer.close()


def example_4_stopword_filtering():
    """Example 4: Filter medical stopwords"""
    print("\n" + "="*60)
    print("Example 4: Stopword Filtering")
    print("="*60)
    
    normalizer = KeywordNormalizer()
    
    # Sample text with stopwords
    tokens = [
        "the", "patient", "has", "a", "large", "pulmonary", 
        "nodule", "in", "the", "right", "upper", "lobe"
    ]
    
    print(f"\nOriginal: {' '.join(tokens)}")
    
    filtered = normalizer.filter_stopwords(tokens)
    
    print(f"Filtered: {' '.join(filtered)}")
    print(f"\nRemoved {len(tokens) - len(filtered)} stopwords")
    
    normalizer.close()


def example_5_characteristic_normalization():
    """Example 5: Normalize LIDC characteristic values"""
    print("\n" + "="*60)
    print("Example 5: LIDC Characteristic Normalization")
    print("="*60)
    
    normalizer = KeywordNormalizer()
    
    # LIDC characteristic values
    characteristics = [
        ("subtlety", "1", "5"),
        ("malignancy", "1", "5"),
        ("sphericity", "1", "3"),
        ("texture", "1", "5"),
        ("calcification", "1", "6"),
    ]
    
    print("\nNormalizing LIDC values:")
    for char, min_val, max_val in characteristics:
        print(f"\n  {char.upper()}:")
        for val in ["1", "3", "5"]:
            if int(val) <= int(max_val):
                desc = normalizer.normalize_characteristic_value(char, val)
                print(f"    {val} → {desc}")
    
    normalizer.close()


def example_6_anatomical_terms():
    """Example 6: Get anatomical term lists"""
    print("\n" + "="*60)
    print("Example 6: Anatomical Terms by Region")
    print("="*60)
    
    normalizer = KeywordNormalizer()
    
    # Get terms by anatomical region
    regions = ["lobes", "airways", "vasculature", "lymph_nodes"]
    
    print("\nAnatomical terms by region:")
    for region in regions:
        terms = normalizer.get_anatomical_terms(region)
        print(f"\n  {region.upper()} ({len(terms)} terms):")
        print(f"    {', '.join(terms[:5])}...")
    
    normalizer.close()


def example_7_diagnostic_terms():
    """Example 7: Get diagnostic term lists"""
    print("\n" + "="*60)
    print("Example 7: Diagnostic Terms by Category")
    print("="*60)
    
    normalizer = KeywordNormalizer()
    
    # Get terms by diagnostic category
    categories = ["benign", "malignant", "infectious", "inflammatory"]
    
    print("\nDiagnostic terms by category:")
    for category in categories:
        terms = normalizer.get_diagnostic_terms(category)
        print(f"\n  {category.upper()} ({len(terms)} terms):")
        print(f"    {', '.join(terms[:5])}...")
    
    normalizer.close()


def example_8_batch_processing():
    """Example 8: Batch normalize keywords"""
    print("\n" + "="*60)
    print("Example 8: Batch Normalization")
    print("="*60)
    
    normalizer = KeywordNormalizer()
    
    # Batch of keywords to normalize
    keywords = [
        "lung", "lesion", "CT", "mass", "GGO", 
        "cancer", "density", "tumor", "MRI", "nodule",
        "opacity", "calcification", "ground glass"
    ]
    
    print(f"\nNormalizing {len(keywords)} keywords in batch:")
    
    normalized = normalizer.normalize_batch(keywords)
    
    # Show unique normalizations
    unique_normalized = set(normalized.values())
    print(f"\nResult: {len(unique_normalized)} unique canonical forms")
    
    # Group by canonical form
    canonical_groups = {}
    for orig, canonical in normalized.items():
        canonical_groups.setdefault(canonical, []).append(orig)
    
    print("\nGrouped by canonical form:")
    for canonical, originals in sorted(canonical_groups.items())[:5]:
        print(f"  {canonical}: {', '.join(originals)}")
    
    normalizer.close()


def example_9_database_integration():
    """Example 9: Integrate with KeywordRepository"""
    print("\n" + "="*60)
    print("Example 9: Database Integration")
    print("="*60)
    
    try:
        # Create normalizer with database connection
        repo = KeywordRepository()
        normalizer = KeywordNormalizer(keyword_repo=repo)
        
        print("\n✓ Connected to database")
        print("  Normalizer will use database synonyms if available")
        
        # Test normalization (will check database first)
        test_terms = ["pulmonary", "nodule", "malignancy"]
        
        print("\nNormalizing with database lookup:")
        for term in test_terms:
            normalized = normalizer.normalize(term)
            print(f"  {term} → {normalized}")
        
        normalizer.close()
        repo.close()
        
    except Exception as e:
        print(f"\n✗ Database connection failed: {e}")
        print("  Using dictionary-only normalization")


def example_10_quality_descriptors():
    """Example 10: Get quality descriptor terms"""
    print("\n" + "="*60)
    print("Example 10: Quality Descriptors")
    print("="*60)
    
    normalizer = KeywordNormalizer()
    
    # Get quality descriptors
    categories = ["size", "shape", "density", "margin"]
    
    print("\nQuality descriptors by category:")
    for category in categories:
        descriptors = normalizer.get_quality_descriptors(category)
        print(f"\n  {category.upper()} ({len(descriptors)} terms):")
        print(f"    {', '.join(descriptors[:5])}...")
    
    normalizer.close()


if __name__ == '__main__':
    print("\nKeywordNormalizer Usage Examples")
    print("="*60 + "\n")
    
    # Run all examples
    try:
        example_1_basic_normalization()
        example_2_synonym_expansion()
        example_3_multi_word_detection()
        example_4_stopword_filtering()
        example_5_characteristic_normalization()
        example_6_anatomical_terms()
        example_7_diagnostic_terms()
        example_8_batch_processing()
        example_9_database_integration()
        example_10_quality_descriptors()
        
        print("\n" + "="*60)
        print("✅ All examples completed successfully!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
