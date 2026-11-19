// Gera os JPGs dos anúncios (1080x1350) a partir dos HTML desta pasta.
const { chromium } = require('playwright'); const path = require('path');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1080, height: 1350 } });
  for (const n of ['anuncio-1-oferta', 'anuncio-2-localizacao']) {
    await p.goto('file://' + path.join(__dirname, n + '.html'));
    await p.evaluate(async () => { await document.fonts.ready; await Promise.all([...document.images].map(i => i.decode().catch(() => {}))); });
    await p.screenshot({ path: path.join(__dirname, n + '.jpg'), type: 'jpeg', quality: 95 });
  }
  await b.close();
})();
