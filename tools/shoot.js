// Capture chaque bloc de preview/index.html en PNG (utilisé par make_thumbs.py).
// Usage : NODE_PATH=$(npm root -g) node tools/shoot.js <page.html> <dossier_sortie> <clé1> <clé2> ...
const { chromium } = require('playwright');
(async () => {
  const [page_, outDir, ...keys] = process.argv.slice(2);
  const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || undefined });
  const page = await browser.newPage({ viewport: { width: 1200, height: 900 } });
  await page.goto('file://' + require('path').resolve(page_));
  await page.addStyleTag({ content: '.sk-menu{position:static !important}' });
  const sections = await page.$$('body > section');
  if (sections.length !== keys.length) throw new Error(sections.length + ' sections pour ' + keys.length + ' clés');
  for (let i = 0; i < keys.length; i++) {
    await sections[i].screenshot({ path: require('path').join(outDir, keys[i] + '.png') });
  }
  await browser.close();
})().catch(e => { console.error(e.message); process.exit(1); });
