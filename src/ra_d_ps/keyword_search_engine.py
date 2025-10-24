"""
Keyword search engine for radiology annotation corpus.

This module provides search capabilities across the keyword corpus with:
- Boolean query parsing (AND/OR operators)
- Synonym expansion using KeywordNormalizer
- TF-IDF ranking for relevance scoring
- Sector filtering (lidc_annotations, research_papers)
- Result snippets with keyword highlighting
- Pagination support

Integrates with KeywordRepository for data access and
KeywordNormalizer for query expansion.
"""

import re
import math
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Tuple
from collections import defaultdict

from src.ra_d_ps.keyword_normalizer import KeywordNormalizer
from src.ra_d_ps.database.keyword_repository import KeywordRepository


@dataclass
class SearchResult:
    """single search result with relevance score and context."""
    keyword_id: int
    keyword_text: str
    normalized_form: str
    category: str
    source: str
    document_count: int
    relevance_score: float
    context: str = ""
    highlighted_context: str = ""
    matched_query_terms: List[str] = field(default_factory=list)


@dataclass
class SearchResponse:
    """search response with results and metadata."""
    query: str
    total_results: int
    page: int
    page_size: int
    results: List[SearchResult] = field(default_factory=list)
    expanded_query_terms: List[str] = field(default_factory=list)
    search_time_ms: float = 0.0


class QueryParser:
    """parse boolean search queries with AND/OR operators."""
    
    def __init__(self):
        self.and_pattern = re.compile(r'\s+AND\s+', re.IGNORECASE)
        self.or_pattern = re.compile(r'\s+OR\s+', re.IGNORECASE)
    
    def parse(self, query: str) -> Dict[str, any]:
        """
        parse query into structured form.
        
        args:
            query: search query string
            
        returns:
            dict with 'operator' and 'terms' keys
        """
        query = query.strip()
        
        # check for AND operator
        if self.and_pattern.search(query):
            terms = self.and_pattern.split(query)
            return {
                'operator': 'AND',
                'terms': [term.strip().lower() for term in terms if term.strip()]
            }
        
        # check for OR operator
        if self.or_pattern.search(query):
            terms = self.or_pattern.split(query)
            return {
                'operator': 'OR',
                'terms': [term.strip().lower() for term in terms if term.strip()]
            }
        
        # single term or implicit AND
        terms = query.split()
        if len(terms) > 1:
            return {
                'operator': 'AND',
                'terms': [term.strip().lower() for term in terms if term.strip()]
            }
        
        return {
            'operator': 'SINGLE',
            'terms': [query.lower()]
        }


