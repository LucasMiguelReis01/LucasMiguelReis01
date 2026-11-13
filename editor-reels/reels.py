#!/usr/bin/env python3
"""
Editor automático de Reels — estilo padrão (vertical 9:16, cortes secos, legenda animada).

O que ele faz, em ordem:
  1. Transcreve a fala (Whisper local, palavra por palavra, em português).
  2. Corta silêncios e pausas longas (jump cuts), deixando um respiro curto.
  3. Enquadra em 1080x1920 (corta o centro, ou fundo desfocado com --layout blur).
  4. Alterna zoom a cada corte (punch-in), o "efeito câmera mexendo" dos Reels.
  5. Queima legendas grandes, em CAIXA ALTA, 2-3 palavras por vez,
     com a palavra falada destacada em amarelo e animação de "pop".
  6. Título/gancho opcional no topo nos primeiros segundos.
  7. Música de fundo opcional, que abaixa sozinha quando você fala (ducking).
  8. Áudio normalizado para o volume do Instagram (-14 LUFS).

Uso:
  python3 reels.py video.mp4
  python3 reels.py video.mp4 -o pronto.mp4 --titulo "3 DICAS DE EDIÇÃO" --musica musica.mp3
  python3 reels.py video.mp4 --layout blur      # vídeo horizontal sem cortar as laterais

Ajustes do estilo ficam no dicionário ESTILO logo abaixo.
"""
import argparse, json, os, re, subprocess, sys, hashlib
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
MODELO = os.path.join(AQUI, '.modelo', 'whisper-small')
FONTES = os.path.join(AQUI, 'fontes')

ESTILO = {
    'largura': 1080, 'altura': 1920, 'fps': 30,
    # cortes
    'pausa_minima': 0.35,      # silêncio maior que isso é cortado (segundos)
    'respiro': 0.08,           # quanto de silêncio fica antes/depois da fala
    'limiar_db': -38,          # abaixo disso (relativo ao pico) conta como silêncio
    # zoom
    'zoom': 1.15,              # zoom do punch-in (1.0 = sem zoom)
    # legenda
    'fonte': 'Montserrat Black',
    'tamanho': 112,
    'cor': '&H00FFFFFF',       # branco (formato ASS: &HAABBGGRR)
    'cor_destaque': '&H0000E5FF',  # amarelo
    'contorno': 11,
    'sombra': 3,
    'margem_baixo': 560,       # altura da legenda (acima da interface do Instagram)
    'palavras_por_vez': 3,
    'caracteres_max': 16,
    # título
    'fonte_titulo': 'Anton',
    'tamanho_titulo': 128,
    'duracao_titulo': 3.0,
    # áudio
    'lufs': -14,
    'volume_musica': 0.22,
}


def rodar(cmd, **kw):
    return subprocess.run(cmd, check=True, **kw)


def info_video(caminho):
    out = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                          'stream=width,height:format=duration', '-of', 'json', caminho],
                         capture_output=True, check=True, text=True).stdout
    d = json.loads(out)
    s = d['streams'][0]
    return s['width'], s['height'], float(d['format']['duration'])


def carregar_audio(caminho, sr=16000):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', caminho, '-vn', '-ac', '1', '-ar', str(sr),
                          '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)


# ---------------------------------------------------------------- 1. transcrição
def transcrever(caminho, audio):
    h = hashlib.sha1(open(caminho, 'rb').read(1 << 22) + str(os.path.getsize(caminho)).encode()).hexdigest()[:12]
    cache = os.path.join(os.path.dirname(os.path.abspath(caminho)), f'.transcricao_{h}.json')
    if os.path.exists(cache):
        return json.load(open(cache))
    if not os.path.exists(os.path.join(MODELO, 'model.bin')):
        sys.exit('Modelo Whisper não encontrado. Rode primeiro:  bash baixar_modelo.sh')
    from faster_whisper import WhisperModel
    print('• Transcrevendo a fala...')
    m = WhisperModel(MODELO, device='cpu', compute_type='int8')
    segs, _ = m.transcribe(audio, language='pt', word_timestamps=True, vad_filter=False)
    palavras = [{'p': w.word.strip(), 'i': float(w.start), 'f': float(w.end)}
                for s in segs for w in s.words if w.word.strip()]
    json.dump(palavras, open(cache, 'w'), ensure_ascii=False)
    return palavras


