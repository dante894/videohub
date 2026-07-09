import { analyzeVideo } from "./api.js";
import { showVideoInfo } from "./ui.js";

export async function analyze() {

    const url = document
        .getElementById("videoUrl")
        .value
        .trim();

    if (url === "") {
        alert("Ingrese una URL");
        return;
    }

    try {
        const data = await analyzeVideo(url);
        showVideoInfo(data, url);
    } catch (e) {
        alert(e.message);
    }
}

document
    .getElementById("analyzeBtn")
    .addEventListener("click", analyze);
