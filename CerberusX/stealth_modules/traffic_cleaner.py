import os

def clean():
    print("[*] Sanitizing environment...")
    os.system("iptables --flush")
    os.system("iptables -t nat --flush")
    os.system("echo 0 > /proc/sys/net/ipv4/ip_forward")
    os.system("ip neigh flush all")
    print("[+] Cerberus is now a ghost.")

if __name__ == "__main__":
    clean()