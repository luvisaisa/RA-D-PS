"""
usage examples for keyword search engine.

demonstrates how to:
1. simple keyword search
2. boolean queries (AND/OR)
3. synonym expansion
4. category filtering
5. source filtering
6. pagination
7. related keywords
8. statistics
9. result highlighting
10. relevance ranking
"""

import sys
from pathlib import Path

# add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ra_d_ps.keyword_search_engine import KeywordSearchEngine
from src.ra_d_ps.keyword_normalizer import KeywordNormalizer
from src.ra_d_ps.database.keyword_repository import KeywordRepository


def example_1_simple_search():
    """example 1: simple keyword search"""
    print("\n" + "="*70)
    print("EXAMPLE 1: Simple Keyword Search")
    print("="*70)
    
    print("\nBasic search:")
    print("  repo = KeywordRepository()")
    print("  normalizer = KeywordNormalizer()")
    print("  engine = KeywordSearchEngine(repository=repo, normalizer=normalizer)")
    print("  ")
    print("  response = engine.search('nodule', page=1, page_size=10)")
    print("  ")
    print("  print(f'Found {response.total_results} results')")
    print("  print(f'Search time: {response.search_time_ms}ms')")
    print("  ")
    print("  for result in response.results:")
    print("      print(f'{result.keyword_text} (score: {result.relevance_score})')")


def example_2_boolean_queries():
    """example 2: boolean AND/OR queries"""
    print("\n" + "="*70)
    print("EXAMPLE 2: Boolean Queries")
    print("="*70)
    
    print("\nAND query (all terms must match):")
    print("  response = engine.search('lung AND nodule')")
    print("  # returns keywords containing both 'lung' and 'nodule'")
    print("  ")
    print("OR query (any term can match):")
    print("  response = engine.search('nodule OR lesion OR mass')")
    print("  # returns keywords containing any of the terms")
    print("  ")
    print("Implicit AND (multi-word):")
    print("  response = engine.search('pulmonary nodule')")
    print("  # same as 'pulmonary AND nodule'")


def example_3_synonym_expansion():
    """example 3: automatic synonym expansion"""
    print("\n" + "="*70)
    print("EXAMPLE 3: Synonym Expansion")
    print("="*70)
    
    print("\nAutomatic expansion (default):")
    print("  response = engine.search('lesion', expand_synonyms=True)")
    print("  ")
    print("  print(f'Expanded terms: {response.expanded_query_terms}')")
    print("  # ['lesion', 'nodule', 'mass', ...]")
    print("  ")
    print("Disable expansion:")
    print("  response = engine.search('lesion', expand_synonyms=False)")
    print("  # only searches for exact term 'lesion'")


def example_4_category_filtering():
    """example 4: filter by category"""
    print("\n" + "="*70)
    print("EXAMPLE 4: Category Filtering")
    print("="*70)
    
    print("\nSearch within category:")
    print("  # search only XML characteristic keywords")
    print("  response = engine.search_by_category(")
    print("      query='nodule',")
    print("      category='characteristic'")
    print("  )")
    print("  ")
    print("  # search only PDF abstract keywords")
    print("  response = engine.search_by_category(")
    print("      query='cancer',")
    print("      category='abstract'")
    print("  )")
    print("  ")
    print("Multiple categories:")
    print("  response = engine.search(")
    print("      query='nodule',")
    print("      categories=['characteristic', 'diagnosis', 'anatomy']")
    print("  )")


def example_5_source_filtering():
    """example 5: filter by source"""
    print("\n" + "="*70)
    print("EXAMPLE 5: Source Filtering")
    print("="*70)
    
    print("\nSearch within XML files:")
    print("  response = engine.search_by_source(")
    print("      query='nodule',")
    print("      source_pattern='*.xml'")
    print("  )")
    print("  ")
    print("Search within PDF files:")
    print("  response = engine.search_by_source(")
    print("      query='cancer',")
    print("      source_pattern='*.pdf'")
    print("  )")
    print("  ")
    print("Search specific file:")
    print("  response = engine.search_by_source(")
    print("      query='nodule',")
    print("      source_pattern='LIDC-IDRI-0001*.xml'")
    print("  )")


def example_6_pagination():
    """example 6: paginate results"""
    print("\n" + "="*70)
    print("EXAMPLE 6: Pagination")
    print("="*70)
    
    print("\nPage through results:")
    print("  # first page")
    print("  page1 = engine.search('nodule', page=1, page_size=20)")
    print("  print(f'Page {page1.page} of {page1.total_results // page1.page_size + 1}')")
    print("  ")
    print("  # second page")
    print("  page2 = engine.search('nodule', page=2, page_size=20)")
    print("  ")
    print("  # last page")
    print("  last_page_num = page1.total_results // page1.page_size + 1")
    print("  last_page = engine.search('nodule', page=last_page_num, page_size=20)")


