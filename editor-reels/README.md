# Editor automático de Reels

Pega um vídeo bruto (você falando para a câmera) e devolve um Reels editado, de graça, rodando local.

## O que ele faz

| Etapa | Resultado |
|---|---|
| Corta pausas | Remove silêncios maiores que 0,35 s (jump cuts) |
| Formato | 1080x1920 (9:16), 30 fps. Vídeo horizontal: corta o centro, ou usa fundo desfocado (`--layout blur`) |
| Zoom | Alterna zoom de 1,15x a cada corte (punch-in) |
| Legenda | Caixa alta, Montserrat Black, 2-3 palavras por vez, palavra falada em amarelo com "pop" |
| Título | Gancho no topo nos 3 primeiros segundos (`--titulo`) |
| Música | Fundo opcional (`--musica`), abaixa sozinha quando você fala |
| Áudio | Normalizado a -14 LUFS (volume padrão do Instagram/TikTok) |
| Extra | Gera também um `.srt` com a transcrição |

## Como usar

```bash
bash baixar_modelo.sh                 # só na primeira vez (~250 MB)
python3 reels.py meu_video.mp4
python3 reels.py meu_video.mp4 --titulo "3 ERROS QUE TE FAZEM PERDER VIEWS" --musica fundo.mp3
python3 reels.py meu_video.mp4 --layout blur --pausa 0.5 --sem-zoom
```

O resultado sai como `meu_video_reels.mp4`.

## Manual de estilo (como me "ensinar")

Todo o estilo está no dicionário `ESTILO`, no topo de `reels.py`: cores, fonte, tamanho, altura da legenda, pausa cortada, zoom e volume da música. Quando você me mostrar um exemplo de edição que gostou, eu ajusto esses valores ou crio um estilo novo. As regras ficam anotadas em `.claude/skills/editar-reels/SKILL.md`, então eu sigo o mesmo padrão nas próximas conversas.
