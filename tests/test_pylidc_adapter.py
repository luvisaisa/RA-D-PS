"""
Tests for PyLIDC Adapter

Tests the integration between pylidc library and RA-D-PS canonical schema.
Tests use mock pylidc objects since actual LIDC database may not be available.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from decimal import Decimal
from datetime import datetime
import numpy as np


# Test if pylidc is available
try:
    import pylidc as pl
    PYLIDC_AVAILABLE = True
except ImportError:
    PYLIDC_AVAILABLE = False


# Always import our adapter
from src.ra_d_ps.adapters.pylidc_adapter import PyLIDCAdapter
from src.ra_d_ps.schemas.canonical import EntityType


class TestPyLIDCAdapter:
    """Test suite for PyLIDC adapter functionality."""
    
    def setup_method(self):
        """Setup for each test method."""
        if PYLIDC_AVAILABLE:
            self.adapter = PyLIDCAdapter()
    
    def create_mock_scan(self):
        """Create a mock pylidc Scan object."""
        scan = Mock()
        scan.patient_id = "LIDC-IDRI-0001"
        scan.study_instance_uid = "1.3.6.1.4.1.14519.5.2.1.6279.6001.test"
        scan.series_instance_uid = "1.3.6.1.4.1.14519.5.2.1.6279.6001.test.series"
        scan.slice_thickness = 0.625
        scan.slice_spacing = 0.625
        scan.pixel_spacing = 0.703125
        scan.contrast_used = False
        scan.is_from_initial = True
        scan.slice_zvals = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        scan.annotations = []
        return scan
    
    def create_mock_annotation(self, nodule_id=1):
        """Create a mock pylidc Annotation object."""
        ann = Mock()
        ann.subtlety = 3
        ann.internalStructure = 1
        ann.calcification = 6
        ann.sphericity = 3
        ann.margin = 3
        ann.lobulation = 2
        ann.spiculation = 1
        ann.texture = 3
        ann.malignancy = 3
        
        # Semantic properties
        ann.Subtlety = "Fairly Subtle"
        ann.Malignancy = "Indeterminate"
        
        # Geometric properties
        ann.centroid = np.array([100.5, 200.3, 50.7])
        ann.diameter = 12.5
        ann.volume = 1024.8
        ann.surface_area = 490.6
        ann.bbox_dims = Mock(return_value=np.array([15.2, 14.8, 16.1]))
        
        # Contour info
        ann.contours = [Mock() for _ in range(5)]
        ann.contour_slice_indices = np.array([10, 11, 12, 13, 14])
        ann.contour_slice_zvals = np.array([50.0, 51.0, 52.0, 53.0, 54.0])
        
        return ann
    
    @pytest.mark.skipif(not PYLIDC_AVAILABLE, reason="pylidc not installed")
    def test_adapter_initialization(self):
        """Test that adapter initializes correctly."""
        adapter = PyLIDCAdapter()
        assert adapter is not None
    
    @pytest.mark.skipif(PYLIDC_AVAILABLE, reason="Skip when pylidc IS installed")
    def test_adapter_requires_pylidc(self):
        """Test that adapter raises error when pylidc not available."""
        # This test only runs when pylidc is NOT installed
        with patch('src.ra_d_ps.adapters.pylidc_adapter.PYLIDC_AVAILABLE', False):
            with pytest.raises(ImportError, match="pylidc library is not installed"):
                PyLIDCAdapter()
    
    @pytest.mark.skipif(not PYLIDC_AVAILABLE, reason="pylidc not installed")
    def test_scan_to_canonical_basic(self):
        """Test basic scan to canonical conversion."""
        scan = self.create_mock_scan()
        scan.cluster_annotations = Mock(return_value=[])
        
        doc = self.adapter.scan_to_canonical(scan, cluster_nodules=True)
        
        assert doc is not None
        assert doc.document_metadata.document_type == "radiology_report"
        assert doc.document_metadata.source_system == "LIDC-IDRI"
        assert doc.study_instance_uid == scan.study_instance_uid
        assert doc.series_instance_uid == scan.series_instance_uid
        assert doc.modality == "CT"
        assert doc.fields["patient_id"] == "LIDC-IDRI-0001"
        assert doc.fields["slice_thickness"] == 0.625
        assert doc.fields["pixel_spacing"] == 0.703125
    
    @pytest.mark.skipif(not PYLIDC_AVAILABLE, reason="pylidc not installed")
    def test_scan_to_canonical_with_annotations(self):
        """Test scan conversion with annotations."""
        scan = self.create_mock_scan()
        ann1 = self.create_mock_annotation(1)
        ann2 = self.create_mock_annotation(2)
        
        # Mock cluster_annotations to return one nodule with 2 radiologists
        scan.cluster_annotations = Mock(return_value=[[ann1, ann2]])
        
        doc = self.adapter.scan_to_canonical(scan, cluster_nodules=True)
        
        assert len(doc.nodules) == 1
        nodule = doc.nodules[0]
        assert nodule["nodule_id"] == "1"
        assert nodule["num_radiologists"] == 2
        assert "radiologists" in nodule
        assert "1" in nodule["radiologists"]
        assert "2" in nodule["radiologists"]
    
    @pytest.mark.skipif(not PYLIDC_AVAILABLE, reason="pylidc not installed")
    def test_annotation_to_dict(self):
        """Test annotation to dictionary conversion."""
        ann = self.create_mock_annotation()
        
        ann_dict = self.adapter._annotation_to_dict(ann)
        
        assert ann_dict["subtlety"] == 3
        assert ann_dict["malignancy"] == 3
        assert ann_dict["subtlety_text"] == "Fairly Subtle"
        assert ann_dict["malignancy_text"] == "Indeterminate"
        assert ann_dict["diameter_mm"] == 12.5
        assert ann_dict["volume_mm3"] == 1024.8
        assert "centroid" in ann_dict
        assert ann_dict["centroid"]["x"] == 100.5
        assert ann_dict["centroid"]["y"] == 200.3
        assert ann_dict["centroid"]["z"] == 50.7
    
    @pytest.mark.skipif(not PYLIDC_AVAILABLE, reason="pylidc not installed")
    def test_cluster_to_nodule(self):
        """Test clustering annotations into nodule."""
        ann1 = self.create_mock_annotation()
        ann2 = self.create_mock_annotation()
        ann3 = self.create_mock_annotation()
        annotations = [ann1, ann2, ann3]
        
        nodule_data = self.adapter._cluster_to_nodule(1, annotations)
        
        assert nodule_data["nodule_id"] == "1"
        assert nodule_data["num_radiologists"] == 3
        assert len(nodule_data["radiologists"]) == 3
        assert "consensus" in nodule_data
    
    @pytest.mark.skipif(not PYLIDC_AVAILABLE, reason="pylidc not installed")
    def test_calculate_consensus(self):
        """Test consensus calculation across annotations."""
        ann1 = self.create_mock_annotation()
        ann1.malignancy = 3
        ann1.diameter = 10.0
        ann1.volume = 500.0
        
        ann2 = self.create_mock_annotation()
        ann2.malignancy = 4
        ann2.diameter = 12.0
        ann2.volume = 600.0
        
        ann3 = self.create_mock_annotation()
        ann3.malignancy = 3
        ann3.diameter = 11.0
        ann3.volume = 550.0
        
        consensus = self.adapter._calculate_consensus([ann1, ann2, ann3])
        
        assert "malignancy_mean" in consensus
        assert "malignancy_std" in consensus
        assert "diameter_mean_mm" in consensus
        assert abs(consensus["malignancy_mean"] - 3.333) < 0.01
        assert abs(consensus["diameter_mean_mm"] - 11.0) < 0.01
    
    @pytest.mark.skipif(not PYLIDC_AVAILABLE, reason="pylidc not installed")
    def test_annotation_to_entity(self):
        """Test annotation to entity conversion."""
        ann = self.create_mock_annotation()
        
        entity = self.adapter.annotation_to_entity(ann, nodule_id=1)
        
        assert entity.entity_type == EntityType.MEDICAL_TERM
        assert "Nodule at" in entity.value
        assert entity.confidence == Decimal("0.95")
        assert entity.source_field == "pylidc_annotation"
        assert entity.metadata["nodule_id"] == 1
        assert entity.metadata["diameter_mm"] == 12.5
        assert entity.metadata["malignancy"] == 3
    
    @pytest.mark.skipif(not PYLIDC_AVAILABLE, reason="pylidc not installed")
    def test_scan_to_entities(self):
        """Test extracting entities from scan."""
        scan = self.create_mock_scan()
        ann1 = self.create_mock_annotation()
        ann2 = self.create_mock_annotation()
        
        scan.cluster_annotations = Mock(return_value=[[ann1, ann2]])
        
        entities = self.adapter.scan_to_entities(scan, cluster_nodules=True)
        
        assert len(entities.medical_terms) == 2
        assert len(entities.identifiers) == 1
        assert entities.identifiers[0].value == "LIDC-IDRI-0001"
    
    @pytest.mark.skipif(not PYLIDC_AVAILABLE, reason="pylidc not installed")
    def test_scan_without_clustering(self):
        """Test scan conversion without nodule clustering."""
        scan = self.create_mock_scan()
        ann1 = self.create_mock_annotation()
        ann2 = self.create_mock_annotation()
        scan.annotations = [ann1, ann2]
        
        doc = self.adapter.scan_to_canonical(scan, cluster_nodules=False)
        
        # Without clustering, should have radiologist_readings
        assert len(doc.radiologist_readings) == 2
        assert len(doc.nodules) == 0  # No nodules when not clustering


@pytest.mark.skipif(not PYLIDC_AVAILABLE, reason="pylidc not installed")
class TestPyLIDCConvenienceFunctions:
    """Test convenience functions for quick access."""
    
    @patch('src.ra_d_ps.adapters.pylidc_adapter.pl')
    def test_scan_to_canonical_function(self, mock_pl):
        """Test scan_to_canonical convenience function."""
        from src.ra_d_ps.adapters.pylidc_adapter import scan_to_canonical
        
        # Create mock scan
        mock_scan = Mock()
        mock_scan.patient_id = "TEST-001"
        mock_scan.study_instance_uid = "1.2.3"
        mock_scan.series_instance_uid = "1.2.3.4"
        mock_scan.slice_thickness = 1.0
        mock_scan.slice_spacing = 1.0
        mock_scan.pixel_spacing = 0.7
        mock_scan.contrast_used = False
        mock_scan.is_from_initial = True
        mock_scan.slice_zvals = np.array([1, 2, 3])
        mock_scan.cluster_annotations = Mock(return_value=[])
        
        doc = scan_to_canonical(mock_scan)
        
        assert doc is not None
        assert doc.document_metadata.document_type == "radiology_report"


class TestPyLIDCAdapterEdgeCases:
    """Test edge cases and error handling."""
    
    @pytest.mark.skipif(not PYLIDC_AVAILABLE, reason="pylidc not installed")
    def test_annotation_with_none_values(self):
        """Test handling of annotations with None values."""
        adapter = PyLIDCAdapter()
        
        ann = Mock()
        ann.subtlety = None
        ann.malignancy = None
        ann.internalStructure = 1
        ann.calcification = 6
        ann.sphericity = 3
        ann.margin = 3
        ann.lobulation = 2
        ann.spiculation = 1
        ann.texture = 3
        ann.Subtlety = None
        ann.Malignancy = None
        ann.centroid = np.array([0, 0, 0])
        ann.diameter = 0.0
        ann.volume = 0.0
        ann.surface_area = 0.0
        ann.bbox_dims = Mock(return_value=np.array([0, 0, 0]))
        ann.contours = []
        ann.contour_slice_indices = np.array([])
        ann.contour_slice_zvals = np.array([])
        
        ann_dict = adapter._annotation_to_dict(ann)
        
        assert ann_dict["subtlety"] is None
        assert ann_dict["malignancy"] is None
        assert ann_dict["subtlety_text"] is None
        assert ann_dict["malignancy_text"] is None
    
    @pytest.mark.skipif(not PYLIDC_AVAILABLE, reason="pylidc not installed")
    def test_consensus_with_single_annotation(self):
        """Test consensus calculation with single annotation."""
        adapter = PyLIDCAdapter()
        
        ann = Mock()
        ann.malignancy = 3
        ann.diameter = 10.0
        ann.volume = 500.0
        ann.subtlety = 2
        ann.internalStructure = 1
        ann.calcification = 6
        ann.sphericity = 3
        ann.margin = 3
        ann.lobulation = 2
        ann.spiculation = 1
        ann.texture = 3
        
        consensus = adapter._calculate_consensus([ann])
        
        # With single annotation, mean = value, std = 0
        assert consensus["malignancy_mean"] == 3.0
        assert consensus["malignancy_std"] == 0.0


def test_import_without_pylidc():
    """Test that module can be imported even without pylidc."""
    # This should not raise an error
    from src.ra_d_ps.adapters import pylidc_adapter
    
    assert hasattr(pylidc_adapter, 'PyLIDCAdapter')
    assert hasattr(pylidc_adapter, 'PYLIDC_AVAILABLE')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
