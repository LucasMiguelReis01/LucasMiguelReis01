# Sintetiza trilha instrumental + efeitos sonoros sincronizados com as animações
# e mixa com a narração (ducking). Tempos vêm de ../timeline.json (gerado pela narração).
# Saída: mix.wav (44.1 kHz, estéreo).
import json, os, numpy as np, soundfile as sf
from scipy.signal import fftconvolve, butter, sosfilt, resample_poly

TL = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'timeline.json')))
SC = [s['start'] for s in TL['scenes']]          # início de cada cena
ANC = TL['anchors']
def rt(scene, rel): return SC[scene - 1] + rel     # cena 1..8, tempo relativo
def anc(name): return rt(int(name[1]), ANC[name]) - 0.15
SR, DUR = 44100, TL['duration']
N = int(SR * DUR)
rng = np.random.default_rng(7)
BEAT = 60 / 96          # 96 BPM
BAR = BEAT * 4

def t_(d): return np.arange(int(d * SR)) / SR
def midi(m): return 440 * 2 ** ((m - 69) / 12)
def lp(x, f, o=2): return sosfilt(butter(o, f, 'low', fs=SR, output='sos'), x)
def hp(x, f, o=2): return sosfilt(butter(o, f, 'high', fs=SR, output='sos'), x)
def bp(x, lo, hi, o=2): return sosfilt(butter(o, [lo, hi], 'band', fs=SR, output='sos'), x)
def add(buf, x, at, gain=1.0, pan=0.0):
    a = int(at * SR)
    if a >= len(buf): return
    x = x[: len(buf) - a] * gain
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    buf[a:a + len(x), 0] += x * l * 1.414; buf[a:a + len(x), 1] += x * r * 1.414
def env_adsr(n, a, r):
    e = np.ones(n); na, nr = int(a * SR), int(r * SR)
    e[:na] = np.linspace(0, 1, na); e[-nr:] *= np.linspace(1, 0, nr); return e
def reverb(x, secs=2.2, mix=0.25):
    ir = rng.standard_normal(int(secs * SR)) * np.exp(-np.linspace(0, 7, int(secs * SR)))
    ir = lp(ir, 6000); ir /= np.abs(ir).sum() ** .5 * 6
    wet = np.stack([fftconvolve(x[:, c], ir if c == 0 else np.roll(ir, 331))[: len(x)] for c in (0, 1)], 1)
    return x * (1 - mix) + wet * mix

# ------------------------------------------------------------------ MÚSICA
# D – A – Bm – G (2 compassos cada), tom de Ré maior
CHORDS = [[50, 54, 57, 62], [45, 52, 57, 61], [47, 54, 59, 62], [43, 50, 55, 59]]
music = np.zeros((N, 2))
pad = np.zeros((N, 2)); bass = np.zeros((N, 2)); arp = np.zeros((N, 2)); drums = np.zeros((N, 2))

def section_on(t, part):
    # arranjo: intro só pad; baixo/kick na cena 2; arpejo na 3; hats na 4;
    # respiro (só pad) na cena 7; volta tudo na 8; acorde final sustentado
    if part == 'pad': return True
    if SC[6] <= t < SC[7] or t >= DUR - 1.5: return False
    return {'bass': t >= SC[1], 'kick': t >= SC[1], 'arp': t >= SC[2], 'hat': t >= SC[3]}[part]

