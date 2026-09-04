import os,uuid,asyncio,shutil
from pathlib import Path
from fastapi import FastAPI,HTTPException,UploadFile,File,Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel,HttpUrl
from downloader import download_video
from transcriber import transcribe
from analyzer import select_clips
from clipper import render_clip

BASE=Path(__file__).parent
DATA=Path(os.getenv("WORK_DIR",str(BASE/"data")));DATA.mkdir(parents=True,exist_ok=True)
app=FastAPI()
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_methods=["*"],allow_headers=["*"])
app.mount("/files",StaticFiles(directory=str(DATA)),name="files")
jobs={}

class Req(BaseModel):
    url:HttpUrl
    amount:int=10

@app.get("/")
def root():
    return {"ok":True,"service":"AI Cuts"}

def validate_amount(amount):
    if amount not in [5,10,30]:
        raise HTTPException(400,"amount deve ser 5, 10 ou 30")

@app.post("/jobs")
async def create(r:Req):
    validate_amount(r.amount)
    i=str(uuid.uuid4());jobs[i]={"status":"processing","message":"Iniciando..."}
    asyncio.create_task(process_url(i,str(r.url),r.amount))
    return {"id":i}

@app.post("/jobs/upload")
async def create_upload(video:UploadFile=File(...),amount:int=Form(10)):
    validate_amount(amount)
    if not video.filename:
        raise HTTPException(400,"Arquivo de vídeo inválido.")
    allowed={".mp4",".mov",".m4v",".webm",".mkv",".avi",".mpeg",".mpg"}
    ext=Path(video.filename).suffix.lower()
    if ext not in allowed:
        raise HTTPException(400,"Formato não suportado. Envie MP4, MOV, WebM ou outro formato de vídeo comum.")
    i=str(uuid.uuid4());folder=DATA/i;folder.mkdir()
    source=folder/("source"+ext)
    try:
        with source.open("wb") as f:
            while True:
                chunk=await video.read(1024*1024)
                if not chunk: break
                f.write(chunk)
    finally:
        await video.close()
    jobs[i]={"status":"processing","message":"Vídeo recebido. Preparando..."}
    asyncio.create_task(process_file(i,source,amount))
    return {"id":i}

@app.get("/jobs/{i}")
def get(i:str):
    if i not in jobs: raise HTTPException(404,"job não encontrado")
    return jobs[i]

async def process_url(i,url,amount):
    try:
        folder=DATA/i;folder.mkdir()
        jobs[i]["message"]="Baixando vídeo..."
        video=await asyncio.to_thread(download_video,url,folder)
        await process_video(i,video,amount)
    except Exception as e:
        jobs[i]={"status":"error","message":str(e)}

async def process_file(i,video,amount):
    try:
        await process_video(i,video,amount)
    except Exception as e:
        jobs[i]={"status":"error","message":str(e)}

async def process_video(i,video,amount):
    jobs[i]["message"]="Transcrevendo..."
    segments=await asyncio.to_thread(transcribe,video)
    jobs[i]["message"]="IA escolhendo os melhores momentos..."
    clips=await asyncio.to_thread(select_clips,segments,amount)
    out=[]
    folder=video.parent
    for n,c in enumerate(clips):
        jobs[i]["message"]=f"Gerando corte {n+1}/{len(clips)}..."
        name=f"clip_{n+1:02d}.mp4"
        await asyncio.to_thread(render_clip,video,c["start"],c["end"],folder/name)
        out.append({**c,"url":f"/files/{i}/{name}"})
    base=os.getenv("PUBLIC_API_URL","").rstrip("/")
    if base:
        for c in out:c["url"]=base+c["url"]
    jobs[i]={"status":"done","message":"Concluído","clips":out}
