# Gera a narração (pt-BR) com Kokoro TTS offline.
# Uso: python3 narracao.py <dir_com_kokoro.onnx_e_voices.bin> [voz]
import sys, json, soundfile as sf, numpy as np
from kokoro_onnx import Kokoro

MODEL_DIR = sys.argv[1]
VOICE = sys.argv[2] if len(sys.argv) > 2 else 'pm_alex'
# (início em segundos, fim máximo, texto) — grafia fonética onde a pronúncia pede
LINES = [
    (0.5,  6.0,  "Seu terreno em Mogi das Cruzes. Sem banco, e sem consulta ao Serasa."),
    (6.5,  13.0, "Conheça o Grin Vílidji Um: um residencial de baixa densidade, pra você construir o seu futuro."),
    (13.5, 21.0, "São trinta e nove lotes, em três quadras, de duzentos e cinquenta a quatrocentos e seis metros quadrados."),
    (21.5, 30.0, "Escolha o seu lote na planta. Os lotes vinte e seis e vinte e sete já foram vendidos. Restam só trinta e sete."),
    (30.5, 38.0, "Lotes a partir de setenta mil reais, com entrada de vinte mil."),
    (38.5, 46.0, "Direto com os proprietários, sem aprovação bancária, e com parcelas que cabem no bolso. Dá até pra usar carro ou moto na entrada."),
    (46.4, 51.0, "Documentação completa, e cópia de tudo na sua mão."),
    (51.5, 58.0, "Qual lote combina com você? Chame no uótsápi: onze, nove três sete zero zero, quatro dois nove cinco."),
]
k = Kokoro(f'{MODEL_DIR}/kokoro.onnx', f'{MODEL_DIR}/voices.bin')
SR = 24000
out, meta = np.zeros(int(SR * 58.5), dtype=np.float32), []
for t0, t1, text in LINES:
    speed = 1.05
    while True:
        s, sr = k.create(text, voice=VOICE, speed=speed, lang='pt-br')
        # corta silêncio das pontas
        idx = np.where(np.abs(s) > 0.01)[0]; s = s[max(0, idx[0] - 200): idx[-1] + 2400]
        if len(s) / sr <= (t1 - t0) - 0.25 or speed >= 1.3: break
        speed += 0.05
    meta.append(dict(start=t0, dur=round(len(s) / sr, 2), speed=round(speed, 2), text=text))
    a = int(t0 * SR); out[a:a + len(s)] += s[: len(out) - a]
out /= max(1e-6, np.abs(out).max()) / 0.9
sf.write('narracao.wav', out, SR)
print(json.dumps(meta, ensure_ascii=False, indent=1))
