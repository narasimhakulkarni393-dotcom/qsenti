"""
Q-Sentinel: Phishing URL Detection API
Serverless endpoint for Vercel deployment
"""

import os
import sys
import json
import joblib
from urllib.parse import urlparse

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.features import extract_features
from src.threat_intel import check_threat_intel

# Load model
MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models', 'phishing_model.pkl')
SCALER_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models', 'phishing_model_scaler.pkl')

try:
    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
except Exception as e:
    model = None
    scaler = None
    error_msg = f"Model loading error: {str(e)}"


def handler(request):
    """
    Handle prediction requests
    POST /api/predict
    Body: {"url": "https://example.com"}
    """
    
    if request.method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
            },
        }
    
    if request.method != 'POST':
        return {
            'statusCode': 405,
            'body': json.dumps({'error': 'Method not allowed. Use POST.'}),
        }
    
    # Check if model loaded
    if model is None:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': error_msg}),
        }
    
    try:
        body = json.loads(request.body or '{}')
        url = body.get('url', '').strip()
        
        if not url:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'URL is required'}),
                'headers': {'Content-Type': 'application/json'},
            }
        
        # Validate URL
        try:
            urlparse(url)
        except Exception:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Invalid URL format'}),
                'headers': {'Content-Type': 'application/json'},
            }
        
        # Extract features
        features = extract_features(url)
        features_scaled = scaler.transform([features])
        
        # Predict
        ml_prediction = model.predict(features_scaled)[0]
        ml_probability = model.predict_proba(features_scaled)[0]
        
        # Threat intelligence
        threat_intel = check_threat_intel(url)
        
        # Combine predictions
        if threat_intel['is_malicious']:
            final_prediction = 1  # Phishing
            confidence = max(ml_probability[1], 0.9)
        else:
            final_prediction = ml_prediction
            confidence = ml_probability[1] if ml_prediction == 1 else ml_probability[0]
        
        # Risk level
        if final_prediction == 1 and confidence > 0.7:
            risk_level = 'HIGH'
            risk_emoji = '🔴'
        elif final_prediction == 1:
            risk_level = 'MEDIUM'
            risk_emoji = '🟡'
        else:
            risk_level = 'LOW'
            risk_emoji = '🟢'
        
        response = {
            'url': url,
            'prediction': 'PHISHING' if final_prediction == 1 else 'LEGITIMATE',
            'confidence': float(confidence),
            'risk_level': risk_level,
            'risk_emoji': risk_emoji,
            'threat_intel': threat_intel,
            'ml_prediction': 'PHISHING' if ml_prediction == 1 else 'LEGITIMATE',
            'ml_probability': float(ml_probability[1]),
        }
        
        return {
            'statusCode': 200,
            'body': json.dumps(response),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
        }
    
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid JSON'}),
            'headers': {'Content-Type': 'application/json'},
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
            'headers': {'Content-Type': 'application/json'},
        }
