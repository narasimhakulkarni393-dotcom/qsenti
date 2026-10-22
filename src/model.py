"""
Model Training and Prediction Module

Trains a RandomForest classifier, evaluates it, and provides predictions.
Handles preprocessing, stratified splits, and metric calculation.
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    precision_score, recall_score, f1_score, confusion_matrix,
    roc_auc_score, accuracy_score
)
import joblib
import json
from datetime import datetime


class URLPhishingModel:
    """
    A RandomForest-based classifier for URL phishing detection.
    
    Attributes:
        model: The trained RandomForestClassifier.
        scaler: The fitted StandardScaler for feature normalization.
        feature_names: List of feature names.
        is_trained: Boolean indicating if model has been trained.
        training_timestamp: Timestamp of when model was trained.
    """
    
    def __init__(self, n_estimators=100, random_state=42):
        """
        Initialize the model.
        
        Args:
            n_estimators (int): Number of trees in the forest.
            random_state (int): Random seed for reproducibility.
        """
        self.model = RandomForestClassifier(
            n_estimators=n_estimators,
            random_state=random_state,
            n_jobs=-1,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2
        )
        self.scaler = StandardScaler()
        self.feature_names = None
        self.is_trained = False
        self.training_timestamp = None
    
    def train(self, X_train, y_train, X_test, y_test):
        """
        Train the model on training data and evaluate on test data.
        
        Args:
            X_train (np.ndarray): Training feature vectors.
            y_train (np.ndarray): Training labels.
            X_test (np.ndarray): Test feature vectors.
            y_test (np.ndarray): Test labels.
            
        Returns:
            dict: Training and evaluation metrics.
            
        Raises:
            ValueError: If data shapes are invalid or training fails.
        """
        if X_train.shape[0] != y_train.shape[0]:
            raise ValueError("X_train and y_train must have same number of samples")
        
        if X_train.shape[1] != X_test.shape[1]:
            raise ValueError("X_train and X_test must have same number of features")
        
        # Fit scaler on training data only
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train the model
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate on test set
        y_pred = self.model.predict(X_test_scaled)
        y_pred_proba = self.model.predict_proba(X_test_scaled)[:, 1]
        
        # Calculate metrics
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred),
            'recall': recall_score(y_test, y_pred),
            'f1_score': f1_score(y_test, y_pred),
            'roc_auc': roc_auc_score(y_test, y_pred_proba),
            'confusion_matrix': confusion_matrix(y_test, y_pred).tolist(),
        }
        
        # Calculate false positive rate: FP / (FP + TN)
        tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        metrics['false_positive_rate'] = fpr
        
        self.is_trained = True
        self.training_timestamp = datetime.now().isoformat()
        
        # Store test predictions for later analysis
        self.test_predictions = {
            'y_true': y_test.tolist(),
            'y_pred': y_pred.tolist(),
            'y_pred_proba': y_pred_proba.tolist()
        }
        
        return metrics
    
    def predict(self, X):
        """
        Predict on new data.
        
        Args:
            X (np.ndarray): Feature vectors.
            
        Returns:
            tuple: (y_pred, y_pred_proba) where y_pred is class labels
                   and y_pred_proba is probability for class 1 (phishing).
                   
        Raises:
            ValueError: If model is not trained.
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        
        X_scaled = self.scaler.transform(X)
        y_pred = self.model.predict(X_scaled)
        y_pred_proba = self.model.predict_proba(X_scaled)[:, 1]
        
        return y_pred, y_pred_proba
    
    def predict_single(self, features):
        """
        Predict on a single feature vector.
        
        Args:
            features (list or np.ndarray): A single 12-element feature vector.
            
        Returns:
            tuple: (prediction, probability) where prediction is 0 or 1
                   and probability is the confidence for phishing (class 1).
                   
        Raises:
            ValueError: If model is not trained or input is invalid.
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        
        X = np.array(features).reshape(1, -1)
        prediction, proba = self.predict(X)
        
        return prediction[0], proba[0]
    
    def save(self, model_path, scaler_path=None, metadata_path=None):
        """
        Save the trained model and scaler to disk.
        
        Args:
            model_path (str): Path to save the model.
            scaler_path (str): Path to save the scaler. If None, uses model_path + '_scaler'.
            metadata_path (str): Path to save metadata. If None, uses model_path + '_metadata'.
            
        Raises:
            ValueError: If model is not trained.
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before saving")
        
        if scaler_path is None:
            scaler_path = model_path.replace('.pkl', '_scaler.pkl')
        if metadata_path is None:
            metadata_path = model_path.replace('.pkl', '_metadata.json')
        
        joblib.dump(self.model, model_path)
        joblib.dump(self.scaler, scaler_path)
        
        metadata = {
            'feature_names': self.feature_names,
            'training_timestamp': self.training_timestamp,
            'n_estimators': self.model.n_estimators,
            'random_state': self.model.random_state
        }
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def load(self, model_path, scaler_path=None, metadata_path=None):
        """
        Load a trained model and scaler from disk.
        
        Args:
            model_path (str): Path to the saved model.
            scaler_path (str): Path to the saved scaler. If None, uses model_path + '_scaler'.
            metadata_path (str): Path to the saved metadata. If None, uses model_path + '_metadata'.
            
        Raises:
            FileNotFoundError: If files do not exist.
        """
        if scaler_path is None:
            scaler_path = model_path.replace('.pkl', '_scaler.pkl')
        if metadata_path is None:
            metadata_path = model_path.replace('.pkl', '_metadata.json')
        
        try:
            self.model = joblib.load(model_path)
            self.scaler = joblib.load(scaler_path)
            
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            self.feature_names = metadata.get('feature_names')
            self.training_timestamp = metadata.get('training_timestamp')
            self.is_trained = True
        
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Failed to load model: {e}")
    
    def get_feature_importance(self, top_n=12):
        """
        Get feature importances from the trained model.
        
        Args:
            top_n (int): Number of top features to return.
            
        Returns:
            list: List of (feature_name, importance) tuples, sorted by importance.
            
        Raises:
            ValueError: If model is not trained.
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before getting importance")
        
        importances = self.model.feature_importances_
        
        feature_importance_list = list(zip(self.feature_names, importances))
        feature_importance_list.sort(key=lambda x: x[1], reverse=True)
        
        return feature_importance_list[:top_n]


def train_model_from_dataframe(df, feature_extractor, test_size=0.2, 
                               random_state=42):
    """
    Convenience function to train a model from a DataFrame of URLs and labels.
    
    Args:
        df (pd.DataFrame): DataFrame with 'url' and 'label' columns.
        feature_extractor: Function that extracts features from a URL string.
        test_size (float): Fraction of data to use for testing.
        random_state (int): Random seed.
        
    Returns:
        tuple: (model, metrics, feature_names) where model is trained URLPhishingModel,
               metrics is dict of evaluation metrics, and feature_names is list of names.
               
    Raises:
        ValueError: If data is invalid or training fails.
    """
    if df.empty:
        raise ValueError("DataFrame is empty")
    
    # Remove duplicates
    df_dedup = df.drop_duplicates(subset=['url']).copy()
    
    # Extract features
    features_list = []
    valid_indices = []
    
    for idx, url in enumerate(df_dedup['url']):
        try:
            features = feature_extractor(url)
            features_list.append(features)
            valid_indices.append(idx)
        except Exception as e:
            print(f"Warning: Skipping URL '{url}': {e}")
            continue
    
    if len(features_list) < 10:
        raise ValueError(f"Not enough valid URLs to train a model (need at least 10, got {len(features_list)})")
    
    # Keep only rows with valid extracted features
    df_valid = df_dedup.iloc[valid_indices].copy()
    
    X = np.array(features_list)
    y = df_valid['label'].values
    
    # Stratified train-test split
    try:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )
    except ValueError as e:
        raise ValueError(f"Cannot create stratified split: {e}")
    
    # Train model
    model = URLPhishingModel(random_state=random_state)
    
    # Get feature names
    from .features import get_feature_names
    model.feature_names = get_feature_names()
    
    metrics = model.train(X_train, y_train, X_test, y_test)
    
    return model, metrics, model.feature_names
