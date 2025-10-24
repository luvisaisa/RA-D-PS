# Phase 5C: Keyword Extraction Pipeline Implementation Plan

**Status:** In Progress  
**Started:** October 19, 2025  
**Goal:** Extract, normalize, and index keywords from XML annotations, PDFs, and research papers

## Overview

Implement a comprehensive keyword extraction system that:
1. Extracts keywords from XML annotations (LIDC-IDRI characteristics)
2. Parses PDF metadata and extracts keywords/abstract text
3. Normalizes medical terminology (handle synonyms, abbreviations)
4. Stores keywords in PostgreSQL with frequency tracking
5. Supports TF-IDF ranking and cross-sector search
6. Enables GUI highlighting and snippet extraction

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Keyword Extraction Pipeline                │
└─────────────────────────────────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
    ┌─────────┐      ┌─────────┐    ┌────────────┐
    │   XML   │      │   PDF   │    │  Research  │
    │ Parser  │      │ Parser  │    │   Papers   │
    └─────────┘      └─────────┘    └────────────┘
          │                │                │
          └────────────────┼────────────────┘
                           │
                           ▼
              ┌──────────────────────┐
              │  Keyword Normalizer  │
              │  - Synonyms          │
              │  - Abbreviations     │
              │  - Medical terms     │
              └──────────────────────┘
                           │
                           ▼
              ┌──────────────────────┐
              │  PostgreSQL Storage  │
              │  - keywords table    │
              │  - keyword_index     │
              │  - keyword_sources   │
              └──────────────────────┘
                           │
                           ▼
              ┌──────────────────────┐
              │   Search & Ranking   │
              │  - TF-IDF scoring    │
              │  - Boolean queries   │
              │  - Highlighting      │
              └──────────────────────┘
