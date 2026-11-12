// Uso: node src/render.js  (rodar dentro de capa-imobiliaria/)
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const b = await chromium.launch();
  const base = 'file://' + path.resolve(__dirname, 'capa.html');
  const jobs = [];
  for (const t of ['claro', 'escuro']) {
    const suf = t === 'escuro' ? '-escuro' : '';
    jobs.push(['retrato', t, 1240, 1754, `capa-reis-imoveis-retrato${suf}.png`]);
    jobs.push(['banner', t, 1640, 624, `capa-reis-imoveis-banner${suf}.png`]);
  }
  for (const [v, t, w, h, out] of jobs) {
    const p = await b.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 2 });
    await p.goto(`${base}?v=${v}&t=${t}`);
    await p.waitForSelector('body[data-ready="1"]'); await p.waitForTimeout(300);
    await p.screenshot({ path: out, clip: { x: 0, y: 0, width: w, height: h } });
    await p.close();
  }
  await b.close();
})();
