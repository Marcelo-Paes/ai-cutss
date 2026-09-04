import subprocess

def render_clip(video, start, end, out):
    duration = max(1, float(end) - float(start))
    vf = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-ss", str(max(0, float(start))),
            "-i", str(video),
            "-t", str(duration),
            "-vf", vf,
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "23",
            "-c:a", "aac",
            "-movflags", "+faststart",
            str(out),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )
