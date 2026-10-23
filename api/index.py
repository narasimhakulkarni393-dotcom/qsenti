"""
Q-Sentinel: Phishing URL Detection - Vercel Landing Page
"""

from datetime import datetime

def handler(request):
    """Landing page for Q-Sentinel API"""
    
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
            <h1>🔐 Q-Sentinel</h1>
            <p class="subtitle">Phishing URL Detection API powered by ML + Threat Intelligence</p>
            
            <div class="status">✅ API is Live and Running</div>
            
            <div class="section">
                <h2>🚀 Quick Start</h2>
                <p>Send a POST request to analyze URLs for phishing:</p>
                <div class="code-block">
                    <span class="method">POST</span> <span class="endpoint">/api/predict</span>
                </div>
            </div>
            
            <div class="section">
                <h2>📨 Request Body</h2>
                <div class="example-request">
                    <code>{<br/>
                    &nbsp;&nbsp;"url": "https://example.com"<br/>
                    }</code>
                </div>
            </div>
            
            <div class="section">
                <h2>✅ Response Example</h2>
                <div class="example-response">
                    <code>{<br/>
                    &nbsp;&nbsp;"url": "https://example.com",<br/>
                    &nbsp;&nbsp;"prediction": "LEGITIMATE",<br/>
                    &nbsp;&nbsp;"confidence": 0.95,<br/>
                    &nbsp;&nbsp;"risk_level": "LOW",<br/>
                    &nbsp;&nbsp;"risk_emoji": "🟢",<br/>
                    &nbsp;&nbsp;"threat_intel": {<br/>
                    &nbsp;&nbsp;&nbsp;&nbsp;"is_malicious": false,<br/>
                    &nbsp;&nbsp;&nbsp;&nbsp;"source": "AlienVault OTX"<br/>
                    &nbsp;&nbsp;}<br/>
                    }</code>
                </div>
            </div>
            
            <div class="section">
                <h2>🔗 Try It</h2>
                <p>Use curl or any HTTP client:</p>
                <div class="code-block">
curl -X POST https://your-domain.vercel.app/api/predict \\<br/>
&nbsp;&nbsp;-H "Content-Type: application/json" \\<br/>
&nbsp;&nbsp;-d '{"url": "https://paypal-confirm.tk/verify"}'
                </div>
            </div>
            
            <div class="section">
                <h2>📊 Features</h2>
                <ul>
                    <li>🤖 Classical ML (RandomForest) with 12 URL features</li>
                    <li>🌐 Real-time threat intelligence from AlienVault OTX</li>
                    <li>⚡ Sub-100ms response times</li>
                    <li>🔄 Confidence scores and risk levels</li>
                    <li>📈 Hybrid decision engine (ML + Threat Intel)</li>
                </ul>
            </div>
            
            <div class="footer">
                <p>Q-Sentinel v0.2.0 | <a href="https://github.com/narasimhakulkarni393-dotcom/qsenti" target="_blank">GitHub</a> | VTU-QFF Hackathon 2026</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return {
        'statusCode': 200,
        'body': html,
        'headers': {
            'Content-Type': 'text/html; charset=utf-8',
        },
    }
