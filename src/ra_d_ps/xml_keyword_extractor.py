"""
XML Keyword Extractor

Extracts keywords from LIDC-IDRI XML annotation files.
Handles multiple parse case formats and extracts:
- Characteristic values (subtlety, malignancy, etc.)
- Diagnostic text (reason field)
- Anatomical terms
- Metadata fields

Database: PostgreSQL (ra_d_ps) via KeywordRepository
"""

import xml.etree.ElementTree as ET
import re
import logging
from typing import List, Dict, Tuple, Set, Optional
from pathlib import Path
from dataclasses import dataclass

from .database.keyword_repository import KeywordRepository

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ExtractedKeyword:
    """Container for an extracted keyword with metadata"""
    text: str
    category: str  # 'characteristic', 'diagnosis', 'anatomy', 'metadata'
    context: str  # Surrounding text snippet
    frequency: int = 1
    position: Tuple[int, int] = None  # (start, end) for highlighting
    
    def __repr__(self):
        return f"<ExtractedKeyword(text='{self.text}', category='{self.category}', freq={self.frequency})>"


class XMLKeywordExtractor:
    """
    Extract keywords from LIDC-IDRI XML annotation files.
    
    Features:
    - Extracts from all characteristic fields (LIDC v1 and v2 formats)
    - Parses diagnostic reason text
    - Identifies anatomical terms
    - Preserves context for snippet display
    - Handles multiple radiologist annotations
    - Compatible with all parse case formats
    """
    
    # LIDC v1 characteristic fields (legacy format)
    LIDC_V1_CHARACTERISTICS = [
        'subtlety', 'confidence', 'obscuration', 'reason'
    ]
    
    # LIDC v2 characteristic fields (modern format)
    LIDC_V2_CHARACTERISTICS = [
        'subtlety', 'malignancy', 'internalStructure', 'calcification',
        'sphericity', 'margin', 'lobulation', 'spiculation', 'texture'
    ]
    
    # Common anatomical terms in radiology (simplified list)
    ANATOMICAL_TERMS = {
        'lung', 'lobe', 'nodule', 'lesion', 'mass', 'opacity',
        'pleura', 'fissure', 'hilum', 'mediastinum', 'bronchus',
        'airway', 'vessel', 'lymph', 'parenchyma', 'apex'
    }
    
    # Medical stopwords (common words to exclude)
    STOPWORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
        'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should',
        'can', 'could', 'may', 'might', 'must', 'shall', 'this', 'that', 'these', 'those'
    }
    
    def __init__(self, keyword_repo: KeywordRepository = None, 
                 medical_terms_path: str = None):
        """
        Initialize XML keyword extractor.
        
        Args:
            keyword_repo: KeywordRepository instance (creates new if None)
            medical_terms_path: Path to medical terms dictionary JSON (optional)
        """
        self.repo = keyword_repo or KeywordRepository()
        self.medical_terms = self._load_medical_terms(medical_terms_path)
        self._extraction_stats = {
            'total_keywords': 0,
            'by_category': {},
            'files_processed': 0
        }
    
    def _load_medical_terms(self, path: str = None) -> Dict:
        """
        Load medical terms dictionary.
        
        Args:
            path: Path to medical_terms.json (optional)
            
        Returns:
            Dictionary with medical terms, synonyms, abbreviations
        """
        # For now, return empty dict (will implement medical_terms.json later)
        return {
            'synonyms': {},
            'abbreviations': {},
            'multi_word_terms': []
        }
    
    def extract_from_xml(self, xml_path: str, store_in_db: bool = True) -> List[ExtractedKeyword]:
        """
        Extract all keywords from an XML file.
        
        Args:
            xml_path: Path to XML file
            store_in_db: Whether to store keywords in database (default: True)
            
        Returns:
            List of ExtractedKeyword objects
        """
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            # Extract namespace
            namespace = self._extract_namespace(root)
            
            # Extract keywords from different sources
            keywords = []
            keywords.extend(self._extract_characteristics(root, namespace))
            keywords.extend(self._extract_diagnostic_text(root, namespace))
            keywords.extend(self._extract_anatomical_terms(root, namespace))
            keywords.extend(self._extract_metadata(root, namespace))
            
            # Consolidate duplicate keywords (sum frequencies)
            keywords = self._consolidate_keywords(keywords)
            
            # Store in database if requested
            if store_in_db:
                self._store_keywords(keywords, xml_path)
            
            # Update stats
            self._extraction_stats['files_processed'] += 1
            self._extraction_stats['total_keywords'] += len(keywords)
            
            logger.debug(f"Extracted {len(keywords)} keywords from {Path(xml_path).name}")
            
            return keywords
            
        except Exception as e:
            logger.error(f"Error extracting keywords from {xml_path}: {e}")
            raise
    
    def _extract_namespace(self, root) -> str:
        """Extract XML namespace if present"""
        match = re.match(r'\{(.*)\}', root.tag)
        return match.group(1) if match else ''
    
    def _make_tag(self, name: str, namespace: str) -> str:
        """Make namespaced tag"""
        return f"{{{namespace}}}{name}" if namespace else name
    
    def _extract_characteristics(self, root, namespace: str) -> List[ExtractedKeyword]:
        """
        Extract keywords from characteristic fields.
        
        Handles both LIDC v1 and v2 formats.
        """
        keywords = []
        
        # Try LIDC v2 characteristics first
        for char in self.LIDC_V2_CHARACTERISTICS:
            tag = self._make_tag(char, namespace)
            elements = root.findall(f'.//{tag}')
            
            for elem in elements:
                if elem.text and elem.text.strip():
                    value = elem.text.strip()
                    
                    # Create keyword with characteristic name and value
                    keyword_text = f"{char}:{value}"
                    context = f"Characteristic {char} = {value}"
                    
                    keywords.append(ExtractedKeyword(
                        text=keyword_text,
                        category='characteristic',
                        context=context
                    ))
        
        # Try LIDC v1 characteristics
        for char in self.LIDC_V1_CHARACTERISTICS:
            if char == 'reason':  # Handle separately in diagnostic text
                continue
                
            tag = self._make_tag(char, namespace)
            elements = root.findall(f'.//{tag}')
            
            for elem in elements:
                if elem.text and elem.text.strip():
                    value = elem.text.strip()
                    
                    keyword_text = f"{char}:{value}"
                    context = f"Characteristic {char} = {value}"
                    
                    keywords.append(ExtractedKeyword(
                        text=keyword_text,
                        category='characteristic',
                        context=context
                    ))
        
        return keywords
    
    def _extract_diagnostic_text(self, root, namespace: str) -> List[ExtractedKeyword]:
        """
        Extract keywords from diagnostic text fields (reason field).
        """
        keywords = []
        
        # Extract from 'reason' field
        reason_tag = self._make_tag('reason', namespace)
        reason_elements = root.findall(f'.//{reason_tag}')
        
        for reason_elem in reason_elements:
            if reason_elem.text and reason_elem.text.strip():
                text = reason_elem.text.strip()
                
                # Tokenize diagnostic text
                tokens = self._tokenize_medical_text(text)
                
                for token in tokens:
                    if token.lower() not in self.STOPWORDS and len(token) > 2:
                        # Create context snippet (50 chars around token)
                        context = self._create_context_snippet(text, token)
                        
                        keywords.append(ExtractedKeyword(
                            text=token.lower(),
                            category='diagnosis',
                            context=context
                        ))
        
        return keywords
    
    def _extract_anatomical_terms(self, root, namespace: str) -> List[ExtractedKeyword]:
        """
        Extract anatomical terms from XML content.
        
        Looks for known anatomical terms in text fields.
        """
        keywords = []
        
        # Get all text content from XML
        text_content = ' '.join([
            elem.text for elem in root.iter()
            if elem.text and isinstance(elem.text, str)
        ])
        
        # Tokenize
        tokens = set(self._tokenize_medical_text(text_content))
        
        # Find anatomical terms
        for token in tokens:
            if token.lower() in self.ANATOMICAL_TERMS:
                context = self._create_context_snippet(text_content, token)
                
                keywords.append(ExtractedKeyword(
                    text=token.lower(),
                    category='anatomy',
                    context=context
                ))
        
        return keywords
    
    def _extract_metadata(self, root, namespace: str) -> List[ExtractedKeyword]:
        """
        Extract keywords from metadata fields.
        
        Extracts Study UID, Modality, etc. as metadata keywords.
        """
        keywords = []
        
        # Extract Study UID (if present)
        study_uid_tag = self._make_tag('StudyInstanceUID', namespace)
        study_uid_elem = root.find(f'.//{study_uid_tag}')
        
        if study_uid_elem is not None and study_uid_elem.text:
            keywords.append(ExtractedKeyword(
                text=f"study_uid:{study_uid_elem.text}",
                category='metadata',
                context=f"Study UID: {study_uid_elem.text}"
            ))
        
        # Extract Modality (if present)
        modality_tag = self._make_tag('imagingModality', namespace)
        modality_elem = root.find(f'.//{modality_tag}')
        
        if modality_elem is not None and modality_elem.text:
            keywords.append(ExtractedKeyword(
                text=f"modality:{modality_elem.text.lower()}",
                category='metadata',
                context=f"Imaging Modality: {modality_elem.text}"
            ))
        
        return keywords
    
    def _tokenize_medical_text(self, text: str) -> List[str]:
        """
        Tokenize medical text preserving multi-word terms.
        
        Args:
            text: Input text
            
        Returns:
            List of tokens
        """
        # Remove punctuation except hyphens and spaces
        text = re.sub(r'[^\w\s-]', ' ', text)
        
        # Split on whitespace
        tokens = text.split()
        
        # Check for multi-word medical terms (future enhancement)
        # For now, just return single tokens
        
        return tokens
    
    def _create_context_snippet(self, text: str, keyword: str, 
                                window: int = 50) -> str:
        """
        Create a context snippet around a keyword.
        
        Args:
            text: Full text
            keyword: Keyword to find
            window: Characters before/after keyword (default: 50)
            
        Returns:
            Context snippet (max 200 chars)
        """
        # Find keyword position
        pos = text.lower().find(keyword.lower())
        
        if pos == -1:
            return text[:200]  # Return first 200 chars if not found
        
        # Extract context window
        start = max(0, pos - window)
        end = min(len(text), pos + len(keyword) + window)
        
        snippet = text[start:end]
        
        # Add ellipsis if truncated
        if start > 0:
            snippet = '...' + snippet
        if end < len(text):
            snippet = snippet + '...'
        
        return snippet[:200]  # Limit to 200 chars
    
    def _consolidate_keywords(self, keywords: List[ExtractedKeyword]) -> List[ExtractedKeyword]:
        """
        Consolidate duplicate keywords by summing frequencies.
        
        Args:
            keywords: List of extracted keywords
            
        Returns:
            List of consolidated keywords
        """
        keyword_map = {}
        
        for kw in keywords:
            key = (kw.text, kw.category)
            
            if key in keyword_map:
                keyword_map[key].frequency += 1
            else:
                keyword_map[key] = kw
        
        return list(keyword_map.values())
    
    def _store_keywords(self, keywords: List[ExtractedKeyword], 
                       xml_path: str) -> None:
        """
        Store extracted keywords in database.
        
        Args:
            keywords: List of extracted keywords
            xml_path: Path to XML file (used as source_file)
        """
        for kw in keywords:
            # Add keyword (or get existing)
            db_keyword = self.repo.add_keyword(
                keyword_text=kw.text,
                category=kw.category,
                normalized_form=kw.text.lower()
            )
            
            # Add keyword source
            self.repo.add_keyword_source(
                keyword_id=db_keyword.keyword_id,
                source_type='xml',
                source_file=xml_path,
                frequency=kw.frequency,
                context=kw.context,
                sector='lidc_annotations'
            )
            
            # Update category stats
            if kw.category not in self._extraction_stats['by_category']:
                self._extraction_stats['by_category'][kw.category] = 0
            self._extraction_stats['by_category'][kw.category] += 1
    
    def extract_from_multiple(self, xml_paths: List[str], 
                             show_progress: bool = True) -> Dict:
        """
        Extract keywords from multiple XML files.
        
        Args:
            xml_paths: List of XML file paths
            show_progress: Show progress messages (default: True)
            
        Returns:
            Extraction statistics dictionary
        """
        total_keywords = []
        errors = []
        
        for i, xml_path in enumerate(xml_paths, 1):
            try:
                keywords = self.extract_from_xml(xml_path, store_in_db=True)
                total_keywords.extend(keywords)
                
                if show_progress and i % 10 == 0:
                    print(f"   Processed {i}/{len(xml_paths)} files ({i/len(xml_paths)*100:.1f}%)")
            
            except Exception as e:
                errors.append({
                    'file': xml_path,
                    'error': str(e)
                })
                logger.error(f"Error processing {xml_path}: {e}")
        
        # Update statistics for all keywords
        if show_progress:
            print(f"\n   Updating statistics for {len(total_keywords)} keywords...")
        
        # Get unique keyword IDs
        keyword_ids = set()
        for kw in total_keywords:
            db_kw = self.repo.get_keyword_by_text(kw.text)
            if db_kw:
                keyword_ids.add(db_kw.keyword_id)
        
        # Update statistics
        for keyword_id in keyword_ids:
            self.repo.update_keyword_statistics(keyword_id)
        
        return {
            'files_processed': len(xml_paths),
            'total_keywords': len(total_keywords),
            'unique_keywords': len(keyword_ids),
            'errors': errors,
            'by_category': self._extraction_stats['by_category']
        }
    
    def get_extraction_stats(self) -> Dict:
        """Get extraction statistics"""
        return self._extraction_stats.copy()
    
    def close(self):
        """Close database connection"""
        if self.repo:
            self.repo.close()
