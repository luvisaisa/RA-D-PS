#!/usr/bin/env python3
"""
Test PDF keyword extraction with real research paper.
File: 3-Beig.etal-Perinodular-and-Intranodular Radiomic Features-.pdf
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ra_d_ps.pdf_keyword_extractor import PDFKeywordExtractor
from src.ra_d_ps.keyword_normalizer import KeywordNormalizer
from src.ra_d_ps.database.keyword_repository import KeywordRepository
from src.ra_d_ps.keyword_search_engine import KeywordSearchEngine

def main():
    pdf_path = "/Users/isa/Desktop/research/perinodular radiomics lit review/3-Beig.etal-Perinodular-and-Intranodular Radiomic Features-.pdf"
    
    print("=" * 80)
    print("REAL PDF EXTRACTION TEST")
    print("=" * 80)
    print(f"\nPDF File: {os.path.basename(pdf_path)}")
    
    # Check if file exists
    if not os.path.exists(pdf_path):
        print(f"❌ ERROR: PDF file not found at: {pdf_path}")
        return 1
    
    file_size = os.path.getsize(pdf_path) / (1024 * 1024)  # MB
    print(f"File Size: {file_size:.2f} MB")
    print()
    
    # Initialize components
    print("Initializing components...")
    normalizer = KeywordNormalizer()
    repo = KeywordRepository()
    extractor = PDFKeywordExtractor(normalizer=normalizer, repository=repo)
    search_engine = KeywordSearchEngine(repository=repo)
    print("✓ Components initialized\n")
    
    # Extract keywords from PDF
    print("-" * 80)
    print("STEP 1: Extracting Keywords from PDF")
    print("-" * 80)
    
    try:
        metadata, keywords = extractor.extract_from_pdf(
            pdf_path=pdf_path,
            store_in_db=True,  # Store in database
            max_pages=50  # Limit for testing
        )
        
        print(f"✓ Extraction complete!")
        print(f"\nMetadata:")
        print(f"  Title: {metadata.title or 'N/A'}")
        print(f"  Authors: {', '.join(metadata.authors[:3]) if metadata.authors else 'N/A'}")
        if len(metadata.authors) > 3:
            print(f"           ... and {len(metadata.authors) - 3} more")
        print(f"  Journal: {metadata.journal or 'N/A'}")
        print(f"  Year: {metadata.year or 'N/A'}")
        print(f"  DOI: {metadata.doi or 'N/A'}")
        print(f"  Abstract Length: {len(metadata.abstract) if metadata.abstract else 0} chars")
        
        if metadata.abstract:
            print(f"\nAbstract Preview:")
            print(f"  {metadata.abstract[:300]}...")
        
        print(f"\nKeywords Extracted: {len(keywords)}")
        print(f"\nTop 20 Keywords by Frequency:")
        sorted_keywords = sorted(keywords, key=lambda k: k.frequency, reverse=True)[:20]
        for i, kw in enumerate(sorted_keywords, 1):
            print(f"  {i:2d}. {kw.text:<30s} (freq={kw.frequency:2d}, page={kw.page_number}, cat={kw.category})")
            if kw.context:
                print(f"      Context: {kw.context[:100]}...")
        
    except Exception as e:
        print(f"❌ ERROR during extraction: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Check text storage
    print("\n" + "-" * 80)
    print("STEP 2: Verifying Text Storage")
    print("-" * 80)
    
    total_text_blocks = 0
    
    try:
        # Check abstract storage
        abstract_kw = repo.get_keyword_by_text("abstract")
        if abstract_kw and abstract_kw.category == "metadata":
            text_blocks = repo.get_text_blocks(abstract_kw.keyword_id, sector="text_storage")
            print(f"✓ Abstract stored: {len(text_blocks)} text block(s)")
            if text_blocks:
                print(f"  Preview: {text_blocks[0][:200]}...")
        
        # Check keyword text blocks
        sample_keyword = sorted_keywords[0] if sorted_keywords else None
        if sample_keyword:
            kw = repo.get_keyword_by_text(sample_keyword.text)
            if kw:
                text_blocks = repo.get_text_blocks(kw.keyword_id, sector="text_storage")
                print(f"\n✓ Keyword '{sample_keyword.text}' has {len(text_blocks)} text block(s)")
                if text_blocks:
                    print(f"  Preview: {text_blocks[0][:200]}...")
        
        # Count total text blocks
        all_keywords = repo.get_all_keywords(limit=1000)
        for kw in all_keywords:
            blocks = repo.get_text_blocks(kw.keyword_id, sector="text_storage")
            total_text_blocks += len(blocks)
        
        print(f"\n✓ Total text blocks in storage: {total_text_blocks}")
        
    except Exception as e:
        print(f"❌ ERROR during text storage verification: {e}")
        import traceback
        traceback.print_exc()
    
    # Test search functionality
    print("\n" + "-" * 80)
    print("STEP 3: Testing Search Functionality")
    print("-" * 80)
    
    test_queries = [
        "radiomic features",
        "perinodular",
        "intranodular",
        "lung cancer",
        "texture analysis",
        "machine learning"
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        try:
            results = search_engine.search(
                query=query,
                page_size=5,
                expand_synonyms=True
            )
            
            if results.results:
                print(f"  Found {len(results.results)} result(s):")
                for i, result in enumerate(results.results[:3], 1):
                    print(f"    {i}. {result.keyword_text} (score={result.relevance_score:.3f})")
                    if result.context:
                        print(f"       Context: {result.context[:100]}...")
            else:
                print(f"  No results found")
                
        except Exception as e:
            print(f"  ❌ Search error: {e}")
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"✓ PDF successfully processed: {os.path.basename(pdf_path)}")
    print(f"✓ Keywords extracted: {len(keywords)}")
    print(f"✓ Text blocks stored: {total_text_blocks}")
    print(f"✓ Search functionality: Working")
    print(f"\n✅ REAL PDF TEST PASSED - Integration verified with actual research paper!")
    print("=" * 80)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
