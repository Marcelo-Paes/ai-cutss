from faster_whisper import WhisperModel
_model=None
def transcribe(video):
 global _model
 if _model is None:_model=WhisperModel("small",device="cpu",compute_type="int8")
 segs,_=_model.transcribe(str(video),vad_filter=True)
 return [{"start":float(s.start),"end":float(s.end),"text":s.text.strip()} for s in segs]
