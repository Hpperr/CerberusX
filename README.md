# CERBERUS X v2.0
# Advanced Mobile RAT Framework - Red Team Edition

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 14+](https://img.shields.io/badge/node.js-14+-green.svg)](https://nodejs.org/)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey)]()

---

## 📖 Table of Contents

- Overview
- Features
- Architecture
- Installation
- Quick Start
- Modules
- Attack Chain
- Configuration
- Usage Guide
- Payload Development
- Defensive Considerations
- Comparison with Commercial Tools
- Roadmap
- Contributing
- License
- Disclaimer

---

## 🎯 Overview

**CERBERUS X v2.0** is an advanced Mobile RAT (Remote Access Trojan) Framework designed for professional Red Team operations and mobile security testing. Inspired by commercial solutions like Pegasus (NSO Group) and open-source projects like Amyth, Cerberus X brings enterprise-grade capabilities to the security community — completely free and open source.

### Core Philosophy

> *"Democratizing mobile security testing — making professional-grade tools accessible to everyone."*

---

## 🔥 Features

### Multi-Layer Attack Chain
Reconnaissance (Passive & Active)
Network Positioning (ARP Spoofing)
SSL/TLS Downgrade (HSTS Bypass)
Payload Injection (MITM)
Persistence (Service Worker)
Data Exfiltration (Vault Cracker)
Surveillance (Screen Mirror)
Cleanup (Forensic Removal)


### Key Capabilities

- **Full MITM Attack Chain** — ARP spoofing → SSL stripping → Payload injection
- **Mobile Device Targeting** — Android & iOS support via browser exploits
- **Service Worker Persistence** — Persistent backdoor in victim browsers
- **Vault Cracking** — Extract credentials from browser vaults
- **Live Screen Mirroring** — Real-time screen streaming via WebRTC
- **Zero Trust Architecture** — Multi-layer stealth and evasion
- **Modular Design** — Each component can be used independently
- **Enterprise Dashboard** — Professional real-time monitoring interface

---

## 🏗️ Architecture
CERBERUS X v2.0
├── C2 Infrastructure
│ ├── central_brain.js (WebSocket Server)
│ └── dashboard_v3.html (Monitoring Dashboard)
├── Kernel Core
│ ├── recon_scanner.py (Network Discovery)
│ ├── interceptor_v3.py (ARP Spoofing)
│ ├── injector_v4.py (Payload Injection)
│ ├── ssl_bypass_v2.py (SSL/TLS Downgrade)
│ └── traffic_cleaner.py (Forensic Cleanup)
├── Payload Factory
│ ├── ghost_sw_v2.js (Service Worker)
│ ├── vault_cracker_v2.js (Data Exfiltration)
│ └── live_mirror_v2.js (Screen Mirroring)
└── Deploy Scripts
└── deploy_hell_v2.sh (One-Click Deployment)

---

## 📦 Installation

### System Requirements

- **OS**: Linux (Kali/Ubuntu/Debian recommended)
- **Python**: 3.8+
- **Node.js**: 14+
- **Root privileges** — Required for network operations
- **Network interface** — With monitor mode support

### Install Dependencies

```bash
# Install system packages
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
    net-tools

# Install Python dependencies
pip3 install -r requirements.txt

# Install Node dependencies
cd c2_infrastructure
npm install ws express
cd ..

# Make scripts executable
chmod +x deploy_hell_v2.sh

# Generate SSL certificates
openssl req -x509 -newkey rsa:4096 -keyout /etc/ssl/private/cerberus.key \
    -out /etc/ssl/certs/cerberus.crt -days 365 -nodes \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=cerberus.local"
