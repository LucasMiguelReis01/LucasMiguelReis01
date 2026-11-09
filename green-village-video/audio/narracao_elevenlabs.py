# Gera a narração com ElevenLabs (voz natural pt-BR) e a linha do tempo do vídeo.
# A chave é injetada pelo proxy do ambiente (cabeçalho xi-api-key).
#
# - Cada cena dura o tempo da sua fala (o vídeo se ajusta à voz, não o contrário).
# - Usa o endpoint /with-timestamps para saber quando cada palavra é dita e
#   sincronizar elementos ("37", "Entrada", cada condição, WhatsApp) com a fala.
# - Falas geradas ficam em cache (audio/cache/) para não gastar créditos de novo.
#
# Saídas: audio/narracao.wav, timeline.json e timeline.js (lido por index.html).
# Uso: python3 narracao_elevenlabs.py [voice_id]
import sys, os, json, base64, hashlib, subprocess, urllib.request, io
import numpy as np, soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
VOICE = sys.argv[1] if len(sys.argv) > 1 else 'LqFVmWbm4eksPPIUSMaE'  # "Leão Reis."
MODEL = 'eleven_multilingual_v2'
SPEED = 1.05
SR = 44100
LEAD, TAIL = 0.5, 0.55          # respiro antes/depois da fala em cada cena
MAX_TOTAL = 59.5

# (texto, duração mínima da cena, âncoras {nome: trecho falado}, ocorrência a partir de)
SCENES = [
    ("Seu terreno em Mogi das Cruzes. Sem banco, e sem consulta ao Serasa.", 4.0, {}),
    ("Conheça o Green Village um, um residencial pra você construir o seu futuro.", 4.0, {}),
    ("São trinta e nove lotes, de duzentos e cinquenta a quatrocentos e seis metros quadrados.", 5.0, {}),
    ("Escolha o seu lote na planta. Quatro já foram vendidos, e restam só trinta e cinco!", 6.0,
     {'s4.n37': 'trinta e cinco'}),
    ("Lotes a partir de setenta mil reais, com entrada de vinte mil.", 4.5, {'s5.entrada': 'entrada'}),
    ("Direto com os proprietários, sem banco, e com parcelas que cabem no bolso. E dá pra usar carro ou moto na entrada.", 5.5,
     {'s6.c1': 'Direto', 's6.c2': 'sem banco', 's6.c3': 'parcelas', 's6.c4': 'carro'}),
    ("Terreno com procedência, documentação completa, e cópia de tudo na sua mão.", 3.5, {}),
    ("Chama no WhatsApp: onze, nove três sete zero zero, quatro dois nove cinco.", 6.0,
     {'s8.wa': 'WhatsApp'}),
]
CTA_HOLD = 1.8                   # tempo extra no final com o contato na tela

def tts(text, prev, nxt):
    key = hashlib.sha1(json.dumps([VOICE, MODEL, SPEED, text, prev, nxt]).encode()).hexdigest()[:16]
    cache = os.path.join(HERE, 'cache', key + '.json')
    if os.path.exists(cache):
        return json.load(open(cache))
    body = json.dumps({
        'text': text, 'model_id': MODEL, 'language_code': 'pt',
        'previous_text': prev, 'next_text': nxt,
        'voice_settings': {'stability': 0.45, 'similarity_boost': 0.8, 'style': 0.25,
                           'use_speaker_boost': True, 'speed': SPEED},
    }).encode()
    req = urllib.request.Request(
        f'https://api.elevenlabs.io/v1/text-to-speech/{VOICE}/with-timestamps?output_format=mp3_44100_128',
        data=body, headers={'Content-Type': 'application/json'})
    data = json.loads(urllib.request.urlopen(req, timeout=180).read())
    os.makedirs(os.path.dirname(cache), exist_ok=True)
    json.dump(data, open(cache, 'w'))
    return data

def decode(b64):
    wav = subprocess.run(['ffmpeg', '-v', 'error', '-i', '-', '-ac', '1', '-ar', str(SR), '-f', 'wav', '-'],
                         input=base64.b64decode(b64), capture_output=True, check=True).stdout
    return sf.read(io.BytesIO(wav))[0]

clips = []
for i, (text, mn, anchors) in enumerate(SCENES):
    prev = ' '.join(s[0] for s in SCENES[:i])[-300:]
    nxt = SCENES[i + 1][0] if i + 1 < len(SCENES) else ''
    d = tts(text, prev, nxt)
    s = decode(d['audio_base64'])
    idx = np.where(np.abs(s) > 0.01)[0]
    a0, a1 = max(0, idx[0] - 400), idx[-1] + 4000
    trim = a0 / SR
    al = d['alignment']; chars = ''.join(al['characters']); starts = al['character_start_times_seconds']
    found = {}
    for name, phrase in anchors.items():
        pos = chars.rfind(phrase) if name == 's4.n37' else chars.find(phrase)
        found[name] = round(starts[pos] - trim, 2)
    clips.append((s[a0:a1], found, mn))

# monta a linha do tempo
scenes, anchors, t = [], {}, 0.0
for i, (clip, found, mn) in enumerate(clips):
    dur = len(clip) / SR
    need = [mn, LEAD + dur + TAIL] + [LEAD + v + 1.6 for v in found.values()]
    if i == len(clips) - 1: need.append(LEAD + dur + CTA_HOLD)
    length = round(max(need), 2)
    scenes.append({'start': round(t, 2), 'end': round(t + length, 2), 'voice': round(t + LEAD, 2), 'voice_dur': round(dur, 2)})
    for k, v in found.items(): anchors[k] = round(LEAD + v, 2)   # relativo ao início da cena
    t += length
total = round(t, 2)
assert total <= MAX_TOTAL, f'vídeo ficaria com {total}s'

out = np.zeros(int(SR * (total + 0.5)))
for sc, (clip, _, _) in zip(scenes, clips):
    a = int(sc['voice'] * SR); out[a:a + len(clip)] += clip
out /= np.abs(out).max() / 0.9
sf.write(os.path.join(HERE, 'narracao.wav'), out.astype(np.float32), SR)

tl = {'duration': total, 'scenes': scenes, 'anchors': anchors}
json.dump(tl, open(os.path.join(ROOT, 'timeline.json'), 'w'), indent=1)
open(os.path.join(ROOT, 'timeline.js'), 'w').write('window.TIMELINE = ' + json.dumps(tl) + ';\n')
print(json.dumps(tl, indent=1))
