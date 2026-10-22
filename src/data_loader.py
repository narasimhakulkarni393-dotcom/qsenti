"""
Data Loader Module

Loads labelled URLs from CSV files, validates datasets, and maps labels.
Supports various label formats (phishing/legitimate, 1/0, etc.).
"""

import pandas as pd
import numpy as np


class DataLoader:
    """
    Handles CSV loading, validation, and label mapping for URL datasets.
    
    Attributes:
        phishing_label: The canonical value representing a phishing URL.
        legitimate_label: The canonical value representing a legitimate URL.
    """
    
    def __init__(self, phishing_label=1, legitimate_label=0):
        """
        Initialize the DataLoader.
        
        Args:
            phishing_label: The value used in the canonical label column for phishing.
            legitimate_label: The value used in the canonical label column for legitimate.
        """
        self.phishing_label = phishing_label
        self.legitimate_label = legitimate_label
    
    def load_csv(self, filepath, url_column='url', label_column='label'):
        """
        Load and validate a labelled URL dataset from CSV.
        
        Args:
            filepath (str): Path to the CSV file.
            url_column (str): Name of the column containing URLs.
            label_column (str): Name of the column containing labels.
            
        Returns:
            pd.DataFrame: DataFrame with 'url' and 'label' columns.
            
        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If columns are missing, data is malformed, or contains NaN values.
        """
        try:
            df = pd.read_csv(filepath)
        except FileNotFoundError:
            raise FileNotFoundError(f"CSV file not found: {filepath}")
        except Exception as e:
            raise ValueError(f"Failed to read CSV file: {e}")
        
        # Check for required columns
        if url_column not in df.columns:
            raise ValueError(f"Column '{url_column}' not found in CSV. Available: {list(df.columns)}")
        if label_column not in df.columns:
            raise ValueError(f"Column '{label_column}' not found in CSV. Available: {list(df.columns)}")
        
        # Check for missing values
        if df[url_column].isna().any():
            raise ValueError(f"Column '{url_column}' contains missing (NaN) values")
        if df[label_column].isna().any():
            raise ValueError(f"Column '{label_column}' contains missing (NaN) values")
        
        # Create output dataframe with standardized column names
        result = pd.DataFrame({
            'url': df[url_column].astype(str).str.strip(),
            'label': df[label_column]
        })
        
        return result
    
    def map_labels(self, df, label_mapping):
        """
        Map arbitrary label values to canonical phishing/legitimate labels.
        
        Args:
            df (pd.DataFrame): DataFrame with 'url' and 'label' columns.
            label_mapping (dict): Mapping from original labels to canonical values.
                                  E.g., {'phishing': 1, 'legitimate': 0}
            
        Returns:
            pd.DataFrame: DataFrame with mapped labels.
            
        Raises:
            ValueError: If label_mapping is invalid or contains unmapped labels.
        """
        if not isinstance(label_mapping, dict) or len(label_mapping) < 2:
            raise ValueError("label_mapping must be a dict with at least 2 entries")
        
        # Check for unmapped labels
        unique_labels = df['label'].unique()
        unmapped = set(unique_labels) - set(label_mapping.keys())
        if unmapped:
            raise ValueError(f"Unmapped labels in dataset: {unmapped}")
        
        df_copy = df.copy()
        df_copy['label'] = df_copy['label'].map(label_mapping)
        
        return df_copy
    
    def validate_and_prepare(self, df):
        """
        Validate and prepare a dataset for training.
        
        Args:
            df (pd.DataFrame): DataFrame with 'url' and 'label' columns.
            
        Returns:
            tuple: (df_clean, class_counts) where df_clean is the validated DataFrame
                   and class_counts is a dict of {label: count}.
            
        Raises:
            ValueError: If dataset is invalid or lacks both classes.
        """
        if df is None or df.empty:
            raise ValueError("DataFrame is empty")
        
        if 'url' not in df.columns or 'label' not in df.columns:
            raise ValueError("DataFrame must have 'url' and 'label' columns")
        
        # Remove rows with empty URLs
        df_clean = df[df['url'].str.strip().astype(bool)].copy()
        
        if df_clean.empty:
            raise ValueError("No valid URLs found in dataset after cleaning")
        
        # Check class balance
        class_counts = df_clean['label'].value_counts().to_dict()
        
        # Ensure both classes are present
        unique_labels = set(class_counts.keys())
        expected_labels = {self.phishing_label, self.legitimate_label}
        
        if not unique_labels.issubset(expected_labels) or len(unique_labels) < 2:
            raise ValueError(
                f"Dataset must contain both phishing (label={self.phishing_label}) "
                f"and legitimate (label={self.legitimate_label}) URLs. "
                f"Found labels: {unique_labels}"
            )
        
        return df_clean, class_counts


def load_dataset(filepath, url_column='url', label_column='label', 
                 label_mapping=None, phishing_label=1, legitimate_label=0):
    """
    Convenience function to load a dataset in one call.
    
    Args:
        filepath (str): Path to CSV file.
        url_column (str): Name of URL column.
        label_column (str): Name of label column.
        label_mapping (dict): Optional mapping from original to canonical labels.
        phishing_label: Canonical phishing label value.
        legitimate_label: Canonical legitimate label value.
        
    Returns:
        tuple: (df_clean, class_counts) ready for training.
        
    Raises:
        ValueError or FileNotFoundError: If dataset cannot be loaded or is invalid.
    """
    loader = DataLoader(phishing_label=phishing_label, 
                       legitimate_label=legitimate_label)
    
    df = loader.load_csv(filepath, url_column=url_column, label_column=label_column)
    
    if label_mapping:
        df = loader.map_labels(df, label_mapping)
    
    df_clean, class_counts = loader.validate_and_prepare(df)
    
    return df_clean, class_counts
