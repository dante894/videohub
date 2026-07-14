import { refreshStatus } from "./status.js";

const socket = io();

socket.on("progress", (data) => {
    const percent = parseFloat(data.percent) || 0;

    const bar = document.getElementById("progressBar");
    bar.style.width = percent + "%";

    document.getElementById("downloadSpeed").innerHTML = "🚀 " + data.speed;
    document.getElementById("downloadEta").innerHTML = "⏳ " + data.eta;
});

socket.on("download_complete", (data) => {
    document.getElementById("progressWrap").style.display = "none";

    document.getElementById("limitBanner").innerHTML = `
        <div class="vh-banner vh-banner-success">
            <span>✅ Listo: ${data.filename}</span>
            <a href="${data.download_url}" class="vh-download-link">Descargar archivo</a>
        </div>
    `;

    refreshStatus();
});

socket.on("download_error", (data) => {
    document.getElementById("progressWrap").style.display = "none";
    alert("❌ Error al descargar: " + data.error);
});

socket.on("pro_activated", () => {
    refreshStatus();
    document.getElementById("limitBanner").innerHTML = `
        <div class="vh-banner vh-banner-success">
            <span>🎉 ¡Listo! Ya sos usuario PRO.</span>
        </div>
    `;
});
