"""
Canonical Schema Definitions for RA-D-PS Schema-Agnostic Data Ingestion System

This module defines the flexible canonical schema using Pydantic v2 models.
All source formats (XML, JSON, CSV, PDF, etc.) are normalized into this schema.

Version: 1.0.0
Python: 3.9+
Dependencies: pydantic>=2.0
"""

from __future__ import annotations  # Enable forward references for Python 3.9

from datetime import datetime, date as dt_date
from typing import Optional, Dict, Any, List, Union, Annotated
from decimal import Decimal
from enum import Enum
from pydantic import (
    BaseModel, 
    Field, 
    ConfigDict,
    field_validator,
    model_validator
)


# =====================================================================
# ENUMS AND CONSTANTS
# =====================================================================

class DocumentType(str, Enum):
    """Standard document types supported by the system"""
    RADIOLOGY_REPORT = "radiology_report"
    INVOICE = "invoice"
    MEDICAL_RECORD = "medical_record"
    RESEARCH_DATA = "research_data"
    FORM = "form"
    CONTRACT = "contract"
    EMAIL = "email"
    OTHER = "other"


class EntityType(str, Enum):
    """Types of entities that can be extracted"""
    DATE = "date"
    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    MONEY = "money"
    PERCENTAGE = "percentage"
    MEASUREMENT = "measurement"
    IDENTIFIER = "identifier"
    MEDICAL_TERM = "medical_term"


