"""Fonctions communes aux scripts de build : lecture des blocs, styles, CSS embarqué."""
import base64
import glob
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOCKS_DIR = os.path.join(ROOT, "blocks")
CSS_FILE = os.path.join(ROOT, "theme", "skyline.css")

# Ordre d'affichage des groupes (galerie et aperçu)
GROUP_ORDER = ["Navigation", "Headers", "Text", "Info", "Features", "Steps", "Pricing",
               "Schedule", "Gallery", "FAQ", "Forms", "CTA", "Footers"]

# Visuel de remplacement : SVG dégradé en base64 (sans guillemets ni parenthèses, donc sûr dans url(...))
_SVG = ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 9'><defs>"
        "<linearGradient id='g' x1='0' y1='0' x2='1' y2='1'><stop offset='0' stop-color='#b5cce8'/>"
        "<stop offset='1' stop-color='#38bdf5'/></linearGradient></defs>"
        "<rect width='16' height='9' fill='url(#g)'/></svg>")
PLACEHOLDER = "data:image/svg+xml;base64," + base64.b64encode(_SVG.encode()).decode()
PLACEHOLDER_TOKEN = "@PROJECT_PATH@/assets/images/mbr-1620x1080.jpg"


def block_files():
    """Liste (groupe, chemin) triée selon GROUP_ORDER puis par nom."""
    out = []
    for g in GROUP_ORDER:
        for f in sorted(glob.glob(os.path.join(BLOCKS_DIR, g, "*.html"))):
            out.append((g, f))
    known = {g for g in GROUP_ORDER}
    for f in sorted(glob.glob(os.path.join(BLOCKS_DIR, "*", "*.html"))):
        if os.path.basename(os.path.dirname(f)) not in known:
            raise SystemExit("Groupe inconnu (ajoutez-le à GROUP_ORDER) : " + f)
    return out


def parameters(html):
    """Valeurs par défaut des options du panneau « engrenage » : {nom: valeur}."""
    m = re.search(r"<mbr-parameters>(.*?)</mbr-parameters>", html, re.S)
    params = m.group(1) if m else ""
    vals = {}
    for im in re.finditer(r"<input([^>]*)>", params):
        a = im.group(1)
        n = re.search(r'name="([^"]+)"', a)
        if not n:
            continue
        v = re.search(r'value="([^"]*)"', a)
        if 'type="checkbox"' in a:
            vals[n.group(1)] = bool(re.search(r"\bchecked\b", a))
        else:
            vals[n.group(1)] = v.group(1) if v else ""
    for sm in re.finditer(r'<select[^>]*name="([^"]+)"[^>]*>(.*?)</select>', params, re.S):
        sel = re.search(r'<option value="([^"]*)" selected', sm.group(2)) or re.search(r'<option value="([^"]*)"', sm.group(2))
        vals[sm.group(1)] = sel.group(1)
    return vals


def has_background_fieldset(html):
    return bool(re.search(r'<fieldset type="background" name="bg"', html))


def infer_styles(html):
    """Construit `_styles` (format LESS-JSON de Mobirise, comme dans les projets de référence)."""
    names = parameters(html)
    styles = {}
    pad = {}
    if "paddingTop" in names:
        pad["padding-top"] = "(@paddingTop * 15px)"
    if "paddingBottom" in names:
        pad["padding-bottom"] = "(@paddingBottom * 15px)"
    if pad:
        if "fullScreen" in names:
            styles["& when not (@fullScreen)"] = pad
        else:
            styles.update(pad)
    if has_background_fieldset(html):
        styles["& when (@bg-type = 'color')"] = {"background-color": "@bg-value"}
        styles["& when (@bg-type = 'image')"] = {"background-image": "url(@bg-value)"}
    elif "bgColor" in names and "<nav" not in html:
        styles["background-color"] = "@bgColor"
    return styles


def preview_style(html):
    """Équivalent de `_styles` en CSS en ligne, pour l'aperçu navigateur (valeurs par défaut)."""
    v = parameters(html)
    css = []
    full = bool(v.get("fullScreen"))
    if "paddingTop" in v and not full:
        css.append("padding-top:%dpx" % (int(v["paddingTop"]) * 15))
    if "paddingBottom" in v and not full:
        css.append("padding-bottom:%dpx" % (int(v["paddingBottom"]) * 15))
    if has_background_fieldset(html):
        m = re.search(r'<input type="color" title="Background Color" value="([^"]+)"', html)
        sel = re.search(r'<input type="image"[^>]*selected', html)
        if sel:
            css.append("background-image:url(%s);background-size:cover;background-position:center" % PLACEHOLDER)
        elif m:
            css.append("background-color:" + m.group(1))
    elif "bgColor" in v and "<nav" not in html:
        css.append("background-color:" + v["bgColor"])
    return ";".join(css)


# ---------- CSS : extraction des règles utiles à un bloc ----------

def _split_rules(css):
    """Découpe une feuille en règles de premier niveau (gère les @media imbriqués)."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    rules, depth, start = [], 0, 0
    for i, ch in enumerate(css):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                rules.append(css[start:i + 1].strip())
                start = i + 1
    return [r for r in rules if r]


def _selector_ok(selector, used):
    classes = set(re.findall(r"\.(sk-[\w-]+)", selector))
    if selector.strip() == ":root":
        return True
    return bool(classes) and classes <= used


def _filter_rule(rule, used):
    head, _, body = rule.partition("{")
    head = head.strip()
    body = body.rsplit("}", 1)[0]
    if head.startswith("@media"):
        inner = [r for r in (_filter_rule(x, used) for x in _split_rules(body)) if r]
        return "%s{%s}" % (head, "".join(inner)) if inner else ""
    keep = [s.strip() for s in head.split(",") if _selector_ok(s, used)]
    return "%s{%s}" % (",".join(keep), re.sub(r"\s+", " ", body).strip()) if keep else ""


def css_for(html):
    """CSS minimal pour un bloc : jetons :root + règles dont toutes les classes `sk-*` sont utilisées."""
    used = set(re.findall(r"sk-[\w-]+", html))
    css = open(CSS_FILE, encoding="utf-8").read()
    return "".join(r for r in (_filter_rule(x, used) for x in _split_rules(css)) if r)


# ---------- Bloc complet ----------

def load_block(group, path):
    html = open(path, encoding="utf-8").read()
    name = os.path.splitext(os.path.basename(path))[0]
    title = re.search(r"<!--\s*title:\s*(.*?)\s*-->", html)
    return {
        "key": name,
        "group": group,
        "title": title.group(1) if title else name,
        "html": html,
        "styles": infer_styles(html),
    }


def shipped_html(block):
    """HTML final embarqué dans l'extension : visuels de remplacement + CSS du bloc dans la section."""
    html = re.sub(r"^<!--\s*title:.*?-->\s*", "", block["html"]).replace(PLACEHOLDER_TOKEN, PLACEHOLDER)
    css = css_for(html)
    return re.sub(r"\s*</section>\s*$", "\n\n    <style>%s</style>\n</section>\n" % css, html.rstrip() + "\n", count=1)
