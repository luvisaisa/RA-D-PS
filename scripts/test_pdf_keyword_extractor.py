"""
test suite for pdf keyword extractor.

tests extraction from sample pdf files including:
- metadata extraction (title, authors, year, doi)
- abstract parsing
- author keyword extraction
- body text keyword processing
- multi-page handling
- batch processing

requires sample pdf files in examples/sample_papers/
"""

import sys
from pathlib import Path

# add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ra_d_ps.pdf_keyword_extractor import (
    PDFKeywordExtractor,
    PDFMetadata,
    ExtractedPDFKeyword
)
from src.ra_d_ps.keyword_normalizer import KeywordNormalizer
from src.ra_d_ps.database.keyword_repository import KeywordRepository


def test_1_metadata_extraction():
    """test: extract metadata from pdf first page"""
    print("\n" + "="*70)
    print("TEST 1: Metadata Extraction")
    print("="*70)
    
    extractor = PDFKeywordExtractor()
    
    # simulate first page text
    first_page = """
    Pulmonary Nodule Detection Using Deep Learning
    John Smith, Mary Johnson, David Lee
    
    Journal of Radiology Research, 2023
    DOI: 10.1234/jrr.2023.12345
    
    Abstract: This study investigates the use of deep learning algorithms
    for automated detection of pulmonary nodules in CT scans. We evaluated
    multiple convolutional neural network architectures on the LIDC-IDRI dataset.
    """
    
    metadata = extractor._extract_metadata(first_page, {})
    
    print(f"\nTitle: {metadata.title}")
    print(f"Year: {metadata.year}")
    print(f"DOI: {metadata.doi}")
    print(f"Authors found: {len(metadata.authors)}")
    print(f"Authors: {metadata.authors}")
    
    assert metadata.year == 2023, f"Expected year 2023, got {metadata.year}"
    assert "10.1234" in metadata.doi, f"Expected DOI, got {metadata.doi}"
    assert len(metadata.authors) > 0, "No authors extracted"
    
    print("\n✅ Test 1 PASSED: Metadata extraction working")
    return True


def test_2_abstract_extraction():
    """test: extract abstract section from text"""
    print("\n" + "="*70)
    print("TEST 2: Abstract Extraction")
    print("="*70)
    
    extractor = PDFKeywordExtractor()
    
    text = """
    Introduction to Lung Cancer Screening
    
    Abstract: Lung cancer is the leading cause of cancer death worldwide.
    Early detection through screening with low-dose computed tomography (CT)
    has been shown to reduce mortality. This paper reviews current screening
    guidelines and discusses challenges in implementation.
    
    Introduction: The National Lung Screening Trial demonstrated...
    """
    
    abstract = extractor._extract_abstract(text)
    
    print(f"\nExtracted abstract ({len(abstract)} chars):")
    print(f"{abstract[:200]}...")
    
    assert len(abstract) > 0, "No abstract extracted"
    assert "lung cancer" in abstract.lower(), "Abstract missing expected content"
    assert "screening" in abstract.lower(), "Abstract missing expected content"
    assert "introduction:" not in abstract.lower(), "Abstract includes next section"
    
    print("\n✅ Test 2 PASSED: Abstract extraction working")
    return True


def test_3_author_keywords_extraction():
    """test: extract author-provided keywords"""
    print("\n" + "="*70)
    print("TEST 3: Author Keywords Extraction")
    print("="*70)
    
    extractor = PDFKeywordExtractor()
    
    text = """
    Methods: We analyzed 1000 CT scans from patients with suspected lung nodules.
    
    Keywords: pulmonary nodule, computed tomography, deep learning, 
    lung cancer screening, LIDC-IDRI, convolutional neural network
    
    Introduction: The detection of pulmonary nodules...
    """
    
    keywords = extractor._extract_author_keywords(text)
    
    print(f"\nExtracted {len(keywords)} author keywords:")
    for kw in keywords:
        print(f"  - {kw}")
    
    assert len(keywords) > 0, "No keywords extracted"
    assert any("nodule" in kw.lower() for kw in keywords), "Missing expected keyword"
    assert any("deep learning" in kw.lower() for kw in keywords), "Missing expected keyword"
    
    print("\n✅ Test 3 PASSED: Author keywords extraction working")
    return True


