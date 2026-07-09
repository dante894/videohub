import { formatTime } from "./utils.js";
import { enqueueDownload, createProCheckout } from "./api.js";
import { refreshStatus } from "./status.js";

const QUALITIES = [
    { fmt: "1080", label: "1080p HD" },
    { fmt: "720", label: "720p" },
    { fmt: "480", label: "480p" },
    { fmt: "360", label: "360p" },
    { fmt: "audio", label: "🎵 Solo audio (MP3)" },
];

export function showVideoInfo(data, url) {
    const result = document.getElementById("result");
    result.style.display = "block";

    const chips = QUALITIES.map(q =>
        `<button class="vh-chip" data-fmt="${q.fmt}">${q.label}</button>`
    ).join("");

    result.innerHTML = `
    <div class="vh-result-card">
        <div class="vh-filmstrip"></div>
        <div class="vh-thumb-wrap">
            <img src="${data.thumbnail}">
        </div>
        <div class="vh-result-body">
            <h3>${data.title}</h3>
            <div class="vh-result-meta">
                <span>👤 ${data.uploader}</span>
                <span>⏱ ${formatTime(data.duration)}</span>
            </div>
            <div class="vh-quality-label">Elegí la calidad (máximo 1080p)</div>
            <div class="vh-quality-grid">${chips}</div>
        </div>
    </div>
    `;

    result.querySelectorAll(".vh-chip").forEach(btn => {
        btn.addEventListener("click", () => handleDownloadClick(btn, url));
    });
}

async function handleDownloadClick(btn, url) {
    const fmt = btn.dataset.fmt;
    const isAudio = fmt === "audio";

    btn.classList.add("is-loading");
    btn.disabled = true;

    document.getElementById("limitBanner").innerHTML = "";

    try {
        await enqueueDownload(url, fmt, isAudio);
        showProgress();
        refreshStatus();
    } catch (e) {
        if (e.limitReached) {
            showLimitBanner();
        } else {
            alert(e.message);
        }
    } finally {
        btn.classList.remove("is-loading");
        btn.disabled = false;
    }
}

function showProgress() {
    document.getElementById("progressWrap").style.display = "block";
}

export function showLimitBanner() {
    document.getElementById("limitBanner").innerHTML = `
        <div class="vh-banner vh-banner-warn">
            <span>🚫 Alcanzaste tu límite de descargas gratis de hoy.</span>
            <button id="proFromLimitBtn" class="vh-btn vh-btn-gold">Hazte PRO</button>
        </div>
    `;

    document.getElementById("proFromLimitBtn").addEventListener("click", goPro);
}

export async function goPro() {
    try {
        const { checkout_url } = await createProCheckout();
        window.location.href = checkout_url;
    } catch (e) {
        alert(e.message);
    }
}
