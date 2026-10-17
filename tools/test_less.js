// Compile chaque src/components/*/style.less avec LESS (variables factices).
// Usage : npm i --no-save less@4 && node tools/test_less.js src/components
const less = require('less'), fs = require('fs'), path = require('path');
const root = process.argv[2];
const vars = "@paddingTop:6;@paddingBottom:6;@fullScreen:true;@bg-type:'color';@bg-value:#fff;@bgColor:#fff;";
(async () => {
  let bad = 0, n = 0;
  for (const d of fs.readdirSync(root).filter(d => d.startsWith('sk-'))) {
    const src = fs.readFileSync(path.join(root, d, 'style.less'), 'utf8');
    try { const out = await less.render(vars + '.cid{' + src + '}'); n++; if (d === 'sk-hero1') console.log(out.css.trim().replace(/\n/g,' ').slice(0,200)); }
    catch (e) { bad++; console.log('ERREUR', d, e.message); }
  }
  console.log(n + ' style.less compilés, ' + bad + ' erreur(s)'); process.exit(bad ? 1 : 0);
})();