```

## Implementation Phases

### Phase 1: Database Schema (Day 1) ✅ CURRENT
**Goal:** Design PostgreSQL schema for keyword storage

#### Tables
```sql
-- Core keyword table
CREATE TABLE keywords (
    keyword_id SERIAL PRIMARY KEY,
    keyword_text VARCHAR(255) NOT NULL UNIQUE,
    normalized_form VARCHAR(255),
    category VARCHAR(100),  -- 'anatomy', 'characteristic', 'diagnosis', 'metadata'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Keyword sources (which documents contain which keywords)
CREATE TABLE keyword_sources (
    source_id SERIAL PRIMARY KEY,
    keyword_id INTEGER REFERENCES keywords(keyword_id),
    source_type VARCHAR(50),  -- 'xml', 'pdf', 'research_paper'
    source_file VARCHAR(500),  -- file path or identifier
    sector VARCHAR(100),  -- 'lidc_annotations', 'research_papers', etc.
    frequency INTEGER DEFAULT 1,  -- count in this document
    tf_idf_score FLOAT,  -- term frequency-inverse document frequency
    context TEXT,  -- surrounding text for snippet
    page_number INTEGER,  -- for PDFs
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(keyword_id, source_type, source_file)
);

-- Keyword statistics (global metrics)
CREATE TABLE keyword_statistics (
    keyword_id INTEGER PRIMARY KEY REFERENCES keywords(keyword_id),
    total_frequency INTEGER DEFAULT 0,
    document_count INTEGER DEFAULT 0,  -- number of documents containing keyword
    idf_score FLOAT,  -- inverse document frequency (cached)
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Keyword synonyms and normalization rules
CREATE TABLE keyword_synonyms (
    synonym_id SERIAL PRIMARY KEY,
    synonym_text VARCHAR(255) NOT NULL,
    canonical_keyword_id INTEGER REFERENCES keywords(keyword_id),
    synonym_type VARCHAR(50),  -- 'abbreviation', 'medical_term', 'alternate_spelling'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for fast search
CREATE INDEX idx_keywords_text ON keywords(keyword_text);
CREATE INDEX idx_keywords_normalized ON keywords(normalized_form);
CREATE INDEX idx_keyword_sources_file ON keyword_sources(source_file);
CREATE INDEX idx_keyword_sources_sector ON keyword_sources(sector);
CREATE INDEX idx_keyword_sources_tfidf ON keyword_sources(tf_idf_score DESC);
CREATE INDEX idx_keyword_statistics_freq ON keyword_statistics(total_frequency DESC);
```

#### Repository Interface
```python
class KeywordRepository:
    def __init__(self, database: str = "ra_d_ps")
    
    # Keyword CRUD
    def add_keyword(self, text: str, category: str = None) -> Keyword
    def get_keyword(self, keyword_id: int) -> Keyword
    def get_keyword_by_text(self, text: str) -> Keyword
    def search_keywords(self, query: str, limit: int = 50) -> List[Keyword]
    
    # Source tracking
    def add_keyword_source(self, keyword_id: int, source_type: str, 
                          source_file: str, context: str = None) -> KeywordSource
    def get_sources_for_keyword(self, keyword_id: int) -> List[KeywordSource]
    def get_keywords_for_source(self, source_file: str) -> List[Keyword]
    
    # Statistics
    def update_keyword_statistics(self, keyword_id: int) -> None
    def calculate_tfidf_scores(self, source_file: str) -> None
    def get_top_keywords(self, limit: int = 100) -> List[Tuple[Keyword, int]]
    
    # Synonyms
    def add_synonym(self, synonym: str, canonical_keyword_id: int) -> None
    def get_canonical_form(self, text: str) -> Keyword
```

### Phase 2: XML Keyword Extraction (Day 1-2)
**Goal:** Extract keywords from LIDC-IDRI XML annotations

#### Extraction Sources
1. **Characteristics** - `subtlety`, `malignancy`, `calcification`, etc.
2. **Anatomical terms** - nodule locations, structures
3. **Diagnostic reasons** - `reason` field text
4. **Metadata** - Study UID, modality, annotations

#### Implementation
```python
# src/ra_d_ps/keyword_extractor.py

class XMLKeywordExtractor:
    """Extract keywords from LIDC-IDRI XML files"""
    
    def __init__(self, keyword_repo: KeywordRepository):
        self.repo = keyword_repo
        self.stopwords = self._load_stopwords()
        self.medical_terms = self._load_medical_dictionary()
    
    def extract_from_xml(self, xml_path: str) -> List[Keyword]:
        """
        Extract all keywords from XML file.
        Returns list of Keyword objects with context.
        """
        keywords = []
        
        # 1. Parse XML
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # 2. Extract from characteristics
        keywords.extend(self._extract_characteristics(root))
        
        # 3. Extract from diagnostic text
        keywords.extend(self._extract_diagnostic_text(root))
        
        # 4. Extract anatomical terms
        keywords.extend(self._extract_anatomical_terms(root))
        
        # 5. Store in database
        for keyword in keywords:
            self.repo.add_keyword_source(
                keyword_id=keyword.id,
                source_type='xml',
                source_file=xml_path,
                context=keyword.context
            )
        
        return keywords
    
    def _extract_characteristics(self, root) -> List[Keyword]:
        """Extract LIDC characteristic values as keywords"""
        characteristics = [
            'subtlety', 'malignancy', 'internalStructure',
            'calcification', 'sphericity', 'margin',
            'lobulation', 'spiculation', 'texture',
            'confidence', 'obscuration'
        ]
        
        keywords = []
        for char in characteristics:
            elements = root.findall(f'.//{char}')
            for elem in elements:
                if elem.text:
                    # Create keyword with context
                    keyword_text = f"{char}:{elem.text}"
                    keywords.append(Keyword(
                        text=keyword_text,
                        category='characteristic',
                        context=f"Characteristic {char} = {elem.text}"
                    ))
        
        return keywords
    
    def _extract_diagnostic_text(self, root) -> List[Keyword]:
        """Extract keywords from 'reason' and diagnostic fields"""
        reason_elements = root.findall('.//reason')
        keywords = []
        
        for reason_elem in reason_elements:
            if reason_elem.text:
                # Tokenize diagnostic text
                tokens = self._tokenize_medical_text(reason_elem.text)
                for token in tokens:
                    if token not in self.stopwords:
                        keywords.append(Keyword(
                            text=token,
                            category='diagnosis',
                            context=reason_elem.text[:200]  # snippet
                        ))
        
        return keywords
    
    def _tokenize_medical_text(self, text: str) -> List[str]:
        """Tokenize medical text, preserving multi-word terms"""
        # Split on whitespace and punctuation
        tokens = re.findall(r'\b\w+\b', text.lower())
        
        # Check for known medical multi-word terms
        # e.g., "ground glass opacity", "pleural effusion"
        for term in self.medical_terms:
            if term in text.lower():
                tokens.append(term)
        
        return list(set(tokens))
```

### Phase 3: PDF Keyword Extraction (Day 2-3)
**Goal:** Parse PDF metadata and extract keywords from research papers

#### Dependencies
- `PyPDF2` or `pdfplumber` for PDF parsing
- `python-magic` for file type detection

#### Implementation
```python
# src/ra_d_ps/pdf_keyword_extractor.py

import pdfplumber
from typing import List, Dict

class PDFKeywordExtractor:
    """Extract keywords from PDF research papers"""
    
    def __init__(self, keyword_repo: KeywordRepository):
        self.repo = keyword_repo
        self.medical_terms = self._load_medical_dictionary()
    
    def extract_from_pdf(self, pdf_path: str) -> Dict:
        """
        Extract keywords, abstract, and metadata from PDF.
        
        Returns:
            {
                'metadata': {...},
                'keywords': [Keyword, ...],
                'abstract': str,
                'citations': [...]
            }
        """
        result = {
            'metadata': {},
            'keywords': [],
            'abstract': None,
            'citations': []
        }
        
        with pdfplumber.open(pdf_path) as pdf:
            # 1. Extract metadata
            result['metadata'] = self._extract_metadata(pdf)
            
            # 2. Extract abstract (usually first page)
            result['abstract'] = self._extract_abstract(pdf)
            
            # 3. Extract keywords from metadata
            if 'Keywords' in result['metadata']:
                result['keywords'].extend(
                    self._parse_metadata_keywords(result['metadata']['Keywords'])
                )
            
            # 4. Extract keywords from abstract
            if result['abstract']:
                result['keywords'].extend(
                    self._extract_from_text(result['abstract'])
                )
            
            # 5. Store in database
            for keyword in result['keywords']:
                self.repo.add_keyword_source(
                    keyword_id=keyword.id,
                    source_type='pdf',
                    source_file=pdf_path,
                    context=keyword.context,
                    page_number=keyword.page_number
                )
        
        return result
    
    def _extract_abstract(self, pdf) -> str:
        """Extract abstract from first 2 pages"""
        abstract = None
        
        for page in pdf.pages[:2]:
            text = page.extract_text()
            
            # Look for abstract section
            match = re.search(
                r'abstract[:\s]+(.+?)(?:introduction|keywords|1\.|$)',
                text.lower(),
                re.DOTALL | re.IGNORECASE
            )
            
            if match:
                abstract = match.group(1).strip()
                break
        
        return abstract
```

### Phase 4: Keyword Normalization (Day 3-4)
**Goal:** Normalize medical terminology and handle synonyms

#### Medical Term Dictionary
Create `data/medical_terms.json`:
```json
{
  "synonyms": {
    "pulmonary": ["lung", "pneumonic"],
    "nodule": ["lesion", "mass", "opacity"],
    "malignant": ["cancerous", "malignancy"],
    "benign": ["non-malignant", "non-cancerous"]
  },
  "abbreviations": {
    "CT": "computed tomography",
    "LIDC": "lung image database consortium",
    "GGO": "ground glass opacity",
    "SPN": "solitary pulmonary nodule"
  },
  "multi_word_terms": [
    "ground glass opacity",
    "pleural effusion",
    "hilar lymphadenopathy",
    "air bronchogram"
  ]
}
```

#### Normalizer Implementation
```python
# src/ra_d_ps/keyword_normalizer.py

class KeywordNormalizer:
    """Normalize medical terminology and handle synonyms"""
    
    def __init__(self, dictionary_path: str = "data/medical_terms.json"):
        self.dictionary = self._load_dictionary(dictionary_path)
        self.synonyms = self.dictionary['synonyms']
        self.abbreviations = self.dictionary['abbreviations']
    
    def normalize(self, keyword: str) -> str:
        """
        Normalize keyword to canonical form.
        
        Examples:
            "lung" -> "pulmonary"
            "CT" -> "computed_tomography"
            "mass" -> "nodule"
        """
        keyword_lower = keyword.lower()
        
        # 1. Expand abbreviations
        if keyword_lower in self.abbreviations:
            keyword_lower = self.abbreviations[keyword_lower]
        
        # 2. Find canonical form from synonyms
        for canonical, synonyms in self.synonyms.items():
            if keyword_lower in synonyms or keyword_lower == canonical:
                return canonical
        
        # 3. Return original if no normalization found
        return keyword_lower
    
    def get_all_forms(self, keyword: str) -> List[str]:
        """Get all synonym forms of a keyword for search"""
        canonical = self.normalize(keyword)
        
        if canonical in self.synonyms:
            return [canonical] + self.synonyms[canonical]
        
        return [canonical]
```

### Phase 5: Search & TF-IDF Ranking (Day 4-5)
**Goal:** Implement search with relevance ranking

#### Search Interface
```python
# src/ra_d_ps/keyword_search.py

class KeywordSearchEngine:
    """Search keywords with TF-IDF ranking"""
    
    def __init__(self, keyword_repo: KeywordRepository):
        self.repo = keyword_repo
        self.normalizer = KeywordNormalizer()
    
    def search(self, query: str, sector: str = None, 
               limit: int = 50) -> List[SearchResult]:
        """
        Search keywords with relevance ranking.
        
        Args:
            query: Search string (supports boolean AND/OR)
            sector: Filter by sector ('lidc_annotations', 'research_papers')
            limit: Max results to return
            
        Returns:
            List of SearchResult objects ranked by TF-IDF score
        """
        # 1. Normalize query terms
        query_terms = self._parse_query(query)
        
        # 2. Expand synonyms
        expanded_terms = []
        for term in query_terms:
            expanded_terms.extend(self.normalizer.get_all_forms(term))
        
        # 3. Execute search
        results = self.repo.search_keywords_tfidf(
            terms=expanded_terms,
            sector=sector,
            limit=limit
        )
        
        # 4. Rank by TF-IDF
        ranked_results = self._rank_results(results, query_terms)
        
        return ranked_results
    
    def _calculate_tfidf(self, term_freq: int, doc_count: int, 
                         total_docs: int) -> float:
        """Calculate TF-IDF score"""
        import math
        
        tf = term_freq
        idf = math.log(total_docs / (1 + doc_count))
        return tf * idf
```

## Testing Strategy

### Unit Tests
```python
# tests/test_keyword_extraction.py

def test_xml_keyword_extraction():
    """Test XML keyword extraction"""
    extractor = XMLKeywordExtractor(mock_repo)
    keywords = extractor.extract_from_xml("examples/test.xml")
    
    assert len(keywords) > 0
    assert any(k.category == 'characteristic' for k in keywords)
    assert any(k.category == 'diagnosis' for k in keywords)

def test_keyword_normalization():
    """Test keyword normalization"""
    normalizer = KeywordNormalizer()
    
    assert normalizer.normalize("lung") == "pulmonary"
    assert normalizer.normalize("CT") == "computed_tomography"
    assert normalizer.normalize("mass") == "nodule"

def test_tfidf_ranking():
    """Test TF-IDF ranking"""
    # Setup test documents with known frequencies
    # Verify TF-IDF scores are calculated correctly
    pass
```

### Integration Tests
```python
# tests/integration/test_keyword_pipeline.py

def test_full_keyword_pipeline():
    """Test end-to-end keyword extraction and search"""
    # 1. Extract keywords from test XML
    # 2. Store in database
    # 3. Search for keywords
    # 4. Verify results are ranked correctly
    pass
```

## Timeline

| Day | Task | Status |
|-----|------|--------|
| 1 | Database schema design & creation | ⏳ Pending |
| 1 | KeywordRepository implementation | ⏳ Pending |
| 2 | XMLKeywordExtractor implementation | ⏳ Pending |
| 2 | Unit tests for XML extraction | ⏳ Pending |
| 3 | PDFKeywordExtractor implementation | ⏳ Pending |
| 3 | Medical term dictionary creation | ⏳ Pending |
| 4 | KeywordNormalizer implementation | ⏳ Pending |
| 4 | Synonym database population | ⏳ Pending |
| 5 | KeywordSearchEngine implementation | ⏳ Pending |
| 5 | TF-IDF ranking and integration tests | ⏳ Pending |

## Success Criteria

✅ Keyword extraction works for all 5 parse case formats  
✅ PDF parsing extracts abstract and metadata keywords  
✅ Medical term normalization handles common synonyms  
✅ Search returns relevant results ranked by TF-IDF  
✅ All tests passing (unit + integration)  
✅ Performance: <50ms extraction per XML file  
✅ Database queries: <10ms for keyword search

## Next Steps

1. **Create database schema** - Run SQL migration
2. **Implement KeywordRepository** - CRUD operations
3. **Build XMLKeywordExtractor** - Start with characteristics
4. **Test with XML-COMP dataset** - Validate extraction accuracy
5. **Iterate based on results** - Refine normalization rules

---

**References:**
- LIDC-IDRI Documentation: https://wiki.cancerimagingarchive.net/display/Public/LIDC-IDRI
- TF-IDF Algorithm: https://en.wikipedia.org/wiki/Tf%E2%80%93idf
- Medical Terminology: UMLS (Unified Medical Language System)
