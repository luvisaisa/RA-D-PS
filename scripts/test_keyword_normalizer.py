#!/usr/bin/env python3
"""
Test KeywordNormalizer

Validates medical keyword normalization:
1. Synonym mapping
2. Abbreviation expansion
3. Multi-word term detection
4. Stopword filtering
5. Characteristic value normalization
6. Batch normalization

Requirements:
- data/medical_terms.json must exist
- PostgreSQL optional (for database synonym lookups)
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ra_d_ps.keyword_normalizer import KeywordNormalizer


def print_section(title):
    """Print section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def test_synonym_mapping():
    """Test synonym normalization"""
    print_section("TEST 1: Synonym Mapping")
    
    normalizer = KeywordNormalizer()
    
    # Test synonym mapping
    test_cases = [
        ("lung", "pulmonary"),
        ("lesion", "nodule"),
        ("mass", "nodule"),
        ("tumor", "nodule"),
        ("cancer", "malignancy"),
        ("density", "opacity"),
        ("ground glass", "ground glass"),  # Should map to itself if canonical
    ]
    
    print("\n  Testing synonym mappings:")
    passed = 0
    for input_word, expected in test_cases:
        result = normalizer.normalize(input_word)
        status = "✓" if result == expected else "✗"
        print(f"    {status} '{input_word}' → '{result}' (expected: '{expected}')")
        if result == expected:
            passed += 1
    
    normalizer.close()
    
    if passed == len(test_cases):
        print(f"\n✅ TEST 1 PASSED ({passed}/{len(test_cases)} mappings correct)")
        return True
    else:
        print(f"\n❌ TEST 1 FAILED ({passed}/{len(test_cases)} mappings correct)")
        return False


def test_abbreviation_expansion():
    """Test abbreviation expansion"""
    print_section("TEST 2: Abbreviation Expansion")
    
    normalizer = KeywordNormalizer()
    
    # Test abbreviations
    test_cases = [
        ("CT", "computed tomography"),
        ("MRI", "magnetic resonance imaging"),
        ("GGO", "ground glass opacity"),
        ("GGN", "ground glass nodule"),
        ("NSCLC", "non-small cell lung cancer"),
        ("PET", "positron emission tomography"),
    ]
    
    print("\n  Testing abbreviation expansion:")
    passed = 0
    for abbr, expected in test_cases:
        result = normalizer.normalize(abbr, expand_abbreviations=True)
        status = "✓" if result == expected else "✗"
        print(f"    {status} '{abbr}' → '{result}' (expected: '{expected}')")
        if result == expected:
            passed += 1
    
    normalizer.close()
    
    if passed == len(test_cases):
        print(f"\n✅ TEST 2 PASSED ({passed}/{len(test_cases)} expansions correct)")
        return True
    else:
        print(f"\n❌ TEST 2 FAILED ({passed}/{len(test_cases)} expansions correct)")
        return False


def test_synonym_expansion():
    """Test getting all synonym forms"""
    print_section("TEST 3: Synonym Expansion")
    
    normalizer = KeywordNormalizer()
    
    # Test synonym expansion
    test_cases = [
        ("pulmonary", {"pulmonary", "lung", "pneumonic", "pulmonic"}),
        ("nodule", {"nodule", "lesion", "mass", "growth", "tumor"}),
        ("opacity", {"opacity", "density", "attenuation", "opacification"}),
    ]
    
    print("\n  Testing synonym expansion:")
    passed = 0
    for word, expected_set in test_cases:
        result = normalizer.get_all_forms(word)
        result_set = set(result)
        
        if result_set == expected_set:
            print(f"    ✓ '{word}' → {len(result)} forms: {', '.join(sorted(result_set)[:3])}...")
            passed += 1
        else:
            print(f"    ✗ '{word}' → {result_set} (expected: {expected_set})")
    
    normalizer.close()
    
    if passed == len(test_cases):
        print(f"\n✅ TEST 3 PASSED ({passed}/{len(test_cases)} expansions correct)")
        return True
    else:
        print(f"\n❌ TEST 3 FAILED ({passed}/{len(test_cases)} expansions correct)")
        return False


def test_multi_word_detection():
    """Test multi-word term detection"""
    print_section("TEST 4: Multi-Word Term Detection")
    
    normalizer = KeywordNormalizer()
    
    # Test text with multi-word terms
    text = "Patient has ground glass opacity in the right upper lobe with pleural effusion"
    
    detected = normalizer.detect_multi_word_terms(text)
    
    print(f"\n  Testing text: '{text}'")
    print(f"\n  Detected {len(detected)} multi-word terms:")
    for term, start, end in detected:
        print(f"    - '{term}' at position {start}-{end}")
    
    # Check if expected terms were found
    expected_terms = {"ground glass opacity", "right upper lobe", "pleural effusion", "upper lobe"}
    found_terms = {term for term, _, _ in detected}
    
    if expected_terms.issubset(found_terms):
        print(f"\n✅ TEST 4 PASSED (found {len(detected)} terms including expected ones)")
        normalizer.close()
        return True
    else:
        missing = expected_terms - found_terms
        print(f"\n❌ TEST 4 FAILED (missing terms: {missing})")
        normalizer.close()
        return False


