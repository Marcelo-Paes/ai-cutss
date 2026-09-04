const API_URL = "https://ai-cuts.onrender.com";

const btn = document.querySelector("#generate");
const status = document.querySelector("#status");
const results = document.querySelector("#results");

let timerInterval = null;
let startTime = null;

btn.onclick = async () => {
  const url = document.querySelector("#url").value.trim();
  const amount = +document.querySelector("#amount").value;

  if (!url) {
    status.textContent = "Cole um link do vídeo.";
    return;
  }

  btn.disabled = true;
  results.innerHTML = "";

  // Inicia timer
  startTime = Date.now();

  clearInterval(timerInterval);

  timerInterval = setInterval(() => {
    const seconds = Math.floor((Date.now() - startTime) / 1000);
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;

    status.textContent =
      `⚙️ Processando... ⏱️ ${String(minutes).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
  }, 1000);

  status.textContent = "📥 Iniciando...";

  try {
    const r = await fetch(API_URL + "/jobs", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        url,
        amount
      })
    });

    if (!r.ok) {
      throw new Error("Não foi possível iniciar o processamento.");
    }

    const job = await r.json();

    const timer = setInterval(async () => {
      try {
        const x = await fetch(API_URL + "/jobs/" + job.id);

        if (!x.ok) {
          throw new Error("Servidor não respondeu.");
        }

        const d = await x.json();

        // Mostra a mensagem do backend
        const seconds = Math.floor((Date.now() - startTime) / 1000);
        const minutes = Math.floor(seconds / 60);
        const secs = seconds % 60;

        const tempo =
          `${String(minutes).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;

        status.textContent =
          `⚙️ ${d.message || "Processando..."} ⏱️ ${tempo}`;

        // Terminou
        if (d.status === "done") {
          clearInterval(timer);
          clearInterval(timerInterval);

          status.textContent = `✅ Cortes prontos! ⏱️ ${tempo}`;

          results.innerHTML = (d.clips || [])
            .map((c, i) => `
              <div class="clip">
                <h3>🎬 Corte ${i + 1}: ${esc(c.title || "Corte")}</h3>

                <p>
                  Score viral:
                  <strong>${c.viral_score ?? "-"}/100</strong>
                </p>

                <p>${esc(c.reason || "")}</p>

                <a href="${c.url}" target="_blank">
                  ▶️ Abrir corte
                </a>
              </div>
            `)
            .join("");

          btn.disabled = false;
        }

        // Deu erro
        if (d.status === "error") {
          clearInterval(timer);
          clearInterval(timerInterval);

          status.textContent =
            "❌ Erro: " + (d.message || "Erro desconhecido.");

          btn.disabled = false;
        }

      } catch (e) {
        clearInterval(timer);
        clearInterval(timerInterval);

        status.textContent =
          "❌ Erro ao consultar servidor.";

        btn.disabled = false;
      }

    }, 2500);

  } catch (e) {
    clearInterval(timerInterval);

    status.textContent = "❌ " + e.message;

    btn.disabled = false;
  }
};

function esc(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}
