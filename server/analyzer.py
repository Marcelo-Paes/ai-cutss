import os, json

def select_clips(segments, amount):
    key = os.getenv("OPENAI_API_KEY")
    if key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=key)
            txt = "\n".join(
                f"[{s['start']:.1f}-{s['end']:.1f}] {s['text']}"
                for s in segments
            )
            prompt = f"""Escolha os {amount} melhores trechos para Shorts/Reels/TikTok.
Priorize hook, curiosidade, emoção, surpresa, utilidade, humor e retenção.
Cada trecho deve ter entre 15 e 90 segundos.
Responda SOMENTE JSON neste formato:
{{"clips":[{{"start":0,"end":30,"title":"...","reason":"...","viral_score":90}}]}}
TRANSCRIÇÃO:
{txt[:60000]}"""
            response = client.responses.create(
                model=os.getenv("OPENAI_MODEL", "gpt-5-mini"),
                input=prompt,
            )
            data = json.loads(response.output_text)
            result = []
            for c in data.get("clips", []):
                start = float(c["start"])
                end = min(float(c["end"]), start + 90)
                if end > start:
                    result.append({
                        "start": start,
                        "end": end,
                        "title": c.get("title", "Corte"),
                        "reason": c.get("reason", ""),
                        "viral_score": int(c.get("viral_score", 0)),
                    })
            if result:
                return sorted(
                    result,
                    key=lambda x: x["viral_score"],
                    reverse=True
                )[:amount]
        except Exception:
            pass

    # Fallback: blocos de 45s
    out = []
    i = 0
    while i < len(segments) and len(out) < amount:
        st = segments[i]["start"]
        en = st + 45
        j = i
        while j < len(segments) and segments[j]["start"] < en:
            j += 1
        if j > i:
            out.append({
                "start": st,
                "end": min(en, segments[j-1]["end"]),
                "title": "Corte automático",
                "reason": "Trecho selecionado automaticamente.",
                "viral_score": max(1, 100 - len(out) * 5),
            })
        i = max(j, i + 1)
    return out
