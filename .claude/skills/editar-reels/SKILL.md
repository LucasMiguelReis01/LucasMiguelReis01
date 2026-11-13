---
name: editar-reels
description: Editar vídeos curtos (Reels, TikTok, Shorts) no estilo do Lucas. Use quando ele pedir para editar um vídeo, cortar pausas, colocar legenda animada, fazer um Reels ou mudar o estilo de edição.
---

# Editar Reels no estilo do Lucas

Ferramenta: `editor-reels/reels.py` (ffmpeg + Whisper local). Primeira vez na sessão: `bash editor-reels/baixar_modelo.sh`.
A transcrição da ElevenLabs NÃO funciona (a chave não tem a permissão speech_to_text). Use o Whisper local.
A ElevenLabs serve para narração (TTS) e efeitos sonoros.

## Estilo padrão (aprovado em 2026-11-13)
- Vertical 1080x1920, 30 fps, cortes secos removendo pausas > 0,35 s (respiro de 0,08 s).
- Zoom alternado de 1,15x a cada corte.
- Legenda: CAIXA ALTA, Montserrat Black 112, branca com contorno preto grosso, 2-3 palavras (até 16 caracteres),
  palavra falada em amarelo (#FFE500) a 112%, entrada com "pop". Fica a ~560 px do rodapé, acima da interface do Instagram.
- Título/gancho opcional: Anton 128, caixa preta no topo, 3 s.
- Áudio a -14 LUFS. Música de fundo a 22% com ducking.

## Como trabalhar
1. Rode o editor e confira quadros (`ffmpeg ... select=eq(n\,N),tile`) antes de entregar.
2. Mande o MP4 final para o Lucas com SendUserFile.
3. Quando ele aprovar ou pedir um ajuste de estilo, atualize `ESTILO` em `reels.py` E esta seção, registrando a preferência.

## Preferências do Lucas
- Fala português; responda em português.
- Não paga ferramentas de edição. Tudo precisa ser gratuito e local.
