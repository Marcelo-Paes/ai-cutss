import subprocess
from pathlib import Path
def download_video(url,folder):
 out=folder/"source.%(ext)s";subprocess.run(["yt-dlp","--no-playlist","-f","bv*[height<=1080]+ba/b[height<=1080]","--merge-output-format","mp4","-o",str(out),url],check=True)
 mp4=folder/"source.mp4"
 if mp4.exists(): return mp4
 c=list(folder.glob("source.*"))
 if not c: raise RuntimeError("Vídeo não foi baixado.")
 return c[0]
