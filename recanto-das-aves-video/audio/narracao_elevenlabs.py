# Narração dinâmica (ElevenLabs, com timestamps por caractere) + linha do tempo.
# Gera: audio/narracao.wav e timeline.json/timeline.js com
#   lines   -> início/fim de cada frase
#   words   -> cada palavra com tempo absoluto (legenda palavra por palavra)
#   anchors -> momentos-chave (tempo absoluto) para cortes e animações
# Falas ficam em cache (audio/cache/) para não gastar créditos de novo.
import sys, os, json, base64, hashlib, subprocess, urllib.request, io
import numpy as np, soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
VOICE = sys.argv[1] if len(sys.argv) > 1 else 'LqFVmWbm4eksPPIUSMaE'  # "Leão Reis."
MODEL = 'eleven_multilingual_v2'
SPEED = 1.2
SR = 44100
START, GAP, END_HOLD = 0.25, 0.06, 2.6
SETTINGS = {'stability': 0.32, 'similarity_boost': 0.8, 'style': 0.5, 'use_speaker_boost': True, 'speed': SPEED}

# (texto, {âncora: trecho falado})
LINES = [
    ("Imagina ter o seu lote no meio da natureza, a cinco minutos da Avenida Japão?",
     {'natureza': 'natureza', 'japao': 'cinco minutos'}),
    ("É o Recanto das Aves: condomínio de chácaras no Santo Ângelo, em Mogi!",
     {'logo': 'Recanto', 'cond': 'condomínio', 'bairro': 'Santo'}),
    ("A partir de setenta e cinco mil, com só vinte mil de entrada!", {'lotes': 'A partir', 'preco': 'setenta', 'entrada': 'vinte'}),
    ("O resto, parcelado direto com o proprietário. Sem Serasa e sem banco!",
     {'parc': 'parcelado', 'prop': 'proprietário', 'c1': 'Sem Serasa', 'c2': 'sem banco'}),
    ("Já pode construir, e são só quarenta e seis lotes!", {'constr': 'construir', 'n46': 'quarenta'}),
    ("Chama no WhatsApp agora!", {'wa': 'WhatsApp', 'num': 'agora'}),
]

def tts(text, prev, nxt):
    key = hashlib.sha1(json.dumps([VOICE, MODEL, SETTINGS, text, prev, nxt]).encode()).hexdigest()[:16]
    cache = os.path.join(HERE, 'cache', key + '.json')
    if os.path.exists(cache):
        return json.load(open(cache))
    body = json.dumps({'text': text, 'model_id': MODEL, 'language_code': 'pt',
                       'previous_text': prev, 'next_text': nxt, 'voice_settings': SETTINGS}).encode()
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

t = START
lines, words, anchors, clips = [], [], {}, []
for i, (text, anc) in enumerate(LINES):
    prev = ' '.join(l[0] for l in LINES[:i])[-300:]
    nxt = LINES[i + 1][0] if i + 1 < len(LINES) else ''
    d = tts(text, prev, nxt)
    s = decode(d['audio_base64'])
    idx = np.where(np.abs(s) > 0.01)[0]
    a0, a1 = max(0, idx[0] - 300), idx[-1] + 2500
    trim = a0 / SR
    clip = s[a0:a1]
    al = d['alignment']; chars = ''.join(al['characters'])
    cs, ce = al['character_start_times_seconds'], al['character_end_times_seconds']
    for name, phrase in anc.items():
        pos = chars.find(phrase); assert pos >= 0, (name, phrase)
        anchors[name] = round(t + cs[pos] - trim, 3)
    # palavras
    j = 0
    while j < len(chars):
        if chars[j].isspace(): j += 1; continue
        k = j
        while k < len(chars) and not chars[k].isspace(): k += 1
        words.append({'w': chars[j:k], 's': round(t + cs[j] - trim, 3), 'e': round(t + ce[k - 1] - trim, 3), 'line': i})
        j = k
    dur = len(clip) / SR
    lines.append({'start': round(t, 3), 'end': round(t + dur, 3)})
    clips.append((t, clip))
    t += dur + GAP
total = round(t - GAP + END_HOLD, 2)

out = np.zeros(int(SR * (total + 0.5)))
for at, clip in clips:
    a = int(at * SR); out[a:a + len(clip)] += clip
out /= np.abs(out).max() / 0.9
sf.write(os.path.join(HERE, 'narracao.wav'), out.astype(np.float32), SR)

tl = {'duration': total, 'lines': lines, 'words': words, 'anchors': anchors}
json.dump(tl, open(os.path.join(ROOT, 'timeline.json'), 'w'), indent=1)
open(os.path.join(ROOT, 'timeline.js'), 'w').write('window.TIMELINE = ' + json.dumps(tl) + ';\n')
print('duração', total)
print('frases', [l['start'] for l in lines])
print('âncoras', anchors)
