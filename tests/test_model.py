"""
Tests for model training and prediction module.

Covers:
- Model training with test data
- Prediction on single and batch URLs
- Model serialization (save/load)
- Metric calculation
"""

import pytest
import sys
import os
import tempfile
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.model import URLPhishingModel, train_model_from_dataframe
from src.features import extract_features, get_feature_names


class TestURLPhishingModel:
    """Tests for the URLPhishingModel class."""
    
    @pytest.fixture
    def sample_data(self):
        """Create small sample training data."""
        np.random.seed(42)
        
        # Create features for 30 URLs
        X = np.random.randn(30, 12)
        y = np.array([0]*15 + [1]*15)  # 15 legitimate, 15 phishing
        
        return X, y
    
    def test_model_initialization(self):
        """Model should initialize properly."""
        model = URLPhishingModel(n_estimators=10, random_state=42)
        assert model.is_trained == False
        assert model.model is not None
    
    def test_model_training(self, sample_data):
        """Model should train without errors."""
        X, y = sample_data
        X_train, X_test = X[:20], X[20:]
        y_train, y_test = y[:20], y[20:]
        
        model = URLPhishingModel(random_state=42)
        model.feature_names = get_feature_names()
        
        metrics = model.train(X_train, y_train, X_test, y_test)
        
        assert model.is_trained == True
        assert 'accuracy' in metrics
        assert 'precision' in metrics
        assert 'recall' in metrics
        assert 'f1_score' in metrics
        assert 'roc_auc' in metrics
        assert 'false_positive_rate' in metrics
        assert 'confusion_matrix' in metrics
    
    def test_model_metrics_range(self, sample_data):
        """All metrics should be in valid ranges."""
        X, y = sample_data
        X_train, X_test = X[:20], X[20:]
        y_train, y_test = y[:20], y[20:]
        
        model = URLPhishingModel(random_state=42)
        model.feature_names = get_feature_names()
        metrics = model.train(X_train, y_train, X_test, y_test)
        
        assert 0 <= metrics['accuracy'] <= 1
        assert 0 <= metrics['precision'] <= 1
        assert 0 <= metrics['recall'] <= 1
        assert 0 <= metrics['f1_score'] <= 1
        # ROC-AUC can be NaN on tiny random test sets with only one class
        assert metrics['roc_auc'] >= 0 or np.isnan(metrics['roc_auc'])
        assert 0 <= metrics['false_positive_rate'] <= 1
    
    def test_confusion_matrix_shape(self, sample_data):
        """Confusion matrix should be 2x2."""
        X, y = sample_data
        X_train, X_test = X[:20], X[20:]
        y_train, y_test = y[:20], y[20:]
        
        model = URLPhishingModel(random_state=42)
        model.feature_names = get_feature_names()
        metrics = model.train(X_train, y_train, X_test, y_test)
        
        cm = metrics['confusion_matrix']
        assert len(cm) == 2
        assert len(cm[0]) == 2


class TestModelPrediction:
    """Tests for model prediction functionality."""
    
    @pytest.fixture
    def trained_model(self):
        """Create and train a model for testing."""
        np.random.seed(42)
        X = np.random.randn(30, 12)
        y = np.array([0]*15 + [1]*15)
        
        X_train, X_test = X[:20], X[20:]
        y_train, y_test = y[:20], y[20:]
        
        model = URLPhishingModel(random_state=42)
        model.feature_names = get_feature_names()
        model.train(X_train, y_train, X_test, y_test)
        
        return model, X_test
    
    def test_predict_batch(self, trained_model):
        """Model should predict on batch data."""
        model, X_test = trained_model
        
        y_pred, y_proba = model.predict(X_test)
        
        assert len(y_pred) == len(X_test)
        assert len(y_proba) == len(X_test)
        assert all(p in [0, 1] for p in y_pred)
        assert all(0 <= p <= 1 for p in y_proba)
    
    def test_predict_single(self, trained_model):
        """Model should predict on single feature vector."""
        model, X_test = trained_model
        
        single_features = X_test[0]
        pred, proba = model.predict_single(single_features)
        
        assert pred in [0, 1]
        assert 0 <= proba <= 1
    
    def test_predict_before_training_raises_error(self):
        """Predicting before training should raise error."""
        model = URLPhishingModel()
        X = np.random.randn(5, 12)
        
        with pytest.raises(ValueError, match="trained"):
            model.predict(X)
    
    def test_predict_single_before_training_raises_error(self):
        """Predicting single before training should raise error."""
        model = URLPhishingModel()
        features = np.random.randn(12)
        
        with pytest.raises(ValueError, match="trained"):
            model.predict_single(features)


