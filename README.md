# Skyline — blocs Mobirise

Bibliothèque de blocs personnalisés pour **Mobirise 6.1.12** (Bootstrap 5.1), avec un système de style marine / bleu ciel : titres en police d'affichage, boutons pilule, cartes arrondies, pied de page marine.

## Contenu

| Groupe | Bloc | Contenu / options |
|---|---|---|
| Navigation | `sk-menu1` | barre sticky, bouton, 1–8 entrées, couleur |
| Headers | `sk-hero1` | plein écran, capsule date/lieu, titre, texte, boutons, fond image/couleur/vidéo, overlay |
| Text | `sk-text1` | introduction centrée + signature |
| Text | `sk-positions1` | postes repliables par département (responsabilités / profil), 1–5 |
| Info | `sk-venue1` | lieu : texte, adresse, liste d'accès (métro, train, bus, voiture), image à gauche/droite |
| Info | `sk-notice1` | bandeau d'avis (note / alerte / succès) |
| Features | `sk-cards1` | 1–4 cartes, icônes, style doux / glace / contour |
| Features | `sk-goodies1` | produits : visuel, crédit artiste, badge de niveau, 4 ou 6 |
| Features | `sk-perks1` | liste d'avantages à coches + bouton |
| Features | `sk-departments1` | 2–6 équipes (titre + paragraphe) |
| Steps | `sk-steps1` | 2–4 étapes numérotées |
| Pricing | `sk-pricing1` | 2 ou 3 formules, badge « populaire » |
| Pricing | `sk-tiers1` | niveaux de soutien cumulatifs (+ prix), 2 ou 3 |
| Pricing | `sk-table1` | grille tarifaire (type de chambre × nombre de personnes) + note |
| Schedule | `sk-schedule1` | programme par jour, horaires et pastilles de catégorie |
| Gallery | `sk-gallery1` | grille de photos, 3 ou 6 |
| FAQ | `sk-faq1` | 1–6 questions (accordéon) |
| Forms | `sk-form1` | formulaire de contact (`mbr-form`) |
| CTA | `sk-cta1` | bandeau d'appel à l'action sur fond marine |
| Footers | `sk-footer1`, `sk-footer2` | colonnes + réseaux ; groupes de liens + mention légale |

Chaque bloc est un fichier `.html` unique : balise `<section>` + `<mbr-parameters>` (options) + balisage utilisant les attributs Mobirise (`mbr-if`, `mbr-class`, `mbr-style`, `mbr-theme-style`, `mbr-buttons`, `mbr-list`, `mbr-icon`).

```
blocks/<Groupe>/<bloc>.html   modèles de blocs
theme/skyline.css             jetons (--sk-*) et styles des blocs
preview/index.html            aperçu navigateur (généré)
tools/build_preview.py        génère l'aperçu à partir des blocs
```

## Aperçu navigateur

```bash
python3 -I tools/build_preview.py   # puis ouvrir preview/index.html
```

L'aperçu retire la syntaxe Mobirise et applique les valeurs par défaut des options ; il sert à contrôler le rendu, pas à remplacer un test dans Mobirise.

## Personnalisation

Couleurs, rayons, polices : variables `--sk-*` en tête de `theme/skyline.css`. Les polices (titres / texte) se règlent dans Mobirise via *Style Editor*.

## Compatibilité — à lire

- Le format des modèles de blocs (`<mbr-parameters>`, `mbr-*`) est celui des projets de référence publiés par Mobirise (historique du dépôt `Mobirise/Mobirise`, dossier `bootstrap-templates`) et du format d'extension communautaire (`params.json` / `component.js` / `template.html`).
- **Non testé dans Mobirise 6.1.12 lui-même** (application de bureau, non disponible dans l'environnement de génération). Le rendu HTML/CSS est vérifié dans Chromium ; le comportement des options dans l'application reste à valider à l'import.
- Le code de padding (`paddingTop * 15 + 'px'`) et les listes (`mbr-list-grow`) suivent les exemples de référence ; à ajuster si Mobirise 6 attend une autre syntaxe.
