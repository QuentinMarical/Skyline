#!/usr/bin/env python3
"""Génère preview/index.html : assemble les blocs en retirant la syntaxe Mobirise
(<mbr-parameters>, mbr-*), pour contrôler le rendu dans un navigateur ordinaire.
Usage : python3 -I tools/build_preview.py [dossier_blocs] [fichier_sortie]"""
import re, sys, glob, os

ORDER = ["Navigation", "Headers", "Features", "Steps", "Pricing", "FAQ", "Footers"]
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
blocks_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(root, "blocks")
out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(root, "preview", "index.html")

def defaults(params):
    vals = {}
    for m in re.finditer(r'<input([^>]*)>', params):
        a = m.group(1)
        n = re.search(r'name="([^"]+)"', a)
        if not n: continue
        v = re.search(r'value="([^"]*)"', a)
        vals[n.group(1)] = ("checked" in a) if 'type="checkbox"' in a else (v.group(1) if v else "")
    for m in re.finditer(r'<select[^>]*name="([^"]+)"[^>]*>(.*?)</select>', params, re.S):
        sel = re.search(r'<option value="([^"]*)" selected', m.group(2)) or re.search(r'<option value="([^"]*)"', m.group(2))
        vals[m.group(1)] = sel.group(1)
    return vals

def evaluate(expr, vals):
    e = expr
    for k in sorted(vals, key=len, reverse=True):
        v = vals[k]
        rep = ("true" if v else "false") if isinstance(v, bool) else (v if re.fullmatch(r"-?\d+(\.\d+)?", v) else repr(v))
        e = re.sub(r'(?<![\w.\'"])' + re.escape(k) + r'(?![\w\'"])', rep, e)
    e = re.sub(r"'(-?\d+(?:\.\d+)?)'", r"\1", e)  # JS : '3' == 3
    e = e.replace("&&", " and ").replace("||", " or ").replace("===", "==").replace("!==", "!=")
    e = e.replace("true", "True").replace("false", "False")
    try: return bool(eval(e, {"__builtins__": {}}, {}))
    except Exception: return True

def render(html):
    pm = re.search(r'<mbr-parameters>(.*?)</mbr-parameters>', html, re.S)
    vals = defaults(pm.group(1)) if pm else {}
    html = re.sub(r'<mbr-parameters>.*?</mbr-parameters>', '', html, flags=re.S)
    # mbr-if : retire les éléments dont la condition est fausse (par balise ouvrante + fermante équilibrée)
    def drop(html):
        while True:
            m = re.search(r'<(\w+)\b[^>]*\bmbr-if="([^"]*)"[^>]*>', html)
            if not m: return html
            tag, cond = m.group(1), m.group(2)
            if evaluate(cond, vals):
                html = html[:m.start()] + re.sub(r'\s*mbr-if="[^"]*"', '', m.group(0)) + html[m.end():]
                continue
            depth, i = 0, m.start()
            for t in re.finditer(r'</?%s\b[^>]*>' % tag, html[m.start():]):
                depth += -1 if t.group(0).startswith('</') else 1
                if depth == 0:
                    html = html[:m.start()] + html[m.start()+t.end():]; break
            else: return html
    html = drop(html)
    def mbr_class(m):
        body = m.group(1)
        if body.strip().startswith('{'):
            names = [k for k, c in re.findall(r"'([^']+)'\s*:\s*([^,}]+)", body) if evaluate(c.strip(), vals)]
            return ' data-add-class="%s"' % " ".join(names)
        return ' data-add-class="%s"' % vals.get(body.strip(), "")
    html = re.sub(r'\s*mbr-class="([^"]*)"', mbr_class, html, flags=re.S)
    def mbr_style(m):
        css = []
        for k, v in re.findall(r"'([^']+)'\s*:\s*([^,}]+)", m.group(1)):
            val = evaluate_val(v.strip(), vals)
            if val is not None: css.append(f"{k}:{val}")
        return ' style="%s"' % ";".join(css)
    html = re.sub(r'\s*mbr-style="([^"]*)"', mbr_style, html)
    # applique data-add-class
    html = re.sub(r'class="([^"]*)"([^>]*?) data-add-class="([^"]*)"', lambda m: 'class="%s %s"%s' % (m.group(1), m.group(3), m.group(2)), html)
    html = re.sub(r'\s*(mbr-[a-z-]+(="[^"]*")?|data-app-selector="[^"]*"|data-toolbar="[^"]*"|data-bg-video="[^"]*"|global|once)(?=[\s>])', '', html)
    return html

def evaluate_val(v, vals):
    m = re.match(r"(\w+)\s*\?\s*0\s*:\s*(\w+)\s*\*\s*15\s*\+\s*'px'", v)
    if m: return "0" if vals.get(m.group(1)) else "%dpx" % (int(vals.get(m.group(2), 0)) * 15)
    if v in vals and re.fullmatch(r"#[0-9a-fA-F]{3,8}", str(vals[v])): return vals[v]
    m = re.match(r"(\w+)\s*\*\s*15\s*\+\s*'px'", v)
    if m: return "%dpx" % (int(vals.get(m.group(1), 0)) * 15)
    return vals.get(v) if v in vals else None

parts = []
for g in ORDER:
    for f in sorted(glob.glob(os.path.join(blocks_dir, g, "*.html"))):
        parts.append("<!-- %s -->\n%s" % (os.path.basename(f), render(open(f, encoding="utf-8").read())))
page = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Skyline blocks – preview</title>
<link rel="stylesheet" href="vendor/bootstrap.min.css">
<link rel="stylesheet" href="../theme/skyline.css">
<style>.sk-hero.sk-fullscreen{min-height:70vh}.sk-hero{background-image:linear-gradient(135deg,#dce7f5,#b5cce8)}</style>
</head><body>
%s
<script src="vendor/bootstrap.bundle.min.js"></script></body></html>""" % "\n".join(parts)
os.makedirs(os.path.dirname(out), exist_ok=True)
open(out, "w", encoding="utf-8").write(page)
print("écrit", out, "-", len(parts), "blocs")
