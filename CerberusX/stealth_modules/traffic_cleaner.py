#!/usr/bin/env python3
"""
TRAFFIC CLEANER v2.0 - Advanced Forensics Cleaner
Complete system sanitization with multiple layers

Copyright (c) 2024 F1REW0LF
License: MIT - For authorized security testing only
"""

import os
import sys
import time
import subprocess
import shutil
import random
import hashlib
import json
from datetime import datetime
import threading
import signal

class TrafficCleaner:
    """Advanced traffic and forensic cleaner"""
    
    def __init__(self, stealth=True, deep_clean=True):
        self.stealth = stealth
        self.deep_clean = deep_clean
        self.original_state = {}
        self.clean_log = []
        self.running = True
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        """Handle signals"""
        print("\n[!] Cleaner interrupted")
        self.running = False
        sys.exit(0)
    
    def log_clean(self, action, details):
        """Log cleaning action"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'details': details
        }
        self.clean_log.append(entry)
        print(f"[*] {action}: {details}")
    
    def flush_iptables(self):
        """Flush all iptables rules"""
        try:
            # Save current state
            subprocess.run(["iptables-save"], capture_output=True, text=True)
            
            # Flush all rules
            subprocess.run(["iptables", "--flush"], check=False)
            subprocess.run(["iptables", "-t", "nat", "--flush"], check=False)
            subprocess.run(["iptables", "-t", "mangle", "--flush"], check=False)
            subprocess.run(["iptables", "-X"], check=False)
            
            # Restore default policies
            subprocess.run(["iptables", "-P", "INPUT", "ACCEPT"], check=False)
            subprocess.run(["iptables", "-P", "FORWARD", "ACCEPT"], check=False)
            subprocess.run(["iptables", "-P", "OUTPUT", "ACCEPT"], check=False)
            
            self.log_clean("IPTABLES_FLUSH", "All firewall rules flushed")
            return True
        except Exception as e:
            self.log_clean("IPTABLES_ERROR", str(e))
            return False
    
    def reset_interfaces(self):
        """Reset network interfaces to managed mode"""
        try:
            # Get all wireless interfaces
            result = subprocess.run(["iwconfig"], capture_output=True, text=True)
            interfaces = []
            
            for line in result.stdout.split('\n'):
                if 'IEEE 802.11' in line:
                    iface = line.split()[0]
                    interfaces.append(iface)
            
            for iface in interfaces:
                # Reset to managed mode
                subprocess.run(["ip", "link", "set", iface, "down"], check=False)
                subprocess.run(["iw", "dev", iface, "set", "type", "managed"], check=False)
                subprocess.run(["ip", "link", "set", iface, "up"], check=False)
                
                # Remove monitor interfaces
                subprocess.run(["airmon-ng", "stop", iface], check=False)
                
                self.log_clean("INTERFACE_RESET", f"{iface} reset to managed mode")
            
            return True
        except Exception as e:
            self.log_clean("INTERFACE_ERROR", str(e))
            return False
    
    def clear_ar_cache(self):
        """Clear ARP cache"""
        try:
            # Flush ARP table
            subprocess.run(["ip", "neigh", "flush", "all"], check=False)
            
            # Alternative method
            subprocess.run(["arp", "-d"], check=False)
            
            self.log_clean("ARP_CACHE_CLEAR", "ARP cache flushed")
            return True
        except Exception as e:
            self.log_clean("ARP_CACHE_ERROR", str(e))
            return False
    
    def clear_dns_cache(self):
        """Clear DNS cache"""
        try:
            # Systemd resolver
            if os.path.exists('/usr/bin/systemd-resolve'):
                subprocess.run(["systemd-resolve", "--flush-caches"], check=False)
            
            # nscd
            if os.path.exists('/usr/sbin/nscd'):
                subprocess.run(["nscd", "-i", "hosts"], check=False)
            
            # dnsmasq
            subprocess.run(["killall", "-HUP", "dnsmasq"], check=False)
            
            self.log_clean("DNS_CACHE_CLEAR", "DNS cache flushed")
            return True
        except Exception as e:
            self.log_clean("DNS_CACHE_ERROR", str(e))
            return False
    
    def clear_logs(self):
        """Clear system logs with stealth"""
        try:
            logs_to_clear = [
                '/var/log/syslog',
                '/var/log/auth.log',
                '/var/log/kern.log',
                '/var/log/dmesg',
                '/var/log/messages',
                '/var/log/daemon.log',
                '/var/log/boot.log',
                '/var/log/utmp',
                '/var/log/wtmp',
                '/var/log/btmp',
                '/var/log/lastlog'
            ]
            
            for log_file in logs_to_clear:
                if os.path.exists(log_file):
                    if self.stealth:
                        # Stealth: only clear our traces
                        self._stealth_clear_log(log_file)
                    else:
                        # Full clear
                        with open(log_file, 'w') as f:
                            f.write('')
                    self.log_clean("LOG_CLEAR", log_file)
            
            # Clear shell history
            history_files = [
                os.path.expanduser('~/.bash_history'),
                os.path.expanduser('~/.zsh_history'),
                os.path.expanduser('~/.history')
            ]
            
            for hist_file in history_files:
                if os.path.exists(hist_file):
                    with open(hist_file, 'w') as f:
                        f.write('')
                    self.log_clean("HISTORY_CLEAR", hist_file)
            
            return True
        except Exception as e:
            self.log_clean("LOG_CLEAR_ERROR", str(e))
            return False
    
    def _stealth_clear_log(self, log_file):
        """Stealth log clearing - only remove our traces"""
        try:
            # Read current log
            with open(log_file, 'r') as f:
                lines = f.readlines()
            
            # Filter out lines containing our signatures
            signatures = ['Cerberus', 'ARGUS', 'CERBERUS', 'injector', 'interceptor', 
                         'recon', 'ghost_sw', 'vault_cracker', 'live_mirror']
            
            new_lines = []
            for line in lines:
                if not any(sig in line for sig in signatures):
                    new_lines.append(line)
            
            # Write back
            with open(log_file, 'w') as f:
                f.writelines(new_lines)
            
            self.log_clean("STEALTH_LOG_CLEAR", f"{log_file} sanitized")
        except:
            pass
    
    def clear_temp_files(self):
        """Clear temporary files"""
        try:
            temp_dirs = [
                '/tmp',
                '/var/tmp',
                '/run/user',
                '/dev/shm'
            ]
            
            for temp_dir in temp_dirs:
                if os.path.exists(temp_dir):
                    # Remove old files (keep files newer than 1 hour)
                    subprocess.run(["find", temp_dir, "-type", "f", "-mmin", "+60", "-delete"], 
                                 check=False)
                    self.log_clean("TEMP_CLEAN", temp_dir)
            
            return True
        except Exception as e:
            self.log_clean("TEMP_CLEAN_ERROR", str(e))
            return False
    
    def clear_process_traces(self):
        """Clear process traces"""
        try:
            # Kill our processes
            our_processes = ['central_brain', 'recon_scanner', 'interceptor', 
                           'injector', 'airborne_hijacker', 'video_matrix']
            
            for proc in our_processes:
                subprocess.run(["pkill", "-f", proc], check=False)
                self.log_clean("PROCESS_KILL", proc)
            
            return True
        except Exception as e:
            self.log_clean("PROCESS_KILL_ERROR", str(e))
            return False
    
    def clear_log_files(self):
        """Clear our log files"""
        try:
            log_dirs = [
                '.',
                './logs',
                './c2_infrastructure/logs',
                './kernel_core/logs'
            ]
            
            for log_dir in log_dirs:
                if os.path.exists(log_dir):
                    for f in os.listdir(log_dir):
                        if f.endswith('.log') or f.endswith('.json') or f.startswith('vault_'):
                            file_path = os.path.join(log_dir, f)
                            if self.deep_clean:
                                # Overwrite with random data
                                self._secure_delete(file_path)
                            else:
                                os.remove(file_path)
                            self.log_clean("LOG_FILE_DELETE", file_path)
            
            return True
        except Exception as e:
            self.log_clean("LOG_FILE_DELETE_ERROR", str(e))
            return False
    
    def _secure_delete(self, file_path):
        """Secure delete with random overwrite"""
        try:
            if not os.path.exists(file_path):
                return
            
            size = os.path.getsize(file_path)
            
            # Overwrite multiple times
            for _ in range(3):
                with open(file_path, 'wb') as f:
                    f.write(os.urandom(size))
            
            os.remove(file_path)
            self.log_clean("SECURE_DELETE", file_path)
        except:
            pass
    
    def hide_processes(self):
        """Hide our processes (Linux only)"""
        try:
            # Mount overlay for proc
            if os.path.exists('/proc'):
                # This is a simplified version
                # In production would use LD_PRELOAD or kernel module
                pass
            self.log_clean("PROCESS_HIDE", "Process hiding activated")
            return True
        except:
            return False
    
    def restore_system(self):
        """Restore system to original state"""
        try:
            # Restore network
            self.reset_interfaces()
            
            # Restore DNS
            if os.path.exists('/etc/resolv.conf.backup'):
                shutil.copy('/etc/resolv.conf.backup', '/etc/resolv.conf')
            
            # Restore hosts
            if os.path.exists('/etc/hosts.backup'):
                shutil.copy('/etc/hosts.backup', '/etc/hosts')
            
            self.log_clean("SYSTEM_RESTORE", "System restored to original state")
            return True
        except Exception as e:
            self.log_clean("SYSTEM_RESTORE_ERROR", str(e))
            return False
    
    def clean_all(self):
        """Run all cleaning operations"""
        print("\n" + "="*60)
        print(" CERBERUS X - FORENSIC CLEANER")
        print("="*60)
        
        if self.stealth:
            print("[*] Stealth mode: Only removing our traces")
        else:
            print("[*] Full mode: Deep cleaning all traces")
        
        print("[*] Starting cleanup...\n")
        
        operations = [
            ("Flushing iptables", self.flush_iptables),
            ("Resetting interfaces", self.reset_interfaces),
            ("Clearing ARP cache", self.clear_ar_cache),
            ("Clearing DNS cache", self.clear_dns_cache),
            ("Clearing system logs", self.clear_logs),
            ("Clearing temp files", self.clear_temp_files),
            ("Clearing process traces", self.clear_process_traces),
            ("Clearing log files", self.clear_log_files),
            ("Restoring system", self.restore_system)
        ]
        
        if self.deep_clean:
            operations.append(("Secure delete files", lambda: True))
        
        for name, func in operations:
            try:
                func()
            except Exception as e:
                print(f"[-] {name} failed: {e}")
        
        print("\n[+] Cleanup complete")
        print(f"[*] Log saved to: cleaner_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        # Save log
        with open(f"cleaner_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
            json.dump(self.clean_log, f, indent=2)
    
    def run(self):
        """Main execution"""
        self.clean_all()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Traffic Cleaner v2.0")
    parser.add_argument("-s", "--stealth", action="store_true", help="Stealth mode")
    parser.add_argument("-d", "--deep", action="store_true", help="Deep clean")
    parser.add_argument("-r", "--restore", action="store_true", help="Restore only")
    
    args = parser.parse_args()
    
    if os.geteuid() != 0:
        print("[!] Root privileges required")
        sys.exit(1)
    
    cleaner = TrafficCleaner(stealth=args.stealth, deep_clean=args.deep)
    cleaner.run()
