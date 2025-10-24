"""
Generic XML Parser for RA-D-PS

Profile-driven XML parser that converts XML documents to canonical schema
using profile-defined field mappings and transformations.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import re
import logging

from .base import BaseParser, ValidationError, ParseError
from ..schemas.canonical import (
    RadiologyCanonicalDocument,
    DocumentMetadata,
    Entity,
    ExtractedEntities
)
from ..schemas.profile import Profile

logger = logging.getLogger(__name__)


class XMLParser(BaseParser):
    """
    Profile-driven XML parser that extracts data based on profile definitions
    and outputs canonical schema documents.
    """
    
    def __init__(self, profile: Profile, config: Optional[Dict[str, Any]] = None):
        """
        Initialize XML parser with a profile.
        
        Args:
            profile: Profile defining how to parse the XML
            config: Optional parser configuration
        """
        super().__init__(config)
        self.profile = profile
        self._namespace_cache = {}
    
    def can_parse(self, file_path: str) -> bool:
        """
        Check if this parser can handle the file.
        
        Args:
            file_path: Path to file
            
        Returns:
            True if file is XML and matches profile criteria
        """
        try:
            path = Path(file_path)
            if path.suffix.lower() not in ['.xml']:
                return False
            
            # Try to parse as XML
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Check if root element matches profile (if specified)
            if hasattr(self.profile, 'root_element'):
                root_tag = self._strip_namespace(root.tag)
                return root_tag == self.profile.root_element
            
            return True
            
        except Exception:
            return False
    
    def validate(self, file_path: str) -> tuple[bool, Optional[str]]:
        """
        Validate XML file structure.
        
        Args:
            file_path: Path to XML file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            self._validate_file_exists(file_path)
            self._validate_file_readable(file_path)
            
            # Parse XML
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Validate against profile requirements
            if hasattr(self.profile, 'required_fields'):
                for field in self.profile.required_fields:
                    xpath = self.profile.field_mappings.get(field, {}).get('xpath')
                    if xpath and not root.find(xpath):
                        return False, f"Required field missing: {field}"
            
            return True, None
            
        except ET.ParseError as e:
            return False, f"XML parse error: {e}"
        except Exception as e:
            return False, f"Validation error: {e}"
    
    def parse(self, file_path: str) -> RadiologyCanonicalDocument:
        """
        Parse XML file using profile definitions.
        
        Args:
            file_path: Path to XML file
            
        Returns:
            RadiologyCanonicalDocument with extracted data
            
        Raises:
            ParseError: If parsing fails
        """
        try:
            # Validate first
            is_valid, error_msg = self.validate(file_path)
            if not is_valid:
                raise ValidationError(f"Validation failed: {error_msg}")
            
            # Parse XML
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Extract namespace
            namespace = self._extract_namespace(root)
            self._namespace_cache[file_path] = namespace
            
            # Build canonical document
            doc = self._build_canonical_document(root, file_path, namespace)
            
            return doc
            
        except Exception as e:
            raise ParseError(f"Failed to parse {file_path}: {e}")
    
    def _build_canonical_document(
        self, 
        root: ET.Element, 
        file_path: str,
        namespace: str
    ) -> RadiologyCanonicalDocument:
        """
        Build canonical document from XML tree.
        
        Args:
            root: XML root element
            file_path: Source file path
            namespace: XML namespace
            
        Returns:
            RadiologyCanonicalDocument instance
        """
        # Build metadata
        metadata = DocumentMetadata(
            source_file=Path(file_path).name,
            source_path=str(file_path),
            file_format=self.profile.file_type.value if hasattr(self.profile, 'file_type') else 'XML',
            profile_id=self.profile.profile_id if self.profile.profile_id else 'unknown',
            profile_version=self.profile.version,
            ingestion_timestamp=datetime.now(),
            document_type=self.profile.target_document_type if hasattr(self.profile, 'target_document_type') else 'radiology'
        )
        
        # Extract fields based on profile
        fields = self._extract_fields(root, namespace)
        
        # Extract study/series UIDs
        study_uid = fields.get('study_uid') or fields.get('study_instance_uid')
        series_uid = fields.get('series_uid') or fields.get('series_instance_uid')
        
        # Extract entities (nodules, findings, etc.)
        entities = self._extract_entities(root, namespace, fields)
        
        # Build canonical document
        doc = RadiologyCanonicalDocument(
            document_metadata=metadata,
            study_instance_uid=study_uid,
            series_instance_uid=series_uid,
            modality=fields.get('modality'),
            fields=fields,
            nodules=entities.get('nodules', []),
            radiologist_readings=entities.get('readings', [])
        )
        
        return doc
    
    def _extract_fields(self, root: ET.Element, namespace: str) -> Dict[str, Any]:
        """
        Extract fields from XML based on profile mappings.
        
        Args:
            root: XML root element
            namespace: XML namespace
            
        Returns:
            Dictionary of extracted field values
        """
        fields = {}
        
        if not hasattr(self.profile, 'mappings') or not self.profile.mappings:
            return fields
        
        for mapping in self.profile.mappings:
            field_name = mapping.target_path
            try:
                value = self._extract_field_value(root, mapping, namespace)
                if value is not None:
                    fields[field_name] = value
                elif mapping.default_value is not None:
                    fields[field_name] = mapping.default_value
            except Exception as e:
                print(f"Warning: Failed to extract field {field_name}: {e}")
                fields[field_name] = None
        
        return fields
    
    def _extract_field_value(
        self, 
        root: ET.Element, 
        mapping: Any,  # FieldMapping object
        namespace: str
    ) -> Any:
        """
        Extract a single field value using xpath or other method.
        
        Args:
            root: XML root element
            mapping: FieldMapping object
            namespace: XML namespace
            
        Returns:
            Extracted value
        """
        xpath = mapping.source_path
        if not xpath:
            return None
        
        # Build tag function for namespace handling
        tag = lambda name: f"{{{namespace}}}{name}" if namespace else name
        
        # Parse XPath and add namespace to each element
        if namespace and not xpath.startswith('.//{'):
            # Split path and add namespace to each element
            parts = xpath.split('/')
            namespaced_parts = []
            for part in parts:
                if part in ['', '.', '..']:
                    namespaced_parts.append(part)
                elif '[' in part:  # Handle predicates like nodules[]
                    namespaced_parts.append(part)
                else:
                    namespaced_parts.append(f"{{{namespace}}}{part}")
            search_path = '/'.join(namespaced_parts)
        else:
            search_path = xpath
        
        # Find element using findall (works with absolute paths)
        try:
            elements = root.findall(search_path)
            element = elements[0] if elements else None
        except Exception as e:
            # Try simpler approach - navigate step by step
            try:
                current = root
                # Remove leading .// or //
                clean_path = xpath.lstrip('.').lstrip('/')
                for part in clean_path.split('/'):
                    if '[' in part or not part:  # Skip array notation and empty
                        continue
                    current = current.find(tag(part))
                    if current is None:
                        break
                element = current
            except Exception:
                element = None
        
        if element is None:
            return mapping.default_value
        
        # Extract value (attribute or text)
        if mapping.source_attribute:
            value = element.get(mapping.source_attribute)
        else:
            value = element.text if element.text else None
        
        # Apply type conversion
        value = self._convert_type(value, mapping.data_type.value)
        
        # Apply transformations
        if mapping.transformations:
            for transform in mapping.transformations:
                value = self._apply_transformation(value, transform)
        
        return value
    
    def _extract_entities(
        self, 
        root: ET.Element, 
        namespace: str,
        fields: Dict[str, Any]
    ) -> Dict[str, List[Any]]:
        """
        Extract medical entities (nodules, radiologist readings, etc.) from XML.
        
        This method extracts structured entities based on the profile's entity
        extraction configuration. For LIDC-IDRI, this includes:
        - Nodules with characteristics and ROI coordinates
        - Radiologist readings and sessions
        
        Args:
            root: XML root element
            namespace: XML namespace
            fields: Already extracted fields
            
        Returns:
            Dictionary with 'nodules' and 'readings' lists
        """
        entities = {
            'nodules': [],
            'readings': []
        }
        
        # Check if entity extraction is configured
        if not self.profile.entity_extraction or not self.profile.entity_extraction.enabled:
            return entities
        
        tag = lambda name: f"{{{namespace}}}{name}" if namespace else name
        
        # Extract nodules from reading sessions
        try:
            nodules_data = self._extract_nodules(root, namespace, tag)
            entities['nodules'] = nodules_data
        except Exception as e:
            logger.warning(f"Failed to extract nodules: {e}")
        
        # Extract radiologist readings
        try:
            readings_data = self._extract_radiologist_readings(root, namespace, tag)
            entities['readings'] = readings_data
        except Exception as e:
            logger.warning(f"Failed to extract radiologist readings: {e}")
        
        return entities
    
    def _extract_nodules(
        self,
        root: ET.Element,
        namespace: str,
        tag: callable
    ) -> List[Dict[str, Any]]:
        """
        Extract nodule data from XML structure.
        
        Handles both LIDC and CXR reading session formats.
        
        Args:
            root: XML root element
            namespace: XML namespace
            tag: Tag creation function with namespace
            
        Returns:
            List of nodule dictionaries
        """
        nodules = []
        
        # Find all reading sessions (LIDC or CXR format)
        sessions = (root.findall(tag('readingSession')) or 
                   root.findall(tag('CXRreadingSession')))
        
        for session_idx, session in enumerate(sessions):
            # Find unblinded nodule reads
            unblinded_reads = (session.findall(tag('unblindedReadNodule')) or
                              session.findall(tag('unblindedRead')))
            
            for unblinded in unblinded_reads:
                nodule_data = self._extract_single_nodule(
                    unblinded, 
                    tag, 
                    session_idx
                )
                if nodule_data:
                    nodules.append(nodule_data)
        
        return nodules
    
    def _extract_single_nodule(
        self,
        unblinded: ET.Element,
        tag: callable,
        session_idx: int
    ) -> Dict[str, Any]:
        """
        Extract data for a single nodule.
        
        Args:
            unblinded: Unblinded nodule element
            tag: Tag creation function
            session_idx: Index of reading session
            
        Returns:
            Dictionary with nodule data
        """
        # Extract nodule ID
        nodule_id_elem = unblinded.find(tag('noduleID'))
        nodule_id = nodule_id_elem.text if nodule_id_elem is not None else None
        
        # Extract characteristics
        characteristics = self._extract_characteristics(unblinded, tag)
        
        # Extract ROI data
        rois = self._extract_rois(unblinded, tag)
        
        nodule_data = {
            'entity_id': nodule_id,
            'entity_type': 'nodule',
            'session_index': session_idx,
            'characteristics': characteristics,
            'rois': rois,
            'roi_count': len(rois)
        }
        
        return nodule_data
    
    def _extract_characteristics(
        self,
        unblinded: ET.Element,
        tag: callable
    ) -> Dict[str, Any]:
        """
        Extract nodule characteristics.
        
        Args:
            unblinded: Unblinded nodule element
            tag: Tag creation function
            
        Returns:
            Dictionary of characteristics
        """
        characteristics = {}
        
        char_elem = unblinded.find(tag('characteristics'))
        if char_elem is not None:
            # Extract common characteristics
            for char_name in ['confidence', 'subtlety', 'obscuration', 'reason']:
                elem = char_elem.find(tag(char_name))
                if elem is not None and elem.text:
                    try:
                        # Try to convert to float for numeric values
                        if char_name != 'reason':
                            characteristics[char_name] = float(elem.text)
                        else:
                            characteristics[char_name] = elem.text
                    except ValueError:
                        characteristics[char_name] = elem.text
                else:
                    characteristics[char_name] = None
        
        return characteristics
    
    def _extract_rois(
        self,
        unblinded: ET.Element,
        tag: callable
    ) -> List[Dict[str, Any]]:
        """
        Extract ROI (Region of Interest) data.
        
        Args:
            unblinded: Unblinded nodule element
            tag: Tag creation function
            
        Returns:
            List of ROI dictionaries
        """
        rois = []
        
        roi_elements = unblinded.findall(tag('roi'))
        
        for roi in roi_elements:
            roi_data = {}
            
            # Extract SOP UID
            sop_elem = roi.find(tag('imageSOP_UID'))
            if sop_elem is not None and sop_elem.text:
                roi_data['sop_uid'] = sop_elem.text
            
            # Extract Z coordinate from ROI level
            z_elem = roi.find(tag('imageZposition'))
            if z_elem is not None and z_elem.text:
                try:
                    roi_data['z_coord'] = float(z_elem.text)
                except ValueError:
                    roi_data['z_coord'] = z_elem.text
            
            # Extract edge map coordinates
            edge_maps = roi.findall(tag('edgeMap'))
            if edge_maps:
                # Use first edge map for primary coordinates
                first_edge = edge_maps[0]
                
                x_elem = first_edge.find(tag('xCoord'))
                if x_elem is not None and x_elem.text:
                    try:
                        roi_data['x_coord'] = float(x_elem.text)
                    except ValueError:
                        roi_data['x_coord'] = x_elem.text
                
                y_elem = first_edge.find(tag('yCoord'))
                if y_elem is not None and y_elem.text:
                    try:
                        roi_data['y_coord'] = float(y_elem.text)
                    except ValueError:
                        roi_data['y_coord'] = y_elem.text
                
                # Try Z from edge map if not found at ROI level
                if 'z_coord' not in roi_data:
                    z_edge_elem = first_edge.find(tag('imageZposition'))
                    if z_edge_elem is not None and z_edge_elem.text:
                        try:
                            roi_data['z_coord'] = float(z_edge_elem.text)
                        except ValueError:
                            roi_data['z_coord'] = z_edge_elem.text
                
                # Store count of all edge maps
                roi_data['edge_map_count'] = len(edge_maps)
            
            if roi_data:  # Only add if we extracted some data
                rois.append(roi_data)
        
        return rois
    
    def _extract_radiologist_readings(
        self,
        root: ET.Element,
        namespace: str,
        tag: callable
    ) -> List[Dict[str, Any]]:
        """
        Extract radiologist reading sessions.
        
        Args:
            root: XML root element
            namespace: XML namespace
            tag: Tag creation function
            
        Returns:
            List of radiologist reading dictionaries
        """
        readings = []
        
        # Find all reading sessions
        sessions = (root.findall(tag('readingSession')) or 
                   root.findall(tag('CXRreadingSession')))
        
        for session_idx, session in enumerate(sessions):
            # Extract radiologist ID
            rad_elem = session.find(tag('servicingRadiologistID'))
            rad_base = rad_elem.text if rad_elem is not None else 'unknown'
            
            # Create anonymized radiologist identifier
            radiologist_id = f"anonRad{session_idx + 1}"
            
            reading_data = {
                'radiologist_id': radiologist_id,
                'radiologist_base_id': rad_base,
                'session_index': session_idx,
                'is_last_session': session_idx == len(sessions) - 1
            }
            
            readings.append(reading_data)
        
        return readings
    
    def _extract_namespace(self, root: ET.Element) -> str:
        """
        Extract XML namespace from root element.
        
        Args:
            root: XML root element
            
        Returns:
            Namespace string or empty string
        """
        match = re.match(r'\{(.*)\}', root.tag)
        return match.group(1) if match else ''
    
    def _strip_namespace(self, tag: str) -> str:
        """
        Remove namespace from tag name.
        
        Args:
            tag: Tag name with or without namespace
            
        Returns:
            Tag name without namespace
        """
        return tag.split('}')[-1] if '}' in tag else tag
    
    def _add_namespace_to_xpath(self, xpath: str, namespace: str) -> str:
        """
        Add namespace to xpath expression.
        
        Args:
            xpath: XPath expression
            namespace: Namespace to add
            
        Returns:
            XPath with namespace
        """
        # Simple implementation - can be enhanced
        if namespace:
            return f"{{{namespace}}}{xpath}"
        return xpath
    
    def _convert_type(self, value: Any, field_type: str) -> Any:
        """
        Convert value to specified type.
        
        Args:
            value: Value to convert
            field_type: Target type name
            
        Returns:
            Converted value
        """
        if value is None:
            return None
        
        try:
            if field_type == 'integer' or field_type == 'int':
                return int(value)
            elif field_type == 'float' or field_type == 'number':
                return float(value)
            elif field_type == 'boolean' or field_type == 'bool':
                return value.lower() in ('true', '1', 'yes')
            elif field_type == 'date':
                return datetime.strptime(value, '%Y-%m-%d').date()
            elif field_type == 'datetime':
                return datetime.fromisoformat(value)
            else:  # string
                return str(value)
        except Exception:
            return value
    
    def _apply_transformation(self, value: Any, transform: Any) -> Any:
        """
        Apply transformation to extracted value.
        
        Args:
            value: Value to transform
            transform: Transformation object
            
        Returns:
            Transformed value
        """
        if value is None:
            return value
        
        transform_type = transform.transformation_type
        
        if transform_type.value == 'trim_whitespace':
            return str(value).strip()
        elif transform_type.value == 'uppercase':
            return str(value).upper()
        elif transform_type.value == 'lowercase':
            return str(value).lower()
        elif transform_type.value == 'extract_numbers':
            numbers = re.findall(r'\d+', str(value))
            return ''.join(numbers) if numbers else value
        
        # For now, return value as-is for unsupported transformations
        return value
