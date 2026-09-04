const API_URL="https://ai-cuts.onrender.com";
const btn=document.querySelector("#generate"),status=document.querySelector("#status"),results=document.querySelector("#results");

btn.onclick=async()=>{
  const file=document.querySelector("#video").files[0],amount=+document.querySelector("#amount").value;
  if(!file){status.textContent="Escolha um vídeo.";return}
  btn.disabled=true;results.innerHTML="";status.textContent="Enviando vídeo...";
  try{
    const form=new FormData();form.append("video",file);form.append("amount",amount);
    const r=await fetch(API_URL+"/jobs/upload",{method:"POST",body:form});
    if(!r.ok){const t=await r.text();throw Error(t||"Não foi possível enviar o vídeo.")}
    const job=await r.json();
    const timer=setInterval(async()=>{
      try{
        const x=await fetch(API_URL+"/jobs/"+job.id);
        if(!x.ok)throw Error("Falha ao consultar o processamento.");
        const d=await x.json();
        status.textContent=d.message||"Processando...";
        if(d.status==="done"){
          clearInterval(timer);status.textContent="Cortes prontos!";
          results.innerHTML=(d.clips||[]).map((c,i)=>`<div class="clip"><h3>🎬 Corte ${i+1}: ${esc(c.title||"Corte")}</h3><p>Score viral: ${c.viral_score??"-"}/100</p><p>${esc(c.reason||"")}</p><a href="${c.url}" target="_blank" rel="noopener">Abrir corte</a></div>`).join("");
          btn.disabled=false;
        }
        if(d.status==="error"){
          clearInterval(timer);status.textContent="Erro: "+d.message;btn.disabled=false;
        }
      }catch(e){clearInterval(timer);status.textContent="Erro ao consultar servidor: "+e.message;btn.disabled=false}
    },2500)
  }catch(e){status.textContent="Erro: "+e.message;btn.disabled=false}
};
function esc(s){return String(s).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;")}