# ---------------------------------------------------------------- 2. cortes
def trechos_com_fala(audio, duracao, sr=16000):
    """Devolve [(inicio, fim)] das partes que ficam, removendo silêncios longos."""
    janela = int(sr * 0.02)
    n = len(audio) // janela
    if n == 0:
        return [(0.0, duracao)]
    rms = np.sqrt(np.mean(audio[:n * janela].reshape(n, janela) ** 2, axis=1) + 1e-12)
    db = 20 * np.log10(rms / (rms.max() + 1e-12))
    voz = db > ESTILO['limiar_db']
    # suaviza: ignora "buracos" e "estalos" curtíssimos
    t = np.arange(n) * 0.02
    trechos, em_voz, ini = [], False, 0.0
    for k in range(n):
        if voz[k] and not em_voz:
            em_voz, ini = True, t[k]
        elif not voz[k] and em_voz:
            em_voz = False
            trechos.append([ini, t[k]])
    if em_voz:
        trechos.append([ini, n * 0.02])
    # junta trechos separados por pausa curta
    juntos = []
    for a, b in trechos:
        if juntos and a - juntos[-1][1] < ESTILO['pausa_minima']:
            juntos[-1][1] = b
        else:
            juntos.append([a, b])
    juntos = [(a, b) for a, b in juntos if b - a > 0.12]  # descarta ruídos isolados
    r = ESTILO['respiro']
    final = []
    for a, b in juntos:
        a, b = max(0.0, a - r), min(duracao, b + r)
        if final and a <= final[-1][1]:
            final[-1] = (final[-1][0], b)
        else:
            final.append((a, b))
    return final or [(0.0, duracao)]


def mapear_tempo(trechos):
    """Função que converte tempo do vídeo original -> tempo do vídeo editado."""
    acumulado, base = [], 0.0
    for a, b in trechos:
        acumulado.append((a, b, base))
        base += b - a

    def f(t):
        for a, b, off in acumulado:
            if t < a:
                return off          # caiu num corte: vai para o início do próximo trecho
            if t <= b:
                return off + (t - a)
        return base
    return f, base


# ---------------------------------------------------------------- 5. legendas
def limpar(p):
    p = p.upper()
    p = re.sub(r'[.,;:]+$', '', p)
    return p.replace('{', '(').replace('}', ')')


def agrupar(palavras):
    grupos, atual = [], []
    for k, w in enumerate(palavras):
        atual.append(w)
        texto = ' '.join(limpar(x['p']) for x in atual)
        prox = palavras[k + 1] if k + 1 < len(palavras) else None
        quebra = (len(atual) >= ESTILO['palavras_por_vez']
                  or len(texto) >= ESTILO['caracteres_max']
                  or re.search(r'[.?!,;:]$', w['p'])
                  or prox is None or prox['i'] - w['f'] > 0.5)
        if prox and not quebra:
            texto2 = texto + ' ' + limpar(prox['p'])
            if len(texto2) > ESTILO['caracteres_max'] + 4:
                quebra = True
        if quebra:
            grupos.append(atual)
            atual = []
    if atual:
        grupos.append(atual)
    return grupos


def ts(t):
    t = max(0.0, t)
    h, t = divmod(t, 3600)
    m, s = divmod(t, 60)
    return f'{int(h)}:{int(m):02d}:{s:05.2f}'


