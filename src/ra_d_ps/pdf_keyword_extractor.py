"""
PDF keyword extractor for radiology research literature.

This module extracts keywords from research papers in PDF format, including:
- Metadata (title, authors, journal, year, DOI)
- Abstract content
- Author-provided keywords and MeSH terms
- Body text keywords with page tracking

Integrates with KeywordNormalizer for term standardization and
KeywordRepository for database persistence.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional, Set
import pdfplumber

from src.ra_d_ps.keyword_normalizer import KeywordNormalizer
from src.ra_d_ps.database.keyword_repository import KeywordRepository


@dataclass
class PDFMetadata:
    """metadata extracted from pdf document."""
    title: str = ""
    authors: List[str] = field(default_factory=list)
    journal: str = ""
    year: Optional[int] = None
    doi: str = ""
    abstract: str = ""
    author_keywords: List[str] = field(default_factory=list)
    mesh_terms: List[str] = field(default_factory=list)


@dataclass
class ExtractedPDFKeyword:
    """keyword extracted from pdf with context and location."""
    text: str
    category: str  # metadata, abstract, keyword, body
    page_number: int
    context: str = ""
    frequency: int = 1
    normalized_form: Optional[str] = None


class PDFKeywordExtractor:
    """extract keywords from pdf research papers."""
    
    def __init__(
        self,
        normalizer: Optional[KeywordNormalizer] = None,
        repository: Optional[KeywordRepository] = None
    ):
        """
        initialize pdf keyword extractor.
        
        args:
            normalizer: optional keyword normalizer for term standardization
            repository: optional keyword repository for database storage
        """
        self.normalizer = normalizer or KeywordNormalizer()
        self.repository = repository
        
        # patterns for section detection
        self.abstract_patterns = [
            r'\babstract\b',
            r'\bsummary\b',
            r'\bbackground\b'
        ]
        
        self.keyword_patterns = [
            r'\bkeywords?\b',
            r'\bkey\s+words?\b',
            r'\bindex\s+terms?\b',
            r'\bmesh\s+terms?\b'
        ]
        
        self.method_patterns = [
            r'\bmethods?\b',
            r'\bmaterials?\s+and\s+methods?\b',
            r'\bexperimental\s+design\b',
            r'\bstudy\s+design\b'
        ]
        
    def extract_from_pdf(
        self,
        pdf_path: str,
        store_in_db: bool = True,
        max_pages: Optional[int] = None
    ) -> tuple[PDFMetadata, List[ExtractedPDFKeyword]]:
        """
        extract keywords from pdf file.
        
        args:
            pdf_path: path to pdf file
            store_in_db: whether to store keywords in database
            max_pages: optional maximum number of pages to process
            
        returns:
            tuple of (metadata, list of extracted keywords)
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"pdf not found: {pdf_path}")
            
        metadata = PDFMetadata()
        all_keywords = []
        candidate_keywords = set()
        
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            pages_to_process = min(max_pages, total_pages) if max_pages else total_pages
            
            # extract metadata from first page
            if total_pages > 0:
                first_page_text = pdf.pages[0].extract_text() or ""
                metadata = self._extract_metadata(first_page_text, pdf.metadata or {})
            
            # extract keywords from each page
            for page_num, page in enumerate(pdf.pages[:pages_to_process], start=1):
                page_text = page.extract_text() or ""
                
                # extract abstract from first 2 pages
                if page_num <= 2 and not metadata.abstract:
                    abstract = self._extract_abstract(page_text)
                    if abstract:
                        metadata.abstract = abstract
                        abstract_keywords = self._extract_keywords_from_text(
                            abstract, 'abstract', page_num
                        )
                        all_keywords.extend(abstract_keywords)
                
                # extract author keywords from first 2 pages
                if page_num <= 2 and not metadata.author_keywords:
                    author_kws = self._extract_author_keywords(page_text)
                    if author_kws:
                        metadata.author_keywords = author_kws
                        for kw in author_kws:
                            all_keywords.append(ExtractedPDFKeyword(
                                text=kw,
                                category='keyword',
                                page_number=page_num,
                                frequency=1
                            ))
                
                # extract body text keywords
                body_keywords = self._extract_keywords_from_text(
                    page_text, 'body', page_num
                )
                all_keywords.extend(body_keywords)

                # --- Candidate keyword collection for approval ---
                # Find all unique words/phrases in the page text
                words = set(re.findall(r'\b[a-zA-Z][a-zA-Z\-]{2,}\b', page_text))
                # Remove known keywords (already in medical_terms or DB)
                known_terms = set(self.normalizer.multi_word_set)
                # Add all normalized forms from DB
                if self.repository:
                    db_keywords = {k.keyword_text.lower() for k in self.repository.get_all_keywords(limit=2000)}
                    known_terms.update(db_keywords)
                # Remove stopwords and connectors
                stopwords = self.normalizer.stopwords
                filtered = [w for w in words if w.lower() not in stopwords and w.lower() not in known_terms and len(w) > 2]
                # Heuristic: only keep capitalized or long words (likely technical)
                filtered = [w for w in filtered if w[0].isupper() or len(w) > 6]
                candidate_keywords.update(filtered)
        
        # consolidate duplicate keywords
        all_keywords = self._consolidate_keywords(all_keywords)
        
        # normalize keywords
        for keyword in all_keywords:
            normalized = self.normalizer.normalize(keyword.text)
            keyword.normalized_form = normalized
        
        # store in database if requested
        if store_in_db and self.repository:
            self._store_keywords_in_db(pdf_path.name, all_keywords, metadata)
            # Store candidate keywords for approval in a special sector
            for cand in candidate_keywords:
                # Only add if not already present
                self.repository.add_keyword_source(
                    keyword_id=self.repository.add_keyword(
                        keyword_text=cand,
                        category="pending_approval",
                        normalized_form=cand.lower()
                    ).keyword_id,
                    source_type="pdf",
                    source_file=str(pdf_path.name),
                    frequency=1,
                    context=None,
                    sector="pending_keywords",
                    page_number=None
                )
        
        return metadata, all_keywords
    
    def extract_from_multiple(
        self,
        pdf_paths: List[str],
        store_in_db: bool = True,
        max_pages_per_pdf: Optional[int] = None,
        progress_callback: Optional[callable] = None
    ) -> List[tuple[str, PDFMetadata, List[ExtractedPDFKeyword]]]:
        """
        extract keywords from multiple pdf files.
        
        args:
            pdf_paths: list of paths to pdf files
            store_in_db: whether to store keywords in database
            max_pages_per_pdf: optional maximum pages per pdf
            progress_callback: optional callback(current, total, filename)
            
        returns:
            list of (pdf_path, metadata, keywords) tuples
        """
        results = []
        total = len(pdf_paths)
        
        for i, pdf_path in enumerate(pdf_paths, start=1):
            try:
                if progress_callback:
                    progress_callback(i, total, Path(pdf_path).name)
                
                metadata, keywords = self.extract_from_pdf(
                    pdf_path,
                    store_in_db=store_in_db,
                    max_pages=max_pages_per_pdf
                )
                results.append((pdf_path, metadata, keywords))
                
            except Exception as e:
                print(f"error processing {pdf_path}: {e}")
                continue
        
        return results
    
    def _extract_metadata(
        self,
        first_page_text: str,
        pdf_metadata: Dict
    ) -> PDFMetadata:
        """
        extract metadata from first page and pdf metadata.
        
        args:
            first_page_text: text from first page
            pdf_metadata: pdf metadata dictionary
            
        returns:
            extracted metadata
        """
        metadata = PDFMetadata()
        
        # try to extract title from pdf metadata or first page
        if 'Title' in pdf_metadata:
            metadata.title = pdf_metadata['Title']
        else:
            # first non-empty line is often the title
            lines = [line.strip() for line in first_page_text.split('\n') if line.strip()]
            if lines:
                metadata.title = lines[0]
        
        # extract year from text
        year_match = re.search(r'\b(19|20)\d{2}\b', first_page_text)
        if year_match:
            metadata.year = int(year_match.group())
        
        # extract doi
        doi_match = re.search(r'doi:\s*([^\s]+)', first_page_text, re.IGNORECASE)
        if doi_match:
            metadata.doi = doi_match.group(1)
        
        # extract authors (simple heuristic: capitalized names near top)
        author_pattern = r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b'
        author_matches = re.findall(author_pattern, first_page_text[:500])
        metadata.authors = list(set(author_matches[:10]))  # limit to first 10 unique
        
        return metadata
    
    def _extract_abstract(self, text: str) -> str:
        """
        extract abstract section from text.
        
        args:
            text: page text
            
        returns:
            abstract text or empty string
        """
        text_lower = text.lower()
        
        # find abstract section
        for pattern in self.abstract_patterns:
            match = re.search(pattern, text_lower)
            if match:
                start_pos = match.end()
                
                # find end of abstract (next section heading or empty line)
                end_patterns = [
                    r'\b(introduction|background|methods|keywords)\b',
                    r'\n\n',
                ]
                
                end_pos = len(text)
                for end_pattern in end_patterns:
                    end_match = re.search(end_pattern, text_lower[start_pos:])
                    if end_match:
                        end_pos = start_pos + end_match.start()
                        break
                
                abstract = text[start_pos:end_pos].strip()
                
                # clean up abstract
                abstract = re.sub(r'\s+', ' ', abstract)
                return abstract[:2000]  # limit to 2000 chars
        
        return ""
    
    def _extract_author_keywords(self, text: str) -> List[str]:
        """
        extract author-provided keywords from text.
        
        args:
            text: page text
            
        returns:
            list of keywords
        """
        text_lower = text.lower()
        keywords = []
        
        # find keywords section
        for pattern in self.keyword_patterns:
            match = re.search(pattern, text_lower)
            if match:
                start_pos = match.end()
                
                # extract next 200 chars after "Keywords:"
                keyword_text = text[start_pos:start_pos + 200]
                
                # split by common delimiters
                kw_parts = re.split(r'[;,\n]', keyword_text)
                
                for kw in kw_parts:
                    kw = kw.strip().rstrip('.')
                    if kw and len(kw) > 2 and len(kw) < 50:
                        keywords.append(kw)
                
                break
        
        return keywords[:20]  # limit to 20 keywords
    
    def _extract_keywords_from_text(
        self,
        text: str,
        category: str,
        page_number: int
    ) -> List[ExtractedPDFKeyword]:
        """
        extract keywords from text using multi-word detection and filtering.
        
        args:
            text: text to extract from
            category: keyword category
            page_number: page number
            
        returns:
            list of extracted keywords
        """
        keywords = []
        
        # detect multi-word medical terms
        multi_word_terms = self.normalizer.detect_multi_word_terms(text)
        
        # create set for tracking positions
        used_positions = set()
        for term, start, end in multi_word_terms:
            for pos in range(start, end):
                used_positions.add(pos)
            
            # get context snippet
            context_start = max(0, start - 50)
            context_end = min(len(text), end + 50)
            context = text[context_start:context_end].strip()
            
            keywords.append(ExtractedPDFKeyword(
                text=term,
                category=category,
                page_number=page_number,
                context=context,
                frequency=1
            ))
        
        # extract single-word terms (not in used positions)
        words = re.findall(r'\b[a-zA-Z]+\b', text)
        for word in words:
            # skip short words and stopwords
            if len(word) < 3:
                continue
            
            word_lower = word.lower()
            
            # check if stopword
            if self.normalizer.filter_stopwords([word_lower]) == []:
                continue
            
            # check if medical term
            normalized = self.normalizer.normalize(word_lower)
            if normalized != word_lower or word_lower in self.normalizer.medical_terms.get('anatomical_terms', []):
                # find position in text
                pos = text.lower().find(word_lower)
                if pos != -1 and pos not in used_positions:
                    context_start = max(0, pos - 50)
                    context_end = min(len(text), pos + len(word) + 50)
                    context = text[context_start:context_end].strip()
                    
                    keywords.append(ExtractedPDFKeyword(
                        text=word_lower,
                        category=category,
                        page_number=page_number,
                        context=context,
                        frequency=1
                    ))
        
        return keywords
    
    def _consolidate_keywords(
        self,
        keywords: List[ExtractedPDFKeyword]
    ) -> List[ExtractedPDFKeyword]:
        """
        consolidate duplicate keywords by summing frequencies.
        
        args:
            keywords: list of extracted keywords
            
        returns:
            list of consolidated keywords
        """
        keyword_map: Dict[tuple, ExtractedPDFKeyword] = {}
        
        for kw in keywords:
            key = (kw.text.lower(), kw.category)
            
            if key in keyword_map:
                keyword_map[key].frequency += 1
            else:
                keyword_map[key] = kw
        
        return list(keyword_map.values())
    
    def get_statistics(self) -> Dict[str, int]:
        """
        get extraction statistics from database.
        
        returns:
            dictionary of statistics
        """
        if not self.repository:
            return {}
        
        stats = {
            'total_keywords': 0,
            'unique_keywords': 0,
            'by_category': {}
        }
        
        all_keywords = self.repository.get_all_keywords()
        stats['total_keywords'] = sum(kw.document_count for kw in all_keywords)
        stats['unique_keywords'] = len(all_keywords)
        
        # count by category
        for kw in all_keywords:
            category = kw.category or 'unknown'
            stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
        
        return stats
    
    def _store_keywords_in_db(
        self,
        source_file: str,
        keywords: List[ExtractedPDFKeyword],
        metadata: PDFMetadata
    ):
        """
        Store extracted keywords and text blocks in database with dedicated sectors.
        
        Sectors used:
        - pdf_keywords: Actual keywords extracted from PDFs
        - text_storage: Full-text context and abstracts
        - research_papers: Legacy sector for frequency tracking
        
        Args:
            source_file: Name of the PDF file
            keywords: List of extracted keywords
            metadata: PDF metadata including abstract
        """
        # Store abstract as a text block if available
        if metadata.abstract:
            abstract_kw = self.repository.add_keyword(
                keyword_text="abstract",
                category="metadata",
                normalized_form="abstract"
            )
            self.repository.add_text_block(
                keyword_id=abstract_kw.keyword_id,
                text=metadata.abstract,
                source_file=source_file,
                sector="text_storage"
            )
        
        # Store each keyword with its context in dedicated sectors
        for keyword in keywords:
            # Add or get keyword
            kw = self.repository.add_keyword(
                keyword_text=keyword.text,
                category=keyword.category,
                normalized_form=keyword.normalized_form
            )
            
            # Add to pdf_keywords sector (dedicated for PDF extractions)
            self.repository.add_keyword_source(
                keyword_id=kw.keyword_id,
                source_type="pdf",
                source_file=source_file,
                frequency=keyword.frequency,
                context=keyword.context[:500] if keyword.context else None,
                sector="pdf_keywords",
                page_number=keyword.page_number
            )
            
            # Also add to research_papers sector for backward compatibility
            self.repository.add_keyword_source(
                keyword_id=kw.keyword_id,
                source_type="pdf",
                source_file=source_file,
                frequency=keyword.frequency,
                context=keyword.context[:500] if keyword.context else None,
                sector="research_papers",
                page_number=keyword.page_number
            )
            
            # Store full context as text block if available
            if keyword.context:
                self.repository.add_text_block(
                    keyword_id=kw.keyword_id,
                    text=keyword.context,
                    source_file=f"{source_file}#page{keyword.page_number}",
                    sector="text_storage"
                )
