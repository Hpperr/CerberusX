#!/bin/bash
# CERBERUS X - SURGICAL DEPLOYMENT ENGINE
KALI_IP=$(hostname -I | awk '{print $1}')
GATEWAY_IP=$(ip route | grep default | awk '{print $3}')

echo "[*] Kali IP: $KALI_IP | Gateway: $GATEWAY_IP"

# Khởi động Backend
cd c2_infrastructure && node central_brain.js &
BACKEND_PID=$!
sleep 2

# Mở Dashboard
xdg-open dashboard_v3.html &

# Chạy Trinh sát
echo "[!] Awaiting target signatures on Dashboard..."
cd ../kernel_core && sudo python3 recon_scanner.py

trap "kill $BACKEND_PID; exit" INT