class ConfidenceLevel(str, Enum):
    """Confidence levels for extraction quality"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


# =====================================================================
# CORE CANONICAL SCHEMA
# =====================================================================

class DocumentMetadata(BaseModel):
    """Standard metadata fields present in most documents"""
    model_config = ConfigDict(extra='allow')  # Allow additional fields
    
    document_type: Optional[str] = Field(
        default=None, 
        description="Type of document (radiology_report, invoice, etc.)"
    )
    title: Optional[str] = Field(
        default=None, 
        description="Document title or subject"
    )
    date: Annotated[
        Union[dt_date, datetime, str, None], 
        Field(default=None, description="Primary document date (creation, service, etc.)")
    ]
    author: Optional[str] = Field(
        default=None, 
        description="Document creator or author"
    )
    creator: Optional[str] = Field(
        default=None, 
        description="System or person that created the document"
    )
    description: Optional[str] = Field(
        default=None, 
        description="Brief description or summary"
    )
    subject: Optional[str] = Field(
        default=None, 
        description="Subject matter or topic"
    )
    keywords: Optional[List[str]] = Field(
        default_factory=list, 
        description="Keywords or tags"
    )
    language: Optional[str] = Field(
        default="en", 
        description="Document language (ISO 639-1 code)"
    )
    
    # Identification
    document_id: Optional[str] = Field(
        default=None, 
        description="Original document identifier from source system"
    )
    version: Optional[str] = Field(
        default=None, 
        description="Document version"
    )
    
    # Time tracking
    created_date: Optional[Union[dt_date, datetime, str]] = Field(default=None)
    modified_date: Optional[Union[dt_date, datetime, str]] = Field(default=None)
    
    @field_validator('date', 'created_date', 'modified_date', mode='before')
    @classmethod
    def parse_dates(cls, v):
        """Accept dates as strings, date objects, or datetime objects"""
        if v is None:
            return None
        if isinstance(v, (date, datetime)):
            return v
        # Keep as string if already string - will be validated later
        return v


class Entity(BaseModel):
    """Represents an extracted entity (person, date, organization, etc.)"""
    model_config = ConfigDict(extra='allow')
    
    entity_type: EntityType = Field(
        ..., 
        description="Type of entity extracted"
    )
    value: str = Field(
        ..., 
        description="The extracted text value"
    )
    normalized_value: Optional[str] = Field(
        default=None, 
        description="Normalized or standardized form of the value"
    )
    confidence: Optional[Decimal] = Field(
        default=None, 
        ge=0, 
        le=1, 
        description="Confidence score (0-1)"
    )
    source_field: Optional[str] = Field(
        default=None, 
        description="Field from which this entity was extracted"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict, 
        description="Additional entity-specific metadata"
    )


class ExtractedEntities(BaseModel):
    """Container for all extracted entities from a document"""
    model_config = ConfigDict(extra='allow')
    
    dates: List[Entity] = Field(
        default_factory=list, 
        description="Extracted dates"
    )
    people: List[Entity] = Field(
        default_factory=list, 
        description="Extracted person names"
    )
    organizations: List[Entity] = Field(
        default_factory=list, 
        description="Extracted organization names"
    )
    locations: List[Entity] = Field(
        default_factory=list, 
        description="Extracted locations"
    )
    amounts: List[Entity] = Field(
        default_factory=list, 
        description="Extracted monetary amounts or measurements"
    )
    identifiers: List[Entity] = Field(
        default_factory=list, 
        description="Extracted IDs, codes, or reference numbers"
    )
    medical_terms: List[Entity] = Field(
        default_factory=list, 
        description="Extracted medical terminology (for radiology/medical docs)"
    )
    other: List[Entity] = Field(
        default_factory=list, 
        description="Other extracted entities"
    )


class ExtractionMetadata(BaseModel):
    """Metadata about the extraction process itself"""
    model_config = ConfigDict(extra='allow')
    
    extraction_timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the extraction occurred"
    )
    profile_id: Optional[str] = Field(
        default=None, 
        description="UUID of the profile used for extraction"
    )
    profile_name: Optional[str] = Field(
        default=None, 
        description="Name of the profile used"
    )
    parser_version: Optional[str] = Field(
        default=None, 
        description="Version of the parser used"
    )
    
    # Quality metrics
    confidence_scores: Dict[str, Decimal] = Field(
        default_factory=dict, 
        description="Per-field confidence scores"
    )
    overall_confidence: Optional[Decimal] = Field(
        default=None, 
        ge=0, 
        le=1, 
        description="Overall extraction confidence"
    )
    
    # Missing data tracking
    unmapped_fields: List[str] = Field(
        default_factory=list, 
        description="Source fields that couldn't be mapped"
    )
    missing_required_fields: List[str] = Field(
        default_factory=list, 
        description="Required canonical fields that are missing"
    )
    
    # Warnings and errors
    warnings: List[str] = Field(
        default_factory=list, 
        description="Non-fatal warnings during extraction"
    )
    validation_errors: List[str] = Field(
        default_factory=list, 
        description="Validation errors encountered"
    )
    
    # Processing metrics
    processing_time_ms: Optional[int] = Field(
        default=None, 
        ge=0, 
        description="Time taken to process in milliseconds"
    )


# =====================================================================
# MAIN CANONICAL SCHEMA
# =====================================================================

class CanonicalDocument(BaseModel):
    """
    The main canonical schema for normalized document data.
    
    This is the target schema that all source formats are mapped to.
    It's designed to be flexible enough to handle various document types
    while maintaining structure for common patterns.
    """
    model_config = ConfigDict(extra='allow')  # Allow format-specific extensions
    
    # Version of the canonical schema (for future migrations)
    canonical_version: str = Field(
        default="1.0", 
        description="Version of the canonical schema"
    )
    
    # Standard metadata (common across all document types)
    document_metadata: DocumentMetadata = Field(
        ..., 
        description="Standard document metadata fields"
    )
    
    # Flexible fields container (format-specific data)
    fields: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Format-specific fields that don't fit standard metadata"
    )
    
    # Structured entity extraction
    entities: ExtractedEntities = Field(
        default_factory=ExtractedEntities, 
        description="Entities extracted from the document"
    )
    
    # Extraction quality and provenance
    extraction_metadata: ExtractionMetadata = Field(
        default_factory=ExtractionMetadata, 
        description="Metadata about the extraction process"
    )
    
    @model_validator(mode='after')
    def validate_document(self):
        """Perform cross-field validation"""
        # Ensure at least some content exists
        has_metadata = bool(getattr(self.document_metadata, 'title', None) or 
                           getattr(self.document_metadata, 'document_type', None) or 
                           getattr(self.document_metadata, 'date', None))
        has_fields = bool(getattr(self, 'fields', None))
        has_entities = any([
            getattr(self.entities, 'dates', []),
            getattr(self.entities, 'people', []),
            getattr(self.entities, 'organizations', []),
            getattr(self.entities, 'amounts', [])
        ])
        # Ensure warnings is a list
        if not hasattr(self.extraction_metadata, 'warnings') or getattr(self.extraction_metadata, 'warnings', None) is None:  # type: ignore[attr-defined]
            self.extraction_metadata.warnings = []  # type: ignore[attr-defined]
        # Use .dict() to access warnings if FieldInfo
        try:
            warnings_list = self.extraction_metadata.warnings  # type: ignore[attr-defined]
        except AttributeError:
            warnings_list = getattr(self.extraction_metadata, 'warnings', [])  # type: ignore[attr-defined]
            self.extraction_metadata.warnings = warnings_list  # type: ignore[attr-defined]
        if not (has_metadata or has_fields or has_entities):
            warnings_list.append("Document appears to have no extractable content")
        return self


# =====================================================================
# DOMAIN-SPECIFIC CANONICAL SCHEMAS
# =====================================================================

class RadiologyCanonicalDocument(CanonicalDocument):
    """
    Specialized canonical schema for radiology documents (LIDC-IDRI, etc.)
    
    Extends the base CanonicalDocument with radiology-specific fields
    while maintaining compatibility with the generic schema.
    """
    
    # Radiology-specific metadata
    study_instance_uid: Optional[str] = Field(
        default=None, 
        description="DICOM Study Instance UID"
    )
    series_instance_uid: Optional[str] = Field(
        default=None, 
        description="DICOM Series Instance UID"
    )
    modality: Optional[str] = Field(
        default=None, 
        description="Imaging modality (CT, MRI, etc.)"
    )
    
    # Radiology-specific structured data
    nodules: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="Detected nodules with annotations"
    )
    radiologist_readings: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="Radiologist readings and annotations"
    )
    
    @field_validator('document_metadata', mode='before')
    @classmethod
    def set_radiology_type(cls, v):
        """Automatically set document_type to radiology_report"""
        if isinstance(v, dict):
            v.setdefault('document_type', 'radiology_report')
        elif isinstance(v, DocumentMetadata) and v.document_type is None:
            v.document_type = 'radiology_report'
        return v


class InvoiceCanonicalDocument(CanonicalDocument):
    """
    Specialized canonical schema for invoices.
    
    Example of how to extend for other document types.
    """
    
    invoice_number: Optional[str] = None
    invoice_date: Annotated[Union[date, str, None], Field(default=None)]
    due_date: Annotated[Union[date, str, None], Field(default=None)]
    total_amount: Optional[Decimal] = None
    currency: Optional[str] = "USD"
    
    vendor: Optional[Dict[str, str]] = Field(
        default_factory=dict,
        description="Vendor/seller information"
    )
    customer: Optional[Dict[str, str]] = Field(
        default_factory=dict,
        description="Customer/buyer information"
    )
    line_items: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Invoice line items"
    )
    
    @field_validator('document_metadata', mode='before')
    @classmethod
    def set_invoice_type(cls, v):
        """Automatically set document_type to invoice"""
        if isinstance(v, dict):
            v.setdefault('document_type', 'invoice')
        elif isinstance(v, DocumentMetadata) and v.document_type is None:
            v.document_type = 'invoice'
        return v


# =====================================================================
# VALIDATION RESULT MODEL
# =====================================================================

class ValidationResult(BaseModel):
    """Result of validating a canonical document against a profile's rules"""
    
    is_valid: bool = Field(
        ..., 
        description="Whether the document passed all validation rules"
    )
    errors: List[str] = Field(
        default_factory=list, 
        description="List of validation errors"
    )
    warnings: List[str] = Field(
        default_factory=list, 
        description="List of validation warnings"
    )
    missing_required_fields: List[str] = Field(
        default_factory=list, 
        description="Required fields that are missing"
    )
    invalid_values: Dict[str, str] = Field(
        default_factory=dict, 
        description="Map of field -> error message for invalid values"
    )
    confidence_score: Optional[Decimal] = Field(
        default=None, 
        ge=0, 
        le=1, 
        description="Overall validation confidence score"
    )


