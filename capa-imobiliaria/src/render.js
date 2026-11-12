// Uso: node src/render.js  (rodar dentro de capa-imobiliaria/)
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const b = await chromium.launch();
  const files = { A: 'capa.html', B: 'capa-b.html', C: 'capa-c.html' };
  const jobs = [];
  for (const c of ['A', 'B', 'C']) for (const t of ['claro', 'escuro']) {
    const pre = { A: 'capa-reis-imoveis', B: 'capa-B-selo', C: 'capa-C-casa' }[c];
    const suf = t === 'escuro' ? '-escuro' : '';
    jobs.push([c, 'retrato', t, 1240, 1754, `${pre}-retrato${suf}.png`]);
    jobs.push([c, 'banner', t, 1640, 624, `${pre}-banner${suf}.png`]);
  }
  for (const [c, v, t, w, h, out] of jobs) {
    const base = 'file://' + path.resolve(__dirname, files[c]);
    const p = await b.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 2 });
    await p.goto(`${base}?v=${v}&t=${t}`);
    await p.waitForSelector('body[data-ready="1"]'); await p.waitForTimeout(300);
    await p.screenshot({ path: out, clip: { x: 0, y: 0, width: w, height: h } });
    await p.close();
  }
  await b.close();
})();
