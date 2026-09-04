import os
import uuid
import asyncio
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from downloader import download_video
from transcriber import transcribe
from analyzer import select_clips
from clipper import render_clip


BASE = Path(__file__).parent

DATA = Path(
    os.getenv("WORK_DIR", str(BASE / "data"))
)

DATA.mkdir(parents=True, exist_ok=True)


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(
    "/files",
    StaticFiles(directory=str(DATA)),
    name="files"
)


jobs = {}


@app.get("/")
def root():
    return {
        "ok": True,
        "service": "AI Cuts"
    }


@app.post("/jobs/upload")
async def create_upload(
    video: UploadFile = File(...),
    amount: int = Form(10)
):

    if amount not in [5, 10, 30]:
        raise HTTPException(
            400,
            "amount deve ser 5, 10 ou 30"
        )

    if not video.filename:
        raise HTTPException(
            400,
            "Nenhum vídeo enviado."
        )

    extension = Path(video.filename).suffix.lower()

    allowed = [
        ".mp4",
        ".mov",
        ".webm",
        ".mkv",
        ".avi"
    ]

    if extension not in allowed:
        raise HTTPException(
            400,
            "Formato de vídeo não suportado."
        )

    job_id = str(uuid.uuid4())

    folder = DATA / job_id
    folder.mkdir(parents=True, exist_ok=True)

    source = folder / f"source{extension}"

    with open(source, "wb") as f:
        while True:
            chunk = await video.read(1024 * 1024)

            if not chunk:
                break

            f.write(chunk)

    jobs[job_id] = {
        "status": "processing",
        "message": "Vídeo recebido. Iniciando..."
    }

    asyncio.create_task(
        process_video(
            job_id,
            source,
            amount
        )
    )

    return {
        "id": job_id
    }


@app.get("/jobs/{job_id}")
def get_job(job_id: str):

    if job_id not in jobs:
        raise HTTPException(
            404,
            "job não encontrado"
        )

    return jobs[job_id]


async def process_video(
    job_id,
    video,
    amount
):

    try:

        folder = DATA / job_id

        jobs[job_id]["message"] = \
            "🎙️ Transcrevendo vídeo..."

        segments = await asyncio.to_thread(
            transcribe,
            video
        )

        jobs[job_id]["message"] = \
            "🧠 IA escolhendo os melhores momentos..."

        clips = await asyncio.to_thread(
            select_clips,
            segments,
            amount
        )

        output = []

        for index, clip in enumerate(clips):

            jobs[job_id]["message"] = (
                f"✂️ Gerando corte "
                f"{index + 1}/{len(clips)}..."
            )

            name = f"clip_{index + 1:02d}.mp4"

            await asyncio.to_thread(
                render_clip,
                video,
                clip["start"],
                clip["end"],
                folder / name
            )

            output.append({
                **clip,
                "url": f"/files/{job_id}/{name}"
            })

        base = os.getenv(
            "PUBLIC_API_URL",
            ""
        ).rstrip("/")

        if base:

            for clip in output:

                clip["url"] = (
                    base + clip["url"]
                )

        jobs[job_id] = {
            "status": "done",
            "message": "Concluído!",
            "clips": output
        }

    except Exception as error:

        jobs[job_id] = {
            "status": "error",
            "message": str(error)
        }
