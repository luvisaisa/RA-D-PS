# PyLIDC Integration Guide for RA-D-PS

## Overview

This guide explains how to integrate the [pylidc library](https://pylidc.github.io/) with the RA-D-PS schema-agnostic system. The pylidc library provides an Object-Relational Mapping (ORM) interface to the LIDC-IDRI (Lung Image Database Consortium and Image Database Resource Initiative) dataset.

## Why PyLIDC Integration?

**Benefits:**
- ✅ **Direct DICOM Access**: Query LIDC-IDRI dataset without XML parsing
- ✅ **Rich API**: Object-oriented interface with computed properties (volume, diameter, surface area)
- ✅ **Advanced Features**: Annotation clustering, consensus calculation, 3D visualization
- ✅ **Schema Compatibility**: Seamlessly integrates with RA-D-PS canonical schema
- ✅ **Unified Workflow**: Process both XML and DICOM data in same pipeline

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     RA-D-PS System                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐        ┌──────────────────────────────┐     │
│  │ PyLIDC       │───────▶│  PyLIDCAdapter               │     │
│  │ ORM          │        │  - scan_to_canonical()       │     │
│  │              │        │  - annotation_to_entity()    │     │
│  │ - Scan       │        │  - cluster_to_nodule()       │     │
│  │ - Annotation │        └──────────┬───────────────────┘     │
│  │ - Contour    │                   │                         │
│  └──────────────┘                   │                         │
│                                     ▼                         │
│              ┌───────────────────────────────────────┐        │
│              │  Canonical Schema                     │        │
│              │  - RadiologyCanonicalDocument         │        │
│              │  - DocumentMetadata                   │        │
│              │  - ExtractedEntities                  │        │
│              └───────────┬───────────────────────────┘        │
│                          │                                    │
│                          ▼                                    │
│      ┌──────────────────────────────────────────────┐        │
│      │  Storage & Export                            │        │
│      │  - PostgreSQL Repository                     │        │
│      │  - Excel Export                              │        │
│      │  - REST API                                  │        │
│      └──────────────────────────────────────────────┘        │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

## Installation

### 1. Install PyLIDC

```bash
pip install pylidc
```

Or add to your requirements.txt:
```
pylidc>=0.2.3
```

### 2. Configure PyLIDC Database

PyLIDC uses a SQLite database to store LIDC-IDRI metadata. Configure it:

```bash
# Create configuration directory
mkdir -p ~/.pylidc

# Create configuration file
cat > ~/.pylidc/pylidc.conf << EOF
[dicom]
path = /path/to/LIDC-IDRI
warn = True
EOF
```

Replace `/path/to/LIDC-IDRI` with your actual dataset path.

### 3. Download LIDC-IDRI Dataset

Download from: https://wiki.cancerimagingarchive.net/display/Public/LIDC-IDRI

### 4. Initialize PyLIDC Database

```python
import pylidc as pl

# This scans your DICOM files and builds the database
# (May take several minutes on first run)
scans = pl.query(pl.Scan).all()
print(f"Found {len(scans)} scans")
```

## Usage

### Quick Start

```python
import pylidc as pl
from src.ra_d_ps.adapters import PyLIDCAdapter

# Query a scan
scan = pl.query(pl.Scan).first()

# Convert to canonical format
adapter = PyLIDCAdapter()
canonical_doc = adapter.scan_to_canonical(scan, cluster_nodules=True)

# Access data
print(f"Patient: {canonical_doc.fields['patient_id']}")
print(f"Nodules: {len(canonical_doc.nodules)}")
print(f"Modality: {canonical_doc.modality}")
```

### PyLIDC Data Model

**Key Classes:**

1. **Scan** - Represents a CT scan
   - `patient_id`: Patient identifier (e.g., "LIDC-IDRI-0001")
   - `study_instance_uid`: DICOM Study UID
   - `series_instance_uid`: DICOM Series UID
   - `slice_thickness`: Slice thickness in mm
   - `pixel_spacing`: Pixel spacing in mm
   - `annotations`: List of Annotation objects

2. **Annotation** - Radiologist's nodule annotation
   - Characteristics (1-5 scale):
     * `subtlety`: Difficulty of detection
     * `internalStructure`: Internal composition
     * `calcification`: Calcification pattern
     * `sphericity`: 3D shape roundness
     * `margin`: Margin definition
     * `lobulation`: Degree of lobulation
     * `spiculation`: Extent of spiculation
     * `texture`: Radiographic solidity
     * `malignancy`: Likelihood of malignancy
   - Geometric properties:
     * `diameter`: Estimated diameter (mm)
     * `volume`: Estimated volume (mm³)
     * `surface_area`: Surface area (mm²)
     * `centroid`: Center of mass coordinates
   - Contours: `contours` (list of Contour objects)

3. **Contour** - 2D contour for single slice

## Common Workflows

### Workflow 1: Query and Convert Scans

```python
import pylidc as pl
from src.ra_d_ps.adapters.pylidc_adapter import query_and_convert

# Query scans with specific criteria
canonical_docs = query_and_convert(
    query_filter=(pl.Scan.slice_thickness <= 1.0),
    limit=10,
    cluster_nodules=True
)

# Process results
for doc in canonical_docs:
    print(f"Patient: {doc.fields['patient_id']}")
    print(f"Nodules: {len(doc.nodules)}")
```

### Workflow 2: Analyze High-Risk Nodules

```python
import pylidc as pl
from src.ra_d_ps.adapters import PyLIDCAdapter

adapter = PyLIDCAdapter()

# Query highly suspicious annotations
suspicious = pl.query(pl.Annotation).filter(
    pl.Annotation.malignancy >= 4
).all()

print(f"Found {len(suspicious)} highly suspicious nodules")

for ann in suspicious:
    print(f"Malignancy: {ann.malignancy} ({ann.Malignancy})")
    print(f"Diameter: {ann.diameter:.2f} mm")
    print(f"Volume: {ann.volume:.2f} mm³")
    
    # Convert to entity for further processing
    entity = adapter.annotation_to_entity(ann)
```

### Workflow 3: Consensus Analysis

```python
import pylidc as pl
from src.ra_d_ps.adapters import PyLIDCAdapter

# Get scan with clustered annotations
scan = pl.query(pl.Scan).first()
nodule_clusters = scan.cluster_annotations()

adapter = PyLIDCAdapter()

for i, cluster in enumerate(nodule_clusters):
    print(f"\nNodule {i+1}:")
    print(f"  Radiologists: {len(cluster)}")
    
    # Convert cluster to canonical format
    nodule_data = adapter._cluster_to_nodule(i+1, cluster)
    
    if 'consensus' in nodule_data:
        consensus = nodule_data['consensus']
        print(f"  Mean Malignancy: {consensus.get('malignancy_mean', 'N/A'):.2f}")
        print(f"  Std Dev: {consensus.get('malignancy_std', 'N/A'):.2f}")
```

### Workflow 4: Export to PostgreSQL

```python
import pylidc as pl
from src.ra_d_ps.adapters.pylidc_adapter import scan_to_canonical
from src.ra_d_ps.repositories import DocumentRepository  # Phase 7

# Convert scan
scan = pl.query(pl.Scan).first()
canonical_doc = scan_to_canonical(scan)

# Store in PostgreSQL (requires Phase 7 implementation)
repo = DocumentRepository()
doc_id = repo.create(canonical_doc)

print(f"Stored document: {doc_id}")
```

### Workflow 5: Export to Excel (RA-D-PS Format)

```python
import pylidc as pl
from src.ra_d_ps.adapters.pylidc_adapter import query_and_convert
from src.ra_d_ps.parser import export_excel  # Existing function

# Convert scans
canonical_docs = query_and_convert(limit=5)

# Convert to RA-D-PS records format
records = []
for doc in canonical_docs:
    for nodule in doc.nodules:
        record = {
            'file #': doc.fields['patient_id'],
            'Study UID': doc.study_instance_uid,
            'NoduleID': nodule['nodule_id'],
            'radiologists': nodule['radiologists']
        }
        records.append(record)

# Export using existing Excel exporter
export_excel(records, '/path/to/output')
```

## Mapping: PyLIDC → Canonical Schema

### Scan Mapping

| PyLIDC Field | Canonical Field | Notes |
|--------------|----------------|-------|
| `patient_id` | `fields['patient_id']` | LIDC-IDRI identifier |
| `study_instance_uid` | `study_instance_uid` | DICOM attribute |
| `series_instance_uid` | `series_instance_uid` | Also used as document_id |
| `slice_thickness` | `fields['slice_thickness']` | In millimeters |
| `slice_spacing` | `fields['slice_spacing']` | Computed median |
| `pixel_spacing` | `fields['pixel_spacing']` | In millimeters |
| `contrast_used` | `fields['contrast_used']` | Boolean |

### Annotation Mapping

| PyLIDC Field | Canonical Field | Scale |
|--------------|----------------|-------|
| `subtlety` | `radiologists[N]['subtlety']` | 1-5 |
| `internalStructure` | `radiologists[N]['internalStructure']` | 1-4 |
| `calcification` | `radiologists[N]['calcification']` | 1-6 |
| `sphericity` | `radiologists[N]['sphericity']` | 1-5 |
| `margin` | `radiologists[N]['margin']` | 1-5 |
| `lobulation` | `radiologists[N]['lobulation']` | 1-5 |
| `spiculation` | `radiologists[N]['spiculation']` | 1-5 |
| `texture` | `radiologists[N]['texture']` | 1-5 |
| `malignancy` | `radiologists[N]['malignancy']` | 1-5 |
| `diameter` | `radiologists[N]['diameter_mm']` | Float (mm) |
| `volume` | `radiologists[N]['volume_mm3']` | Float (mm³) |
| `surface_area` | `radiologists[N]['surface_area_mm2']` | Float (mm²) |
| `centroid` | `radiologists[N]['centroid']` | {x, y, z} dict |

## Advanced Features

### 1. Nodule Clustering

PyLIDC can cluster annotations from multiple radiologists into nodules:

```python
import pylidc as pl

scan = pl.query(pl.Scan).first()

# Cluster with default parameters
nodules = scan.cluster_annotations()

# Custom clustering
nodules = scan.cluster_annotations(
    metric='jaccard',  # or 'min', 'max', 'avg'
    tol=3.5,          # distance threshold in mm
    factor=0.9        # reduction factor if too many groups
)

print(f"Found {len(nodules)} unique nodules")
```

### 2. Consensus Calculation

The adapter automatically calculates consensus metrics:

```python
from src.ra_d_ps.adapters import PyLIDCAdapter

adapter = PyLIDCAdapter()
scan = pl.query(pl.Scan).first()
canonical_doc = adapter.scan_to_canonical(scan)

for nodule in canonical_doc.nodules:
    if 'consensus' in nodule:
        consensus = nodule['consensus']
        print(f"Malignancy: {consensus['malignancy_mean']:.2f} ± {consensus['malignancy_std']:.2f}")
        print(f"Diameter: {consensus['diameter_mean_mm']:.2f} ± {consensus['diameter_std_mm']:.2f} mm")
```

### 3. Boolean Masks and Volumes

PyLIDC provides rich geometric operations:

```python
import pylidc as pl
import numpy as np

ann = pl.query(pl.Annotation).first()

# Get boolean mask
mask = ann.boolean_mask()
print(f"Mask shape: {mask.shape}")

# Get CT volume for nodule
vol = ann.scan.to_volume()
bbox = ann.bbox()

# Extract nodule region
nodule_region = vol[bbox][mask]
print(f"Mean HU: {nodule_region.mean():.1f}")

# Get resampled cubic volume
ct_vol, seg_mask = ann.uniform_cubic_resample(side_length=50)
print(f"Resampled to: {ct_vol.shape}")
```

## Integration with Existing RA-D-PS Workflow

### Before (XML Only):
```
XML Files → Parser → RA-D-PS Format → Excel/SQLite
```

### After (Unified):
```
┌─ XML Files ──→ Parser ─┐
│                        ├──→ Canonical Schema ──→ Repository ──→ Export
└─ PyLIDC DB ──→ Adapter ┘
```

### Key Benefits:

1. **Unified Schema**: Both XML and pylidc data use `RadiologyCanonicalDocument`
2. **Interoperability**: Process data from different sources together
3. **Flexibility**: Query LIDC database OR parse XML files
4. **Rich Features**: Access pylidc's advanced features (clustering, consensus, volumes)
5. **Future-Proof**: Easy to add more data sources (JSON, CSV, DICOM, etc.)

## Testing

Run the examples to test your integration:

```bash
python examples/pylidc_integration.py
```

Expected output:
```
======================================================================
PyLIDC Integration Examples for RA-D-PS
======================================================================

✅ PyLIDC database configured: 1018 scans available

======================================================================
EXAMPLE 1: Basic Scan Conversion
======================================================================
✅ Found scan: LIDC-IDRI-0001
   Study UID: 1.3.6.1.4.1.14519.5.2.1.6279.6001...
   ...
```

## Performance Considerations

### Query Optimization

```python
import pylidc as pl

# ✅ GOOD: Use specific filters
scans = pl.query(pl.Scan).filter(
    pl.Scan.slice_thickness <= 1.0,
    pl.Scan.contrast_used == False
).limit(100)

# ❌ BAD: Query all scans then filter
scans = pl.query(pl.Scan).all()
filtered = [s for s in scans if s.slice_thickness <= 1.0]
```

### Batch Processing

```python
from src.ra_d_ps.adapters.pylidc_adapter import query_and_convert

# Process in batches
batch_size = 50
total = pl.query(pl.Scan).count()

for offset in range(0, total, batch_size):
    docs = query_and_convert(
        query_filter=None,
        limit=batch_size
    )
    
    # Process batch
    for doc in docs:
        # Store, export, analyze...
        pass
```

## Troubleshooting

### Issue: "pylidc not installed"

**Solution:**
```bash
pip install pylidc
```

### Issue: "No scans found in database"

**Solution:**
1. Check configuration: `cat ~/.pylidc/pylidc.conf`
2. Verify DICOM path is correct
3. Run database initialization: `python -c "import pylidc as pl; pl.query(pl.Scan).count()"`

### Issue: "Unable to find DICOM files"

**Solution:**
- Ensure LIDC-IDRI dataset is downloaded and extracted
- Update configuration with correct path
- Check file permissions

### Issue: Import errors

**Solution:**
```bash
# Install all dependencies
pip install -r requirements.txt

# Install numpy (required by pylidc)
pip install numpy>=1.21.0
```

## References

- **PyLIDC Documentation**: https://pylidc.github.io/
- **LIDC-IDRI Dataset**: https://wiki.cancerimagingarchive.net/display/Public/LIDC-IDRI
- **RA-D-PS Canonical Schema**: See `src/ra_d_ps/schemas/canonical.py`
- **Adapter Implementation**: See `src/ra_d_ps/adapters/pylidc_adapter.py`
- **Examples**: See `examples/pylidc_integration.py`

## Next Steps

1. ✅ Install pylidc and configure database
2. ✅ Run example script to validate integration
3. ⏳ Integrate with Phase 7 (Repository Layer) for PostgreSQL storage
4. ⏳ Add pylidc support to Phase 9 (REST API)
5. ⏳ Create unified query interface for XML + pylidc data

---

**Status**: ✅ PyLIDC adapter implemented and tested with Python 3.9.6  
**Date**: January 2025  
**Version**: 1.0.0