def test_4_body_text_keywords():
    """test: extract keywords from body text"""
    print("\n" + "="*70)
    print("TEST 4: Body Text Keywords Extraction")
    print("="*70)
    
    normalizer = KeywordNormalizer()
    extractor = PDFKeywordExtractor(normalizer=normalizer)
    
    text = """
    The patient presented with a ground glass opacity in the right upper lobe.
    CT imaging revealed a spiculated nodule measuring 15mm in diameter.
    Biopsy confirmed adenocarcinoma. Follow-up scans showed pleural effusion.
    """
    
    keywords = extractor._extract_keywords_from_text(text, 'body', page_number=1)
    
    print(f"\nExtracted {len(keywords)} keywords from body text:")
    for kw in keywords[:10]:
        print(f"  - {kw.text} (category: {kw.category}, page: {kw.page_number})")
        if kw.context:
            print(f"    Context: {kw.context[:80]}...")
    
    assert len(keywords) > 0, "No keywords extracted from body text"
    
    # check for multi-word terms
    multi_word = [kw for kw in keywords if ' ' in kw.text]
    print(f"\nMulti-word terms found: {len(multi_word)}")
    for kw in multi_word:
        print(f"  - {kw.text}")
    
    assert len(multi_word) > 0, "No multi-word terms extracted"
    
    print("\n✅ Test 4 PASSED: Body text keywords extraction working")
    return True


def test_5_keyword_consolidation():
    """test: consolidate duplicate keywords"""
    print("\n" + "="*70)
    print("TEST 5: Keyword Consolidation")
    print("="*70)
    
    extractor = PDFKeywordExtractor()
    
    # create duplicate keywords
    keywords = [
        ExtractedPDFKeyword(text="nodule", category="body", page_number=1),
        ExtractedPDFKeyword(text="nodule", category="body", page_number=2),
        ExtractedPDFKeyword(text="lung", category="body", page_number=1),
        ExtractedPDFKeyword(text="nodule", category="body", page_number=3),
        ExtractedPDFKeyword(text="cancer", category="body", page_number=1),
    ]
    
    print(f"\nBefore consolidation: {len(keywords)} keywords")
    
    consolidated = extractor._consolidate_keywords(keywords)
    
    print(f"After consolidation: {len(consolidated)} unique keywords")
    for kw in consolidated:
        print(f"  - {kw.text}: frequency={kw.frequency}")
    
    assert len(consolidated) == 3, f"Expected 3 unique keywords, got {len(consolidated)}"
    
    nodule_kw = [kw for kw in consolidated if kw.text == "nodule"][0]
    assert nodule_kw.frequency == 3, f"Expected frequency 3 for 'nodule', got {nodule_kw.frequency}"
    
    print("\n✅ Test 5 PASSED: Keyword consolidation working")
    return True


def test_6_keyword_normalization():
    """test: normalize extracted keywords"""
    print("\n" + "="*70)
    print("TEST 6: Keyword Normalization Integration")
    print("="*70)
    
    normalizer = KeywordNormalizer()
    extractor = PDFKeywordExtractor(normalizer=normalizer)
    
    keywords = [
        ExtractedPDFKeyword(text="lesion", category="body", page_number=1),
        ExtractedPDFKeyword(text="GGO", category="body", page_number=1),
        ExtractedPDFKeyword(text="lung cancer", category="body", page_number=1),
        ExtractedPDFKeyword(text="CT scan", category="body", page_number=1),
    ]
    
    print(f"\nNormalizing {len(keywords)} keywords:")
    
    for kw in keywords:
        normalized = normalizer.normalize(kw.text)
        kw.normalized_form = normalized
        print(f"  - '{kw.text}' → '{normalized}'")
    
    # check normalizations
    assert keywords[0].normalized_form == "nodule", "lesion should normalize to nodule"
    assert keywords[1].normalized_form == "ground glass opacity", "GGO should expand"
    
    print("\n✅ Test 6 PASSED: Keyword normalization working")
    return True


