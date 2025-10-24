"""
Comprehensive LIDC-IDRI Profile for Phase 5

Maps all extraction logic from parser.py (lines 427-760) to Profile system.
This profile enables full feature parity with the original parser while using
the new generic XML parser architecture.
"""

from ..schemas.profile import (
    Profile,
    FieldMapping,
    DataType,
    FileType,
    Transformation,
    TransformationType,
    ValidationRules,
    EntityExtractionConfig
)

def create_lidc_idri_comprehensive_profile() -> Profile:
    """
    Create comprehensive LIDC-IDRI profile with all field mappings.
    
    This profile maps:
    - Header fields (StudyInstanceUID, SeriesInstanceUID, Modality, DateService, TimeService)
    - Radiologist identification (servicingRadiologistID)
    - Nodule identification (noduleID)
    - Characteristics (confidence, subtlety, obscuration, reason)
    - ROI data (imageSOP_UID, coordinates, edge maps)
    - Session metadata
    
    Returns:
        Complete Profile object for LIDC-IDRI XML parsing
    """
    
    # Header field mappings
    header_mappings = [
        FieldMapping(
            source_path='.//ResponseHeader/StudyInstanceUID',
            target_path='study_instance_uid',
            data_type=DataType.STRING,
            default_value='#N/A',
            transformations=[
                Transformation(
                    transformation_type=TransformationType.TRIM_WHITESPACE
                )
            ]
        ),
        FieldMapping(
            source_path='.//ResponseHeader/SeriesInstanceUID',
            target_path='series_instance_uid',
            data_type=DataType.STRING,
            default_value='#N/A',
            transformations=[
                Transformation(
                    transformation_type=TransformationType.TRIM_WHITESPACE
                )
            ]
        ),
        FieldMapping(
            source_path='.//ResponseHeader/SeriesInstanceUid',  # Alternative spelling
            target_path='series_instance_uid',
            data_type=DataType.STRING,
            default_value='#N/A',
            transformations=[
                Transformation(
                    transformation_type=TransformationType.TRIM_WHITESPACE
                )
            ]
        ),
        FieldMapping(
            source_path='.//ResponseHeader/Modality',
            target_path='modality',
            data_type=DataType.STRING,
            default_value='#N/A'
        ),
        FieldMapping(
            source_path='.//ResponseHeader/DateService',
            target_path='fields.date_service',
            data_type=DataType.STRING,
            default_value='#N/A'
        ),
        FieldMapping(
            source_path='.//ResponseHeader/TimeService',
            target_path='fields.time_service',
            data_type=DataType.STRING,
            default_value='#N/A'
        ),
    ]
    
    # Reading session field mappings
    session_mappings = [
        FieldMapping(
            source_path='.//readingSession/servicingRadiologistID',
            target_path='fields.radiologist_base_id',
            data_type=DataType.STRING,
            default_value='unknown'
        ),
        FieldMapping(
            source_path='.//CXRreadingSession/servicingRadiologistID',  # Alternative format
            target_path='fields.radiologist_base_id',
            data_type=DataType.STRING,
            default_value='unknown'
        ),
    ]
    
    # Nodule characteristic mappings (per unblindedReadNodule)
    nodule_characteristic_mappings = [
        FieldMapping(
            source_path='.//noduleID',
            target_path='nodules[].nodule_id',
            data_type=DataType.INTEGER,
            default_value='#N/A'
        ),
        FieldMapping(
            source_path='.//characteristics/confidence',
            target_path='nodules[].characteristics.confidence',
            data_type=DataType.FLOAT,
            default_value='#N/A'
        ),
        FieldMapping(
            source_path='.//characteristics/subtlety',
            target_path='nodules[].characteristics.subtlety',
            data_type=DataType.FLOAT,
            default_value='#N/A'
        ),
        FieldMapping(
            source_path='.//characteristics/obscuration',
            target_path='nodules[].characteristics.obscuration',
            data_type=DataType.FLOAT,
            default_value='#N/A'
        ),
        FieldMapping(
            source_path='.//characteristics/reason',
            target_path='nodules[].characteristics.reason',
            data_type=DataType.STRING,
            default_value='#N/A'
        ),
    ]
    
    # ROI coordinate mappings
    roi_mappings = [
        FieldMapping(
            source_path='.//roi/imageSOP_UID',
            target_path='nodules[].rois[].sop_uid',
            data_type=DataType.STRING,
            default_value='#N/A'
        ),
        FieldMapping(
            source_path='.//roi/imageZposition',
            target_path='nodules[].rois[].z_coord',
            data_type=DataType.FLOAT,
            default_value='#N/A'
        ),
        FieldMapping(
            source_path='.//edgeMap/xCoord',
            target_path='nodules[].rois[].x_coord',
            data_type=DataType.FLOAT,
            default_value='#N/A'
        ),
        FieldMapping(
            source_path='.//edgeMap/yCoord',
            target_path='nodules[].rois[].y_coord',
            data_type=DataType.FLOAT,
            default_value='#N/A'
        ),
        FieldMapping(
            source_path='.//edgeMap/imageZposition',  # Alternative Z location
            target_path='nodules[].rois[].z_coord',
            data_type=DataType.FLOAT,
            default_value='#N/A'
        ),
    ]
    
    # Combine all field mappings
    all_mappings = (
        header_mappings +
        session_mappings +
        nodule_characteristic_mappings +
        roi_mappings
    )
    
    # Entity extraction configuration for nodules and radiologists
    entity_config = EntityExtractionConfig(
        enabled=True,
        entity_types=['nodule', 'radiologist'],
        extraction_rules={
            'nodule': {
                'source_path': './/unblindedReadNodule',
                'alternative_path': './/unblindedRead',
                'id_field': 'noduleID',
                'characteristics_path': 'characteristics',
                'roi_path': 'roi'
            },
            'radiologist': {
                'source_path': './/readingSession',
                'alternative_path': './/CXRreadingSession',
                'id_field': 'servicingRadiologistID',
                'numbering_scheme': 'anonRad{index}'
            }
        }
    )
    
    # Validation rules based on expected attributes system
    validation_rules = ValidationRules(
        required_fields=['study_instance_uid', 'series_instance_uid'],
        optional_fields=['modality', 'fields.date_service', 'fields.time_service'],
        allow_missing_characteristics=True,
        missing_value_marker='MISSING',
        not_applicable_marker='#N/A'
    )
    
    # Create the comprehensive profile
    profile = Profile(
        profile_name='lidc_idri_comprehensive',
        file_type=FileType.XML,
        description='Comprehensive LIDC-IDRI radiology XML profile with full field mapping',
        version='1.0.0',
        mappings=all_mappings,
        entity_extraction=entity_config,
        validation_rules=validation_rules,
        tags=['lidc', 'idri', 'radiology', 'nodule', 'comprehensive']
    )
    
    return profile


