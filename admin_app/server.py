#!/usr/bin/env python3
"""
Simple HTTP Server for App Usage Admin Dashboard
Serves the Bootstrap 5+ admin frontend on localhost:3000
"""

import http.server
import socketserver
import os
import sys
import webbrowser
from pathlib import Path

# Configuration
PORT = 3000
HOST = 'localhost'

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler to serve files with proper MIME types"""
    
    def end_headers(self):
        # Add CORS headers for API calls
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-API-Key-725d9439')
        super().end_headers()
    
    def do_OPTIONS(self):
        # Handle preflight requests
        self.send_response(200)
        self.end_headers()
    
    def log_message(self, format, *args):
        # Custom logging format
        print(f"[{self.log_date_time_string()}] {format % args}")

def main():
    # Change to admin_app directory
    admin_app_dir = Path(__file__).parent
    os.chdir(admin_app_dir)
    
    print("=" * 60)
    print("🚀 App Usage Admin Dashboard Server")
    print("=" * 60)
    print(f"📁 Serving directory: {admin_app_dir.absolute()}")
    print(f"🌐 Server URL: http://{HOST}:{PORT}")
    print(f"📱 Dashboard: http://{HOST}:{PORT}/index.html")
    print("=" * 60)
    print("💡 Make sure your REST API is running on http://localhost:8000")
    print("   To start REST API: cd rest && python main.py")
    print("=" * 60)
    
    # Create server
    try:
        with socketserver.TCPServer((HOST, PORT), CustomHTTPRequestHandler) as httpd:
            print(f"✅ Server started successfully!")
            print(f"🔗 Opening browser at http://{HOST}:{PORT}")
            
            # Open browser automatically
            try:
                webbrowser.open(f'http://{HOST}:{PORT}')
            except Exception as e:
                print(f"⚠️  Could not open browser automatically: {e}")
                print(f"   Please manually open: http://{HOST}:{PORT}")
            
            print("\n🛑 Press Ctrl+C to stop the server")
            print("-" * 60)
            
            # Start serving
            httpd.serve_forever()
            
    except OSError as e:
        if e.errno == 10048:  # Port already in use
            print(f"❌ Error: Port {PORT} is already in use!")
            print(f"   Try a different port or stop the process using port {PORT}")
        else:
            print(f"❌ Error starting server: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n🛑 Server stopped by user")
        print("👋 Goodbye!")

if __name__ == "__main__":
    main()