class TestModelSerialization:
    """Tests for model save/load functionality."""
    
    @pytest.fixture
    def trained_model(self):
        """Create and train a model for testing."""
        np.random.seed(42)
        X = np.random.randn(30, 12)
        y = np.array([0]*15 + [1]*15)
        
        X_train, X_test = X[:20], X[20:]
        y_train, y_test = y[:20], y[20:]
        
        model = URLPhishingModel(random_state=42)
        model.feature_names = get_feature_names()
        model.train(X_train, y_train, X_test, y_test)
        
        return model, X_test
    
    def test_save_model(self, trained_model):
        """Model should save to disk."""
        model, X_test = trained_model
        
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = os.path.join(tmpdir, 'test_model.pkl')
            model.save(model_path)
            
            assert os.path.exists(model_path)
            assert os.path.exists(model_path.replace('.pkl', '_scaler.pkl'))
            assert os.path.exists(model_path.replace('.pkl', '_metadata.json'))
    
    def test_load_model(self, trained_model):
        """Model should load from disk and work."""
        model_orig, X_test = trained_model
        
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = os.path.join(tmpdir, 'test_model.pkl')
            model_orig.save(model_path)
            
            # Load into new model
            model_new = URLPhishingModel()
            model_new.load(model_path)
            
            assert model_new.is_trained == True
            assert model_new.feature_names == model_orig.feature_names
            
            # Predictions should match
            y_pred_orig, y_proba_orig = model_orig.predict(X_test)
            y_pred_new, y_proba_new = model_new.predict(X_test)
            
            assert np.array_equal(y_pred_orig, y_pred_new)
            np.testing.assert_array_almost_equal(y_proba_orig, y_proba_new)
    
    def test_save_before_training_raises_error(self):
        """Saving untrained model should raise error."""
        model = URLPhishingModel()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = os.path.join(tmpdir, 'model.pkl')
            with pytest.raises(ValueError, match="trained"):
                model.save(model_path)


class TestFeatureImportance:
    """Tests for feature importance extraction."""
    
    @pytest.fixture
    def trained_model(self):
        """Create and train a model."""
        np.random.seed(42)
        X = np.random.randn(30, 12)
        y = np.array([0]*15 + [1]*15)
        
        X_train, X_test = X[:20], X[20:]
        y_train, y_test = y[:20], y[20:]
        
        model = URLPhishingModel(random_state=42)
        model.feature_names = get_feature_names()
        model.train(X_train, y_train, X_test, y_test)
        
        return model
    
    def test_get_feature_importance(self, trained_model):
        """Should return feature importances."""
        importances = trained_model.get_feature_importance()
        
        assert isinstance(importances, list)
        assert len(importances) <= 12
        
        # Each item should be (name, importance)
        for name, importance in importances:
            assert isinstance(name, str)
            assert isinstance(importance, (int, float))
            assert importance >= 0


class TestTrainingPipeline:
    """Tests for the end-to-end training pipeline."""
    
    def test_train_from_dataframe(self):
        """Should train model from DataFrame."""
        # Create sample data
        df = pd.DataFrame({
            'url': [
                'https://google.com',
                'https://github.com',
                'https://python.org',
                'https://wikipedia.org',
                'https://stackoverflow.com',
                'http://suspicious-long-phishing-url.com/verify/login',
                'http://193.168.1.1/admin',
                'http://paypal-confirm.ru',
                'http://fake-amazon.tk',
                'http://free-gift-click-here.net'
            ],
            'label': [0, 0, 0, 0, 0, 1, 1, 1, 1, 1]
        })
        
        model, metrics, feature_names = train_model_from_dataframe(
            df, extract_features, test_size=0.3, random_state=42
        )
        
        assert model.is_trained == True
        assert len(feature_names) == 12
        assert 'accuracy' in metrics
        assert 'precision' in metrics
        assert 'recall' in metrics
    
    def test_train_with_duplicates(self):
        """Should handle duplicate URLs (removed during dedup, still trains)."""
        df = pd.DataFrame({
            'url': [
                'https://www.google.com',
                'https://www.google.com',  # Duplicate - will be removed
                'https://www.github.com',
                'https://www.python.org',
                'https://stackoverflow.com',
                'https://www.wikipedia.org',
                'https://www.wikipedia.org',  # Another duplicate
                'https://docs.python.org',  # New URL
                'http://phishing-detector.tk/verify',
                'http://phishing-detector.tk/verify',  # Duplicate - will be removed
                'http://evil-attack.com/login',
                'http://fake-bank.ru/signin',
                'http://malware-download.net/click'
            ],
            'label': [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1]
        })
        
        # Should not raise error, duplicates removed during preprocessing
        model, metrics, feature_names = train_model_from_dataframe(
            df, extract_features, test_size=0.2, random_state=42
        )
        
        assert model.is_trained == True
    
    def test_train_insufficient_data(self):
        """Should raise error with too little data."""
        df = pd.DataFrame({
            'url': ['https://google.com', 'http://phishing.com'],
            'label': [0, 1]
        })
        
        with pytest.raises(ValueError, match="Not enough"):
            train_model_from_dataframe(df, extract_features)
    
    def test_train_empty_dataframe(self):
        """Should raise error with empty DataFrame."""
        df = pd.DataFrame({'url': [], 'label': []})
        
        with pytest.raises(ValueError):
            train_model_from_dataframe(df, extract_features)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
