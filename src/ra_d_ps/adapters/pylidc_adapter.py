"""
PyLIDC Adapter for RA-D-PS Schema-Agnostic System

This adapter converts pylidc Scan and Annotation objects into the canonical schema format.
Supports direct integration with the pylidc library for LIDC-IDRI dataset processing.

Usage:
    import pylidc as pl
    from src.ra_d_ps.adapters import PyLIDCAdapter
    
    # Query a scan using pylidc
    scan = pl.query(pl.Scan).first()
    
    # Convert to canonical format
    adapter = PyLIDCAdapter()
    canonical_doc = adapter.scan_to_canonical(scan)
    
    # Or convert specific annotations
    annotations = scan.annotations
    for ann in annotations:
        canonical_ann = adapter.annotation_to_entity(ann)

References:
    - pylidc documentation: https://pylidc.github.io/
    - Scan class: https://pylidc.github.io/scan.html
    - Annotation class: https://pylidc.github.io/annotation.html
"""

from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from decimal import Decimal

try:
    import pylidc as pl
    PYLIDC_AVAILABLE = True
except ImportError:
    PYLIDC_AVAILABLE = False
    pl = None

from ..schemas.canonical import (
    CanonicalDocument,
    RadiologyCanonicalDocument,
    DocumentMetadata,
    Entity,
    ExtractedEntities,
    ExtractionMetadata,
    EntityType
)