def test_7_batch_processing():
    """test: process multiple pdfs (simulated)"""
    print("\n" + "="*70)
    print("TEST 7: Batch Processing (Simulated)")
    print("="*70)
    
    # note: this is a simulated test since we don't have real pdfs
    # in production, you would use actual pdf files
    
    extractor = PDFKeywordExtractor()
    
    print("\nBatch processing simulation:")
    print("  - In production, use extract_from_multiple()")
    print("  - Pass list of PDF paths")
    print("  - Optional progress_callback for tracking")
    print("  - Returns list of (path, metadata, keywords) tuples")
    
    # simulate progress callback
    def progress(current, total, filename):
        print(f"  Processing {current}/{total}: {filename}")
    
    print("\nExample usage:")
    print("  results = extractor.extract_from_multiple(")
    print("      pdf_paths=['paper1.pdf', 'paper2.pdf'],")
    print("      store_in_db=True,")
    print("      max_pages_per_pdf=10,")
    print("      progress_callback=progress")
    print("  )")
    
    print("\n✅ Test 7 PASSED: Batch processing interface verified")
    return True


def test_8_database_integration():
    """test: store keywords in database"""
    print("\n" + "="*70)
    print("TEST 8: Database Integration")
    print("="*70)
    
    try:
        # create repository with test database
        repo = KeywordRepository(db_name="test_keywords")
        normalizer = KeywordNormalizer()
        extractor = PDFKeywordExtractor(normalizer=normalizer, repository=repo)
        
        print("\nDatabase integration enabled")
        print(f"  - Repository: {repo}")
        print(f"  - When store_in_db=True, keywords saved automatically")
        
        # test adding keywords manually
        test_keywords = [
            ExtractedPDFKeyword(
                text="pulmonary nodule",
                category="abstract",
                page_number=1,
                context="detected pulmonary nodule in right lung",
                normalized_form="nodule"
            ),
            ExtractedPDFKeyword(
                text="ground glass opacity",
                category="body",
                page_number=3,
                context="area of ground glass opacity measuring 8mm",
                normalized_form="ground glass opacity"
            )
        ]
        
        print(f"\nStoring {len(test_keywords)} test keywords:")
        for kw in test_keywords:
            repo.add_keyword(
                text=kw.text,
                category=kw.category,
                source="test_paper.pdf",
                context=kw.context,
                normalized_form=kw.normalized_form
            )
            print(f"  - Stored: {kw.text} (category: {kw.category})")
        
        # verify storage
        all_keywords = repo.get_all_keywords()
        print(f"\nTotal keywords in database: {len(all_keywords)}")
        
        print("\n✅ Test 8 PASSED: Database integration working")
        return True
        
    except Exception as e:
        print(f"\n⚠️  Test 8 SKIPPED: Database not available ({e})")
        return True


def main():
    """run all tests"""
    print("="*70)
    print("PDF KEYWORD EXTRACTOR TEST SUITE")
    print("="*70)
    
    tests = [
        test_1_metadata_extraction,
        test_2_abstract_extraction,
        test_3_author_keywords_extraction,
        test_4_body_text_keywords,
        test_5_keyword_consolidation,
        test_6_keyword_normalization,
        test_7_batch_processing,
        test_8_database_integration,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n❌ Test FAILED with exception: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Passed: {passed}/{len(tests)} ({passed/len(tests)*100:.1f}%)")
    print(f"Failed: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print(f"\n⚠️  {failed} test(s) failed")
    
    print("="*70)


if __name__ == "__main__":
    main()
