#!/usr/bin/env python3
"""Génère preview/index.html : assemble les blocs en retirant la syntaxe Mobirise
(<mbr-parameters>, mbr-*) et en appliquant les valeurs par défaut des options, pour contrôler
le rendu dans un navigateur ordinaire.
Usage : python3 -I tools/build_preview.py [fichier_sortie]"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skyline as sk  # noqa: E402

def evaluate(expr, vals):
    e = expr
    for k in sorted(vals, key=len, reverse=True):
        v = vals[k]
        rep = ("true" if v else "false") if isinstance(v, bool) else (v if re.fullmatch(r"-?\d+(\.\d+)?", v) else repr(v))
        e = re.sub(r"(?<![\w.'\"])" + re.escape(k) + r"(?![\w'\"])", rep, e)
    e = re.sub(r"'(-?\d+(?:\.\d+)?)'", r"\1", e)  # JS : '3' == 3
    e = e.replace("&&", " and ").replace("||", " or ").replace("===", "==").replace("!==", "!=")
    e = e.replace("true", "True").replace("false", "False")
    try:
        return bool(eval(e, {"__builtins__": {}}, {}))
    except Exception:
        return True


def evaluate_val(v, vals):
    if v in vals and re.fullmatch(r"#[0-9a-fA-F]{3,8}", str(vals[v])):
        return vals[v]
    return vals.get(v) if v in vals else None


def render(block):
    html = re.sub(r"^<!--\s*title:.*?-->\s*", "", block["html"]).replace(sk.PLACEHOLDER_TOKEN, sk.PLACEHOLDER).replace(sk.NATIVE_IMAGE, sk.PLACEHOLDER)
    vals = sk.parameters(html)
    root_style = sk.preview_style(html)
    html = re.sub(r"<mbr-parameters>.*?</mbr-parameters>", "", html, flags=re.S)

    def drop(html):
        while True:
            m = re.search(r'<(\w+)\b[^>]*\bmbr-if="([^"]*)"[^>]*>', html)
            if not m:
                return html
            tag, cond = m.group(1), m.group(2)
            if evaluate(cond, vals):
                html = html[:m.start()] + re.sub(r'\s*mbr-if="[^"]*"', "", m.group(0)) + html[m.end():]
                continue
            depth = 0
            for t in re.finditer(r"</?%s\b[^>]*>" % tag, html[m.start():]):
                depth += -1 if t.group(0).startswith("</") else 1
                if depth == 0:
                    html = html[:m.start()] + html[m.start() + t.end():]
                    break
            else:
                return html

    html = drop(html)

    def mbr_class(m):
        names = [k for k, c in re.findall(r"'([^']+)'\s*:\s*([^,}]+)", m.group(1)) if evaluate(c.strip(), vals)]
        return ' data-add-class="%s"' % " ".join(names)

    html = re.sub(r'\s*mbr-class="([^"]*)"', mbr_class, html, flags=re.S)

    def mbr_style(m):
        css = []
        for k, v in re.findall(r"'([^']+)'\s*:\s*([^,}]+)", m.group(1)):
            val = evaluate_val(v.strip(), vals)
            if val is not None:
                css.append("%s:%s" % (k, val))
        return ' style="%s"' % ";".join(css)

    html = re.sub(r'\s*mbr-style="([^"]*)"', mbr_style, html)
    html = re.sub(r'class="([^"]*)"([^>]*?) data-add-class="([^"]*)"', lambda m: 'class="%s %s"%s' % (m.group(1), m.group(3), m.group(2)), html)
    html = re.sub(r"\s*(mbr-[a-z-]+(=\"[^\"]*\")?|data-app-selector=\"[^\"]*\"|data-toolbar=\"[^\"]*\"|data-bg-video=\"[^\"]*\"|global|once)(?=[\s>])", "", html)
    if root_style:  # équivalent de `_styles` sur la balise <section> racine
        html = re.sub(r"<section ([^>]*?)(\sstyle=\"[^\"]*\")?>", lambda m: '<section %s style="%s">' % (m.group(1), root_style), html, count=1)
    return html


PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s</title>
<link rel="stylesheet" href="%svendor/bootstrap.min.css">
<link rel="stylesheet" href="%s../theme/skyline.css">
<style>.sk-hero.sk-fullscreen{min-height:70vh}</style>
</head><body>
%s
<script src="%svendor/bootstrap.bundle.min.js"></script></body></html>"""


def page(title, body, prefix=""):
    return PAGE % (title, prefix, prefix, body, prefix)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(sk.ROOT, "preview", "index.html")
    parts = []
    for group, path in sk.block_files():
        b = sk.load_block(group, path)
        parts.append("<!-- %s -->\n%s" % (b["key"], render(b)))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write(page("Skyline blocks - preview", "\n".join(parts)))
    print("écrit", out, "-", len(parts), "blocs")
