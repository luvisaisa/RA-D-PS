"""
usage examples for pdf keyword extractor.

demonstrates how to:
1. extract from single pdf
2. batch process multiple pdfs
3. integrate with database
4. access metadata and keywords
5. use with normalizer
6. filter by category
7. get statistics
"""

import sys
from pathlib import Path

# add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ra_d_ps.pdf_keyword_extractor import PDFKeywordExtractor
from src.ra_d_ps.keyword_normalizer import KeywordNormalizer
from src.ra_d_ps.database.keyword_repository import KeywordRepository


def example_1_basic_extraction():
    """example 1: extract keywords from single pdf"""
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic PDF Extraction")
    print("="*70)
    
    extractor = PDFKeywordExtractor()
    
    # note: replace with actual pdf path
    pdf_path = "examples/sample_papers/lung_nodule_study.pdf"
    
    print(f"\nExtracting from: {pdf_path}")
    print("Usage:")
    print("  metadata, keywords = extractor.extract_from_pdf(")
    print("      pdf_path='path/to/paper.pdf',")
    print("      store_in_db=False,  # don't store yet")
    print("      max_pages=10        # process first 10 pages only")
    print("  )")
    
    print("\nResults:")
    print("  metadata.title: 'Pulmonary Nodule Detection...'")
    print("  metadata.year: 2023")
    print("  metadata.authors: ['Smith J', 'Johnson M', ...]")
    print("  metadata.abstract: 'This study investigates...'")
    print("  len(keywords): 45 keywords extracted")


def example_2_metadata_access():
    """example 2: access extracted metadata"""
    print("\n" + "="*70)
    print("EXAMPLE 2: Metadata Access")
    print("="*70)
    
    print("\nMetadata fields available:")
    print("  - title: str")
    print("  - authors: List[str]")
    print("  - journal: str")
    print("  - year: Optional[int]")
    print("  - doi: str")
    print("  - abstract: str")
    print("  - author_keywords: List[str]")
    print("  - mesh_terms: List[str]")
    
    print("\nExample access:")
    print("  if metadata.year and metadata.year > 2020:")
    print("      print(f'Recent paper: {metadata.title}')")
    print("  ")
    print("  if metadata.doi:")
    print("      print(f'DOI: {metadata.doi}')")
    print("  ")
    print("  for author in metadata.authors:")
    print("      print(f'Author: {author}')")


def example_3_keyword_filtering():
    """example 3: filter keywords by category"""
    print("\n" + "="*70)
    print("EXAMPLE 3: Keyword Filtering by Category")
    print("="*70)
    
    print("\nKeyword categories:")
    print("  - 'metadata': title, author keywords")
    print("  - 'abstract': from abstract section")
    print("  - 'keyword': author-provided keywords")
    print("  - 'body': from main text")
    
    print("\nExample filtering:")
    print("  # get only abstract keywords")
    print("  abstract_kws = [kw for kw in keywords if kw.category == 'abstract']")
    print("  ")
    print("  # get high-frequency terms")
    print("  common_kws = [kw for kw in keywords if kw.frequency > 5]")
    print("  ")
    print("  # get keywords from first page")
    print("  first_page = [kw for kw in keywords if kw.page_number == 1]")


def example_4_batch_processing():
    """example 4: process multiple pdfs"""
    print("\n" + "="*70)
    print("EXAMPLE 4: Batch Processing Multiple PDFs")
    print("="*70)
    
    print("\nBatch processing with progress tracking:")
    print("  ")
    print("  def progress_callback(current, total, filename):")
    print("      percent = current / total * 100")
    print("      print(f'{percent:.1f}% - Processing: {filename}')")
    print("  ")
    print("  pdf_files = list(Path('papers/').glob('*.pdf'))")
    print("  ")
    print("  results = extractor.extract_from_multiple(")
    print("      pdf_paths=pdf_files,")
    print("      store_in_db=True,")
    print("      max_pages_per_pdf=20,")
    print("      progress_callback=progress_callback")
    print("  )")
    print("  ")
    print("  # process results")
    print("  for pdf_path, metadata, keywords in results:")
    print("      print(f'{metadata.title}: {len(keywords)} keywords')")


def example_5_database_integration():
    """example 5: integrate with keyword repository"""
    print("\n" + "="*70)
    print("EXAMPLE 5: Database Integration")
    print("="*70)
    
    print("\nSetup with database storage:")
    print("  ")
    print("  # create repository and normalizer")
    print("  repo = KeywordRepository()")
    print("  normalizer = KeywordNormalizer(repository=repo)")
    print("  ")
    print("  # create extractor with database support")
    print("  extractor = PDFKeywordExtractor(")
    print("      normalizer=normalizer,")
    print("      repository=repo")
    print("  )")
    print("  ")
    print("  # extract and auto-store in database")
    print("  metadata, keywords = extractor.extract_from_pdf(")
    print("      pdf_path='paper.pdf',")
    print("      store_in_db=True  # automatically stores")
    print("  )")
    print("  ")
    print("  # query database")
    print("  all_pdfs = repo.get_keywords_by_category('abstract')")
    print("  print(f'Found {len(all_pdfs)} abstract keywords')")


