import { fetchStatus, createProCheckout } from "./api.js";

export async function refreshStatus() {
    const pill = document.getElementById("statusPill");

    try {
        const data = await fetchStatus();

        if (data.is_pro) {
            pill.classList.add("is-pro");
            pill.innerHTML = `💎 PRO · ${data.remaining}/${data.pro_daily_limit} descargas hoy · hasta ${data.pro_until}`;
        } else {
            pill.classList.remove("is-pro");
            pill.innerHTML = `🆓 ${data.remaining}/${data.daily_limit} descargas hoy · <span id="proPillBtn" style="text-decoration:underline;cursor:pointer;">Hazte PRO</span>`;

            const link = document.getElementById("proPillBtn");
            if (link) link.addEventListener("click", goProFromPill);
        }
    } catch (e) {
        pill.innerHTML = "VideoHub";
    }
}

async function goProFromPill() {
    try {
        const { checkout_url } = await createProCheckout();
        window.location.href = checkout_url;
    } catch (e) {
        alert(e.message);
    }
}

refreshStatus();
