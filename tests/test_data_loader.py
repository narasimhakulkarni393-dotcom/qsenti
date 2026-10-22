"""
Tests for data loading and validation module.

Covers:
- CSV loading with various column names
- Label mapping and validation
- Error handling for malformed datasets
"""

import pytest
import sys
import os
import pandas as pd
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.data_loader import DataLoader, load_dataset


class TestDataLoaderCSVLoading:
    """Tests for CSV loading functionality."""
    
    def test_load_valid_csv(self):
        """Load a valid CSV with standard columns."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('url,label\n')
            f.write('https://google.com,0\n')
            f.write('https://phishing.com,1\n')
            f.flush()
            temp_file = f.name
        
        try:
            loader = DataLoader()
            df = loader.load_csv(temp_file)
            assert len(df) == 2
            assert list(df.columns) == ['url', 'label']
        finally:
            os.unlink(temp_file)
    
    def test_load_csv_with_custom_column_names(self):
        """Load CSV with non-standard column names."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('website_url,classification\n')
            f.write('https://google.com,legitimate\n')
            f.write('https://phishing.com,phishing\n')
            f.flush()
            temp_file = f.name
        
        try:
            loader = DataLoader()
            df = loader.load_csv(temp_file, url_column='website_url',
                                label_column='classification')
            assert len(df) == 2
            assert 'url' in df.columns
            assert 'label' in df.columns
        finally:
            os.unlink(temp_file)
    
    def test_csv_not_found(self):
        """Should raise FileNotFoundError for non-existent file."""
        loader = DataLoader()
        with pytest.raises(FileNotFoundError):
            loader.load_csv('/nonexistent/path/file.csv')
    
    def test_missing_url_column(self):
        """Should raise ValueError if URL column is missing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('label\n')
            f.write('0\n')
            f.flush()
            temp_file = f.name
        
        try:
            loader = DataLoader()
            with pytest.raises(ValueError, match="Column 'url' not found"):
                loader.load_csv(temp_file)
        finally:
            os.unlink(temp_file)
    
    def test_missing_label_column(self):
        """Should raise ValueError if label column is missing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('url\n')
            f.write('https://google.com\n')
            f.flush()
            temp_file = f.name
        
        try:
            loader = DataLoader()
            with pytest.raises(ValueError, match="Column 'label' not found"):
                loader.load_csv(temp_file)
        finally:
            os.unlink(temp_file)
    
    def test_missing_values_in_url_column(self):
        """Should raise ValueError if URL column has NaN."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('url,label\n')
            f.write('https://google.com,0\n')
            f.write(',1\n')  # Missing URL
            f.flush()
            temp_file = f.name
        
        try:
            loader = DataLoader()
            with pytest.raises(ValueError, match="missing"):
                loader.load_csv(temp_file)
        finally:
            os.unlink(temp_file)


class TestLabelMapping:
    """Tests for label mapping functionality."""
    
    def test_map_phishing_legitimate_labels(self):
        """Map string labels to canonical 0/1."""
        df = pd.DataFrame({
            'url': ['http://a.com', 'http://b.com'],
            'label': ['legitimate', 'phishing']
        })
        
        loader = DataLoader(phishing_label=1, legitimate_label=0)
        mapping = {'legitimate': 0, 'phishing': 1}
        df_mapped = loader.map_labels(df, mapping)
        
        assert df_mapped.loc[0, 'label'] == 0
        assert df_mapped.loc[1, 'label'] == 1
    
    def test_invalid_label_mapping(self):
        """Should raise ValueError for invalid mapping."""
        df = pd.DataFrame({
            'url': ['http://a.com'],
            'label': ['legitimate']
        })
        
        loader = DataLoader()
        
        # Empty mapping
        with pytest.raises(ValueError):
            loader.map_labels(df, {})
        
        # Only one label
        with pytest.raises(ValueError):
            loader.map_labels(df, {'legitimate': 0})
    
    def test_unmapped_labels_in_data(self):
        """Should raise ValueError if dataset contains unmapped labels."""
        df = pd.DataFrame({
            'url': ['http://a.com', 'http://b.com'],
            'label': ['legitimate', 'unknown']
        })
        
        loader = DataLoader()
        mapping = {'legitimate': 0, 'phishing': 1}
        
        with pytest.raises(ValueError, match="Unmapped"):
            loader.map_labels(df, mapping)


class TestValidationAndPreparation:
    """Tests for data validation and preparation."""
    
    def test_validate_valid_dataset(self):
        """Valid dataset should pass validation."""
        df = pd.DataFrame({
            'url': ['http://a.com', 'http://b.com'],
            'label': [0, 1]
        })
        
        loader = DataLoader(phishing_label=1, legitimate_label=0)
        df_clean, counts = loader.validate_and_prepare(df)
        
        assert len(df_clean) == 2
        assert counts[0] == 1  # legitimate
        assert counts[1] == 1  # phishing
    
    def test_validate_empty_dataframe(self):
        """Empty dataframe should raise ValueError."""
        loader = DataLoader()
        with pytest.raises(ValueError, match="empty"):
            loader.validate_and_prepare(pd.DataFrame())
    
    def test_validate_missing_columns(self):
        """Missing columns should raise ValueError."""
        df = pd.DataFrame({'other': [1, 2]})
        loader = DataLoader()
        
        with pytest.raises(ValueError, match="must have"):
            loader.validate_and_prepare(df)
    
    def test_validate_missing_class(self):
        """Dataset with only one class should raise ValueError."""
        df = pd.DataFrame({
            'url': ['http://a.com', 'http://b.com'],
            'label': [0, 0]  # Only legitimate
        })
        
        loader = DataLoader(phishing_label=1, legitimate_label=0)
        with pytest.raises(ValueError, match="both"):
            loader.validate_and_prepare(df)
    
    def test_removes_empty_urls(self):
        """Empty URLs should be removed."""
        df = pd.DataFrame({
            'url': ['http://a.com', '  ', 'http://b.com'],
            'label': [0, 1, 1]
        })
        
        loader = DataLoader(phishing_label=1, legitimate_label=0)
        df_clean, counts = loader.validate_and_prepare(df)
        
        assert len(df_clean) == 2  # Empty URL removed


class TestConvenienceFunction:
    """Tests for the load_dataset convenience function."""
    
    def test_load_dataset_full_pipeline(self):
        """Full pipeline should work end-to-end."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('url,label\n')
            f.write('https://google.com,0\n')
            f.write('https://phishing.com,1\n')
            f.flush()
            temp_file = f.name
        
        try:
            df, counts = load_dataset(temp_file)
            assert len(df) == 2
            assert 0 in counts
            assert 1 in counts
        finally:
            os.unlink(temp_file)
    
    def test_load_dataset_with_custom_mapping(self):
        """Should work with custom label mapping."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('site,classification\n')
            f.write('https://google.com,safe\n')
            f.write('https://phishing.com,dangerous\n')
            f.flush()
            temp_file = f.name
        
        try:
            df, counts = load_dataset(
                temp_file,
                url_column='site',
                label_column='classification',
                label_mapping={'safe': 0, 'dangerous': 1}
            )
            assert len(df) == 2
            assert 0 in counts and 1 in counts
        finally:
            os.unlink(temp_file)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