def example_6_normalization():
    """example 6: use keyword normalization"""
    print("\n" + "="*70)
    print("EXAMPLE 6: Keyword Normalization")
    print("="*70)
    
    print("\nNormalization automatically applied:")
    print("  ")
    print("  # extractor uses normalizer internally")
    print("  normalizer = KeywordNormalizer()")
    print("  extractor = PDFKeywordExtractor(normalizer=normalizer)")
    print("  ")
    print("  metadata, keywords = extractor.extract_from_pdf('paper.pdf')")
    print("  ")
    print("  # check normalized forms")
    print("  for kw in keywords[:5]:")
    print("      print(f'{kw.text} → {kw.normalized_form}')")
    print("  ")
    print("  # output:")
    print("  #   lesion → nodule")
    print("  #   GGO → ground glass opacity")
    print("  #   lung cancer → lung cancer")
    print("  #   CT → computed tomography")


def example_7_statistics():
    """example 7: get extraction statistics"""
    print("\n" + "="*70)
    print("EXAMPLE 7: Extraction Statistics")
    print("="*70)
    
    print("\nGet statistics from database:")
    print("  ")
    print("  # create extractor with repository")
    print("  repo = KeywordRepository()")
    print("  extractor = PDFKeywordExtractor(repository=repo)")
    print("  ")
    print("  # process multiple pdfs")
    print("  for pdf_path in pdf_files:")
    print("      extractor.extract_from_pdf(pdf_path, store_in_db=True)")
    print("  ")
    print("  # get statistics")
    print("  stats = extractor.get_statistics()")
    print("  ")
    print("  print(f'Total keywords: {stats[\"total_keywords\"]}')")
    print("  print(f'Unique keywords: {stats[\"unique_keywords\"]}')")
    print("  print(f'By category: {stats[\"by_category\"]}')")
    print("  ")
    print("  # output:")
    print("  #   Total keywords: 1250")
    print("  #   Unique keywords: 342")
    print("  #   By category: {'abstract': 89, 'body': 201, 'keyword': 52}")


def example_8_context_snippets():
    """example 8: access keyword context"""
    print("\n" + "="*70)
    print("EXAMPLE 8: Keyword Context Snippets")
    print("="*70)
    
    print("\nEach keyword includes context:")
    print("  ")
    print("  metadata, keywords = extractor.extract_from_pdf('paper.pdf')")
    print("  ")
    print("  # find specific keyword")
    print("  nodule_kws = [kw for kw in keywords if 'nodule' in kw.text.lower()]")
    print("  ")
    print("  for kw in nodule_kws:")
    print("      print(f'Keyword: {kw.text}')")
    print("      print(f'Page: {kw.page_number}')")
    print("      print(f'Context: {kw.context}')")
    print("      print(f'Frequency: {kw.frequency}')")
    print("      print()")
    print("  ")
    print("  # output:")
    print("  #   Keyword: pulmonary nodule")
    print("  #   Page: 1")
    print("  #   Context: ...detected pulmonary nodule in right upper lobe...")
    print("  #   Frequency: 3")


def example_9_page_filtering():
    """example 9: filter keywords by page"""
    print("\n" + "="*70)
    print("EXAMPLE 9: Page-Based Filtering")
    print("="*70)
    
    print("\nFilter keywords by page number:")
    print("  ")
    print("  metadata, keywords = extractor.extract_from_pdf('paper.pdf')")
    print("  ")
    print("  # get keywords from abstract (pages 1-2)")
    print("  abstract_kws = [kw for kw in keywords ")
    print("                  if kw.page_number <= 2 and kw.category == 'abstract']")
    print("  ")
    print("  # get keywords from results section (pages 5-8)")
    print("  results_kws = [kw for kw in keywords ")
    print("                 if 5 <= kw.page_number <= 8]")
    print("  ")
    print("  # analyze keyword distribution")
    print("  from collections import Counter")
    print("  page_dist = Counter(kw.page_number for kw in keywords)")
    print("  print(f'Keywords per page: {dict(page_dist)}')")


def example_10_error_handling():
    """example 10: handle extraction errors"""
    print("\n" + "="*70)
    print("EXAMPLE 10: Error Handling")
    print("="*70)
    
    print("\nRobust error handling:")
    print("  ")
    print("  pdf_files = list(Path('papers/').glob('*.pdf'))")
    print("  successful = []")
    print("  failed = []")
    print("  ")
    print("  for pdf_path in pdf_files:")
    print("      try:")
    print("          metadata, keywords = extractor.extract_from_pdf(pdf_path)")
    print("          successful.append((pdf_path, len(keywords)))")
    print("      except FileNotFoundError:")
    print("          print(f'File not found: {pdf_path}')")
    print("          failed.append(pdf_path)")
    print("      except Exception as e:")
    print("          print(f'Error processing {pdf_path}: {e}')")
    print("          failed.append(pdf_path)")
    print("  ")
    print("  print(f'Successful: {len(successful)}/{len(pdf_files)}')")
    print("  print(f'Failed: {len(failed)}/{len(pdf_files)}')")


def main():
    """run all examples"""
    print("="*70)
    print("PDF KEYWORD EXTRACTOR - USAGE EXAMPLES")
    print("="*70)
    
    examples = [
        example_1_basic_extraction,
        example_2_metadata_access,
        example_3_keyword_filtering,
        example_4_batch_processing,
        example_5_database_integration,
        example_6_normalization,
        example_7_statistics,
        example_8_context_snippets,
        example_9_page_filtering,
        example_10_error_handling,
    ]
    
    for example in examples:
        example()
    
    print("\n" + "="*70)
    print("For more information, see:")
    print("  - src/ra_d_ps/pdf_keyword_extractor.py")
    print("  - scripts/test_pdf_keyword_extractor.py")
    print("  - docs/KEYWORD_EXTRACTION_GUIDE.md")
    print("="*70)


if __name__ == "__main__":
    main()
