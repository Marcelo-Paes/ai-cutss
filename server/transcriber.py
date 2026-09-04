import os
from faster_whisper import WhisperModel

_model = None

def transcribe(video):
    global _model
    if _model is None:
        model_name = os.getenv("WHISPER_MODEL", "tiny")
        _model = WhisperModel(model_name, device="cpu", compute_type="int8")
    segments, _ = _model.transcribe(str(video), vad_filter=True)
    return [
        {"start": float(s.start), "end": float(s.end), "text": s.text.strip()}
        for s in segments
        if s.text.strip()
    ]