def example_7_related_keywords():
    """example 7: find related keywords"""
    print("\n" + "="*70)
    print("EXAMPLE 7: Related Keywords")
    print("="*70)
    
    print("\nFind related terms:")
    print("  related = engine.get_related_keywords('nodule', limit=10)")
    print("  ")
    print("  for result in related:")
    print("      print(f'{result.keyword_text} (score: {result.relevance_score})')")
    print("      print(f'  Normalized: {result.normalized_form}')")
    print("  ")
    print("  # Output:")
    print("  # nodule (score: 0.8765)")
    print("  #   Normalized: nodule")
    print("  # lesion (score: 0.7543)")
    print("  #   Normalized: nodule")
    print("  # mass (score: 0.6321)")
    print("  #   Normalized: nodule")


def example_8_statistics():
    """example 8: search engine statistics"""
    print("\n" + "="*70)
    print("EXAMPLE 8: Search Engine Statistics")
    print("="*70)
    
    print("\nGet corpus statistics:")
    print("  stats = engine.get_statistics()")
    print("  ")
    print("  print(f'Total keywords: {stats[\"total_keywords\"]}')")
    print("  print(f'Total documents: {stats[\"total_documents\"]}')")
    print("  print(f'Average doc count: {stats[\"avg_document_count\"]}')")
    print("  ")
    print("  print('By category:')")
    print("  for category, count in stats['by_category'].items():")
    print("      print(f'  {category}: {count}')")
    print("  ")
    print("  print('Top 10 keywords:')")
    print("  for kw in stats['top_keywords']:")
    print("      print(f'  {kw[\"text\"]}: {kw[\"document_count\"]} docs')")


def example_9_result_highlighting():
    """example 9: highlight matched terms"""
    print("\n" + "="*70)
    print("EXAMPLE 9: Result Highlighting")
    print("="*70)
    
    print("\nAccess highlighted context:")
    print("  response = engine.search('pulmonary nodule')")
    print("  ")
    print("  for result in response.results[:3]:")
    print("      print(f'Keyword: {result.keyword_text}')")
    print("      print(f'Context: {result.highlighted_context}')")
    print("      print()")
    print("  ")
    print("  # Output:")
    print("  # Keyword: pulmonary nodule")
    print("  # Context: detected **pulmonary** **nodule** in right lung")
    print("  # ")
    print("  # Keyword: spiculated nodule")
    print("  # Context: CT shows spiculated **nodule** measuring 12mm")


def example_10_relevance_ranking():
    """example 10: understand relevance scores"""
    print("\n" + "="*70)
    print("EXAMPLE 10: Relevance Ranking")
    print("="*70)
    
    print("\nRelevance scoring factors:")
    print("  1. Term Match Score:")
    print("     - Number of query terms matched")
    print("     - Exact matches get 1.5x boost")
    print("  ")
    print("  2. TF-IDF Score:")
    print("     - TF: Term frequency (document count / total docs)")
    print("     - IDF: Inverse document frequency")
    print("     - Rare terms score higher")
    print("  ")
    print("  3. Document Count:")
    print("     - Small weight for popularity")
    print("  ")
    print("Example ranking:")
    print("  response = engine.search('nodule')")
    print("  ")
    print("  for i, result in enumerate(response.results[:5], 1):")
    print("      print(f'{i}. {result.keyword_text}')")
    print("      print(f'   Score: {result.relevance_score:.4f}')")
    print("      print(f'   Documents: {result.document_count}')")
    print("      print(f'   Matched: {result.matched_query_terms}')")


def example_11_minimum_relevance():
    """example 11: filter by minimum relevance"""
    print("\n" + "="*70)
    print("EXAMPLE 11: Minimum Relevance Filtering")
    print("="*70)
    
    print("\nFilter low-relevance results:")
    print("  # only show highly relevant results")
    print("  response = engine.search(")
    print("      query='nodule',")
    print("      min_relevance=0.5")
    print("  )")
    print("  ")
    print("  print(f'High-relevance results: {response.total_results}')")
    print("  ")
    print("  # compare with all results")
    print("  all_response = engine.search(query='nodule')")
    print("  print(f'All results: {all_response.total_results}')")


def main():
    """run all examples"""
    print("="*70)
    print("KEYWORD SEARCH ENGINE - USAGE EXAMPLES")
    print("="*70)
    
    examples = [
        example_1_simple_search,
        example_2_boolean_queries,
        example_3_synonym_expansion,
        example_4_category_filtering,
        example_5_source_filtering,
        example_6_pagination,
        example_7_related_keywords,
        example_8_statistics,
        example_9_result_highlighting,
        example_10_relevance_ranking,
        example_11_minimum_relevance,
    ]
    
    for example in examples:
        example()
    
    print("\n" + "="*70)
    print("For more information, see:")
    print("  - src/ra_d_ps/keyword_search_engine.py")
    print("  - scripts/test_keyword_search_engine.py")
    print("  - docs/KEYWORD_SEARCH_ENGINE_SUMMARY.md")
    print("="*70)


if __name__ == "__main__":
    main()
