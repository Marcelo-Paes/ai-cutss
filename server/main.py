import os
import uuid
import asyncio
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl

from downloader import download_video
from transcriber import transcribe
from analyzer import select_clips
from clipper import render_clip

BASE = Path(__file__).parent
DATA = Path(os.getenv("WORK_DIR", str(BASE / "data")))
DATA.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="AI Cuts")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/files", StaticFiles(directory=str(DATA)), name="files")

jobs = {}


class UrlRequest(BaseModel):
    url: HttpUrl
    amount: int = 10


@app.get("/")
def root():
    return {"ok": True, "service": "AI Cuts"}


@app.post("/jobs/upload")
async def create_upload(video: UploadFile = File(...), amount: int = Form(10)):
    if amount not in (5, 10, 30):
        raise HTTPException(400, "amount deve ser 5, 10 ou 30")

    if not video.filename:
        raise HTTPException(400, "Nenhum vídeo enviado.")

    ext = Path(video.filename).suffix.lower()
    if ext not in {".mp4", ".mov", ".webm", ".mkv", ".avi"}:
        raise HTTPException(400, "Formato não suportado. Use MP4, MOV, WebM, MKV ou AVI.")

    job_id = str(uuid.uuid4())
    folder = DATA / job_id
    folder.mkdir(parents=True, exist_ok=True)
    source = folder / f"source{ext}"

    try:
        with source.open("wb") as f:
            while True:
                chunk = await video.read(1024 * 1024)
                if not chunk:
                    break
                f.write(chunk)
    finally:
        await video.close()

    jobs[job_id] = {"status": "processing", "message": "Vídeo recebido. Iniciando..."}

    asyncio.create_task(process_video(job_id, source, amount))
    return {"id": job_id}


@app.post("/jobs")
async def create_url(req: UrlRequest):
    if req.amount not in (5, 10, 30):
        raise HTTPException(400, "amount deve ser 5, 10 ou 30")

    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "processing", "message": "Iniciando..."}
    asyncio.create_task(process_url(job_id, str(req.url), req.amount))
    return {"id": job_id}


@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(404, "job não encontrado")
    return job


async def process_url(job_id, url, amount):
    try:
        folder = DATA / job_id
        jobs[job_id]["message"] = "📥 Baixando vídeo..."
        video = await asyncio.to_thread(download_video, url, folder)
        await finish_processing(job_id, video, amount)
    except Exception as e:
        jobs[job_id] = {"status": "error", "message": str(e)}


async def process_video(job_id, video, amount):
    try:
        await finish_processing(job_id, video, amount)
    except Exception as e:
        jobs[job_id] = {"status": "error", "message": str(e)}


async def finish_processing(job_id, video, amount):
    folder = DATA / job_id

    jobs[job_id]["message"] = "🎙️ Transcrevendo vídeo..."
    segments = await asyncio.to_thread(transcribe, video)

    if not segments:
        raise RuntimeError("Não foi possível encontrar fala no vídeo.")

    jobs[job_id]["message"] = "🧠 IA escolhendo os melhores momentos..."
    clips = await asyncio.to_thread(select_clips, segments, amount)

    if not clips:
        raise RuntimeError("A análise não encontrou trechos para cortar.")

    output = []
    for n, clip in enumerate(clips):
        jobs[job_id]["message"] = f"✂️ Gerando corte {n+1}/{len(clips)}..."
        name = f"clip_{n+1:02d}.mp4"
        await asyncio.to_thread(
            render_clip, video, clip["start"], clip["end"], folder / name
        )
        output.append({**clip, "url": f"/files/{job_id}/{name}"})

    base = os.getenv("PUBLIC_API_URL", "https://ai-cuts.onrender.com").rstrip("/")
    for clip in output:
        clip["url"] = base + clip["url"]

    jobs[job_id] = {"status": "done", "message": "Concluído", "clips": output}
