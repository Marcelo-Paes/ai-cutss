import os,json
def select_clips(segments,amount):
 key=os.getenv("OPENAI_API_KEY")
 if key:
  try:
   from openai import OpenAI
   client=OpenAI(api_key=key);txt="\n".join(f"[{s['start']:.1f}-{s['end']:.1f}] {s['text']}" for s in segments)
   p=f'''Escolha os {amount} melhores trechos para Shorts/Reels/TikTok. Priorize hook, curiosidade, emoção, surpresa, utilidade, humor e retenção. Trechos de 15-90s. Responda SOMENTE JSON: {{"clips":[{{"start":0,"end":30,"title":"...","reason":"...","viral_score":90}}]}}\nTRANSCRIÇÃO:\n{txt[:60000]}'''
   d=json.loads(client.responses.create(model=os.getenv("OPENAI_MODEL","gpt-5-mini"),input=p).output_text)
   return sorted([{"start":float(c["start"]),"end":min(float(c["end"]),float(c["start"])+90),"title":c.get("title","Corte"),"reason":c.get("reason",""),"viral_score":int(c.get("viral_score",0))} for c in d.get("clips",[])],key=lambda x:x["viral_score"],reverse=True)[:amount]
  except Exception: pass
 out=[];i=0
 while i<len(segments) and len(out)<amount:
  st=segments[i]["start"];en=st+45;j=i
  while j<len(segments) and segments[j]["start"]<en:j+=1
  if j>i:out.append({"start":st,"end":min(en,segments[j-1]["end"]),"title":"Corte automático","reason":"Trecho selecionado automaticamente.","viral_score":max(1,100-len(out)*5)})
  i=max(j,i+1)
 return out