def test_stopword_filtering():
    """Test stopword filtering"""
    print_section("TEST 5: Stopword Filtering")
    
    normalizer = KeywordNormalizer()
    
    # Test tokens with stopwords
    tokens = ["the", "patient", "has", "a", "pulmonary", "nodule", "in", "the", "lung"]
    
    filtered = normalizer.filter_stopwords(tokens)
    
    print(f"\n  Original tokens: {tokens}")
    print(f"  Filtered tokens: {filtered}")
    
    # Expected content words
    expected = ["patient", "pulmonary", "nodule", "lung"]
    
    if filtered == expected:
        print(f"\n✅ TEST 5 PASSED (removed {len(tokens) - len(filtered)} stopwords)")
        normalizer.close()
        return True
    else:
        print(f"\n❌ TEST 5 FAILED")
        print(f"    Expected: {expected}")
        print(f"    Got: {filtered}")
        normalizer.close()
        return False


def test_characteristic_normalization():
    """Test LIDC characteristic value normalization"""
    print_section("TEST 6: Characteristic Value Normalization")
    
    normalizer = KeywordNormalizer()
    
    # Test characteristic values
    test_cases = [
        ("subtlety", "5", "obvious"),
        ("malignancy", "1", "highly unlikely malignant"),
        ("sphericity", "3", "round"),
        ("texture", "5", "solid"),
        ("calcification", "6", "absent"),
    ]
    
    print("\n  Testing characteristic value normalization:")
    passed = 0
    for char, value, expected in test_cases:
        result = normalizer.normalize_characteristic_value(char, value)
        status = "✓" if result == expected else "✗"
        print(f"    {status} {char}:{value} → '{result}' (expected: '{expected}')")
        if result == expected:
            passed += 1
    
    normalizer.close()
    
    if passed == len(test_cases):
        print(f"\n✅ TEST 6 PASSED ({passed}/{len(test_cases)} normalizations correct)")
        return True
    else:
        print(f"\n❌ TEST 6 FAILED ({passed}/{len(test_cases)} normalizations correct)")
        return False


def test_batch_normalization():
    """Test batch keyword normalization"""
    print_section("TEST 7: Batch Normalization")
    
    normalizer = KeywordNormalizer()
    
    # Test batch of keywords
    keywords = [
        "lung", "lesion", "CT", "mass", "GGO", 
        "cancer", "density", "tumor", "MRI", "nodule"
    ]
    
    normalized = normalizer.normalize_batch(keywords)
    
    print(f"\n  Normalized {len(normalized)} keywords:")
    for original, norm in list(normalized.items())[:5]:
        print(f"    '{original}' → '{norm}'")
    
    print(f"  ... and {len(normalized) - 5} more")
    
    # Check some expected mappings
    expected_mappings = {
        "lung": "pulmonary",
        "lesion": "nodule",
        "CT": "computed tomography",
        "cancer": "malignancy",
    }
    
    passed = 0
    for orig, expected in expected_mappings.items():
        if normalized.get(orig) == expected:
            passed += 1
    
    normalizer.close()
    
    if passed == len(expected_mappings):
        print(f"\n✅ TEST 7 PASSED (batch normalization working)")
        return True
    else:
        print(f"\n❌ TEST 7 FAILED ({passed}/{len(expected_mappings)} mappings correct)")
        return False


def test_anatomical_terms():
    """Test anatomical term retrieval"""
    print_section("TEST 8: Anatomical Terms")
    
    normalizer = KeywordNormalizer()
    
    # Get anatomical terms
    lobes = normalizer.get_anatomical_terms('lobes')
    airways = normalizer.get_anatomical_terms('airways')
    all_anatomy = normalizer.get_anatomical_terms()
    
    print(f"\n  Anatomical terms:")
    print(f"    Lobes: {len(lobes)} terms")
    print(f"      Examples: {', '.join(lobes[:3])}")
    print(f"    Airways: {len(airways)} terms")
    print(f"      Examples: {', '.join(airways[:3])}")
    print(f"    Total anatomical: {len(all_anatomy)} terms")
    
    normalizer.close()
    
    if len(lobes) > 0 and len(airways) > 0 and len(all_anatomy) > 0:
        print(f"\n✅ TEST 8 PASSED")
        return True
    else:
        print(f"\n❌ TEST 8 FAILED")
        return False


def test_diagnostic_terms():
    """Test diagnostic term retrieval"""
    print_section("TEST 9: Diagnostic Terms")
    
    normalizer = KeywordNormalizer()
    
    # Get diagnostic terms
    benign = normalizer.get_diagnostic_terms('benign')
    malignant = normalizer.get_diagnostic_terms('malignant')
    infectious = normalizer.get_diagnostic_terms('infectious')
    
    print(f"\n  Diagnostic terms:")
    print(f"    Benign: {len(benign)} terms")
    print(f"      Examples: {', '.join(benign[:3])}")
    print(f"    Malignant: {len(malignant)} terms")
    print(f"      Examples: {', '.join(malignant[:3])}")
    print(f"    Infectious: {len(infectious)} terms")
    print(f"      Examples: {', '.join(infectious[:3])}")
    
    normalizer.close()
    
    if len(benign) > 0 and len(malignant) > 0 and len(infectious) > 0:
        print(f"\n✅ TEST 9 PASSED")
        return True
    else:
        print(f"\n❌ TEST 9 FAILED")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("  KeywordNormalizer Test Suite")
    print("="*60)
    
    tests = [
        ("Synonym Mapping", test_synonym_mapping),
        ("Abbreviation Expansion", test_abbreviation_expansion),
        ("Synonym Expansion", test_synonym_expansion),
        ("Multi-Word Detection", test_multi_word_detection),
        ("Stopword Filtering", test_stopword_filtering),
        ("Characteristic Normalization", test_characteristic_normalization),
        ("Batch Normalization", test_batch_normalization),
        ("Anatomical Terms", test_anatomical_terms),
        ("Diagnostic Terms", test_diagnostic_terms),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} CRASHED: {e}")
            import traceback
            traceback.print_exc()
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