class PyLIDCAdapter:
    """
    Adapter to convert pylidc Scan and Annotation objects to canonical schema.
    
    The pylidc library provides an ORM interface to the LIDC-IDRI dataset.
    This adapter bridges pylidc's object model with our canonical schema,
    enabling schema-agnostic processing of LIDC data.
    """
    
    def __init__(self):
        """Initialize the PyLIDC adapter."""
        if not PYLIDC_AVAILABLE:
            raise ImportError(
                "pylidc library is not installed. "
                "Install it with: pip install pylidc"
            )
    
    def scan_to_canonical(
        self, 
        scan,  # pylidc.Scan object
        include_annotations: bool = True,
        cluster_nodules: bool = True
    ) -> RadiologyCanonicalDocument:
        """
        Convert a pylidc Scan object to RadiologyCanonicalDocument.
        
        Args:
            scan: pylidc.Scan object
            include_annotations: Whether to include annotation data
            cluster_nodules: Whether to cluster annotations into nodules
            
        Returns:
            RadiologyCanonicalDocument with scan and annotation data
        """
        # Build document metadata
        metadata = DocumentMetadata(
            document_id=scan.series_instance_uid,
            source_file=f"pylidc://{scan.patient_id}",
            document_type="radiology_report",
            title=f"LIDC Scan: {scan.patient_id}",
            date=datetime.utcnow(),  # No date in scan, use processing time
            source_system="LIDC-IDRI",
            language="en"
        )
        
        # Build radiology-specific fields
        nodules_data = []
        radiologist_readings = []
        
        if include_annotations:
            if cluster_nodules:
                # Cluster annotations into nodules (groups of 4 radiologists)
                nodule_clusters = scan.cluster_annotations()
                for nodule_idx, annotations in enumerate(nodule_clusters):
                    nodule_data = self._cluster_to_nodule(
                        nodule_idx + 1, 
                        annotations
                    )
                    nodules_data.append(nodule_data)
            else:
                # Individual annotations without clustering
                for ann in scan.annotations:
                    ann_data = self._annotation_to_dict(ann)
                    radiologist_readings.append(ann_data)
        
        # Build extraction metadata
        extraction_meta = ExtractionMetadata(
            profile_id="pylidc-adapter",
            profile_name="PyLIDC Direct Adapter",
            parser_version="1.0.0"
        )
        
        # Create canonical document
        doc = RadiologyCanonicalDocument(
            document_metadata=metadata,
            study_instance_uid=scan.study_instance_uid,
            series_instance_uid=scan.series_instance_uid,
            modality="CT",  # LIDC is all CT scans
            nodules=nodules_data,
            radiologist_readings=radiologist_readings,
            fields={
                "patient_id": scan.patient_id,
                "slice_thickness": float(scan.slice_thickness),
                "slice_spacing": float(scan.slice_spacing),
                "pixel_spacing": float(scan.pixel_spacing),
                "contrast_used": scan.contrast_used,
                "is_from_initial": scan.is_from_initial,
                "num_slices": len(scan.slice_zvals),
                "slice_range": [float(scan.slice_zvals.min()), 
                               float(scan.slice_zvals.max())]
            },
            extraction_metadata=extraction_meta
        )
        
        return doc
    
    def _cluster_to_nodule(
        self, 
        nodule_id: int, 
        annotations: List  # List[pylidc.Annotation]
    ) -> Dict[str, Any]:
        """
        Convert a cluster of annotations (same nodule, multiple radiologists) to dict.
        
        Args:
            nodule_id: Unique nodule identifier within scan
            annotations: List of pylidc.Annotation objects for same nodule
            
        Returns:
            Dictionary with nodule data including all radiologist annotations
        """
        nodule_data = {
            "nodule_id": str(nodule_id),
            "num_radiologists": len(annotations),
            "radiologists": {}
        }
        
        # Add each radiologist's annotation
        for rad_idx, ann in enumerate(annotations):
            rad_id = str(rad_idx + 1)
            nodule_data["radiologists"][rad_id] = self._annotation_to_dict(ann)
        
        # Calculate consensus/aggregate metrics if multiple annotations
        if len(annotations) > 1:
            nodule_data["consensus"] = self._calculate_consensus(annotations)
        
        return nodule_data
    
    def _annotation_to_dict(self, ann) -> Dict[str, Any]:
        """
        Convert a pylidc Annotation object to dictionary.
        
        Args:
            ann: pylidc.Annotation object
            
        Returns:
            Dictionary with all annotation attributes
        """
        # Get centroid coordinates
        centroid = ann.centroid
        
        return {
            # Core characteristics (1-5 scale)
            "subtlety": int(ann.subtlety) if ann.subtlety else None,
            "internalStructure": int(ann.internalStructure) if ann.internalStructure else None,
            "calcification": int(ann.calcification) if ann.calcification else None,
            "sphericity": int(ann.sphericity) if ann.sphericity else None,
            "margin": int(ann.margin) if ann.margin else None,
            "lobulation": int(ann.lobulation) if ann.lobulation else None,
            "spiculation": int(ann.spiculation) if ann.spiculation else None,
            "texture": int(ann.texture) if ann.texture else None,
            "malignancy": int(ann.malignancy) if ann.malignancy else None,
            
            # Semantic interpretations
            "subtlety_text": ann.Subtlety if ann.subtlety else None,
            "malignancy_text": ann.Malignancy if ann.malignancy else None,
            
            # Geometric properties
            "centroid": {
                "x": float(centroid[0]),
                "y": float(centroid[1]),
                "z": float(centroid[2])
            },
            "diameter_mm": float(ann.diameter),
            "volume_mm3": float(ann.volume),
            "surface_area_mm2": float(ann.surface_area),
            "bbox_dims_mm": [float(d) for d in ann.bbox_dims()],
            
            # Contour information
            "num_contours": len(ann.contours),
            "contour_slice_indices": ann.contour_slice_indices.tolist(),
            "contour_slice_zvals": ann.contour_slice_zvals.tolist()
        }
    
    def _calculate_consensus(self, annotations: List) -> Dict[str, Any]:
        """
        Calculate consensus metrics across multiple radiologist annotations.
        
        Args:
            annotations: List of pylidc.Annotation objects for same nodule
            
        Returns:
            Dictionary with consensus statistics
        """
        import numpy as np
        
        # Collect all numeric characteristics
        characteristics = [
            'subtlety', 'internalStructure', 'calcification', 
            'sphericity', 'margin', 'lobulation', 
            'spiculation', 'texture', 'malignancy'
        ]
        
        consensus = {}
        for char in characteristics:
            values = [getattr(ann, char) for ann in annotations 
                     if getattr(ann, char) is not None]
            if values:
                consensus[f"{char}_mean"] = float(np.mean(values))
                consensus[f"{char}_std"] = float(np.std(values))
                consensus[f"{char}_mode"] = int(np.argmax(np.bincount(values)))
        
        # Geometric consensus
        diameters = [ann.diameter for ann in annotations]
        volumes = [ann.volume for ann in annotations]
        
        consensus["diameter_mean_mm"] = float(np.mean(diameters))
        consensus["diameter_std_mm"] = float(np.std(diameters))
        consensus["volume_mean_mm3"] = float(np.mean(volumes))
        consensus["volume_std_mm3"] = float(np.std(volumes))
        
        return consensus
    
    def annotation_to_entity(
        self, 
        ann,  # pylidc.Annotation object
        nodule_id: Optional[int] = None
    ) -> Entity:
        """
        Convert a pylidc Annotation to an Entity for entity extraction.
        
        Args:
            ann: pylidc.Annotation object
            nodule_id: Optional nodule identifier
            
        Returns:
            Entity object with annotation data
        """
        centroid = ann.centroid
        value = f"Nodule at ({centroid[0]:.1f}, {centroid[1]:.1f}, {centroid[2]:.1f})"
        
        entity = Entity(
            entity_type=EntityType.MEDICAL_TERM,
            value=value,
            confidence=Decimal("0.95"),  # pylidc data is expert-annotated
            source_field="pylidc_annotation",
            metadata={
                "nodule_id": nodule_id,
                "diameter_mm": float(ann.diameter),
                "volume_mm3": float(ann.volume),
                "malignancy": int(ann.malignancy) if ann.malignancy else None,
                "malignancy_text": ann.Malignancy if ann.malignancy else None,
                "subtlety": int(ann.subtlety) if ann.subtlety else None,
                "spiculation": int(ann.spiculation) if ann.spiculation else None
            }
        )
        
        return entity
    
    def scan_to_entities(
        self, 
        scan,  # pylidc.Scan object
        cluster_nodules: bool = True
    ) -> ExtractedEntities:
        """
        Extract all nodule annotations as medical entities.
        
        Args:
            scan: pylidc.Scan object
            cluster_nodules: Whether to cluster annotations into nodules
            
        Returns:
            ExtractedEntities with medical_terms populated
        """
        medical_terms = []
        
        if cluster_nodules:
            nodule_clusters = scan.cluster_annotations()
            for nodule_idx, annotations in enumerate(nodule_clusters):
                for ann in annotations:
                    entity = self.annotation_to_entity(ann, nodule_idx + 1)
                    medical_terms.append(entity)
        else:
            for ann in scan.annotations:
                entity = self.annotation_to_entity(ann)
                medical_terms.append(entity)
        
        # Add scan-level identifier
        identifiers = [
            Entity(
                entity_type=EntityType.IDENTIFIER,
                value=scan.patient_id,
                normalized_value=scan.patient_id,
                confidence=Decimal("1.0"),
                source_field="patient_id"
            )
        ]
        
        return ExtractedEntities(
            medical_terms=medical_terms,
            identifiers=identifiers
        )