def gerar_ass(palavras, mapa, duracao_final, titulo, caminho):
    E = ESTILO
    W, H = E['largura'], E['altura']
    cab = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Leg,{E['fonte']},{E['tamanho']},{E['cor']},&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,{E['contorno']},{E['sombra']},2,70,70,{E['margem_baixo']},1
Style: Tit,{E['fonte_titulo']},{E['tamanho_titulo']},&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,1,0,3,22,0,8,80,80,230,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    linhas = []
    ajust = [{'p': w['p'], 'i': mapa(w['i']), 'f': mapa(w['f'])} for w in palavras]
    grupos = agrupar(ajust)
    for gi, g in enumerate(grupos):
        fim_grupo = g[-1]['f'] + 0.15
        if gi + 1 < len(grupos):
            fim_grupo = min(max(fim_grupo, g[-1]['f']), grupos[gi + 1][0]['i'])
        else:
            fim_grupo = min(duracao_final, g[-1]['f'] + 0.4)
        for k, w in enumerate(g):
            ini = w['i']
            fim = g[k + 1]['i'] if k + 1 < len(g) else fim_grupo
            if fim - ini < 0.02:
                continue
            partes = []
            for j, x in enumerate(g):
                txt = limpar(x['p'])
                if j == k:
                    txt = (r'{\c' + E['cor_destaque'] + r'&\fscx112\fscy112}' + txt +
                           r'{\c' + E['cor'] + r'&\fscx100\fscy100}')
                partes.append(txt)
            pop = r'{\fscx80\fscy80\t(0,90,\fscx100\fscy100)}' if k == 0 else ''
            linhas.append(f"Dialogue: 0,{ts(ini)},{ts(fim)},Leg,,0,0,0,,{pop}{' '.join(partes)}")
    if titulo:
        t = titulo.upper().replace('{', '(').replace('}', ')').replace('\\n', r'\N')
        linhas.append(f"Dialogue: 1,{ts(0)},{ts(E['duracao_titulo'])},Tit,,0,0,0,,"
                      r"{\fad(0,250)\fscx70\fscy70\t(0,120,\fscx100\fscy100)}" + t)
    open(caminho, 'w', encoding='utf-8').write(cab + '\n'.join(linhas) + '\n')
    # também gera um .srt simples (útil para legenda nativa do Instagram/TikTok)
    srt = []
    for n, g in enumerate(grupos, 1):
        def st(t):
            ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
            return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'
        srt.append(f"{n}\n{st(g[0]['i'])} --> {st(g[-1]['f'])}\n{' '.join(x['p'] for x in g)}\n")
    open(os.path.splitext(caminho)[0] + '.srt', 'w', encoding='utf-8').write('\n'.join(srt))


# ---------------------------------------------------------------- 3/4/7. render
def esc_filtro(p):
    return p.replace('\\', '/').replace(':', r'\:').replace("'", r"\'")


