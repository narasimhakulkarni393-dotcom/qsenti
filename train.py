"""
Training Script for Q-Sentinel

Loads a labelled URL dataset, trains a RandomForest model, and saves results.
Usage: python train.py --data <path_to_csv> --url-column <col> --label-column <col> [--label-mapping <json>]
"""

import sys
import os
import argparse
import json
import pandas as pd
import numpy as np
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from src.data_loader import load_dataset
from src.features import extract_features, get_feature_names
from src.model import train_model_from_dataframe, URLPhishingModel


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Train a phishing URL detection model'
    )
    
    parser.add_argument(
        '--data', '-d',
        required=True,
        help='Path to CSV file with labelled URLs'
    )
    
    parser.add_argument(
        '--url-column', '-u',
        default='url',
        help='Name of URL column (default: url)'
    )
    
    parser.add_argument(
        '--label-column', '-l',
        default='label',
        help='Name of label column (default: label)'
    )
    
    parser.add_argument(
        '--label-mapping', '-m',
        default=None,
        help='JSON string mapping original labels to canonical (1=phishing, 0=legitimate). '
             'Example: \'{"phishing":1,"legitimate":0}\''
    )
    
    parser.add_argument(
        '--test-size', '-t',
        type=float,
        default=0.2,
        help='Test set fraction (default: 0.2)'
    )
    
    parser.add_argument(
        '--random-state', '-r',
        type=int,
        default=42,
        help='Random seed for reproducibility (default: 42)'
    )
    
    parser.add_argument(
        '--model-dir',
        default='models',
        help='Directory to save trained model (default: models)'
    )
    
    parser.add_argument(
        '--results-dir',
        default='results',
        help='Directory to save evaluation results (default: results)'
    )
    
    return parser.parse_args()


def save_evaluation_results(metrics, results_dir, feature_names):
    """Save evaluation metrics to JSON and CSV."""
    os.makedirs(results_dir, exist_ok=True)
    
    # Save metrics as JSON
    metrics_file = os.path.join(results_dir, 'evaluation_metrics.json')
    with open(metrics_file, 'w') as f:
        # Convert confusion matrix to list if needed
        metrics_copy = metrics.copy()
        json.dump(metrics_copy, f, indent=2)
    
    print(f"✓ Metrics saved to {metrics_file}")
    
    return metrics_file


def print_metrics(metrics):
    """Pretty-print evaluation metrics."""
    print("\n" + "="*60)
    print("MODEL EVALUATION METRICS")
    print("="*60)
    
    print(f"Accuracy:              {metrics['accuracy']:.4f}")
    print(f"Precision:             {metrics['precision']:.4f}")
    print(f"Recall (TPR):          {metrics['recall']:.4f}")
    print(f"F1-Score:              {metrics['f1_score']:.4f}")
    print(f"ROC-AUC:               {metrics['roc_auc']:.4f}")
    print(f"False Positive Rate:   {metrics['false_positive_rate']:.4f}")
    
    cm = metrics['confusion_matrix']
    print("\nConfusion Matrix:")
    print(f"  True Negatives:   {cm[0][0]}  | False Positives: {cm[0][1]}")
    print(f"  False Negatives:  {cm[1][0]}  | True Positives:  {cm[1][1]}")
    print("="*60 + "\n")


def main():
    """Main training function."""
    args = parse_arguments()
    
    print("\n" + "="*60)
    print("Q-SENTINEL: PHISHING URL DETECTION MODEL TRAINING")
    print("="*60 + "\n")
    
    # Validate data file exists
    if not os.path.exists(args.data):
        print(f"ERROR: Data file not found: {args.data}")
        sys.exit(1)
    
    print(f"Loading dataset from: {args.data}")
    
    # Parse label mapping if provided
    label_mapping = None
    if args.label_mapping:
        try:
            label_mapping = json.loads(args.label_mapping)
            print(f"Label mapping: {label_mapping}")
        except json.JSONDecodeError:
            print(f"ERROR: Invalid JSON for label mapping: {args.label_mapping}")
            sys.exit(1)
    
    # Load and validate dataset
    try:
        df, class_counts = load_dataset(
            args.data,
            url_column=args.url_column,
            label_column=args.label_column,
            label_mapping=label_mapping,
            phishing_label=1,
            legitimate_label=0
        )
        
        print(f"✓ Dataset loaded: {len(df)} URLs")
        print(f"  Phishing:      {class_counts.get(1, 0)}")
        print(f"  Legitimate:    {class_counts.get(0, 0)}")
    
    except Exception as e:
        print(f"ERROR: Failed to load dataset: {e}")
        sys.exit(1)
    
    # Train model
    print("\nTraining model...")
    try:
        model, metrics, feature_names = train_model_from_dataframe(
            df,
            extract_features,
            test_size=args.test_size,
            random_state=args.random_state
        )
        print("✓ Model trained successfully")
    
    except Exception as e:
        print(f"ERROR: Model training failed: {e}")
        sys.exit(1)
    
    # Display metrics
    print_metrics(metrics)
    
    # Save model
    os.makedirs(args.model_dir, exist_ok=True)
    model_path = os.path.join(args.model_dir, 'phishing_model.pkl')
    
    try:
        model.save(model_path)
        print(f"✓ Model saved to {model_path}")
    except Exception as e:
        print(f"ERROR: Failed to save model: {e}")
        sys.exit(1)
    
    # Save evaluation results
    try:
        metrics_file = save_evaluation_results(metrics, args.results_dir, feature_names)
    except Exception as e:
        print(f"ERROR: Failed to save results: {e}")
        sys.exit(1)
    
    # Save test predictions
    try:
        predictions_file = os.path.join(args.results_dir, 'test_predictions.json')
        with open(predictions_file, 'w') as f:
            json.dump(model.test_predictions, f, indent=2)
        print(f"✓ Test predictions saved to {predictions_file}")
    except Exception as e:
        print(f"WARNING: Failed to save predictions: {e}")
    
    print("\n" + "="*60)
    print("TRAINING COMPLETE")
    print("="*60)
    print(f"\nNext steps:")
    print(f"  1. Review metrics: {metrics_file}")
    print(f"  2. Start the Streamlit app: streamlit run app.py")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