nchord = int(DUR / (BAR * 2)) + 1
for i in range(nchord):
    c = CHORDS[i % 4]; start = i * BAR * 2; d = BAR * 2 + 0.6
    tt = t_(d)
    for j, m in enumerate(c + [c[0] + 12]):
        f = midi(m + 12)
        v = sum(((tt * f * dt) % 1 * 2 - 1) for dt in (0.997, 1.0, 1.004)) / 3   # supersaw
        v = lp(v, 1400) * env_adsr(len(tt), 0.6, 0.8)
        add(pad, v, start, 0.05, pan=(j - 2) * 0.35)
    # baixo: padrão sincopado por compasso
    for bar in range(2):
        for off in (0, 1.5, 2, 3.5):
            at = start + bar * BAR + off * BEAT
            if not section_on(at, 'bass') or at >= DUR: continue
            tb = t_(BEAT * 0.9); f = midi(c[0] - 12)
            v = np.tanh(2.2 * np.sin(2 * np.pi * f * tb)) * np.exp(-tb * 3.5)
            add(bass, lp(v, 400), at, 0.32)
    # arpejo pluck (Karplus–Strong) em semicolcheias
    seq = [c[0] + 24, c[2] + 12, c[1] + 24, c[3] + 12, c[2] + 24, c[1] + 24, c[3] + 12, c[2] + 12]
    for k in range(16):
        at = start + k * BEAT / 2
        if not section_on(at, 'arp') or at >= DUR: continue
        f = midi(seq[k % 8]); p = int(SR / f); L = int(0.9 * SR)
        buf = rng.uniform(-1, 1, p); out = np.zeros(L)
        for n in range(L):
            out[n] = buf[n % p]; buf[n % p] = 0.5 * (buf[n % p] + buf[(n + 1) % p]) * 0.996
        add(arp, lp(out, 3500), at, 0.075 if k % 4 else 0.1, pan=0.4 if k % 2 else -0.4)

# bateria
kick_t = t_(0.45)
KICK = np.sin(2 * np.pi * np.cumsum(50 + 110 * np.exp(-kick_t * 30)) / SR) * np.exp(-kick_t * 8)
HAT = hp(rng.standard_normal(int(0.08 * SR)), 7000) * np.exp(-t_(0.08) * 60)
duck_kick = np.ones(N)
b = 0.0
while b < DUR:
    if section_on(b, 'kick') and (round(b / BEAT) % 2 == 0):
        add(drums, KICK, b, 0.5)
        a = int(b * SR); n = min(int(0.3 * SR), N - a)
        duck_kick[a:a + n] *= 1 - 0.45 * np.exp(-np.arange(n) / SR * 12)
    if section_on(b, 'hat'):
        add(drums, HAT, b + BEAT / 2, 0.12, pan=0.3)
    b += BEAT

pad *= duck_kick[:, None]
music = reverb(pad + arp, 2.6, 0.35) + bass + drums
# acorde final + fade
fade = np.ones(N); fs = int((DUR - 1.2) * SR); fade[fs:] = np.linspace(1, 0, N - fs) ** 1.5
fade[: int(0.8 * SR)] = np.linspace(0, 1, int(0.8 * SR))
music *= fade[:, None]

# ------------------------------------------------------------------ EFEITOS
sfx = np.zeros((N, 2))
def whoosh(d=0.7, up=True):
    tt = t_(d); n = rng.standard_normal(len(tt))
    fc = np.linspace(400, 3500, len(tt)) if up else np.linspace(3500, 400, len(tt))
    out = np.zeros_like(n); y1 = 0.0
    a = np.exp(-2 * np.pi * fc / SR)
    for i in range(len(n)): y1 = (1 - a[i]) * n[i] + a[i] * y1; out[i] = y1
    return lp(hp(out, 200), 4500, 4) * np.sin(np.pi * tt / d) ** 2 * 4
def pop(f=880):
    tt = t_(0.12); return (np.sin(2 * np.pi * np.cumsum(f * (1 + 0.6 * np.exp(-tt * 60))) / SR) * np.exp(-tt * 38))
def tick():
    tt = t_(0.03); return np.sin(2 * np.pi * 2200 * tt) * np.exp(-tt * 200)
def bell(f=1318.5, d=1.6):
    tt = t_(d); parts = [(1, 1), (2.76, .4), (5.4, .2), (8.9, .08)]
    return sum(a * np.sin(2 * np.pi * f * r * tt) * np.exp(-tt * (2.5 + r)) for r, a in parts) * 0.6
def riser(d=1.6):
    tt = t_(d); f = 200 * (8 ** (tt / d))
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.3
    noise = lp(hp(rng.standard_normal(len(tt)), 2000), 7000, 4) * 0.4
    return (tone + noise) * (tt / d) ** 2
def impact():
    tt = t_(1.4); return (np.sin(2 * np.pi * np.cumsum(38 + 70 * np.exp(-tt * 12)) / SR) * np.exp(-tt * 3)
                          + lp(rng.standard_normal(len(tt)), 900) * np.exp(-tt * 9) * 0.5)

