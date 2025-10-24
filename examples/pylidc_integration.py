"""
PyLIDC Integration Examples for RA-D-PS

This script demonstrates various ways to integrate pylidc with the
schema-agnostic RA-D-PS system.

Prerequisites:
    1. Install pylidc: pip install pylidc
    2. Configure pylidc database (see: https://pylidc.github.io/install.html)
    3. Download LIDC-IDRI dataset

Usage:
    python examples/pylidc_integration.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import pylidc as pl
    PYLIDC_AVAILABLE = True
except ImportError:
    print("⚠️  pylidc not installed. Install with: pip install pylidc")
    PYLIDC_AVAILABLE = False
    sys.exit(1)

from src.ra_d_ps.adapters import PyLIDCAdapter
from src.ra_d_ps.adapters.pylidc_adapter import query_and_convert, scan_to_canonical
from src.ra_d_ps.schemas.canonical import canonical_to_dict
import json


def example_1_basic_scan_conversion():
    """Example 1: Convert a single scan to canonical format."""
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Scan Conversion")
    print("="*70)
    
    # Query first scan
    scan = pl.query(pl.Scan).first()
    
    if not scan:
        print("❌ No scans found in database. Configure pylidc first.")
        return
    
    print(f"✅ Found scan: {scan.patient_id}")
    print(f"   Study UID: {scan.study_instance_uid}")
    print(f"   Series UID: {scan.series_instance_uid}")
    print(f"   Annotations: {len(scan.annotations)}")
    
    # Convert to canonical format
    adapter = PyLIDCAdapter()
    canonical_doc = adapter.scan_to_canonical(scan, cluster_nodules=True)
    
    print(f"\n📄 Canonical Document Created:")
    print(f"   Document ID: {canonical_doc.document_metadata.document_id}")
    print(f"   Document Type: {canonical_doc.document_metadata.document_type}")
    print(f"   Modality: {canonical_doc.modality}")
    print(f"   Nodules Found: {len(canonical_doc.nodules)}")
    
    # Show first nodule details
    if canonical_doc.nodules:
        nodule = canonical_doc.nodules[0]
        print(f"\n   First Nodule:")
        print(f"      Nodule ID: {nodule['nodule_id']}")
        print(f"      Radiologists: {nodule['num_radiologists']}")
        
        if 'consensus' in nodule:
            print(f"      Consensus Malignancy: {nodule['consensus'].get('malignancy_mean', 'N/A'):.2f}")
            print(f"      Consensus Diameter: {nodule['consensus'].get('diameter_mean_mm', 'N/A'):.2f} mm")


def example_2_query_and_convert():
    """Example 2: Query multiple scans with filters and convert."""
    print("\n" + "="*70)
    print("EXAMPLE 2: Query and Batch Convert")
    print("="*70)
    
    # Query scans with slice thickness <= 1mm
    scans = pl.query(pl.Scan).filter(pl.Scan.slice_thickness <= 1.0)
    count = scans.count()
    
    print(f"✅ Found {count} scans with slice_thickness <= 1mm")
    
    if count == 0:
        print("   Try different filter criteria")
        return
    
    # Convert first 3 scans
    limit = min(3, count)
    print(f"   Converting first {limit} scans...")
    
    canonical_docs = query_and_convert(
        query_filter=(pl.Scan.slice_thickness <= 1.0),
        limit=limit,
        cluster_nodules=True
    )
    
    print(f"\n📦 Converted {len(canonical_docs)} scans to canonical format")
    
    for i, doc in enumerate(canonical_docs):
        print(f"\n   Scan {i+1}:")
        print(f"      Patient: {doc.fields['patient_id']}")
        print(f"      Nodules: {len(doc.nodules)}")
        print(f"      Slice Thickness: {doc.fields['slice_thickness']} mm")
        print(f"      Pixel Spacing: {doc.fields['pixel_spacing']} mm")


def example_3_entity_extraction():
    """Example 3: Extract nodules as medical entities."""
    print("\n" + "="*70)
    print("EXAMPLE 3: Entity Extraction")
    print("="*70)
    
    scan = pl.query(pl.Scan).first()
    
    if not scan:
        print("❌ No scans found in database.")
        return
    
    print(f"✅ Processing scan: {scan.patient_id}")
    
    # Extract entities
    adapter = PyLIDCAdapter()
    entities = adapter.scan_to_entities(scan, cluster_nodules=True)
    
    print(f"\n🔍 Extracted Entities:")
    print(f"   Medical Terms: {len(entities.medical_terms)}")
    print(f"   Identifiers: {len(entities.identifiers)}")
    
    # Show first few medical terms
    for i, entity in enumerate(entities.medical_terms[:3]):
        print(f"\n   Medical Term {i+1}:")
        print(f"      Value: {entity.value}")
        print(f"      Confidence: {entity.confidence}")
        print(f"      Metadata: {entity.metadata}")


def example_4_export_to_json():
    """Example 4: Export canonical document to JSON."""
    print("\n" + "="*70)
    print("EXAMPLE 4: Export to JSON")
    print("="*70)
    
    scan = pl.query(pl.Scan).first()
    
    if not scan:
        print("❌ No scans found in database.")
        return
    
    # Convert to canonical
    canonical_doc = scan_to_canonical(scan)
    
    # Convert to dict and export
    doc_dict = canonical_to_dict(canonical_doc, exclude_none=True)
    
    output_file = Path("/tmp/pylidc_canonical_export.json")
    with open(output_file, 'w') as f:
        json.dump(doc_dict, f, indent=2, default=str)
    
    print(f"✅ Exported to: {output_file}")
    print(f"   File size: {output_file.stat().st_size / 1024:.2f} KB")
    print(f"\n   JSON keys: {list(doc_dict.keys())}")


def example_5_annotation_characteristics():
    """Example 5: Analyze annotation characteristics."""
    print("\n" + "="*70)
    print("EXAMPLE 5: Annotation Characteristics Analysis")
    print("="*70)
    
    # Query annotations with high malignancy
    annotations = pl.query(pl.Annotation).filter(
        pl.Annotation.malignancy >= 4
    ).limit(5)
    
    count = annotations.count()
    print(f"✅ Found {count} highly suspicious annotations (malignancy >= 4)")
    
    adapter = PyLIDCAdapter()
    
    for i, ann in enumerate(annotations):
        print(f"\n   Annotation {i+1}:")
        print(f"      Malignancy: {ann.malignancy} ({ann.Malignancy})")
        print(f"      Subtlety: {ann.subtlety} ({ann.Subtlety})")
        print(f"      Diameter: {ann.diameter:.2f} mm")
        print(f"      Volume: {ann.volume:.2f} mm³")
        print(f"      Spiculation: {ann.spiculation}")
        print(f"      Lobulation: {ann.lobulation}")
        
        # Convert to entity
        entity = adapter.annotation_to_entity(ann)
        print(f"      Entity Value: {entity.value}")


def example_6_clustered_nodules():
    """Example 6: Work with clustered nodule annotations."""
    print("\n" + "="*70)
    print("EXAMPLE 6: Clustered Nodule Analysis")
    print("="*70)
    
    # Find a scan with multiple annotations
    scan = pl.query(pl.Scan).filter(
        pl.Scan.annotations.any()
    ).first()
    
    if not scan:
        print("❌ No annotated scans found.")
        return
    
    print(f"✅ Analyzing scan: {scan.patient_id}")
    print(f"   Total annotations: {len(scan.annotations)}")
    
    # Cluster annotations
    nodule_clusters = scan.cluster_annotations()
    
    print(f"   Clustered into {len(nodule_clusters)} nodules")
    
    for i, cluster in enumerate(nodule_clusters):
        print(f"\n   Nodule {i+1}:")
        print(f"      Number of radiologists: {len(cluster)}")
        
        # Calculate agreement metrics
        malignancies = [ann.malignancy for ann in cluster if ann.malignancy]
        if malignancies:
            import numpy as np
            print(f"      Malignancy ratings: {malignancies}")
            print(f"      Mean malignancy: {np.mean(malignancies):.2f}")
            print(f"      Std dev: {np.std(malignancies):.2f}")
            
            # Check agreement
            if np.std(malignancies) < 0.5:
                print(f"      ✅ High agreement among radiologists")
            else:
                print(f"      ⚠️  Disagreement among radiologists")


def example_7_integration_with_existing_system():
    """Example 7: Integrate with existing RA-D-PS parser."""
    print("\n" + "="*70)
    print("EXAMPLE 7: Integration with Existing System")
    print("="*70)
    
    print("This example shows how pylidc canonical docs can be")
    print("processed alongside XML-parsed canonical docs.")
    
    # Convert pylidc scan
    scan = pl.query(pl.Scan).first()
    if not scan:
        print("❌ No scans found.")
        return
    
    pylidc_doc = scan_to_canonical(scan)
    
    print(f"\n✅ PyLIDC Document:")
    print(f"   Source: {pylidc_doc.document_metadata.source_system}")
    print(f"   Patient: {pylidc_doc.fields['patient_id']}")
    print(f"   Nodules: {len(pylidc_doc.nodules)}")
    
    print("\n📝 This document can now be:")
    print("   1. Stored in PostgreSQL via repository layer")
    print("   2. Exported to Excel using existing exporters")
    print("   3. Queried via REST API")
    print("   4. Combined with XML-parsed data for analysis")
    
    print("\n🔗 Integration points:")
    print("   - Document type: 'radiology_report' (same as XML)")
    print("   - Schema: RadiologyCanonicalDocument (compatible)")
    print("   - Metadata: DocumentMetadata (standardized)")
    print("   - Storage: PostgreSQL JSONB (flexible)")


def main():
    """Run all examples."""
    print("\n" + "="*70)
    print("PyLIDC Integration Examples for RA-D-PS")
    print("="*70)
    
    if not PYLIDC_AVAILABLE:
        return
    
    try:
        # Check if database is configured
        test_query = pl.query(pl.Scan).count()
        print(f"\n✅ PyLIDC database configured: {test_query} scans available")
    except Exception as e:
        print(f"\n❌ PyLIDC database not configured: {e}")
        print("\nPlease configure pylidc first:")
        print("   1. pip install pylidc")
        print("   2. Configure database: https://pylidc.github.io/install.html")
        print("   3. Download LIDC-IDRI dataset")
        return
    
    # Run examples
    examples = [
        example_1_basic_scan_conversion,
        example_2_query_and_convert,
        example_3_entity_extraction,
        example_4_export_to_json,
        example_5_annotation_characteristics,
        example_6_clustered_nodules,
        example_7_integration_with_existing_system
    ]
    
    for example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"\n❌ Error in {example_func.__name__}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*70)
    print("Examples Complete!")
    print("="*70)


if __name__ == "__main__":
    main()
