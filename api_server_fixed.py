#!/usr/bin/env python3
"""
Flask API for Dark Web Observatory Features
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
import traceback

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)
CORS(app)

@app.route('/api/scan', methods=['POST', 'OPTIONS'])
def scan():
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        # Import here to avoid startup issues
        from on_demand_scan import perform_deep_scan
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'})
        
        url = data.get('url', '')
        if not url:
            return jsonify({'success': False, 'error': 'No URL provided'})
        
        result = perform_deep_scan(url)
        return jsonify(result)
    
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'})

@app.route('/api/refresh-news', methods=['POST', 'OPTIONS'])
def refresh():
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        # Import here to avoid startup issues
        from refresh_news import fetch_news
        
        success = fetch_news()
        return jsonify({
            'success': success,
            'message': 'News feed updated successfully' if success else 'Failed to update news feed'
        })
    
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'})

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'service': 'Dark Web Observatory API'})

if __name__ == '__main__':
    print("Starting Dark Web Observatory API on http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=False)