class KeywordSearchEngine:
    """search engine for keyword corpus with TF-IDF ranking."""
    
    def __init__(
        self,
        repository: KeywordRepository,
        normalizer: Optional[KeywordNormalizer] = None
    ):
        """
        initialize search engine.
        
        args:
            repository: keyword repository for data access
            normalizer: optional keyword normalizer for synonym expansion
        """
        self.repository = repository
        self.normalizer = normalizer or KeywordNormalizer()
        self.query_parser = QueryParser()
    
    def search(
        self,
        query: str,
        page: int = 1,
        page_size: int = 20,
        categories: Optional[List[str]] = None,
        min_relevance: float = 0.0,
        expand_synonyms: bool = True
    ) -> SearchResponse:
        """
        search keyword corpus with query.
        
        args:
            query: search query string (supports AND/OR operators)
            page: page number (1-indexed)
            page_size: results per page
            categories: optional category filter (e.g., ['abstract', 'body'])
            min_relevance: minimum relevance score threshold
            expand_synonyms: whether to expand query terms with synonyms
            
        returns:
            search response with results and metadata
        """
        import time
        start_time = time.time()
        
        # parse query
        parsed = self.query_parser.parse(query)
        query_terms = parsed['terms']
        operator = parsed['operator']
        
        # expand query terms with synonyms
        expanded_terms = set()
        for term in query_terms:
            expanded_terms.add(term)
            if expand_synonyms:
                synonym_forms = self.normalizer.get_all_forms(term)
                expanded_terms.update(synonym_forms)
        
        # search keywords
        all_keywords = self.repository.get_all_keywords()
        
        # filter by category if specified
        if categories:
            all_keywords = [kw for kw in all_keywords if kw.category in categories]
        
        # calculate total document count for IDF
        total_docs = sum(
            (kw.statistics.document_count if kw.statistics else 1)
            for kw in all_keywords
        )
        
        # score and filter results
        scored_results = []
        for kw in all_keywords:
            # check if keyword matches query
            matches, matched_terms = self._matches_query(
                kw.keyword_text,
                kw.normalized_form or kw.keyword_text,
                expanded_terms,
                operator
            )
            
            if not matches:
                continue
            
            # calculate relevance score (TF-IDF based)
            relevance = self._calculate_relevance(
                kw,
                matched_terms,
                total_docs
            )
            
            if relevance < min_relevance:
                continue
            
            # create search result
            doc_count = kw.statistics.document_count if kw.statistics else 1
            source_name = kw.sources[0].source_file if kw.sources else 'unknown'
            context_text = kw.sources[0].context if kw.sources else ""
            
            result = SearchResult(
                keyword_id=kw.keyword_id,
                keyword_text=kw.keyword_text,
                normalized_form=kw.normalized_form or kw.keyword_text,
                category=kw.category or 'unknown',
                source=source_name,
                document_count=doc_count,
                relevance_score=relevance,
                context=context_text,
                matched_query_terms=list(matched_terms)
            )
            
            # highlight matched terms in context
            result.highlighted_context = self._highlight_terms(
                result.context,
                matched_terms
            )
            
            scored_results.append(result)
        
        # sort by relevance (descending)
        scored_results.sort(key=lambda r: r.relevance_score, reverse=True)
        
        # paginate
        total_results = len(scored_results)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_results = scored_results[start_idx:end_idx]
        
        # calculate search time
        search_time = (time.time() - start_time) * 1000  # convert to ms
        
        return SearchResponse(
            query=query,
            total_results=total_results,
            page=page,
            page_size=page_size,
            results=page_results,
            expanded_query_terms=sorted(expanded_terms),
            search_time_ms=round(search_time, 2)
        )
    
    def _matches_query(
        self,
        keyword_text: str,
        normalized_form: str,
        query_terms: Set[str],
        operator: str
    ) -> Tuple[bool, Set[str]]:
        """
        check if keyword matches query terms.
        
        args:
            keyword_text: original keyword text
            normalized_form: normalized keyword form
            query_terms: set of expanded query terms
            operator: query operator (AND/OR/SINGLE)
            
        returns:
            tuple of (matches, set of matched terms)
        """
        keyword_lower = keyword_text.lower() if keyword_text else ""
        normalized_lower = normalized_form.lower() if normalized_form else ""
        
        matched_terms = set()
        
        # check each query term
        for term in query_terms:
            if term in keyword_lower or term in normalized_lower:
                matched_terms.add(term)
            # check if term is substring (for multi-word matching)
            elif term in keyword_lower.split() or term in normalized_lower.split():
                matched_terms.add(term)
        
        # apply operator logic
        if operator == 'AND':
            # all original query terms must match
            # (but synonyms count as matching their original term)
            return len(matched_terms) > 0, matched_terms
        elif operator == 'OR':
            # at least one term must match
            return len(matched_terms) > 0, matched_terms
        else:  # SINGLE
            return len(matched_terms) > 0, matched_terms
    
    def _calculate_relevance(
        self,
        keyword,
        matched_terms: Set[str],
        total_docs: int
    ) -> float:
        """
        calculate relevance score using TF-IDF approach.
        
        args:
            keyword: keyword object with statistics
            matched_terms: set of matched query terms
            total_docs: total document count in corpus
            
        returns:
            relevance score (0.0 to 1.0+)
        """
        # get document count from statistics
        doc_count = keyword.statistics.document_count if keyword.statistics else 1
        
        # base score: number of matched terms
        term_score = len(matched_terms)
        
        # TF component: document frequency (normalized)
        tf = doc_count / max(total_docs, 1)
        
        # IDF component: inverse document frequency
        # keywords that appear in fewer documents are more valuable
        idf = math.log(total_docs / max(doc_count, 1) + 1)
        
        # combine scores
        # higher tf = more common (lower value)
        # higher idf = more rare (higher value)
        tf_idf = tf * idf
        
        # final relevance: weighted combination
        relevance = (term_score * 0.5) + (tf_idf * 0.3) + (doc_count * 0.0001)
        
        # boost exact matches
        keyword_text_lower = keyword.keyword_text.lower() if keyword.keyword_text else ""
        if keyword_text_lower in matched_terms:
            relevance *= 1.5
        
        return round(relevance, 4)
    
    def _highlight_terms(
        self,
        context: str,
        matched_terms: Set[str],
        highlight_format: str = "**{term}**"
    ) -> str:
        """
        highlight matched terms in context.
        
        args:
            context: context text
            matched_terms: set of terms to highlight
            highlight_format: format string with {term} placeholder
            
        returns:
            context with highlighted terms
        """
        if not context:
            return ""
        
        highlighted = context
        
        # sort terms by length (longest first) to avoid partial replacements
        sorted_terms = sorted(matched_terms, key=len, reverse=True)
        
        for term in sorted_terms:
            # case-insensitive replacement
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            highlighted = pattern.sub(
                lambda m: highlight_format.format(term=m.group(0)),
                highlighted
            )
        
        return highlighted
    
    def search_by_category(
        self,
        query: str,
        category: str,
        page: int = 1,
        page_size: int = 20
    ) -> SearchResponse:
        """
        search within specific category.
        
        args:
            query: search query
            category: category to search (e.g., 'abstract', 'body')
            page: page number
            page_size: results per page
            
        returns:
            search response filtered by category
        """
        return self.search(
            query=query,
            page=page,
            page_size=page_size,
            categories=[category]
        )
    
    def search_by_source(
        self,
        query: str,
        source_pattern: str,
        page: int = 1,
        page_size: int = 20
    ) -> SearchResponse:
        """
        search within specific source(s).
        
        args:
            query: search query
            source_pattern: source pattern (e.g., '*.xml', '*.pdf')
            page: page number
            page_size: results per page
            
        returns:
            search response filtered by source
        """
        # perform search
        response = self.search(query=query, page=1, page_size=10000)
        
        # filter by source pattern
        import fnmatch
        filtered_results = [
            r for r in response.results
            if fnmatch.fnmatch(r.source.lower(), source_pattern.lower())
        ]
        
        # re-paginate
        total_results = len(filtered_results)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_results = filtered_results[start_idx:end_idx]
        
        return SearchResponse(
            query=query,
            total_results=total_results,
            page=page,
            page_size=page_size,
            results=page_results,
            expanded_query_terms=response.expanded_query_terms,
            search_time_ms=response.search_time_ms
        )
    
    def get_related_keywords(
        self,
        keyword: str,
        limit: int = 10
    ) -> List[SearchResult]:
        """
        get keywords related to given keyword.
        
        args:
            keyword: keyword to find related terms for
            limit: maximum number of results
            
        returns:
            list of related keywords
        """
        # normalize input keyword
        normalized = self.normalizer.normalize(keyword)
        
        # get all synonym forms
        synonym_forms = self.normalizer.get_all_forms(normalized)
        
        # search for each form
        all_results = []
        for form in synonym_forms:
            response = self.search(
                query=form,
                page=1,
                page_size=limit,
                expand_synonyms=False  # already expanded
            )
            all_results.extend(response.results)
        
        # deduplicate by keyword_id
        seen_ids = set()
        unique_results = []
        for result in all_results:
            if result.keyword_id not in seen_ids:
                seen_ids.add(result.keyword_id)
                unique_results.append(result)
        
        # sort by relevance and limit
        unique_results.sort(key=lambda r: r.relevance_score, reverse=True)
        return unique_results[:limit]
    
    def get_statistics(self) -> Dict[str, any]:
        """
        get search engine statistics.
        
        returns:
            dictionary of statistics
        """
        all_keywords = self.repository.get_all_keywords()
        
        stats = {
            'total_keywords': len(all_keywords),
            'total_documents': sum(kw.document_count for kw in all_keywords),
            'by_category': defaultdict(int),
            'top_keywords': [],
            'avg_document_count': 0
        }
        
        # count by category
        for kw in all_keywords:
            category = kw.category or 'unknown'
            stats['by_category'][category] += 1
        
        # top keywords by document count
        sorted_keywords = sorted(
            all_keywords,
            key=lambda k: k.statistics.document_count if k.statistics else 0,
            reverse=True
        )
        stats['top_keywords'] = [
            {
                'text': kw.keyword_text,
                'document_count': kw.statistics.document_count if kw.statistics else 0
            }
            for kw in sorted_keywords[:10]
        ]
        
        # average document count
        if all_keywords:
            doc_counts = [
                kw.statistics.document_count if kw.statistics else 0
                for kw in all_keywords
            ]
            stats['avg_document_count'] = round(
                sum(doc_counts) / len(all_keywords),
                2
            )
        
        return stats
