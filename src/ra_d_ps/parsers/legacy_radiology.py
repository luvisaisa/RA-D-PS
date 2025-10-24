"""
Legacy Radiology Parser - Backward Compatibility Wrapper

This module wraps the new XMLParser to maintain backward compatibility
with the existing parser.py API while internally using the new profile-driven
parser and canonical schema.
"""

import pandas as pd
from pathlib import Path
from typing import Tuple, Dict, Any, List, Optional

from .xml_parser import XMLParser
from ..schemas.canonical import RadiologyCanonicalDocument
from ..schemas.profile import Profile, FieldMapping


class LegacyRadiologyParser:
    """
    Wrapper for backward compatibility with existing parse_radiology_sample() API.
    
    Internally uses the new XMLParser but returns data in the old DataFrame format.
    """
    
    def __init__(self):
        """Initialize with comprehensive LIDC-IDRI profile"""
        # Import comprehensive profile
        from ..profiles.lidc_idri_profile import create_lidc_idri_comprehensive_profile
        self.xml_parser = XMLParser(create_lidc_idri_comprehensive_profile())
    
    def parse_radiology_sample(self, file_path: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Parse XML file and return DataFrames (legacy format).
        
        This method maintains the exact same signature and return format as
        the original parse_radiology_sample() function.
        
        Args:
            file_path: Path to XML file
            
        Returns:
            Tuple of (main_dataframe, unblinded_dataframe)
        """
        # Use new parser to get canonical document
        try:
            # Detect parse case for metadata
            from ..structure_detector import detect_parse_case
            try:
                parse_case = detect_parse_case(file_path)
            except Exception:
                parse_case = 'unknown'
            
            canonical_doc = self.xml_parser.parse(file_path)
            
            # Store parse case in canonical doc for legacy conversion
            if hasattr(canonical_doc, 'fields'):
                canonical_doc.fields['parse_case'] = parse_case
            
            # Convert canonical document to legacy DataFrame format
            main_df, unblinded_df = self._to_legacy_format(canonical_doc, file_path)
            
            return main_df, unblinded_df
            
        except Exception as e:
            print(f"Error in legacy parser wrapper: {e}")
            # Fall back to empty DataFrames to maintain compatibility
            return pd.DataFrame(), pd.DataFrame()
    
    def _create_default_profile(self) -> Profile:
        """
        Create a default profile for LIDC-IDRI XML parsing.
        
        This is a minimal profile that enables basic parsing.
        A complete profile will be created in Phase 5.
        
        Returns:
            Profile instance
        """
        from ..schemas.profile import DataType, FileType, ValidationRules, EntityExtractionConfig
        
        field_mappings_list = [
            FieldMapping(
                source_path='//StudyInstanceUID',
                target_path='study_instance_uid',
                data_type=DataType.STRING,
                required=False
            ),
            FieldMapping(
                source_path='//SeriesInstanceUid',
                target_path='series_instance_uid',
                data_type=DataType.STRING,
                required=False
            ),
            FieldMapping(
                source_path='//PatientID',
                target_path='patient_id',
                data_type=DataType.STRING,
                required=False
            )
        ]
        
        profile = Profile(
            profile_name='lidc_idri_legacy_profile',
            file_type=FileType.XML,
            source_format_description='Minimal profile for backward compatibility',
            version='1.0.0',
            target_document_type='radiology',
            mappings=field_mappings_list,
            validation_rules=ValidationRules(),
            entity_extraction=EntityExtractionConfig()
        )
        
        return profile
    
    def _to_legacy_format(
        self, 
        canonical_doc: RadiologyCanonicalDocument,
        file_path: str
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Convert canonical document to legacy DataFrame format.
        
        Matches the exact column structure from original parser.py:
        - FileID, ParseCase, Radiologist, SessionType, NoduleID
        - Confidence, Subtlety, Obscuration, Reason
        - SOP_UID, X_coord, Y_coord, Z_coord, CoordCount
        - StudyInstanceUID, SeriesInstanceUID, Modality, DateService, TimeService
        
        Args:
            canonical_doc: Canonical document from new parser
            file_path: Original file path
            
        Returns:
            Tuple of (main_dataframe, unblinded_dataframe)
        """
        # Extract file ID from filename
        file_id = Path(file_path).stem
        
        # Extract header values
        study_uid = canonical_doc.study_instance_uid or '#N/A'
        series_uid = canonical_doc.series_instance_uid or '#N/A'
        modality = canonical_doc.modality or '#N/A'
        # Handle both with and without fields. prefix
        date_service = (canonical_doc.fields.get('fields.date_service') or 
                       canonical_doc.fields.get('date_service', '#N/A'))
        time_service = (canonical_doc.fields.get('fields.time_service') or 
                       canonical_doc.fields.get('time_service', '#N/A'))
        # Get parse case from fields if available, otherwise use profile_id
        parse_case = (canonical_doc.fields.get('parse_case') or
                     canonical_doc.document_metadata.profile_id 
                     if canonical_doc.document_metadata else 'unknown')
        
        main_rows = []
        unblinded_rows = []
        
        # Get radiologist readings for session mapping
        radiologist_map = {}
        for reading in canonical_doc.radiologist_readings:
            session_idx = reading.get('session_index', 0)
            radiologist_map[session_idx] = {
                'id': reading.get('radiologist_id', f"anonRad{session_idx + 1}"),
                'is_last': reading.get('is_last_session', False)
            }
        
        # Process each nodule
        for nodule in canonical_doc.nodules:
            session_idx = nodule.get('session_index', 0)
            radiologist_info = radiologist_map.get(session_idx, {
                'id': f"anonRad{session_idx + 1}",
                'is_last': False
            })
            
            # Extract nodule characteristics
            chars = nodule.get('characteristics', {})
            confidence = chars.get('confidence', '#N/A')
            subtlety = chars.get('subtlety', '#N/A')
            obscuration = chars.get('obscuration', '#N/A')
            reason = chars.get('reason', '#N/A')
            
            # Process each ROI for this nodule
            rois = nodule.get('rois', [])
            if not rois:
                # No ROIs - create single entry with MISSING coordinates
                row_data = {
                    "FileID": file_id,
                    "ParseCase": parse_case,
                    "Radiologist": radiologist_info['id'],
                    "SessionType": "Standard",
                    "NoduleID": nodule.get('entity_id', '#N/A'),
                    "Confidence": confidence,
                    "Subtlety": subtlety,
                    "Obscuration": obscuration,
                    "Reason": reason,
                    "SOP_UID": "MISSING",
                    "X_coord": "MISSING",
                    "Y_coord": "MISSING",
                    "Z_coord": "MISSING",
                    "CoordCount": 0,
                    "StudyInstanceUID": study_uid,
                    "SeriesInstanceUID": series_uid,
                    "Modality": modality,
                    "DateService": date_service,
                    "TimeService": time_service
                }
                
                if radiologist_info['is_last']:
                    unblinded_rows.append(row_data)
                else:
                    main_rows.append(row_data)
            else:
                # Process each ROI
                for roi in rois:
                    edge_map_count = roi.get('edge_map_count', 1)
                    session_type = "Detailed" if edge_map_count > 10 else "Standard"
                    
                    row_data = {
                        "FileID": file_id,
                        "ParseCase": parse_case,
                        "Radiologist": radiologist_info['id'],
                        "SessionType": session_type,
                        "NoduleID": nodule.get('entity_id', '#N/A'),
                        "Confidence": confidence,
                        "Subtlety": subtlety,
                        "Obscuration": obscuration,
                        "Reason": reason,
                        "SOP_UID": roi.get('sop_uid', '#N/A'),
                        "X_coord": roi.get('x_coord', '#N/A'),
                        "Y_coord": roi.get('y_coord', '#N/A'),
                        "Z_coord": roi.get('z_coord', '#N/A'),
                        "CoordCount": edge_map_count,
                        "StudyInstanceUID": study_uid,
                        "SeriesInstanceUID": series_uid,
                        "Modality": modality,
                        "DateService": date_service,
                        "TimeService": time_service
                    }
                    
                    if radiologist_info['is_last']:
                        unblinded_rows.append(row_data)
                    else:
                        main_rows.append(row_data)
        
        # If no nodules found, create minimal entry
        if not main_rows and not unblinded_rows:
            row_data = {
                "FileID": file_id,
                "ParseCase": parse_case,
                "Radiologist": "unknown",
                "SessionType": "Standard",
                "NoduleID": "#N/A",
                "Confidence": "#N/A",
                "Subtlety": "#N/A",
                "Obscuration": "#N/A",
                "Reason": "#N/A",
                "SOP_UID": "#N/A",
                "X_coord": "#N/A",
                "Y_coord": "#N/A",
                "Z_coord": "#N/A",
                "CoordCount": 0,
                "StudyInstanceUID": study_uid,
                "SeriesInstanceUID": series_uid,
                "Modality": modality,
                "DateService": date_service,
                "TimeService": time_service
            }
            main_rows.append(row_data)
        
        main_df = pd.DataFrame(main_rows) if main_rows else pd.DataFrame()
        unblinded_df = pd.DataFrame(unblinded_rows) if unblinded_rows else pd.DataFrame()
        
        return main_df, unblinded_df
    
    def parse_multiple(self, files: List[str]) -> Tuple[Dict[str, pd.DataFrame], Dict[str, pd.DataFrame]]:
        """
        Parse multiple files with backward compatibility.
        
        Args:
            files: List of file paths
            
        Returns:
            Tuple of (case_data_dict, case_unblinded_dict)
        """
        case_data = {}
        case_unblinded_data = {}
        
        for file_path in files:
            try:
                main_df, unblinded_df = self.parse_radiology_sample(file_path)
                
                if not main_df.empty:
                    parse_case = main_df['ParseCase'].iloc[0] if 'ParseCase' in main_df.columns else 'Unknown'
                    
                    if parse_case not in case_data:
                        case_data[parse_case] = pd.DataFrame()
                    
                    case_data[parse_case] = pd.concat(
                        [case_data[parse_case], main_df], 
                        ignore_index=True
                    )
                
                if not unblinded_df.empty:
                    parse_case = unblinded_df['ParseCase'].iloc[0] if 'ParseCase' in unblinded_df.columns else 'Unknown'
                    
                    if parse_case not in case_unblinded_data:
                        case_unblinded_data[parse_case] = pd.DataFrame()
                    
                    case_unblinded_data[parse_case] = pd.concat(
                        [case_unblinded_data[parse_case], unblinded_df],
                        ignore_index=True
                    )
                    
            except Exception as e:
                print(f"Error parsing {file_path}: {e}")
                continue
        
        return case_data, case_unblinded_data
