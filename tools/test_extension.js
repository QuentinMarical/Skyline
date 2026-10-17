// Test de src/app.js avec un faux environnement Mobirise.
// Usage : npm i --no-save jsdom@24 jquery@3.7.1 && node tools/test_extension.js src/app.js
const { JSDOM } = require('jsdom');
const fs = require('fs');
const dom = new JSDOM('<!doctype html><body><ul class="navbar-devices"><li data-device="desktop"><a>d</a></li></ul></body>', { runScripts: 'outside-only', pretendToBeVisual: true });
const { window } = dom;
const jQuery = require('jquery')(window);
window.jQuery = window.$ = jQuery;
let ext, dialog, saved = 0, reloaded = 0, alerts = [];
const page = 'index.html';
const mbrApp = {
  theme: { type: 'secondary' },
  regExtension(e) { ext = e; },
  showDialog(o) { dialog = o; jQuery('body').append('<div class="modal ' + o.className + '">' + o.body + '</div>'); },
  alertDlg(m) { alerts.push(m); },
  Core: { currentPage: page, resultJSON: { [page]: { components: [{ _cid: 'AAAAAAAAAA' }] } }, getPages() { return this.resultJSON; } },
  runSaveProject(cb) { saved++; cb(); },
  loadRecentProject(cb) { reloaded++; cb(); },
};
window.defineM = (alias, fn, deps) => fn(jQuery, mbrApp, () => '');
window.eval(fs.readFileSync(process.argv[2], 'utf8'));
const assert = (c, m) => { if (!c) { console.error('ÉCHEC :', m); process.exit(1); } console.log('ok  -', m); };
assert(ext && ext.name === 'skyline-blocks', 'extension enregistrée');
ext.events.load.call({ $body: jQuery('body') });
assert(jQuery('.btnSkylineBlocks').length === 1, 'bouton ajouté dans .navbar-devices');
jQuery('.btnSkylineBlocks').trigger('click');
assert(dialog && dialog.title === 'Skyline Blocks', 'galerie ouverte');
assert(jQuery('.skyline-gallery-item').length === 21, '21 blocs listés (' + jQuery('.skyline-gallery-item').length + ')');
assert(jQuery('.skyline-group').length === 13, '13 groupes (' + jQuery('.skyline-group').length + ')');
const add = dialog.buttons.find(b => b.label === 'ADD BLOCK TO PAGE');
assert(add.callback() === false && alerts.length === 1, 'refus sans sélection');
jQuery('.skyline-gallery-item[data-block="sk-hero1"]').trigger('click');
assert(jQuery('.skyline-selected').length === 1, 'sélection visuelle');
add.callback();
const comps = mbrApp.Core.resultJSON[page].components;
assert(comps.length === 2 && saved === 1 && reloaded === 1, 'composant ajouté puis projet enregistré/rechargé');
const c = comps[1];
assert(/^[A-Za-z0-9]{10}$/.test(c._cid) && c._cid !== 'AAAAAAAAAA', 'identifiant unique ' + c._cid);
assert(c._customHTML.includes('<mbr-parameters>') && c._customHTML.includes('<style>'), '_customHTML avec paramètres et CSS embarqué');
assert(c._customHTML.includes('class="sk-block sk-hero'), 'balise racine du bloc');
assert(!c._customHTML.includes('@PROJECT_PATH@') && !c._customHTML.includes('<!-- title:'), 'pas de jeton de chemin ni de commentaire de titre');
assert(JSON.stringify(c._styles).includes('@paddingTop'), '_styles : ' + JSON.stringify(c._styles).slice(0, 110));
// chaque bloc : CID unique et styles clonés (pas de partage d'objet)
jQuery('.skyline-gallery-item[data-block="sk-hero1"]').trigger('click'); add.callback();
assert(comps[2]._styles !== comps[1]._styles, 'styles clonés à chaque ajout');
// anciens thèmes : pas de bouton
const m2 = jQuery('<div>'); mbrApp.theme.type = 'primary';
assert(ext.events.load.call({ $body: m2 }) === false, 'thème "primary" ignoré');
console.log('TOUS LES TESTS PASSENT');
