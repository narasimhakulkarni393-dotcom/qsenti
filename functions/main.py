"""
Q-Sentinel: Phishing URL Detection
Firebase Cloud Functions
"""

import os
import sys
import json
import joblib
import functions_framework
from urllib.parse import urlparse
from flask import jsonify

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
    MODEL_LOADED = True
except Exception as e:
    model = None
    scaler = None
    MODEL_LOADED = False
    ERROR_MSG = f"Model loading error: {str(e)}"


@functions_framework.http
def predict(request):
    """
    Firebase Cloud Function for URL phishing detection
    POST /api/predict
    """
    
    # Handle CORS
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
        }
        return ('', 204, headers)
    
    # Check method
    if request.method != 'POST':
        return jsonify({'error': 'Method not allowed. Use POST.'}), 405
    
    # Check if model loaded
    if not MODEL_LOADED:
        return jsonify({'error': ERROR_MSG}), 500
    
    try:
        # Parse request
        data = request.get_json() or {}
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Validate URL
        try:
            urlparse(url)
        except Exception:
            return jsonify({'error': 'Invalid URL format'}), 400
        
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
        
        headers = {
            'Access-Control-Allow-Origin': '*',
        }
        
        return jsonify(response), 200, headers
    
    except json.JSONDecodeError:
        return jsonify({'error': 'Invalid JSON'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@functions_framework.http
def index(request):
    """Landing page"""
    
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Q-Sentinel: Phishing URL Detection API</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }
            .container {
                background: white;
                border-radius: 12px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                max-width: 700px;
                padding: 40px;
            }
            h1 {
                color: #333;
                margin-bottom: 10px;
                font-size: 32px;
            }
            .subtitle {
                color: #666;
                margin-bottom: 30px;
                font-size: 16px;
            }
            .section {
                margin-bottom: 30px;
            }
            .section h2 {
                color: #667eea;
                font-size: 20px;
                margin-bottom: 15px;
            }
            .code-block {
                background: #f5f5f5;
                border-left: 4px solid #667eea;
                padding: 15px;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
                font-size: 14px;
                overflow-x: auto;
                margin-bottom: 15px;
            }
            .endpoint {
                color: #667eea;
                font-weight: bold;
            }
            .method {
                background: #667eea;
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
            ul {
                margin-left: 20px;
                line-height: 1.8;
                color: #555;
            }
            .example-request {
                background: #f0f4ff;
                padding: 15px;
                border-radius: 4px;
                margin-bottom: 15px;
            }
            .example-response {
                background: #f0fff4;
                padding: 15px;
                border-radius: 4px;
                margin-bottom: 15px;
            }
            .status {
                display: inline-block;
                padding: 8px 12px;
                border-radius: 4px;
                background: #d4edda;
                color: #155724;
                font-weight: bold;
                margin-bottom: 20px;
            }
            .footer {
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #eee;
                color: #999;
                font-size: 14px;
                text-align: center;
            }
            a {
                color: #667eea;
                text-decoration: none;
            }
            a:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Q-Sentinel</h1>
            <p class="subtitle">Phishing URL Detection API powered by ML + Threat Intelligence</p>
            
            <div class="status">✅ Firebase Cloud Function is Live</div>
            
            <div class="section">
                <h2>API Endpoint</h2>
                <div class="code-block">
                    <span class="method">POST</span> <span class="endpoint">/api/predict</span>
                </div>
            </div>
            
            <div class="section">
                <h2>Request Example</h2>
                <div class="example-request">
                    <code>{<br/>
                    &nbsp;&nbsp;"url": "https://example.com"<br/>
                    }</code>
                </div>
            </div>
            
            <div class="section">
                <h2>Response Example</h2>
                <div class="example-response">
                    <code>{<br/>
                    &nbsp;&nbsp;"url": "https://example.com",<br/>
                    &nbsp;&nbsp;"prediction": "LEGITIMATE",<br/>
                    &nbsp;&nbsp;"confidence": 0.95,<br/>
                    &nbsp;&nbsp;"risk_level": "LOW",<br/>
                    &nbsp;&nbsp;"risk_emoji": "🟢"<br/>
                    }</code>
                </div>
            </div>
            
            <div class="footer">
                <p>Q-Sentinel v0.2.0 | Firebase Cloud Functions | VTU-QFF Hackathon 2026</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html, 200, {'Content-Type': 'text/html; charset=utf-8'}
