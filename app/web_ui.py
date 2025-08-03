#!/usr/bin/env python3
"""
Earthworm Web UI - Simple web interface for social media data collection
Built with Flask for lightweight deployment and easy access.
"""

from flask import Flask, render_template, request, jsonify, send_file
import json
import os
from datetime import datetime
import threading
import queue
from .main import EarthwormApp, Platform

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'earthworm-dev-key')

# Configure Jinja2 to use different delimiters to avoid conflicts with Vue.js
# app.jinja_env.variable_start_string = '{['
# app.jinja_env.variable_end_string = ']}'

# Global app instance and job queue
earthworm_app = None
job_queue = queue.Queue()
active_jobs = {}

class WebEarthwormApp:
    """Web wrapper for EarthwormApp with async job handling."""
    
    def __init__(self):
        self.app = EarthwormApp()
        self.current_platform = None
        self.job_counter = 0
    
    def initialize_platform(self, platform_name, stealth_mode=False):
        """Initialize platform and return status."""
        try:
            if self.app.initialize_platform(platform_name, stealth_mode=stealth_mode):
                self.current_platform = platform_name
                return {"success": True, "message": f"{platform_name.capitalize()} initialized successfully"}
            else:
                return {"success": False, "message": f"Failed to initialize {platform_name}"}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def get_status(self):
        """Get current app status."""
        return {
            "platforms_available": [p.value for p in self.app.available_platforms],
            "current_platform": self.current_platform,
            "initialized": self.current_platform is not None
        }
    
    def start_collection_job(self, job_type, **kwargs):
        """Start a data collection job asynchronously."""
        self.job_counter += 1
        job_id = f"job_{self.job_counter}_{datetime.now().strftime('%H%M%S')}"
        
        def run_job():
            try:
                if job_type == "search":
                    result = self.app.search_across_platform(**kwargs)
                elif job_type == "subreddit":
                    result = self.app.collect_subreddit_data(**kwargs)
                elif job_type == "multi_source":
                    result = self.app.collect_from_multiple_sources(**kwargs)
                elif job_type == "trending":
                    result = self.app.analyze_trending_topics(**kwargs)
                else:
                    result = {"error": f"Unknown job type: {job_type}"}
                
                active_jobs[job_id] = {
                    "status": "completed",
                    "result": result,
                    "completed_at": datetime.now().isoformat()
                }
            except Exception as e:
                active_jobs[job_id] = {
                    "status": "failed",
                    "error": str(e),
                    "completed_at": datetime.now().isoformat()
                }
        
        active_jobs[job_id] = {
            "status": "running",
            "job_type": job_type,
            "started_at": datetime.now().isoformat(),
            "kwargs": kwargs
        }
        
        thread = threading.Thread(target=run_job)
        thread.start()
        
        return job_id

@app.route('/')
def index():
    """Main dashboard."""
    return render_template('dashboard.html')

@app.route('/api/status')
def api_status():
    """Get app status."""
    global earthworm_app
    if not earthworm_app:
        earthworm_app = WebEarthwormApp()
    
    return jsonify(earthworm_app.get_status())

@app.route('/api/initialize', methods=['POST'])
def api_initialize():
    """Initialize a platform."""
    global earthworm_app
    if not earthworm_app:
        earthworm_app = WebEarthwormApp()
    
    data = request.json
    platform = data.get('platform', 'reddit')
    stealth_mode = data.get('stealth_mode', False)
    
    result = earthworm_app.initialize_platform(platform, stealth_mode)
    return jsonify(result)

@app.route('/api/search', methods=['POST'])
def api_search():
    """Start a search job."""
    global earthworm_app
    if not earthworm_app or not earthworm_app.current_platform:
        return jsonify({"success": False, "message": "Platform not initialized"})
    
    data = request.json
    job_id = earthworm_app.start_collection_job(
        "search",
        query=data.get('query'),
        subreddit=data.get('subreddit'),
        limit=data.get('limit', 25),
        include_comments=data.get('include_comments', False)
    )
    
    return jsonify({"success": True, "job_id": job_id})

@app.route('/api/subreddit', methods=['POST'])
def api_subreddit():
    """Start a subreddit collection job."""
    global earthworm_app
    if not earthworm_app or not earthworm_app.current_platform:
        return jsonify({"success": False, "message": "Platform not initialized"})
    
    data = request.json
    job_id = earthworm_app.start_collection_job(
        "subreddit",
        subreddit=data.get('subreddit'),
        sort=data.get('sort', 'hot'),
        limit=data.get('limit', 25),
        include_comments=data.get('include_comments', False)
    )
    
    return jsonify({"success": True, "job_id": job_id})

@app.route('/api/jobs/<job_id>')
def api_job_status(job_id):
    """Get job status and results."""
    if job_id in active_jobs:
        return jsonify(active_jobs[job_id])
    else:
        return jsonify({"error": "Job not found"}), 404

@app.route('/api/export/<job_id>')
def api_export(job_id):
    """Export job results."""
    if job_id not in active_jobs or active_jobs[job_id]['status'] != 'completed':
        return jsonify({"error": "Job not found or not completed"}), 404
    
    format_type = request.args.get('format', 'json')
    result = active_jobs[job_id]['result']
    
    if not earthworm_app:
        return jsonify({"error": "App not initialized"}), 500
    
    try:
        filename = earthworm_app.app.export_data(result, format=format_type)
        return send_file(filename, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/platforms')
def api_platforms():
    """Get available platforms."""
    global earthworm_app
    if not earthworm_app:
        earthworm_app = WebEarthwormApp()
    
    return jsonify({
        "available": [p.value for p in earthworm_app.app.available_platforms],
        "supported": ["reddit", "twitter"]
    })

if __name__ == '__main__':
    print("🌍 Starting Earthworm Web UI...")
    print("📊 Access at: http://localhost:5000")
    print("🔧 Use Ctrl+C to stop")
    app.run(debug=True, host='0.0.0.0', port=5000)
