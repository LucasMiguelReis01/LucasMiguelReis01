#!/bin/bash
# Coloca a capa no primeiro quadro (0,6 s + fade) e grava como miniatura do MP4.
# Uso: node render.js && ./com-capa.sh
set -e; cd "$(dirname "$0")"
mv recanto-das-aves-reels.mp4 base.mp4
ffmpeg -loglevel error -y -loop 1 -t 1.0 -framerate 30 -i capa-recanto-das-aves.jpg -i base.mp4 -i capa-recanto-das-aves.jpg \
 -filter_complex "[0:v]scale=1080:1920,format=yuv420p,setsar=1,fps=30,settb=1/30[c];[1:v]format=yuv420p,setsar=1,fps=30,settb=1/30[v];[c][v]xfade=transition=fade:duration=0.4:offset=0.6[vv];[1:a]adelay=600|600[aa]" \
 -map "[vv]" -map "[aa]" -map 2 -c:v:0 libx264 -preset slow -crf 18 -pix_fmt yuv420p -c:v:1 copy -disposition:v:1 attached_pic \
 -c:a aac -b:a 192k -movflags +faststart recanto-das-aves-reels.mp4
rm base.mp4
