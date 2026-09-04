# AI Cuts - MVP Upload

Fluxo: upload de vídeo -> Whisper -> análise -> FFmpeg -> cortes 9:16.

Para o teste, envie um MP4 curto. O endpoint de YouTube permanece disponível, mas pode ser bloqueado pelo próprio YouTube.

Render:
- Root Directory: `server`
- Language: Docker
- `OPENAI_API_KEY`: sua chave
- `OPENAI_MODEL`: `gpt-5-mini`
- `PUBLIC_API_URL`: `https://ai-cuts.onrender.com`
- `WHISPER_MODEL`: `tiny` para o plano gratuito/teste

Frontend:
- publique `index.html`, `style.css` e `script.js` na Netlify.
