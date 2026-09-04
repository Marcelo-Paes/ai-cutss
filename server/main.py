import os,uuid,asyncio
from pathlib import Path
from fastapi import FastAPI,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel,HttpUrl
from downloader import download_video
from transcriber import transcribe
from analyzer import select_clips
from clipper import render_clip
BASE=Path(__file__).parent
DATA=Path(os.getenv("WORK_DIR",str(BASE/"data")));DATA.mkdir(parents=True,exist_ok=True)
app=FastAPI();app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_methods=["*"],allow_headers=["*"]);app.mount("/files",StaticFiles(directory=str(DATA)),name="files")
jobs={}
class Req(BaseModel): url:HttpUrl; amount:int=10
@app.get("/")
def root(): return {"ok":True,"service":"AI Cuts"}
@app.post("/jobs")
async def create(r:Req):
 if r.amount not in [5,10,30]: raise HTTPException(400,"amount deve ser 5, 10 ou 30")
 i=str(uuid.uuid4());jobs[i]={"status":"processing","message":"Iniciando..."};asyncio.create_task(process(i,str(r.url),r.amount));return {"id":i}
@app.get("/jobs/{i}")
def get(i:str):
 if i not in jobs: raise HTTPException(404,"job não encontrado")
 return jobs[i]
async def process(i,url,amount):
 try:
  folder=DATA/i;folder.mkdir()
  jobs[i]["message"]="Baixando vídeo...";video=await asyncio.to_thread(download_video,url,folder)
  jobs[i]["message"]="Transcrevendo...";segments=await asyncio.to_thread(transcribe,video)
  jobs[i]["message"]="IA escolhendo os melhores momentos...";clips=await asyncio.to_thread(select_clips,segments,amount)
  out=[]
  for n,c in enumerate(clips):
   jobs[i]["message"]=f"Gerando corte {n+1}/{len(clips)}...";name=f"clip_{n+1:02d}.mp4";await asyncio.to_thread(render_clip,video,c["start"],c["end"],folder/name);out.append({**c,"url":f"/files/{i}/{name}"})
  base=os.getenv("PUBLIC_API_URL","").rstrip("/")
  if base:
   for c in out:c["url"]=base+c["url"]
  jobs[i]={"status":"done","message":"Concluído","clips":out}
 except Exception as e: jobs[i]={"status":"error","message":str(e)}
