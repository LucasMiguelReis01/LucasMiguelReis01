#!/usr/bin/env bash
# Baixa o modelo de transcrição (Whisper small, ~250 MB) e as dependências Python.
# O modelo vem do registro do npm (só arquivos de dados, sem scripts) e é conferido por SHA-256.
set -euo pipefail
AQUI="$(cd "$(dirname "$0")" && pwd)"
DEST="$AQUI/.modelo/whisper-small"
pip install -q faster-whisper numpy
if [ -f "$DEST/model.bin" ]; then echo "Modelo já instalado."; exit 0; fi
TMP="$(mktemp -d)"; trap 'rm -rf "${TMP:?}"' EXIT
cd "$TMP"
for i in 0 1 2 3; do
  npm pack -q "@skillninja/shortmovie-telop-model-p$i@1.0.0" >/dev/null
  mkdir -p "p$i" && tar xzf skillninja-shortmovie-telop-model-p$i-1.0.0.tgz -C "p$i"
done
mkdir -p "$DEST"
cp p0/package/{config.json,tokenizer.json,vocabulary.json,preprocessor_config.json} "$DEST/"
cat p0/package/model.bin.part0 p1/package/model.bin.part1 p2/package/model.bin.part2 p3/package/model.bin.part3 > "$DEST/model.bin"
ESPERADO="$(cut -d' ' -f1 p0/package/model.sha256)"
OBTIDO="$(sha256sum "$DEST/model.bin" | cut -d' ' -f1)"
[ "$ESPERADO" = "$OBTIDO" ] || { echo "Checksum não confere!"; rm -f "$DEST/model.bin"; exit 1; }
echo "Modelo instalado em $DEST"
