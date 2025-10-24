"""
Tests for Excel exporters.

Run with: pytest -q tests/test_excel_exporter.py
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from src.ra_d_ps.exporters.excel_exporter import RADPSExcelFormatter, TemplateExcelFormatter
from src.ra_d_ps.exporters.base import ExportError


class TestRADPSExcelFormatter:
    """Test RA-D-PS format Excel exporter."""
    
    @pytest.fixture
    def sample_records(self):
        """Sample RA-D-PS format records."""
        return [
            {
                "file_number": "001",
                "study_uid": "1.2.3.4.5",
                "nodule_id": "N1",
                "radiologists": {
                    "1": {
                        "subtlety": 3,
                        "confidence": 4,
                        "obscuration": 2,
                        "reason": "test reason",
                        "coordinates": "100, 200, 50"
                    },
                    "2": {
                        "subtlety": 2,
                        "confidence": 5,
                        "obscuration": 1,
                        "reason": "",
                        "coordinates": "105, 205, 52"
                    }
                }
            },
            {
                "file_number": "002",
                "study_uid": "1.2.3.4.6",
                "nodule_id": "N2",
                "radiologists": {
                    "1": {
                        "subtlety": 4,
                        "confidence": 3,
                        "obscuration": 3,
                        "reason": "another test",
                        "coordinates": "150, 250, 60"
                    }
                }
            }
        ]
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test outputs."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path)
    
    def test_export_basic(self, sample_records, temp_dir):
        """Test basic RA-D-PS export."""
        exporter = RADPSExcelFormatter()
        output_path = exporter.export(sample_records, temp_dir)
        
        assert output_path.exists()
        assert output_path.suffix == '.xlsx'
        assert 'RA-D-PS' in output_path.name
    
    def test_validate_data_valid(self, sample_records):
        """Test data validation with valid data."""
        exporter = RADPSExcelFormatter()
        assert exporter.validate_data(sample_records)
    
    def test_validate_data_invalid(self):
        """Test data validation with invalid data."""
        exporter = RADPSExcelFormatter()
        assert not exporter.validate_data("not a list")
        assert not exporter.validate_data([123, 456])
    
    def test_get_R_max(self, sample_records):
        """Test radiologist count detection."""
        exporter = RADPSExcelFormatter()
        R_max = exporter._get_R_max(sample_records)
        assert R_max == 2  # Max radiologists in sample data
    
    def test_get_R_max_forced(self, sample_records):
        """Test forced radiologist count."""
        exporter = RADPSExcelFormatter()
        R_max = exporter._get_R_max(sample_records, force_blocks=4)
        assert R_max == 4
    
    def test_build_columns(self):
        """Test column structure building."""
        exporter = RADPSExcelFormatter()
        cols = exporter._build_columns(2)
        
        # Should have: file #, Study UID, spacer, NoduleID, spacer,
        # then 2 radiologist blocks (5 cols + spacer each)
        assert len(cols) == 5 + (2 * 6)
        assert cols[0] == "file #"
        assert cols[2] is None  # First spacer
        assert "R1 Subtlety" in cols
        assert "R2 Confidence" in cols
    
    def test_export_empty_records(self, temp_dir):
        """Test export with empty records list."""
        exporter = RADPSExcelFormatter()
        with pytest.raises(ExportError, match="No records to export"):
            exporter.export([], temp_dir)
    
    def test_auto_versioning(self, sample_records, temp_dir):
        """Test auto-versioning when file exists."""
        exporter = RADPSExcelFormatter()
        
        # Create first file
        path1 = exporter.export(sample_records, temp_dir)
        
        # Create second file - should get versioned name
        path2 = exporter.export(sample_records, temp_dir)
        
        assert path1 != path2
        assert '_v2' in path2.name or path1.name != path2.name


class TestTemplateExcelFormatter:
    """Test template format Excel exporter."""
    
    @pytest.fixture
    def sample_template_data(self):
        """Sample template format data."""
        return [
            {
                'FileID': 'file1',
                'NoduleID': 'N1',
                'ParseCase': 'Complete_Attributes',
                'SessionType': 'Standard',
                'Radiologist 1': 'Conf:4 | Sub:3',
                'Radiologist 2': '',
                'Radiologist 3': '',
                'Radiologist 4': '',
                'SOP_UID': '1.2.3',
                'X_coord': '100',
                'Y_coord': '200',
                'Z_coord': '50',
            }
        ]
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test outputs."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path)
    
    def test_export_template(self, sample_template_data, temp_dir):
        """Test template format export."""
        exporter = TemplateExcelFormatter()
        output_path = temp_dir / "test_template.xlsx"
        result_path = exporter.export(sample_template_data, output_path)
        
        assert result_path.exists()
        assert result_path.suffix == '.xlsx'
    
    def test_validate_template_data(self, sample_template_data):
        """Test template data validation."""
        exporter = TemplateExcelFormatter()
        assert exporter.validate_data(sample_template_data)
        assert not exporter.validate_data("invalid")
        assert not exporter.validate_data([1, 2, 3])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
