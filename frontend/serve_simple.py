#!/usr/bin/env python3
"""
ZTNAS Frontend Server - Direct Routing Version
"""

import os
import sys
import http.server
import socketserver
import logging
from pathlib import Path

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).parent / 'static'
os.chdir(STATIC_DIR)

class Handler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler with direct routing"""

    def end_headers(self):
        """Add security headers"""
        self.send_header('X-Frame-Options', 'SAMEORIGIN')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-XSS-Protection', '1; mode=block')
        self.send_header('Referrer-Policy', 'strict-origin-when-cross-origin')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Content-Security-Policy', 
            "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; font-src 'self'; connect-src 'self' http://localhost:8000 http://127.0.0.1:8000 https:")
        # Disable caching in local development to avoid stale JS/CSS after fixes.
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def do_GET(self):
        """Handle GET requests with intelligent routing"""
        original_path = self.path
        
        # Strip query parameters from path for routing logic
        path_without_query = original_path.split('?')[0]

        # Normalize accidental /static/* requests because static/ is already the server root.
        # Example: /static/js/auth.js -> /js/auth.js
        if path_without_query.startswith('/static/'):
            normalized_path = path_without_query[len('/static'):]
            if '?' in original_path:
                query = original_path.split('?', 1)[1]
                self.path = f"{normalized_path}?{query}"
            else:
                self.path = normalized_path
            path_without_query = normalized_path
            logger.info(f"✓ Normalized {original_path} → {self.path}")
        
        # Block directory listing (but allow root)
        if path_without_query.endswith('/') and path_without_query != '/':
            self.send_error(403, 'Directory listing not allowed')
            return
        
        # ROUTING LOGIC
        if path_without_query == '/':
            # Root → landing page
            self.path = '/html/index.html'
            logger.info(f"✓ Routing / → /html/index.html")

        elif path_without_query == '/favicon.ico':
            # Silence browser favicon 404 noise when no favicon file exists yet.
            self.send_response(204)
            self.send_header('Content-Length', '0')
            self.end_headers()
            return
        
        elif path_without_query.endswith('.html') and not path_without_query.startswith('/html/'):
            # HTML file request (e.g., /login.html) → check in html/ subdirectory
            filename = os.path.basename(path_without_query)
            potential_file = os.path.join(STATIC_DIR, 'html', filename)
            
            if os.path.exists(potential_file):
                self.path = f'/html/{filename}'
                logger.info(f"✓ Routing {original_path} → /html/{filename}")
            else:
                logger.warning(f"✗ File not found: {original_path} (also not in /html/)")
        
        # Serve the (possibly modified) path
        try:
            super().do_GET()
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as e:
            logger.error(f"Error: {e}")

    def log_message(self, format, *args):
        logger.info(format % args)

    def version_string(self):
        return "ZTNAS/1.0"

if __name__ == '__main__':
    PORT = 5500
    
    print("\n" + "="*60)
    print("  ZTNAS Frontend Server (Production-Ready)")
    print("="*60)
    print(f"\n✓ Dashboard: http://localhost:{PORT}")
    print("\nFeatures:")
    print("  ✓ Automatic index.html serving")
    print("  ✓ Security headers enabled") 
    print("  ✓ Direct routing to /html/ subdirectory")
    print("  ✓ Directory listing blocked")
    print("\nPress Ctrl+C to stop\n" + "="*60 + "\n")
    
    try:
        socketserver.TCPServer.allow_reuse_address = True
        server = socketserver.TCPServer(("", PORT), Handler)
        logger.info(f"Server running on port {PORT}")
        print(f"🚀 Server is running - open http://localhost:{PORT}\n")
        server.serve_forever()
    except OSError as e:
        if "already in use" in str(e):
            print(f"✗ Port {PORT} is already in use")
            sys.exit(1)
        raise
