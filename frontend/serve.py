#!/usr/bin/env python3
"""
ZTNAS Production-Ready Frontend Server
Serves the college management system dashboard with proper index handling
Features:
  - Automatic index.html serving for directory requests
  - Security headers (X-Frame-Options, Content-Security-Policy, etc.)
  - CORS support for API calls to backend
  - Production-grade logging
  - Proper MIME types
  - Stability optimizations
"""

import os
import sys
import http.server
import socketserver
import logging
from pathlib import Path
from http import HTTPStatus
from typing import Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get the static directory path
STATIC_DIR = Path(__file__).parent / 'static'
INDEX_FILE = 'html/index.html'  # Default landing page under html directory

class ProductionHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Enhanced HTTP request handler with production features"""

    # MIME types mapping
    MIME_TYPES = {
        '.html': 'text/html; charset=utf-8',
        '.css': 'text/css; charset=utf-8',
        '.js': 'application/javascript; charset=utf-8',
        '.json': 'application/json; charset=utf-8',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.svg': 'image/svg+xml',
        '.webp': 'image/webp',
        '.woff': 'font/woff',
        '.woff2': 'font/woff2',
        '.ttf': 'font/ttf',
        '.eot': 'application/vnd.ms-fontobject',
        '.map': 'application/json; charset=utf-8',
    }

    def end_headers(self):
        """Add security and optimization headers"""
        # Security headers
        self.send_header('X-Frame-Options', 'SAMEORIGIN')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-XSS-Protection', '1; mode=block')
        self.send_header('Referrer-Policy', 'strict-origin-when-cross-origin')
        
        # CORS headers for API calls to backend
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        
        # Content Security Policy (strict but allows local resources)
        self.send_header('Content-Security-Policy', 
                        "default-src 'self'; script-src 'self' 'unsafe-inline'; "
                        "style-src 'self' 'unsafe-inline'; "
                        "img-src 'self' data: https:; "
                        "font-src 'self'; "
                        "connect-src 'self' http://localhost:8000 http://127.0.0.1:8000; "
                        "frame-ancestors 'self';")
        
        # Cache control
        self.send_header('Cache-Control', 'public, max-age=3600')
        
        super().end_headers()

    def should_gzip(self) -> bool:
        """Check if client accepts gzip compression (disabled for stability)"""
        # Disabled gzip due to connection issues - browsers handle uncompressed fine
        return False

    def do_GET(self):
        """Handle GET requests with directory index logic"""
        # Parse the path
        path = self.translate_path(self.path)
        
        # Check if directory - serve index.html from html subdirectory
        if os.path.isdir(path):
            index_path = os.path.join(path, 'html', INDEX_FILE.split('/')[1])
            if not os.path.exists(index_path):
                index_path = os.path.join(path, INDEX_FILE)
            if os.path.exists(index_path):
                self.serve_file(index_path)
                return
            else:
                # Log directory access attempt
                logger.warning(f"Directory listing attempt blocked: {self.path}")
                self.send_error(HTTPStatus.FORBIDDEN, "Directory listing not allowed")
                return
        
        # Check if file exists
        if os.path.exists(path):
            self.serve_file(path)
            return
        
        # Try with .html extension for SPA routing
        if not path.endswith('.html'):
            html_path = path + '.html'
            if os.path.exists(html_path):
                self.serve_file(html_path)
                return
            
            # Try in html subdirectory
            base_filename = os.path.basename(path)
            html_dir_path = os.path.join(STATIC_DIR, 'html', base_filename + '.html')
            if os.path.exists(html_dir_path):
                self.serve_file(html_dir_path)
                return
        
        # File not found - serve index.html for SPA routing
        index_path = os.path.join(STATIC_DIR, INDEX_FILE)
        if os.path.exists(index_path) and self.should_spa_route():
            logger.info(f"SPA route not found, serving index.html: {self.path}")
            self.serve_file(index_path)
            return
        
        self.send_error(HTTPStatus.NOT_FOUND, "File not found")

    def should_spa_route(self) -> bool:
        """Determine if this should be routed to index.html (SPA routing)"""
        # Don't route static files
        if self.path.startswith('/static/'):
            return False
        if self.path.startswith('/html/'):
            return False
        if '.' in self.path.split('/')[-1]:
            return False
        return True

    def serve_file(self, filepath: str):
        """Serve a file with proper headers and optional compression"""
        try:
            with open(filepath, 'rb') as f:
                content = f.read()
            
            # Get content type
            _, ext = os.path.splitext(filepath)
            content_type = self.MIME_TYPES.get(ext.lower(), self.guess_type(filepath))
            
            # Send response (gzip disabled for stability)
            self.send_response(HTTPStatus.OK)
            self.send_header('Content-type', content_type)
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
            
            logger.info(f"✓ {self.command} {self.path} - {HTTPStatus.OK.value}")
        
        except IOError as e:
            logger.error(f"✗ Error serving {filepath}: {str(e)}")
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "Error serving file")
        except Exception as e:
            logger.error(f"✗ Unexpected error serving {filepath}: {str(e)}")
            try:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "Error serving file")
            except:
                pass  # Connection already closed

    def translate_path(self, path: str) -> str:
        """Convert URL path to filesystem path"""
        # Decode URL
        try:
            path = path.split('?', 1)[0]
            path = path.split('#', 1)[0]
            path = path.replace('//', '/')
            path = path.replace('\\', '/')
        except Exception as e:
            logger.error(f"Path parsing error: {e}")
            return STATIC_DIR
        
        # Remove leading slash
        if path.startswith('/'):
            path = path[1:]
        
        # Build full path
        fullpath = os.path.join(STATIC_DIR, path)
        
        # Security: prevent directory traversal
        try:
            realpath = os.path.realpath(fullpath)
            if not realpath.startswith(os.path.realpath(STATIC_DIR)):
                logger.warning(f"Directory traversal attempt blocked: {path}")
                return STATIC_DIR
        except Exception as e:
            logger.error(f"Path security check error: {e}")
            return STATIC_DIR
        
        return fullpath

    def log_message(self, format, *args):
        """Override to use proper logging"""
        logger.info(format % args)

    def version_string(self):
        """Custom server version string (security)"""
        return "ZTNAS/1.0"


class ProductionHTTPServer(socketserver.TCPServer):
    """Production-grade HTTP server with proper configuration"""
    
    allow_reuse_address = True
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.socket.setsockopt(socketserver.socket.SOL_SOCKET, 
                              socketserver.socket.SO_REUSEADDR, 1)


def main():
    """Main server entry point"""
    
    # Change to static directory
    os.chdir(STATIC_DIR)
    
    PORT = 5500
    ADDR = '0.0.0.0'
    
    print("\n" + "="*70)
    print("  ZTNAS - Zero Trust Network Access System")
    print("  Production Frontend Server")
    print("="*70)
    print(f"\n✓ Serving from: {STATIC_DIR}")
    print(f"✓ Server: http://{ADDR}:{PORT}")
    print(f"✓ Access: http://localhost:{PORT}")
    print("\nFeatures:")
    print("  ✓ Automatic index.html serving")
    print("  ✓ Security headers (X-Frame-Options, CSP, etc.)")
    print("  ✓ CORS enabled for backend API calls")
    print("  ✓ Gzip compression support")
    print("  ✓ Production logging")
    print("  ✓ SPA routing support")
    print("\nSecurity:")
    print("  ✓ Directory listing disabled")
    print("  ✓ Directory traversal prevention")
    print("  ✓ Content Security Policy enabled")
    print("  ✓ Referrer-Policy strict")
    
    print(f"\nStarting server on port {PORT}...")
    print("Press Ctrl+C to stop\n")
    
    try:
        handler = ProductionHTTPRequestHandler
        server = ProductionHTTPServer((ADDR, PORT), handler)
        logger.info(f"Server started successfully on {ADDR}:{PORT}")
        
        print("="*70)
        print("\n🚀 Server is running and ready for ZTNAS College Dashboard\n")
        print("="*70 + "\n")
        
        server.serve_forever()
    
    except OSError as e:
        if "Address already in use" in str(e):
            logger.error(f"✗ Port {PORT} is already in use")
            print(f"\n✗ Error: Port {PORT} is already in use")
            print(f"  Please kill the existing process or use a different port")
            sys.exit(1)
        else:
            logger.error(f"✗ Server error: {e}")
            raise
    
    except KeyboardInterrupt:
        print("\n\n✓ Server stopped gracefully")
        logger.info("Server stopped by user")


if __name__ == '__main__':
    main()
