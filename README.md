# Skyline — blocs Mobirise

Bibliothèque de blocs personnalisés pour **Mobirise 6.1.12** (Bootstrap 5.1), avec un système de style marine / bleu ciel : titres en police d'affichage, boutons pilule, cartes arrondies, pied de page marine.

## Contenu

| Groupe | Bloc | Options (panneau « engrenage ») |
|---|---|---|
| Navigation | `sk-menu1` | sticky, bouton, nombre d'entrées, couleur de fond |
| Headers | `sk-hero1` | plein écran, capsule date/lieu, titre, texte, boutons, fond image/couleur/vidéo, overlay |
| Features | `sk-cards1` | 1 à 4 cartes, icônes, style (doux / glace / contour), fond |
| Steps | `sk-steps1` | 2 à 4 étapes numérotées |
| Pricing | `sk-pricing1` | 2 ou 3 formules, badge « populaire », boutons |
| FAQ | `sk-faq1` | 1 à 6 questions (accordéon Bootstrap) |
| Footers | `sk-footer1` | colonnes, réseaux, mention légale, couleur de fond |

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
