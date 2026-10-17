#!/usr/bin/env python3
"""Contrôle d'un projet Mobirise généré : liens, ancres, blocs globaux, textes par défaut oubliés.
Usage : python3 -I tools/check_project.py [projet.mobirise] [--allow-defaults page.html ...]"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skyline as sk  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith("--")]
src = args[0] if args else os.path.join(sk.ROOT, "examples", "demo-site", "project.mobirise")
allow = {"all-blocks.html"}
project = json.load(open(src, encoding="utf-8"))
pages = project["pages"]
known = {os.path.splitext(os.path.basename(p))[0] for _, p in sk.block_files()}
errors = []
globals_seen = {}
DEFAULTS = ["Your Event Name", "Welcome aboard", "Feature one", "Write a clear answer", "Describe the first step", "Illustration: Artist", "Standard room",
            "Open positions", "Please note", "Ready to take off", "Contact us", "Memories from last time", "Our teams", "Volunteer perks", "Get your pass", "Learn more", "Brand<"]

for name, pg in pages.items():
    anchors = set()
    for c in pg["components"]:
        if c["_name"] not in known:
            errors.append("%s : bloc inconnu %s" % (name, c["_name"]))
        if c["_anchor"] in anchors:
            errors.append("%s : ancre en double %s" % (name, c["_anchor"]))
        anchors.add(c["_anchor"])
        if c.get("_global"):
            prev = globals_seen.setdefault(c["_cid"], c["_customHTML"])
            if prev != c["_customHTML"]:
                errors.append("%s : bloc global %s différent d'une page à l'autre" % (name, c["_name"]))
        html = c["_customHTML"]
        if html[html.rfind("<style>") + 7:html.rfind("</style>")] != sk.css_for(html):
            errors.append("%s : CSS embarqué périmé dans %s (relancer tools/build_demo.py)" % (name, c["_name"]))
        if c["_styles"] != sk.infer_styles(html):
            errors.append("%s : _styles périmé dans %s (relancer tools/build_demo.py)" % (name, c["_name"]))
        body = html[html.index("</mbr-parameters>"):html.rfind("<style>")]
        for h in re.findall(r'href="([^"]*)"', body):
            if name in allow:
                continue
            if h in ("#", "") or "mobirise.com" in h or (h.endswith(".html") and h not in pages):
                errors.append("%s : lien invalide %r dans %s" % (name, h, c["_name"]))
        if name not in allow:
            text = re.sub(r"<[^>]+>|\s+", " ", re.sub(r"<mbr-parameters>.*?</mbr-parameters>", "", body, flags=re.S))
            for d in DEFAULTS:
                if d in text or d in body:
                    errors.append("%s : texte par défaut oublié %r dans %s" % (name, d, c["_name"]))
used = {h for pg in pages.values() for c in pg["components"] for h in re.findall(r'href="([^"]*\.html)"', c["_customHTML"])}
for f in pages:
    if f not in used and f != "all-blocks.html":
        errors.append("page jamais liée : " + f)
print("%d pages, %d blocs, %d bloc(s) global(aux)" % (len(pages), sum(len(p["components"]) for p in pages.values()), len(globals_seen)))
for e in errors:
    print("ERREUR", e)
print("OK" if not errors else "%d erreur(s)" % len(errors))
sys.exit(1 if errors else 0)