def renderizar(entrada, saida, trechos, ass, layout, musica, com_zoom):
    E = ESTILO
    W, H, fps = E['largura'], E['altura'], E['fps']
    partes = []
    for k, (a, b) in enumerate(trechos):
        z = E['zoom'] if (com_zoom and k % 2 == 1) else 1.0
        v = f'[0:v]trim={a:.3f}:{b:.3f},setpts=PTS-STARTPTS,'
        if layout == 'blur':
            v += (f'split[f{k}][g{k}];'
                  f'[g{k}]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=30:2,eq=brightness=-0.08[bg{k}];'
                  f'[f{k}]scale={W}:-2[fg{k}];'
                  f'[bg{k}][fg{k}]overlay=(W-w)/2:(H-h)/2,')
        else:
            v += (f"crop=w='min(iw,ih*{W}/{H})':h='min(ih,iw*{H}/{W})',scale={W}:{H},")
        v += (f"crop=w='iw/{z}':h='ih/{z}',scale={W}:{H},setsar=1,fps={fps}[v{k}]")
        au = (f'[0:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS,'
              f'afade=t=in:d=0.012,areverse,afade=t=in:d=0.012,areverse[a{k}]')
        partes += [v, au]
    n = len(trechos)
    entradas = ''.join(f'[v{k}][a{k}]' for k in range(n))
    partes.append(f'{entradas}concat=n={n}:v=1:a=1[vc][ac]')
    partes.append(f"[vc]ass='{esc_filtro(ass)}':fontsdir='{esc_filtro(FONTES)}'[vout]")
    if musica:
        partes.append(f"[ac]asplit[voz][chave]")
        partes.append(f"[1:a]volume={E['volume_musica']},aloop=loop=-1:size=2e9[m]")
        partes.append("[m][chave]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[mduck]")
        partes.append("[voz][mduck]amix=inputs=2:duration=first:normalize=0[mix]")
        partes.append(f"[mix]loudnorm=I={E['lufs']}:TP=-1.5:LRA=11,aresample=48000[aout]")
    else:
        partes.append(f"[ac]loudnorm=I={E['lufs']}:TP=-1.5:LRA=11,aresample=48000[aout]")
    grafo = ';\n'.join(partes)
    arq_grafo = os.path.splitext(saida)[0] + '.filtro.txt'
    open(arq_grafo, 'w').write(grafo)
    cmd = ['ffmpeg', '-v', 'error', '-stats', '-y', '-i', entrada]
    if musica:
        cmd += ['-i', musica]
    cmd += ['-filter_complex_script', arq_grafo, '-map', '[vout]', '-map', '[aout]',
            '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p',
            '-profile:v', 'high', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', saida]
    print('• Renderizando...')
    rodar(cmd)
    os.remove(arq_grafo)


def main():
    ap = argparse.ArgumentParser(description='Editor automático de Reels (estilo padrão).')
    ap.add_argument('entrada')
    ap.add_argument('-o', '--saida')
    ap.add_argument('--titulo', help='texto do gancho no topo nos primeiros segundos')
    ap.add_argument('--musica', help='arquivo de música de fundo (abaixa sozinha quando há fala)')
    ap.add_argument('--layout', choices=['crop', 'blur'], default='crop',
                    help='crop = corta o centro; blur = vídeo inteiro com fundo desfocado')
    ap.add_argument('--sem-cortes', action='store_true', help='não remove pausas')
    ap.add_argument('--sem-zoom', action='store_true', help='não alterna zoom nos cortes')
    ap.add_argument('--sem-legenda', action='store_true')
    ap.add_argument('--pausa', type=float, help=f"pausa mínima cortada (padrão {ESTILO['pausa_minima']}s)")
    a = ap.parse_args()
    if a.pausa:
        ESTILO['pausa_minima'] = a.pausa

    entrada = os.path.abspath(a.entrada)
    saida = os.path.abspath(a.saida or os.path.splitext(entrada)[0] + '_reels.mp4')
    _, _, dur = info_video(entrada)
    audio = carregar_audio(entrada)

    trechos = [(0.0, dur)] if a.sem_cortes else trechos_com_fala(audio, dur)
    mapa, dur_final = mapear_tempo(trechos)
    print(f'• {len(trechos)} trechos mantidos: {dur:.1f}s → {dur_final:.1f}s '
          f'({dur - dur_final:.1f}s de pausas removidas)')

    palavras = [] if a.sem_legenda else transcrever(entrada, audio)
    if palavras:
        print('• Texto:', ' '.join(w['p'] for w in palavras))
    ass = os.path.splitext(saida)[0] + '.ass'
    gerar_ass(palavras, mapa, dur_final, a.titulo, ass)
    renderizar(entrada, saida, trechos, ass, a.layout, a.musica and os.path.abspath(a.musica), not a.sem_zoom)
    print(f'✓ Pronto: {saida}')


if __name__ == '__main__':
    main()
