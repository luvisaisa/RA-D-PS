#!/usr/bin/env python3
"""
XMLKeywordExtractor Usage Examples

Quick reference for extracting keywords from LIDC-IDRI XML files.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ra_d_ps.xml_keyword_extractor import XMLKeywordExtractor
from src.ra_d_ps.database.keyword_repository import KeywordRepository


def example_1_single_file():
    """Example 1: Extract keywords from a single XML file"""
    print("="*60)
    print("Example 1: Single File Extraction")
    print("="*60)
    
    # Create extractor
    extractor = XMLKeywordExtractor()
    
    # Extract from single file
    xml_file = "/Users/isa/Desktop/python projects/XML PARSE/examples/XML-COMP/157/162.xml"
    keywords = extractor.extract_from_xml(xml_file, store_in_db=False)
    
    print(f"\nExtracted {len(keywords)} keywords:")
    for kw in keywords[:5]:  # Show first 5
        print(f"  - {kw.text} ({kw.category}) - {kw.context[:60]}...")
    
    extractor.close()


def example_2_with_database():
    """Example 2: Extract and store in database"""
    print("\n" + "="*60)
    print("Example 2: Extract and Store in Database")
    print("="*60)
    
    # Create extractor
    extractor = XMLKeywordExtractor()
    
    # Extract and store in database
    xml_file = "/Users/isa/Desktop/python projects/XML PARSE/examples/XML-COMP/157/163.xml"
    keywords = extractor.extract_from_xml(xml_file, store_in_db=True)
    
    print(f"\n✓ Stored {len(keywords)} keywords in database")
    
    # Verify storage
    repo = KeywordRepository()
    all_keywords = repo.get_all_keywords(limit=10)
    
    print(f"\n✓ Database now contains {len(all_keywords)} keywords (showing first 10)")
    for kw in all_keywords[:5]:
        print(f"  - {kw.keyword_text} ({kw.category})")
    
    extractor.close()
    repo.close()


def example_3_batch_processing():
    """Example 3: Batch process multiple files"""
    print("\n" + "="*60)
    print("Example 3: Batch Processing")
    print("="*60)
    
    # Get multiple XML files
    xml_dir = Path("/Users/isa/Desktop/python projects/XML PARSE/examples/XML-COMP")
    xml_files = [str(f) for f in list(xml_dir.glob("**/*.xml"))[:5]]
    
    print(f"\nProcessing {len(xml_files)} files...")
    
    # Create extractor
    extractor = XMLKeywordExtractor()
    
    # Batch process
    stats = extractor.extract_from_multiple(xml_files, show_progress=True)
    
    print(f"\n✓ Batch Processing Complete")
    print(f"  Files processed: {stats['files_processed']}")
    print(f"  Total keywords: {stats['total_keywords']}")
    print(f"  Unique keywords: {stats['unique_keywords']}")
    print(f"  Errors: {len(stats['errors'])}")
    
    print(f"\n  Keywords by category:")
    for category, count in stats['by_category'].items():
        print(f"    {category}: {count}")
    
    extractor.close()


def example_4_filter_by_category():
    """Example 4: Filter keywords by category"""
    print("\n" + "="*60)
    print("Example 4: Filter by Category")
    print("="*60)
    
    # Create repository
    repo = KeywordRepository()
    
    # Get characteristics only
    characteristics = repo.get_keywords_by_category('characteristic')
    print(f"\n✓ Found {len(characteristics)} characteristic keywords")
    
    # Show samples
    for kw in characteristics[:5]:
        print(f"  - {kw.keyword_text}")
    
    # Get metadata
    metadata = repo.get_keywords_by_category('metadata')
    print(f"\n✓ Found {len(metadata)} metadata keywords")
    
    for kw in metadata[:3]:
        print(f"  - {kw.keyword_text}")
    
    repo.close()


def example_5_top_keywords():
    """Example 5: Get top keywords by frequency"""
    print("\n" + "="*60)
    print("Example 5: Top Keywords by Frequency")
    print("="*60)
    
    # Create repository
    repo = KeywordRepository()
    
    # Get top 10 keywords
    top_keywords = repo.get_top_keywords(limit=10)
    
    print(f"\n✓ Top 10 keywords:")
    for i, (keyword, stats) in enumerate(top_keywords, 1):
        print(f"  {i}. {keyword.keyword_text}")
        print(f"     Frequency: {stats.total_frequency}, Documents: {stats.document_count}")
    
    repo.close()


def example_6_search_keywords():
    """Example 6: Search keywords"""
    print("\n" + "="*60)
    print("Example 6: Search Keywords")
    print("="*60)
    
    # Create repository
    repo = KeywordRepository()
    
    # Search for keywords containing "subtlety"
    results = repo.search_keywords("subtlety", limit=5)
    
    print(f"\n✓ Found {len(results)} keywords matching 'subtlety':")
    for kw in results:
        print(f"  - {kw.keyword_text} ({kw.category})")
    
    repo.close()


def example_7_extraction_stats():
    """Example 7: Get extraction statistics"""
    print("\n" + "="*60)
    print("Example 7: Extraction Statistics")
    print("="*60)
    
    # Create extractor
    extractor = XMLKeywordExtractor()
    
    # Process some files
    xml_dir = Path("/Users/isa/Desktop/python projects/XML PARSE/examples/XML-COMP")
    xml_files = [str(f) for f in list(xml_dir.glob("**/*.xml"))[:3]]
    
    for xml_file in xml_files:
        extractor.extract_from_xml(xml_file, store_in_db=False)
    
    # Get stats
    stats = extractor.get_extraction_stats()
    
    print(f"\n✓ Extraction Statistics:")
    print(f"  Files processed: {stats['files_processed']}")
    print(f"  Total keywords: {stats['total_keywords']}")
    print(f"\n  By category:")
    for category, count in stats['by_category'].items():
        print(f"    {category}: {count}")
    
    extractor.close()


if __name__ == '__main__':
    print("\nXMLKeywordExtractor Usage Examples")
    print("="*60 + "\n")
    
    # Run all examples
    try:
        example_1_single_file()
        example_2_with_database()
        example_3_batch_processing()
        example_4_filter_by_category()
        example_5_top_keywords()
        example_6_search_keywords()
        example_7_extraction_stats()
        
        print("\n" + "="*60)
        print("✅ All examples completed successfully!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
