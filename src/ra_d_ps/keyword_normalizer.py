"""
Keyword Normalizer

Normalizes medical keywords using synonyms, abbreviations, and medical terminology.
Supports canonical form mapping and synonym expansion for search queries.

Database: PostgreSQL (ra_d_ps) via KeywordRepository
Dictionary: data/medical_terms.json
"""

import json
import logging
from typing import List, Dict, Set, Optional, Tuple
from pathlib import Path

from .database.keyword_repository import KeywordRepository

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KeywordNormalizer:
    """
    Normalize medical keywords using medical terminology dictionary.
    
    Features:
    - Synonym mapping (lung → pulmonary)
    - Abbreviation expansion (CT → computed tomography)
    - Multi-word term detection (ground glass opacity)
    - Canonical form mapping for database storage
    - Synonym expansion for search queries
    - LIDC characteristic value mapping
    - Medical stopword filtering
    """
    
    def __init__(self, medical_terms_path: str = None, 
                 keyword_repo: KeywordRepository = None):
        """
        Initialize keyword normalizer.
        
        Args:
            medical_terms_path: Path to medical_terms.json (default: data/medical_terms.json)
            keyword_repo: KeywordRepository instance (optional, for database synonym lookups)
        """
        self.repo = keyword_repo
        
        # Load medical terms dictionary
        if medical_terms_path is None:
            # Default path relative to this file
            base_dir = Path(__file__).parent.parent.parent
            medical_terms_path = base_dir / "data" / "medical_terms.json"
        
        self.medical_terms = self._load_medical_terms(medical_terms_path)
        
        # Build reverse lookup maps for fast normalization
        self._build_lookup_maps()
        
        logger.info(f"KeywordNormalizer initialized with {len(self.synonym_map)} synonym mappings")
    
    def _load_medical_terms(self, path: str) -> Dict:
        """
        Load medical terms dictionary from JSON.
        
        Args:
            path: Path to medical_terms.json
            
        Returns:
            Dictionary with medical terms
        """
        try:
            with open(path, 'r') as f:
                terms = json.load(f)
            
            logger.debug(f"Loaded medical terms from {path}")
            return terms
        
        except FileNotFoundError:
            logger.warning(f"Medical terms file not found: {path}. Using empty dictionary.")
            return {
                'synonyms': {},
                'abbreviations': {},
                'multi_word_terms': [],
                'stopwords': []
            }
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing medical terms JSON: {e}")
            raise
    
    def _build_lookup_maps(self):
        """
        Build reverse lookup maps for fast normalization.
        
        Creates:
        - synonym_map: term → canonical_form
        - abbreviation_map: abbr → full_form
        - multi_word_set: set of multi-word terms
        """
        # Build synonym map (bidirectional)
        self.synonym_map = {}
        
        for canonical, synonyms in self.medical_terms.get('synonyms', {}).items():
            # Map canonical to itself
            self.synonym_map[canonical.lower()] = canonical.lower()
            
            # Map each synonym to canonical
            for syn in synonyms:
                self.synonym_map[syn.lower()] = canonical.lower()
        
        # Build abbreviation map
        self.abbreviation_map = {
            abbr.lower(): full.lower() 
            for abbr, full in self.medical_terms.get('abbreviations', {}).items()
        }
        
        # Build multi-word term set (for tokenization)
        self.multi_word_set = set(
            term.lower() for term in self.medical_terms.get('multi_word_terms', [])
        )
        
        # Get stopwords
        self.stopwords = set(
            word.lower() for word in self.medical_terms.get('stopwords', [])
        )
        
        logger.debug(f"Built lookup maps: {len(self.synonym_map)} synonyms, "
                    f"{len(self.abbreviation_map)} abbreviations, "
                    f"{len(self.multi_word_set)} multi-word terms")
    
    def normalize(self, keyword: str, expand_abbreviations: bool = True) -> str:
        """
        Normalize a keyword to its canonical form.
        
        Args:
            keyword: Input keyword
            expand_abbreviations: Whether to expand abbreviations (default: True)
            
        Returns:
            Normalized canonical form
            
        Examples:
            normalize("lung") → "pulmonary"
            normalize("CT") → "computed tomography"
            normalize("GGO") → "ground glass opacity"
        """
        keyword_lower = keyword.lower().strip()
        
        # Step 1: Check if it's an abbreviation
        if expand_abbreviations and keyword_lower in self.abbreviation_map:
            keyword_lower = self.abbreviation_map[keyword_lower]
        
        # Step 2: Check if it's a synonym
        if keyword_lower in self.synonym_map:
            return self.synonym_map[keyword_lower]
        
        # Step 3: Check database for stored synonyms (if repo available)
        if self.repo:
            canonical = self.repo.get_canonical_keyword(keyword_lower)
            if canonical:
                return canonical.keyword_text.lower()
        
        # Step 4: Return original (lowercased) if no mapping found
        return keyword_lower
    
    def get_all_forms(self, keyword: str) -> List[str]:
        """
        Get all synonym forms of a keyword (for search expansion).
        
        Args:
            keyword: Input keyword
            
        Returns:
            List of all synonym forms (including canonical)
            
        Examples:
            get_all_forms("pulmonary") → ["pulmonary", "lung", "pneumonic", "pulmonic"]
            get_all_forms("nodule") → ["nodule", "lesion", "mass", "growth", "tumor"]
        """
        # Normalize to canonical form first
        canonical = self.normalize(keyword)
        
        # Find all synonyms for this canonical form
        synonyms = [canonical]
        
        # Check medical_terms.json
        for canon, syns in self.medical_terms.get('synonyms', {}).items():
            if canon.lower() == canonical:
                synonyms.extend([s.lower() for s in syns])
                break
        
        # Check database for stored synonyms (if repo available)
        if self.repo:
            # Get keyword from database
            db_keyword = self.repo.get_keyword_by_text(canonical)
            if db_keyword:
                db_synonyms = self.repo.get_synonyms_for_keyword(db_keyword.keyword_id)
                synonyms.extend([s.synonym_text.lower() for s in db_synonyms])
        
        # Remove duplicates and return
        return list(set(synonyms))
    
    def is_stopword(self, word: str) -> bool:
        """
        Check if a word is a medical stopword.
        
        Args:
            word: Input word
            
        Returns:
            True if word is a stopword
        """
        return word.lower() in self.stopwords
    
    def is_multi_word_term(self, text: str) -> bool:
        """
        Check if text matches a known multi-word medical term.
        
        Args:
            text: Input text
            
        Returns:
            True if text is a multi-word term
        """
        return text.lower() in self.multi_word_set
    
    def detect_multi_word_terms(self, text: str) -> List[Tuple[str, int, int]]:
        """
        Detect multi-word medical terms in text.
        
        Args:
            text: Input text
            
        Returns:
            List of (term, start_pos, end_pos) tuples
            
        Example:
            detect_multi_word_terms("patient has ground glass opacity")
            → [("ground glass opacity", 12, 32)]
        """
        text_lower = text.lower()
        detected = []
        
        # Sort multi-word terms by length (longest first) to prioritize longer matches
        sorted_terms = sorted(self.multi_word_set, key=len, reverse=True)
        
        for term in sorted_terms:
            start = 0
            while True:
                pos = text_lower.find(term, start)
                if pos == -1:
                    break
                
                # Check word boundaries
                before_ok = pos == 0 or not text_lower[pos-1].isalnum()
                after_ok = pos + len(term) == len(text_lower) or not text_lower[pos + len(term)].isalnum()
                
                if before_ok and after_ok:
                    detected.append((term, pos, pos + len(term)))
                
                start = pos + 1
        
        # Sort by position
        detected.sort(key=lambda x: x[1])
        
        return detected
    
    def normalize_characteristic_value(self, characteristic: str, value: str) -> str:
        """
        Normalize LIDC characteristic values to descriptive text.
        
        Args:
            characteristic: Characteristic name (e.g., 'subtlety', 'malignancy')
            value: Numeric or text value
            
        Returns:
            Normalized descriptive text
            
        Examples:
            normalize_characteristic_value("subtlety", "5") → "obvious"
            normalize_characteristic_value("malignancy", "1") → "highly unlikely malignant"
        """
        char_values = self.medical_terms.get('characteristic_values', {})
        
        if characteristic.lower() not in char_values:
            return value  # Return original if not found
        
        value_map = char_values[characteristic.lower()]
        
        if value not in value_map:
            return value  # Return original if not found
        
        # Return first descriptor for this value
        descriptors = value_map[value]
        return descriptors[0] if descriptors else value
    
    def get_anatomical_terms(self, region: str = None) -> List[str]:
        """
        Get list of anatomical terms, optionally filtered by region.
        
        Args:
            region: Anatomical region (e.g., 'lobes', 'airways', 'vasculature')
            
        Returns:
            List of anatomical terms
        """
        anatomical = self.medical_terms.get('anatomical_terms', {})
        
        if region:
            return anatomical.get(region, [])
        
        # Return all anatomical terms (flattened)
        all_terms = []
        for terms_list in anatomical.values():
            all_terms.extend(terms_list)
        
        return all_terms
    
    def get_diagnostic_terms(self, category: str = None) -> List[str]:
        """
        Get list of diagnostic terms, optionally filtered by category.
        
        Args:
            category: Diagnostic category (e.g., 'benign', 'malignant', 'infectious')
            
        Returns:
            List of diagnostic terms
        """
        diagnostic = self.medical_terms.get('diagnostic_terms', {})
        
        if category:
            return diagnostic.get(category, [])
        
        # Return all diagnostic terms (flattened)
        all_terms = []
        for terms_list in diagnostic.values():
            all_terms.extend(terms_list)
        
        return all_terms
    
    def expand_abbreviation(self, abbr: str) -> Optional[str]:
        """
        Expand a medical abbreviation.
        
        Args:
            abbr: Abbreviation to expand
            
        Returns:
            Full form, or None if not found
        """
        return self.abbreviation_map.get(abbr.lower())
    
    def get_modality_terms(self, modality: str = None) -> List[str]:
        """
        Get imaging modality terms.
        
        Args:
            modality: Specific modality (e.g., 'CT', 'MRI')
            
        Returns:
            List of modality terms
        """
        modality_terms = self.medical_terms.get('modality_terms', {})
        
        if modality:
            return modality_terms.get(modality.upper(), [])
        
        # Return all modality terms (flattened)
        all_terms = []
        for terms_list in modality_terms.values():
            all_terms.extend(terms_list)
        
        return all_terms
    
    def filter_stopwords(self, tokens: List[str]) -> List[str]:
        """
        Filter stopwords from a list of tokens.
        
        Args:
            tokens: List of tokens
            
        Returns:
            Filtered list (stopwords removed)
        """
        return [token for token in tokens if not self.is_stopword(token)]
    
    def normalize_batch(self, keywords: List[str], 
                       expand_abbreviations: bool = True) -> Dict[str, str]:
        """
        Normalize a batch of keywords.
        
        Args:
            keywords: List of keywords to normalize
            expand_abbreviations: Whether to expand abbreviations
            
        Returns:
            Dictionary mapping original → normalized
        """
        return {
            kw: self.normalize(kw, expand_abbreviations)
            for kw in keywords
        }
    
    def get_quality_descriptors(self, category: str = None) -> List[str]:
        """
        Get quality descriptor terms.
        
        Args:
            category: Descriptor category (e.g., 'size', 'shape', 'density')
            
        Returns:
            List of quality descriptor terms
        """
        quality = self.medical_terms.get('quality_descriptors', {})
        
        if category:
            return quality.get(category, [])
        
        # Return all quality descriptors (flattened)
        all_terms = []
        for terms_list in quality.values():
            all_terms.extend(terms_list)
        
        return all_terms
    
    def get_research_terms(self) -> List[str]:
        """Get research-related terms"""
        return self.medical_terms.get('research_terms', [])
    
    def close(self):
        """Close database connection (if repo was provided)"""
        if self.repo:
            self.repo.close()
