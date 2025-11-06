#!/usr/bin/env python3
"""
Entry point script for Render deployment.
"""

import os
import sys
import subprocess
import http.server
import threading

def add_http_server():
    """Add a simple HTTP server for health checks."""
    # Get port from environment or use default
    port = int(os.environ.get("PORT", 10000))
    
    class HealthCheckHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/health" or self.path == "/":
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"status": "healthy"}')
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'{"status": "not found"}')
        
        # Silence log messages
        def log_message(self, format, *args):
            return
    
    def run_server():
        server = http.server.HTTPServer(("0.0.0.0", port), HealthCheckHandler)
        print(f"Starting HTTP server on port {port}")
        server.serve_forever()
    
    # Start HTTP server in a separate thread
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    return thread

def main():
    """Run the main application."""
    print("Starting Google Drive Sync application...")
    
    # Add the current directory to the Python path
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    
    # Start HTTP server for health checks
    http_server_thread = add_http_server()
    
    # Set up configuration
    print("Setting up configuration...")
    from setup_config import setup_config
    setup_config()
    
    # Print current directory and list files for debugging
    print(f"Current directory: {os.getcwd()}")
    print("Files in current directory:")
    for item in os.listdir("."):
        print(f"  {item}")
    print("Files in config directory:")
    for item in os.listdir("config"):
        print(f"  {item}")
    
    # Run the main module
    print("Running main application...")
    from src.main import main
    main()

if __name__ == "__main__":
    main()