# =====================================================================
# UTILITY FUNCTIONS
# =====================================================================

def canonical_to_dict(doc: CanonicalDocument, exclude_none: bool = True) -> Dict[str, Any]:
    """
    Convert a canonical document to a dictionary suitable for JSON storage.
    
    Args:
        doc: CanonicalDocument instance
        exclude_none: Whether to exclude None values from output
        
    Returns:
        Dictionary representation
    """
    return doc.model_dump(
        mode='json', 
        exclude_none=exclude_none,
        by_alias=True
    )


def dict_to_canonical(data: Dict[str, Any], doc_class=CanonicalDocument) -> CanonicalDocument:
    """
    Convert a dictionary to a canonical document.
    
    Args:
        data: Dictionary with canonical document data
        doc_class: CanonicalDocument class or subclass to instantiate
        
    Returns:
        CanonicalDocument instance
    """
    return doc_class.model_validate(data)


def merge_canonical_documents(base: CanonicalDocument, update: CanonicalDocument) -> CanonicalDocument:
    """
    Merge two canonical documents, with update taking precedence.
    
    Useful for incremental parsing or combining multiple sources.
    
    Args:
        base: Base document
        update: Document with updates to merge
        
    Returns:
        Merged CanonicalDocument
    """
    base_dict = canonical_to_dict(base, exclude_none=False)
    update_dict = canonical_to_dict(update, exclude_none=True)
    
    # Deep merge fields
    if 'fields' in update_dict:
        base_dict.setdefault('fields', {}).update(update_dict['fields'])
    
    # Merge entities (append lists)
    if 'entities' in update_dict:
        for entity_type in ['dates', 'people', 'organizations', 'amounts']:
            base_dict['entities'].setdefault(entity_type, []).extend(
                update_dict['entities'].get(entity_type, [])
            )
    
    # Update metadata
    for key, value in update_dict.get('document_metadata', {}).items():
        if value is not None:
            base_dict['document_metadata'][key] = value
    
    return dict_to_canonical(base_dict, type(base))


