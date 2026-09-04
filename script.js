const API_URL = "https://ai-cuts.onrender.com";

const btn = document.querySelector("#generate");
const status = document.querySelector("#status");
const results = document.querySelector("#results");
const videoInput = document.querySelector("#video");
const amountInput = document.querySelector("#amount");

let timerInterval = null;
let pollInterval = null;
let startTime = 0;

function elapsed() {
  const s = Math.floor((Date.now() - startTime) / 1000);
  const m = Math.floor(s / 60);
  const sec = s % 60;
  return `${String(m).padStart(2,"0")}:${String(sec).padStart(2,"0")}`;
}

function setStatus(message) {
  status.innerHTML = `<div>${message} <strong>⏱️ ${elapsed()}</strong></div><div class="progress"><span></span></div>`;
}

function esc(s) {
  return String(s ?? "")
    .replaceAll("&","&amp;")
    .replaceAll("<","&lt;")
    .replaceAll(">","&gt;")
    .replaceAll('"',"&quot;");
}

function resetTimers() {
  clearInterval(timerInterval);
  clearInterval(pollInterval);
}

btn.addEventListener("click", async () => {
  const video = videoInput.files[0];
  const amount = Number(amountInput.value);

  if (!video) {
    status.textContent = "❌ Selecione um vídeo primeiro.";
    return;
  }

  resetTimers();
  btn.disabled = true;
  results.innerHTML = "";
  startTime = Date.now();

  timerInterval = setInterval(() => {
    if (status.textContent) {
      const strong = status.querySelector("strong");
      if (strong) strong.textContent = `⏱️ ${elapsed()}`;
    }
  }, 1000);

  setStatus("📤 Enviando vídeo...");

  try {
    const form = new FormData();
    form.append("video", video);
    form.append("amount", String(amount));

    const r = await fetch(`${API_URL}/jobs/upload`, {
      method: "POST",
      body: form
    });

    if (!r.ok) {
      const body = await r.text();
      throw new Error(body || `HTTP ${r.status}`);
    }

    const job = await r.json();
    setStatus("🎬 Vídeo recebido. Processando...");

    pollInterval = setInterval(async () => {
      try {
        const x = await fetch(`${API_URL}/jobs/${job.id}`);
        if (!x.ok) throw new Error(`HTTP ${x.status}`);

        const d = await x.json();
        setStatus(`⚙️ ${esc(d.message || "Processando...")}`);

        if (d.status === "done") {
          resetTimers();
          status.innerHTML = `✅ Cortes prontos! <strong>⏱️ ${elapsed()}</strong>`;
          results.innerHTML = (d.clips || []).map((c,i) => `
            <div class="clip">
              <h3>🎬 Corte ${i+1}: ${esc(c.title || "Corte")}</h3>
              <p>Score viral: <strong>${c.viral_score ?? "-"}/100</strong></p>
              <p>${esc(c.reason || "")}</p>
              <a href="${esc(c.url)}" target="_blank" rel="noopener">▶️ Abrir corte</a>
            </div>
          `).join("") || "<p>Nenhum corte foi gerado.</p>";
          btn.disabled = false;
        }

        if (d.status === "error") {
          resetTimers();
          status.innerHTML = `❌ Erro: ${esc(d.message || "Erro desconhecido.")}`;
          btn.disabled = false;
        }
      } catch (err) {
        resetTimers();
        status.textContent = `❌ Erro ao consultar servidor: ${err.message}`;
        btn.disabled = false;
      }
    }, 2500);

  } catch (err) {
    resetTimers();
    status.textContent = `❌ ${err.message}`;
    btn.disabled = false;
  }
});