# Convenience functions for quick access
def query_and_convert(
    query_filter=None,
    limit: Optional[int] = None,
    cluster_nodules: bool = True
) -> List[RadiologyCanonicalDocument]:
    """
    Query pylidc database and convert results to canonical format.
    
    Args:
        query_filter: SQLAlchemy filter for pylidc.Scan query
        limit: Maximum number of scans to process
        cluster_nodules: Whether to cluster annotations
        
    Returns:
        List of RadiologyCanonicalDocument objects
    
    Example:
        # Get first 10 scans with slice thickness <= 1mm
        docs = query_and_convert(
            query_filter=(pl.Scan.slice_thickness <= 1),
            limit=10
        )
    """
    if not PYLIDC_AVAILABLE:
        raise ImportError("pylidc not installed")
    
    adapter = PyLIDCAdapter()
    
    # Build query
    query = pl.query(pl.Scan)
    if query_filter is not None:
        query = query.filter(query_filter)
    if limit:
        query = query.limit(limit)
    
    # Convert scans
    canonical_docs = []
    for scan in query:
        doc = adapter.scan_to_canonical(
            scan, 
            cluster_nodules=cluster_nodules
        )
        canonical_docs.append(doc)
    
    return canonical_docs


def scan_to_canonical(scan, cluster_nodules: bool = True) -> RadiologyCanonicalDocument:
    """
    Quick conversion of a single pylidc Scan to canonical format.
    
    Args:
        scan: pylidc.Scan object
        cluster_nodules: Whether to cluster annotations
        
    Returns:
        RadiologyCanonicalDocument
    """
    adapter = PyLIDCAdapter()
    return adapter.scan_to_canonical(scan, cluster_nodules=cluster_nodules)