# =====================================================================
# EXAMPLE USAGE
# =====================================================================

if __name__ == "__main__":
    # Example: Creating a radiology canonical document
    radiology_doc = RadiologyCanonicalDocument(
        document_metadata=DocumentMetadata(
            title="CT Chest Scan - Patient 001",
            date=datetime(2024, 1, 15),
            author="Dr. Jane Smith"
        ),
        study_instance_uid="1.2.840.113654.2.55.12345",
        modality="CT",
        fields={
            "slice_thickness": "2.5mm",
            "reconstruction_diameter": "350mm"
        },
        entities=ExtractedEntities(
            dates=[
                Entity(
                    entity_type=EntityType.DATE,
                    value="2024-01-15",
                    normalized_value="2024-01-15",
                    confidence=Decimal("0.99")
                )
            ]
        ),
        nodules=[
            {
                "nodule_id": "1",
                "location": {"x": 120.5, "y": 180.3, "z": 45.0},
                "characteristics": {
                    "subtlety": 3,
                    "confidence": 4,
                    "diameter_mm": 8.5
                }
            }
        ]
    )
    
    # Convert to dict for storage
    doc_dict = canonical_to_dict(radiology_doc)
    print("Canonical document as dict:")
    print(doc_dict)
    
    # Validate
    print(f"\nDocument is valid: {getattr(radiology_doc.extraction_metadata, 'warnings', []) == []}")
