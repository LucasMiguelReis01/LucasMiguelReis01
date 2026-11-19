# Trilha dinâmica (124 BPM) + efeitos sincronizados com os cortes do vídeo.
# Tempos: ../timeline.json (narração) e ../cues.json (cortes e animações; gerado por `node render.js --cues`).
# Saída: mix.wav (voz + música com ducking + efeitos) e trilha-sem-voz.wav.
import json, os, numpy as np, soundfile as sf
from scipy.signal import fftconvolve, butter, sosfilt, resample_poly

HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
TL = json.load(open('../timeline.json')); CU = json.load(open('../cues.json'))
SR, DUR = 44100, TL['duration']
N = int(SR * DUR)
rng = np.random.default_rng(11)
BPM = 124; BEAT = 60 / BPM; BAR = BEAT * 4
DROP, BREAK, CTA = CU['drop'], CU['brk'], CU['cta']

def t_(d): return np.arange(int(d * SR)) / SR
def midi(m): return 440 * 2 ** ((m - 69) / 12)
def lp(x, f, o=2): return sosfilt(butter(o, f, 'low', fs=SR, output='sos'), x)
def hp(x, f, o=2): return sosfilt(butter(o, f, 'high', fs=SR, output='sos'), x)
def add(buf, x, at, gain=1.0, pan=0.0):
    a = int(at * SR)
    if a >= len(buf) or a + len(x) <= 0: return
    if a < 0: x = x[-a:]; a = 0
    x = x[: len(buf) - a] * gain
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    buf[a:a + len(x), 0] += x * l * 1.414; buf[a:a + len(x), 1] += x * r * 1.414
def env(n, a, r):
    e = np.ones(n); na, nr = max(1, int(a * SR)), max(1, int(r * SR))
    e[:na] = np.linspace(0, 1, na); e[-nr:] *= np.linspace(1, 0, nr); return e
def reverb(x, secs=2.0, mix=0.25):
    ir = rng.standard_normal(int(secs * SR)) * np.exp(-np.linspace(0, 7, int(secs * SR)))
    ir = lp(ir, 6000); ir /= np.abs(ir).sum() ** .5 * 6
    wet = np.stack([fftconvolve(x[:, c], ir if c == 0 else np.roll(ir, 331))[: len(x)] for c in (0, 1)], 1)
    return x * (1 - mix) + wet * mix
def full(t): return DROP <= t < BREAK or t >= CTA

# ------------------------------------------------------------ MÚSICA
# Am – F – C – G (um acorde por compasso): pra cima, sem ser melosa
CH = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]
pad = np.zeros((N, 2)); arp = np.zeros((N, 2)); bass = np.zeros((N, 2)); drums = np.zeros((N, 2))
nbar = int(DUR / BAR) + 2
for b in range(nbar):
    c = CH[b % 4]; st = b * BAR; tt = t_(BAR + .4)
    for j, m in enumerate(c + [c[0] + 12]):
        f = midi(m + 12)
        v = sum(((tt * f * dt) % 1 * 2 - 1) for dt in (.996, 1.0, 1.005)) / 3
        add(pad, lp(v, 1800) * env(len(tt), .05, .35), st, .045, (j - 1.5) * .4)
    seq = [c[0] + 24, c[1] + 24, c[2] + 24, c[0] + 36]
    for k in range(16):
        at = st + k * BEAT / 4
        if at >= DUR: break
        f = midi(seq[k % 4] + (12 if k % 8 == 6 else 0)); td = t_(.18)
        v = (np.sin(2 * np.pi * f * td) + .4 * np.sin(4 * np.pi * f * td)) * np.exp(-td * 22)
        add(arp, v, at, .05 if at < DROP else .065, .35 if k % 2 else -.35)
    for k in range(8):                                     # baixo nos contratempos (bombeando)
        at = st + k * BEAT / 2 + BEAT / 2 * (k % 2 == 0)
        if k % 2 == 0 or not full(at) or at >= DUR: continue
        td = t_(BEAT * .45); f = midi(c[0] - 12)
        v = np.tanh(2.5 * np.sin(2 * np.pi * f * td)) * np.exp(-td * 6)
        add(bass, lp(v, 500), at, .34)

kt = t_(.4)
KICK = np.sin(2 * np.pi * np.cumsum(48 + 120 * np.exp(-kt * 35)) / SR) * np.exp(-kt * 9)
nz = rng.standard_normal(int(.25 * SR))
CLAP = hp(lp(nz, 3500), 900) * np.exp(-t_(.25) * 22)
HAT = hp(rng.standard_normal(int(.06 * SR)), 7500) * np.exp(-t_(.06) * 70)
pump = np.ones(N)
b = 0.0
while b < DUR:
    beat = round(b / BEAT)
    if full(b):
        add(drums, KICK, b, .55)
        a = int(b * SR); n = min(int(.3 * SR), N - a)
        if n > 0: pump[a:a + n] *= 1 - .55 * np.exp(-np.arange(n) / SR * 14)
        if beat % 2 == 1: add(drums, CLAP, b, .22)
        add(drums, HAT, b + BEAT / 2, .14, .3)
        add(drums, HAT, b + BEAT / 4, .05, -.3); add(drums, HAT, b + 3 * BEAT / 4, .05, -.3)
    elif b > 3.2 and b < DROP:                            # intro: só chimbal leve
        add(drums, HAT, b + BEAT / 2, .06, .3)
    b += BEAT
