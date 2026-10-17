#!/usr/bin/env python3
"""Génère les miniatures de la galerie (tools/thumbs/*.jpg) à partir de l'aperçu navigateur.
Nécessite Node + Playwright (Chromium) et Pillow. Les miniatures sont versionnées : le build de
l'extension n'en a pas besoin.
Usage : python3 -I tools/make_thumbs.py"""
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skyline as sk  # noqa: E402
from PIL import Image  # noqa: E402

W, H_MAX = 420, 260
out_dir = os.path.join(sk.ROOT, "tools", "thumbs")
os.makedirs(out_dir, exist_ok=True)
subprocess.run([sys.executable, "-I", os.path.join(sk.ROOT, "tools", "build_preview.py")], check=True, stdout=subprocess.DEVNULL)
keys = [os.path.splitext(os.path.basename(p))[0] for _, p in sk.block_files()]
npm_root = subprocess.run(["npm", "root", "-g"], capture_output=True, text=True, check=True).stdout.strip()
env = dict(os.environ, NODE_PATH=npm_root)
with tempfile.TemporaryDirectory() as tmp:
    subprocess.run(["node", os.path.join(sk.ROOT, "tools", "shoot.js"), os.path.join(sk.ROOT, "preview", "index.html"), tmp] + keys, check=True, env=env)
    for k in keys:
        im = Image.open(os.path.join(tmp, k + ".png")).convert("RGB")
        h = max(1, round(im.height * W / im.width))
        im = im.resize((W, h), Image.LANCZOS).crop((0, 0, W, min(h, H_MAX)))
        im.save(os.path.join(out_dir, k + ".jpg"), quality=72, optimize=True)
print(len(keys), "miniatures dans", out_dir)
