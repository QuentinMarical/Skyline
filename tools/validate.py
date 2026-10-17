#!/usr/bin/env python3
"""Contrôle statique des blocs : racine unique, <mbr-parameters> unique, balises équilibrées,
et chaque option utilisée dans mbr-if / mbr-class / mbr-style / condition / {{...}} est déclarée.
Usage : python3 -I tools/validate.py   (code de sortie 1 s'il y a une erreur)"""
import os
import re
import sys
from html.parser import HTMLParser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skyline as sk  # noqa: E402

VOID = {"input", "img", "br", "hr", "meta", "link"}
JS_WORDS = {"true", "false", "null", "undefined"}


class Balance(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack, self.errors = [], []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack or self.stack[-1] != tag:
            self.errors.append("balise </%s> inattendue (ouverte : %s)" % (tag, self.stack[-1] if self.stack else "aucune"))
            return
        self.stack.pop()


def identifiers(expr):
    expr = re.sub(r"'[^']*'|\"[^\"]*\"", " ", expr)            # littéraux de chaîne
    expr = re.sub(r"\b[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+", lambda m: m.group(0).split(".")[0], expr)  # bg.type -> bg
    return {w for w in re.findall(r"\b[A-Za-z_]\w*\b", expr) if w not in JS_WORDS}


def declared(html):
    names = set(sk.parameters(html))
    if sk.has_background_fieldset(html):
        names.add("bg")
    return names


errors = 0
for group, path in sk.block_files():
    b = sk.load_block(group, path)
    html = b["html"]
    errs = []
    if html.count("<mbr-parameters>") != 1:
        errs.append("<mbr-parameters> doit apparaître une fois")
    if len(re.findall(r"^<section\b", html.split("-->", 1)[-1].lstrip(), re.M)) != 1:
        errs.append("une seule balise <section> racine attendue")
    bal = Balance()
    bal.feed(re.sub(r"<mbr-parameters>.*?</mbr-parameters>", "", html, flags=re.S))
    errs += bal.errors + (["balises non fermées : %s" % bal.stack] if bal.stack else [])
    names = declared(html)
    used = set()
    body = re.sub(r"<mbr-parameters>.*?</mbr-parameters>", "", html, flags=re.S)
    for attr in ("mbr-if", "mbr-class", "mbr-style"):
        for m in re.finditer(r'\b%s="([^"]*)"' % attr, body):
            val = m.group(1)
            if attr != "mbr-if":  # {'clé': condition} : seules les conditions comptent
                val = " ".join(re.findall(r":\s*([^,}]+)", val))
            used |= identifiers(val)
    for m in re.finditer(r'\bcondition="([^"]*)"', html):
        used |= identifiers(m.group(1))
    for m in re.finditer(r"\{\{(.*?)\}\}", body):
        used |= identifiers(m.group(1))
    unknown = sorted(used - names)
    if unknown:
        errs.append("options utilisées mais non déclarées : %s" % ", ".join(unknown))
    pad = [n for n in ("paddingTop", "paddingBottom") if n not in names]
    if pad and b["styles"]:
        errs.append("styles supposent des options absentes : %s" % pad)
    print(("ERREUR " if errs else "ok     ") + b["key"] + ("  -> " + " | ".join(errs) if errs else ""))
    errors += bool(errs)
# Cohérence de src/ : composants déclarés dans params.json, fichiers présents
import json
src = os.path.join(sk.ROOT, "src")
params = json.load(open(os.path.join(src, "params.json"), encoding="utf-8"))
for c in params.get("components", []):
    for f in ("template.html", "style.less", "thumb.png"):
        if not os.path.exists(os.path.join(src, c["path"], f)):
            print("ERREUR src : %s/%s manquant (lancer tools/build_extension.py)" % (c["path"], f))
            errors += 1
if len(params.get("components", [])) != len(sk.block_files()):
    print("ERREUR src : params.json ne liste pas tous les blocs (lancer tools/build_extension.py)")
    errors += 1
for plugin in json.load(open(os.path.join(src, "plugins", "plugin.json"))):
    for f in plugin["files"]:
        if not os.path.exists(os.path.join(src, "plugins", f["src"])):
            print("ERREUR plugin : fichier manquant", f["src"])
            errors += 1
print("src : %d composants, plugin(s) %s" % (len(params["components"]), ", ".join(p["name"] for p in json.load(open(os.path.join(src, "plugins", "plugin.json"))))))
sys.exit(1 if errors else 0)
