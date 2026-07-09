export async function analyzeVideo(url) {
    const response = await fetch("/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url })
    });

    if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.error || "Error analizando el video");
    }

    return await response.json();
}

export async function enqueueDownload(url, quality, audio) {
    const response = await fetch("/enqueue", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, quality, audio })
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        const error = new Error(data.error || "Error encolando la descarga");
        error.limitReached = !!data.limit_reached;
        throw error;
    }

    return data;
}

export async function fetchStatus() {
    const response = await fetch("/api/status");
    if (!response.ok) throw new Error("No se pudo obtener el estado");
    return await response.json();
}

export async function createProCheckout() {
    const response = await fetch("/api/pro/checkout", { method: "POST" });
    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        throw new Error(data.error || "No se pudo generar el link de pago");
    }

    return data;
}
