import subprocess
from pathlib import Path

def download_video(url, folder):
    out = folder / "source.%(ext)s"

    try:
        subprocess.run(
            [
                "yt-dlp",
                "--no-playlist",
                "-f",
                "bv*[height<=1080]+ba/b[height<=1080]",
                "--merge-output-format",
                "mp4",
                "-o",
                str(out),
                url,
            ],
            check=True,
        )
    except subprocess.CalledProcessError:
        raise RuntimeError(
            "O YouTube bloqueou o download deste vídeo. "
            "Para o teste, envie o vídeo diretamente ao AI Cuts."
        )

    mp4 = folder / "source.mp4"

    if mp4.exists():
        return mp4

    files = list(folder.glob("source.*"))

    if not files:
        raise RuntimeError("Vídeo não foi baixado.")

    return files[0]