music = reverb(pad * pump[:, None] + arp, 2.2, .3) + bass * pump[:, None] + drums
fade = np.ones(N); fs = int((DUR - 1.0) * SR); fade[fs:] = np.linspace(1, 0, N - fs) ** 1.5
music *= fade[:, None]

# ------------------------------------------------------------ EFEITOS
sfx = np.zeros((N, 2))
def whoosh(d=.35):
    tt = t_(d); n = rng.standard_normal(len(tt)); fc = np.linspace(600, 5000, len(tt))
    out = np.zeros_like(n); y = 0.0; a = np.exp(-2 * np.pi * fc / SR)
    for i in range(len(n)): y = (1 - a[i]) * n[i] + a[i] * y; out[i] = y
    return hp(out, 300) * np.sin(np.pi * tt / d) ** 2 * 5
def impact(big=1.0):
    tt = t_(1.2); return (np.sin(2 * np.pi * np.cumsum(36 + 80 * np.exp(-tt * 14)) / SR) * np.exp(-tt * 3.2)
                          + lp(rng.standard_normal(len(tt)), 1200) * np.exp(-tt * 12) * .6 * big)
def pop(f=900):
    tt = t_(.1); return np.sin(2 * np.pi * np.cumsum(f * (1 + .7 * np.exp(-tt * 70))) / SR) * np.exp(-tt * 40)
def bell(f=1568, d=1.0):
    tt = t_(d); return sum(a * np.sin(2 * np.pi * f * r * tt) * np.exp(-tt * (3 + r)) for r, a in [(1, 1), (2.76, .4), (5.4, .2)]) * .6
def tick():
    tt = t_(.03); return np.sin(2 * np.pi * 2400 * tt) * np.exp(-tt * 200)
def riser(d=1.5):
    tt = t_(d); tone = np.sin(2 * np.pi * np.cumsum(220 * 8 ** (tt / d)) / SR) * .3
    return (tone + lp(hp(rng.standard_normal(len(tt)), 2000), 8000, 4) * .5) * (tt / d) ** 2
def chirp(f0, f1, d):
    tt = t_(d); f = f0 + (f1 - f0) * (tt / d) ** .6 + 180 * np.sin(2 * np.pi * 38 * tt)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * tt / d) ** 1.5

W = whoosh()
for i, c in enumerate(CU['cuts']): add(sfx, W, c - .2, .13, .5 if i % 2 else -.5)
BIG = {round(CU['logo'], 1), round(CU['coins'], 1)}
for h in CU['hits']: add(sfx, impact(), h, .3 if round(h + .1, 1) in BIG or round(h + .08, 1) in BIG else .16)
for i, p in enumerate(CU['pops']): add(sfx, pop(880 + 110 * (i % 4)), p + .03, .16)
add(sfx, riser(1.6), DROP - 1.6, .16); add(sfx, impact(1.4), DROP, .4)
for k in range(9):                                        # moedas no preço
    add(sfx, bell(2093 + 200 * (k % 3), .5), CU['coins'] + k * .06, .07, (k % 3 - 1) * .5)
for k in range(12):                                       # contagem até 46
    add(sfx, tick(), CU['count46'] + .8 * (1 - (1 - k / 12) ** .5), .09)
add(sfx, bell(1568), CU['count46'] + .8, .12)
add(sfx, riser(1.4), CTA - 1.4, .14); add(sfx, impact(1.2), CTA, .35)
add(sfx, bell(1318.5, 1.6), CU['wa'], .14); add(sfx, bell(1975.5, 1.2), CU['wa'] + .12, .09)
add(sfx, impact(1.3), DUR - 1.1, .3)
birds = np.zeros((N, 2))
for at, base, n, g, pan in [(.15, 3300, 6, .06, -.4), (1.2, 4100, 4, .05, .5), (2.3, 3600, 5, .045, -.2)]:
    t = at
    for k in range(n):
        d = rng.uniform(.06, .12); f0 = base * rng.uniform(.9, 1.15)
        add(birds, chirp(f0, f0 * rng.uniform(1.15, 1.5), d), t, g, pan); t += d + rng.uniform(.03, .08)
sfx = reverb(sfx, 1.2, .15) + reverb(birds, 1.8, .35)

# ------------------------------------------------------------ VOZ + MIX
vo, vsr = sf.read('narracao.wav')
vo = resample_poly(vo, SR, vsr)[:N]; vo = np.pad(vo, (0, N - len(vo)))
vo = hp(vo, 90); vo += .1 * hp(vo, 3000)
ev = np.convolve(np.abs(vo), np.ones(int(.12 * SR)) / int(.12 * SR), 'same')
duck = 1 - .5 * np.clip(ev / (ev.max() * .25), 0, 1)
duck = np.convolve(duck, np.ones(int(.2 * SR)) / int(.2 * SR), 'same')
mix = music * duck[:, None] * .85 + sfx * .9 + np.stack([vo, vo], 1) * .85
mix = np.tanh(mix * 1.15) / 1.15
mix /= np.abs(mix).max() / .95
sf.write('mix.wav', mix.astype(np.float32), SR)
bg = music * .85 + sfx * .9
sf.write('trilha-sem-voz.wav', (bg / max(1e-6, np.abs(bg).max()) * .95).astype(np.float32), SR)
print('ok', round(DUR, 2), 's')