# transições de cena
for i, t in enumerate(SC[1:7]):
    add(sfx, whoosh(0.8), t - 0.4, 0.16, pan=-0.5 if i % 2 else 0.5)
add(sfx, whoosh(1.2), 0.0, 0.18)
# títulos revelados (whoosh curto e suave)
for t in [1.0] + [s + 0.6 for s in SC[1:7]] + [SC[7] + 0.3]:
    add(sfx, whoosh(0.45, up=False), t, 0.09)
# itens que aparecem (pop)
for t, f in [(rt(1, .7), 988), (rt(1, 2.1), 880), (rt(2, .5), 988), (rt(2, 1.6), 1175), (rt(3, .4), 988),
             (rt(4, 1.2), 1175), (rt(3, 1.3), 784), (rt(3, 1.4), 880), (rt(3, 1.5), 988), (rt(3, 1.6), 1175),
             (rt(5, 1.3), 784), (rt(5, 1.45), 880), (rt(5, 1.6), 988), (anc('s8.wa') + .6, 1175), (rt(8, .1), 880)]:
    add(sfx, pop(f), t + 0.05, 0.16)
# checks em escada ascendente
for t, f in zip([anc(f's6.c{i}') for i in range(1, 5)], [784, 880, 988, 1175]):
    add(sfx, pop(f), t + 0.05, 0.2); add(sfx, bell(f * 2, 0.6), t + 0.12, 0.05)
# contadores: ticks durante a contagem + sino ao final
N37 = anc('s4.n37') + 0.15
for t0, dur in [(rt(3, 1.4), 1.6), (rt(3, 1.7), 2.0), (N37 - 0.9, 1.4)]:
    for k in range(10):
        add(sfx, tick(), t0 + dur * (1 - (1 - k / 10) ** 0.5) * 0.9, 0.08, pan=0.2)
for t, f in [(rt(3, 3.7), 1318.5), (N37 + 0.5, 1174.7), (N37 - 0.15, 1568)]:
    add(sfx, bell(f), t, 0.12)
# entrada R$ 20.000 e WhatsApp
E, W = anc('s5.entrada'), anc('s8.wa')
add(sfx, bell(1568), E, 0.16); add(sfx, bell(1975.5), E + 0.12, 0.1)
add(sfx, bell(1318.5), W, 0.16); add(sfx, bell(1975.5), W + 0.12, 0.1)
# subida para o final + impacto
add(sfx, riser(1.6), SC[7] - 1.6, 0.16); add(sfx, impact(), SC[7], 0.45)
add(sfx, impact(), 0.05, 0.3)
sfx = reverb(sfx, 1.4, 0.2)

# ------------------------------------------------------------------ NARRAÇÃO + MIX
vo, vsr = sf.read('narracao.wav')
vo = resample_poly(vo, SR, vsr)[:N]; vo = np.pad(vo, (0, N - len(vo)))
vo = hp(vo, 90)
# voz da ElevenLabs já vem tratada: só um leve realce de presença
vo += 0.08 * bp(vo, 2500, 6000)
# ducking da música: envelope da voz
envv = np.convolve(np.abs(vo), np.ones(int(0.15 * SR)) / int(0.15 * SR), 'same')
duck = 1 - 0.55 * np.clip(envv / (envv.max() * 0.25), 0, 1)
duck = np.convolve(duck, np.ones(int(0.25 * SR)) / int(0.25 * SR), 'same')

mix = music * duck[:, None] * 0.75 + sfx * 0.9 + np.stack([vo, vo], 1) * 0.8
mix = np.tanh(mix * 1.1) / 1.1                         # limitador suave
mix /= np.abs(mix).max() / 0.95
sf.write('mix.wav', mix.astype(np.float32), SR)
sf.write('trilha-sem-voz.wav', (music * 0.75 + sfx * 0.9).astype(np.float32) / max(1e-6, np.abs(music * 0.75 + sfx * 0.9).max()) * 0.95, SR)
print('ok', mix.shape, 'peak', np.abs(mix).max())
