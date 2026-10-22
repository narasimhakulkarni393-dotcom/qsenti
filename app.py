"""
Q-Sentinel Streamlit Dashboard with AlienVault OTX Integration

A cybersecurity-themed interface for phishing URL detection.
Combines RandomForest ML with real-time threat intelligence.
"""

import streamlit as st
import os
import sys
import pandas as pd
import numpy as np
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from src.features import extract_features, get_feature_names
from src.model import URLPhishingModel

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Threat intel (optional)
threat_intel_available = False
try:
    from src.threat_intel import OTXThreatIntel
    threat_intel_available = True
except (ImportError, Exception):
    threat_intel_available = False

# ============================================================================
# PAGE CONFIG & STYLING
# ============================================================================

st.set_page_config(
    page_title="Q-Sentinel",
    page_icon="[SHIELD]",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    body {
        background-color: #0a0e27;
        color: #e0e0e0;
        font-family: 'Courier New', monospace;
    }
    .main {
        background-color: #0a0e27;
    }
    h1, h2, h3 {
        color: #00D9FF;
        text-shadow: 0 0 10px rgba(0, 217, 255, 0.3);
    }
    .phishing-alert {
        background: linear-gradient(135deg, #4a0000 0%, #2a0a0a 100%);
        border: 2px solid #ff4444;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        color: #ff6666;
    }
    .legitimate-safe {
        background: linear-gradient(135deg, #0a4a0a 0%, #0a2a2a 100%);
        border: 2px solid #00D9FF;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        color: #00FF00;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

@st.cache_resource
def load_model():
    """Load the trained model."""
    model_path = 'models/phishing_model.pkl'
    
    if not os.path.exists(model_path):
        return None, "Model not found"
    
    try:
        model = URLPhishingModel()
        model.load(model_path)
        return model, None
    except Exception as e:
        return None, str(e)


@st.cache_resource
def init_threat_intel():
    """Initialize OTX threat intelligence."""
    if not threat_intel_available:
        return None
    try:
        otx = OTXThreatIntel()
        return otx
    except (ValueError, Exception):
        return None


def load_evaluation_metrics():
    """Load saved evaluation metrics."""
    metrics_path = 'results/evaluation_metrics.json'
    
    if not os.path.exists(metrics_path):
        return None
    
    try:
        with open(metrics_path, 'r') as f:
            return json.load(f)
    except Exception:
        return None


def predict_url(model, url, threat_intel=None):
    """Make prediction on a single URL with optional threat intel."""
    result = {}
    
    # ML prediction
    try:
        features = extract_features(url)
        pred, proba = model.predict_single(features)
        result['features'] = features
        result['ml_prediction'] = pred
        result['ml_probability'] = proba
        result['error'] = None
    except Exception as e:
        result['features'] = None
        result['ml_prediction'] = None
        result['ml_probability'] = None
        result['error'] = str(e)
    
    # Threat intel
    result['threat_intel'] = None
    if threat_intel:
        try:
            threat_result = threat_intel.check_url(url)
            result['threat_intel'] = threat_result
        except Exception as e:
            result['threat_intel'] = {
                'error': f"Threat intel error: {str(e)}",
                'is_malicious': False
            }
    
    return result


# ============================================================================
# MAIN APP
# ============================================================================

st.markdown("# Q-SENTINEL: Phishing URL Detection")
st.markdown("### Classical ML + Threat Intelligence Analysis")

# Load model
model, model_error = load_model()

if model_error:
    st.error(f"Model error: {model_error}")
    st.info("Run: python train.py --data data/sample_urls.csv")
    st.stop()

# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.markdown("### Navigation")
    page = st.radio(
        "Select page:",
        ["Scanner", "Evaluation", "Batch Analysis"],
        label_visibility="collapsed"
    )
    
    st.divider()
    
    st.markdown("### Info")
    st.markdown("""
    **Q-Sentinel v0.2.0**
    
    - ML: RandomForest (12 features)
    - TI: AlienVault OTX
    - Speed: <1s per URL
    """)

# ============================================================================
# PAGE 1: SCANNER
# ============================================================================

if page == "Scanner":
    st.header("URL Scanner")
    
    threat_intel = init_threat_intel()
    if threat_intel:
        st.success("Threat Intelligence: Connected")
    else:
        st.warning("Threat Intelligence: Unavailable")
    
    url_input = st.text_input(
        "Enter URL:",
        placeholder="https://example.com",
        help="URL to analyze"
    )
    
    show_details = st.checkbox("Show details")
    
    if url_input:
        with st.spinner("Analyzing..."):
            result = predict_url(model, url_input, threat_intel=threat_intel)
        
        st.divider()
        
        if result.get('error'):
            st.error(result['error'])
        else:
            ml_pred = result.get('ml_prediction')
            ml_prob = result.get('ml_probability', 0)
            ti = result.get('threat_intel')
            
            # Determine risk
            risk = "LOW"
            if ti and not ti.get('error'):
                if ti.get('is_malicious') or ml_pred == 1:
                    risk = "HIGH"
            elif ml_pred == 1:
                risk = "MEDIUM"
            
            # Display result
            if risk == "HIGH":
                st.markdown("""
                <div class="phishing-alert">
                <h3>RISK: HIGH</h3>
                </div>
                """, unsafe_allow_html=True)
            elif risk == "MEDIUM":
                st.warning("RISK: MEDIUM - Suspicious")
            else:
                st.markdown("""
                <div class="legitimate-safe">
                <h3>RISK: LOW</h3>
                </div>
                """, unsafe_allow_html=True)
            
            # Metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("ML Confidence", f"{ml_prob*100:.1f}%")
            if ti and not ti.get('error'):
                with col2:
                    rep = ti.get('reputation', 0)
                    st.metric("OTX Rep", f"{rep:+d}")
                with col3:
                    inds = len(ti.get('indicators', []))
                    st.metric("Indicators", inds)
            
            # Details
            if show_details:
                if ti and not ti.get('error'):
                    st.subheader("Threat Intelligence")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"Status: {ti.get('threat_level', 'unknown')}")
                        st.write(f"Malicious: {ti.get('is_malicious', False)}")
                    with col2:
                        for ind in ti.get('indicators', [])[:3]:
                            st.write(f"- {ind}")
                
                st.subheader("ML Features")
                features = result.get('features', [])
                if features:
                    names = get_feature_names()
                    col1, col2 = st.columns(2)
                    with col1:
                        for i in range(6):
                            st.write(f"{names[i]}: {features[i]}")
                    with col2:
                        for i in range(6, 12):
                            st.write(f"{names[i]}: {features[i]}")

# ============================================================================
# PAGE 2: EVALUATION
# ============================================================================

elif page == "Evaluation":
    st.header("Model Evaluation")
    
    metrics = load_evaluation_metrics()
    
    if metrics is None:
        st.error("Metrics not found")
    else:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Accuracy", f"{metrics['accuracy']:.3f}")
        col2.metric("Precision", f"{metrics['precision']:.3f}")
        col3.metric("Recall", f"{metrics['recall']:.3f}")
        col4.metric("F1-Score", f"{metrics['f1_score']:.3f}")
        
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Confusion Matrix")
            cm = metrics['confusion_matrix']
            df_cm = pd.DataFrame(cm, 
                index=['Actual Legit', 'Actual Phish'],
                columns=['Pred Legit', 'Pred Phish'])
            st.dataframe(df_cm, use_container_width=True)
        
        with col2:
            st.subheader("Metrics")
            st.metric("ROC-AUC", f"{metrics.get('roc_auc', 0):.3f}")
            st.metric("False Positive Rate", f"{metrics.get('false_positive_rate', 0):.3f}")

# ============================================================================
# PAGE 3: BATCH ANALYSIS
# ============================================================================

elif page == "Batch Analysis":
    st.header("Batch Analysis")
    
    uploaded_file = st.file_uploader("Upload CSV", type=['csv'])
    
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
        except Exception as e:
            st.error(f"Error reading file: {e}")
            st.stop()
        
        if 'url' not in df.columns:
            st.error("CSV must have 'url' column")
            st.stop()
        
        st.info(f"Loaded {len(df)} URLs")
        
        if st.button("Analyze All"):
            threat_intel = init_threat_intel()
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            predictions = []
            
            for idx, url in enumerate(df['url']):
                status_text.text(f"Processing {idx+1}/{len(df)}...")
                progress_bar.progress((idx+1)/len(df))
                result = predict_url(model, url, threat_intel=threat_intel)
                predictions.append(result)
            
            results_df = df.copy()
            results_df['prediction'] = [
                "Phishing" if p.get('ml_prediction') == 1 else "Legitimate" 
                for p in predictions
            ]
            results_df['confidence'] = [
                f"{p.get('ml_probability', 0)*100:.1f}%" 
                for p in predictions
            ]
            
            st.divider()
            st.subheader("Results")
            
            phishing_count = sum(1 for p in predictions if p.get('ml_prediction') == 1)
            legit_count = sum(1 for p in predictions if p.get('ml_prediction') == 0)
            
            col1, col2 = st.columns(2)
            col1.metric("Phishing", phishing_count)
            col2.metric("Legitimate", legit_count)
            
            st.dataframe(results_df, use_container_width=True)
            
            csv = results_df.to_csv(index=False)
            st.download_button("Download Results", csv, "results.csv", "text/csv")

# ============================================================================
# FOOTER
# ============================================================================

st.divider()
st.markdown("Q-Sentinel v0.2.0 | ML + Threat Intelligence | Cybersecurity Focused")