def create_parse_case_specific_profiles() -> dict:
    """
    Create parse-case-specific profiles for different XML structure variations.
    
    Based on structure_detector.py parse cases:
    - Complete_Attributes
    - With_Reason_Partial
    - Core_Attributes_Only
    - Minimal_Attributes
    - LIDC_Multi_Session_N (1-4 sessions)
    
    Returns:
        Dictionary mapping parse case names to Profile objects
    """
    
    profiles = {}
    
    # Base profile for all cases
    base_profile = create_lidc_idri_comprehensive_profile()
    
    # Complete_Attributes: Full LIDC with all fields
    profiles['Complete_Attributes'] = base_profile
    
    # With_Reason_Partial: Has reason field but may miss other characteristics
    reason_partial_mappings = [m for m in base_profile.mappings 
                               if 'reason' in m.target_path or 
                               not m.target_path.startswith('nodules[].characteristics')]
    
    profiles['With_Reason_Partial'] = Profile(
        profile_name='lidc_idri_with_reason_partial',
        file_type=FileType.XML,
        description='LIDC-IDRI profile with reason field but partial characteristics',
        version='1.0.0',
        mappings=reason_partial_mappings,
        entity_extraction=base_profile.entity_extraction,
        validation_rules=ValidationRules(
            required_fields=['study_instance_uid'],
            allow_missing_characteristics=True,
            missing_value_marker='MISSING',
            not_applicable_marker='#N/A'
        )
    )
    
    # Core_Attributes_Only: No reason field, core characteristics only
    core_mappings = [m for m in base_profile.mappings 
                    if 'reason' not in m.target_path]
    
    profiles['Core_Attributes_Only'] = Profile(
        profile_name='lidc_idri_core_attributes_only',
        file_type=FileType.XML,
        description='LIDC-IDRI profile with core attributes without reason',
        version='1.0.0',
        mappings=core_mappings,
        entity_extraction=base_profile.entity_extraction,
        validation_rules=ValidationRules(
            required_fields=['study_instance_uid'],
            allow_missing_characteristics=True,
            missing_value_marker='MISSING',
            not_applicable_marker='#N/A'
        )
    )
    
    # Minimal_Attributes: Single characteristic only
    minimal_mappings = [m for m in base_profile.mappings 
                       if not m.target_path.startswith('nodules[].characteristics') or
                       'confidence' in m.target_path]  # Keep only confidence
    
    profiles['Minimal_Attributes'] = Profile(
        profile_name='lidc_idri_minimal_attributes',
        file_type=FileType.XML,
        description='LIDC-IDRI profile with single characteristic',
        version='1.0.0',
        mappings=minimal_mappings,
        entity_extraction=base_profile.entity_extraction,
        validation_rules=ValidationRules(
            required_fields=[],
            allow_missing_characteristics=True,
            missing_value_marker='MISSING',
            not_applicable_marker='#N/A'
        )
    )
    
    return profiles


# Export convenience function
def get_profile_for_parse_case(parse_case: str) -> Profile:
    """
    Get the appropriate profile for a given parse case.
    
    Args:
        parse_case: Parse case identifier from structure detector
        
    Returns:
        Profile object configured for that parse case
    """
    profiles = create_parse_case_specific_profiles()
    
    # Map multi-session cases to base profile
    if parse_case.startswith('LIDC_Multi_Session'):
        return profiles['Complete_Attributes']
    
    # Return specific profile or default to comprehensive
    return profiles.get(parse_case, create_lidc_idri_comprehensive_profile())
