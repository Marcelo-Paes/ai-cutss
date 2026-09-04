import subprocess
def render_clip(video,start,end,out):
 subprocess.run(["ffmpeg","-y","-ss",str(start),"-i",str(video),"-t",str(max(1,end-start)),"-vf","crop=ih*9/16:ih,scale=1080:1920","-c:v","libx264","-preset","veryfast","-crf","23","-c:a","aac","-movflags","+faststart",str(out)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
