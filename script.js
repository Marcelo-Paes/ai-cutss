const API_URL = "https://ai-cuts.onrender.com";

const btn = document.querySelector("#generate");
const status = document.querySelector("#status");
const results = document.querySelector("#results");
const videoInput = document.querySelector("#video");
const amountInput = document.querySelector("#amount");

let timerInterval = null;
let startTime = null;

function formatTime() {
  const seconds = Math.floor((Date.now() - startTime) / 1000);
  const minutes = Math.floor(seconds / 60);
  const secs = seconds % 60;

  return `${String(minutes).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
}

btn.onclick = async () => {
  const video = videoInput.files[0];
  const amount = Number(amountInput.value);

  if (!video) {
    status.textContent = "❌ Selecione um vídeo primeiro.";
    return;
  }

  btn.disabled = true;
  results.innerHTML = "";

  startTime = Date.now();

  clearInterval(timerInterval);

  timerInterval = setInterval(() => {
    status.textContent = `⚙️ Processando... ⏱️ ${formatTime()}`;
  }, 1000);

  status.textContent = "📤 Enviando vídeo...";

  try {
    const formData = new FormData();

    formData.append("video", video);
    formData.append("amount", amount);

    const response = await fetch(API_URL + "/jobs/upload", {
      method: "POST",
      body: formData
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || "Não foi possível iniciar.");
    }

    const job = await response.json();

    const timer = setInterval(async () => {
      try {
        const response = await fetch(
          API_URL + "/jobs/" + job.id
        );

        if (!response.ok) {
          throw new Error("Servidor não respondeu.");
        }

        const data = await response.json();

        status.textContent =
          `⚙️ ${data.message || "Processando..."} ⏱️ ${formatTime()}`;

        if (data.status === "done") {
          clearInterval(timer);
          clearInterval(timerInterval);

          status.textContent =
            `✅ Cortes prontos! ⏱️ ${formatTime()}`;

          results.innerHTML = (data.clips || [])
            .map((clip, i) => `
              <div class="clip">
                <h3>
                  🎬 Corte ${i + 1}: ${esc(clip.title || "Corte")}
                </h3>

                <p>
                  Score viral:
                  <strong>${clip.viral_score ?? "-"}/100</strong>
                </p>

                <p>${esc(clip.reason || "")}</p>

                <a href="${clip.url}" target="_blank">
                  ▶️ Abrir corte
                </a>
              </div>
            `)
            .join("");

          btn.disabled = false;
        }

        if (data.status === "error") {
          clearInterval(timer);
          clearInterval(timerInterval);

          status.textContent =
            "❌ Erro: " + (data.message || "Erro desconhecido.");

          btn.disabled = false;
        }

      } catch (error) {
        clearInterval(timer);
        clearInterval(timerInterval);

        status.textContent =
          "❌ Erro ao consultar servidor.";

        btn.disabled = false;
      }

    }, 2500);

  } catch (error) {
    clearInterval(timerInterval);

    status.textContent =
      "❌ " + error.message;

    btn.disabled = false;
  }
};

function esc(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}
