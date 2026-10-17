#!/usr/bin/env python3
"""Rend un projet Mobirise (.mobirise) en pages HTML statiques pour le contrôler dans un navigateur.
Les liens entre pages sont conservés. Usage : python3 -I tools/preview_project.py projet.mobirise dossier_sortie
(le dossier de sortie doit contenir ../preview/vendor et ../theme : utiliser preview/site/ par défaut)"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_preview as bp  # noqa: E402
import skyline as sk  # noqa: E402

src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(sk.ROOT, "examples", "demo-site", "project.mobirise")
out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(sk.ROOT, "preview", "site")
project = json.load(open(src, encoding="utf-8"))
os.makedirs(out, exist_ok=True)
for name, pg in project["pages"].items():
    body = "\n".join(bp.render({"html": c["_customHTML"]}) for c in pg["components"])
    open(os.path.join(out, name), "w", encoding="utf-8").write(bp.page(pg["settings"]["title"], body, prefix="../"))
print(len(project["pages"]), "pages écrites dans", out)
