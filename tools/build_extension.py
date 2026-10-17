#!/usr/bin/env python3
"""Construit l'extension Mobirise (src/app.js) et, avec --zip, le fichier importable .mbrext.

  python3 -I tools/build_extension.py              régénère src/app.js
  python3 -I tools/build_extension.py --zip        + écrit dist/skyline-blocks.mbrext
  python3 -I tools/build_extension.py --check-tag v1   vérifie que la version de src/params.json = tag
"""
import argparse
import base64
import json
import os
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skyline as sk  # noqa: E402

SRC = os.path.join(sk.ROOT, "src")
THUMBS = os.path.join(sk.ROOT, "tools", "thumbs")
ALIAS = "skyline-blocks"

ap = argparse.ArgumentParser()
ap.add_argument("--zip", action="store_true", help="écrit dist/skyline-blocks.mbrext")
ap.add_argument("--check-tag", metavar="vN", help="échoue si la version de params.json ne correspond pas au tag")
args = ap.parse_args()

params = json.load(open(os.path.join(SRC, "params.json"), encoding="utf-8"))
if args.check_tag and args.check_tag != "v%s" % params["version"]:
    sys.exit("Le tag %s ne correspond pas à la version %s de src/params.json" % (args.check_tag, params["version"]))

blocks = {}
for group, path in sk.block_files():
    b = sk.load_block(group, path)
    thumb = os.path.join(THUMBS, b["key"] + ".jpg")
    if not os.path.exists(thumb):
        sys.exit("Miniature manquante : %s (lancer tools/make_thumbs.py)" % thumb)
    blocks[b["key"]] = {
        "group": group,
        "title": b["title"],
        "thumb": "data:image/jpeg;base64," + base64.b64encode(open(thumb, "rb").read()).decode(),
        "styles": b["styles"],
        "html": sk.shipped_html(b),
    }

groups = [g for g in sk.GROUP_ORDER if any(v["group"] == g for v in blocks.values())]
tpl = open(os.path.join(sk.ROOT, "tools", "app.template.js"), encoding="utf-8").read()
js = (tpl.replace("__VERSION__", str(params["version"]))
         .replace("__GROUPS__", json.dumps(groups))
         .replace("__BLOCKS__", json.dumps(blocks, ensure_ascii=False, indent=1)))
open(os.path.join(SRC, "app.js"), "w", encoding="utf-8").write(js)
print("src/app.js :", len(blocks), "blocs,", len(js) // 1024, "Ko")

if args.zip:
    os.makedirs(os.path.join(sk.ROOT, "dist"), exist_ok=True)
    out = os.path.join(sk.ROOT, "dist", ALIAS + ".mbrext")
    files = sorted(f for f in os.listdir(SRC) if os.path.isfile(os.path.join(SRC, f)))
    for needed in ("params.json", "app.js", "splash.html", "thumbnail.jpg", "splash.jpg"):
        if needed not in files:
            sys.exit("Fichier manquant dans src/ : " + needed)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:  # à la racine de l'archive, comme `cd src && zip -r ../x.mbrext .`
            z.write(os.path.join(SRC, f), f)
    print("écrit", out, "(%d Ko)" % (os.path.getsize(out) // 1024))
