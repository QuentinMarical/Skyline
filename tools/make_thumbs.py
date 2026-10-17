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
        # miniature du menu « Add Block » : 500x355, haut du bloc, fond neutre si le bloc est plus bas
        big = Image.open(os.path.join(tmp, k + ".png")).convert("RGB")
        bh = round(big.height * 500 / big.width)
        big = big.resize((500, bh), Image.LANCZOS)
        canvas = Image.new("RGB", (500, 355), (244, 246, 250))
        canvas.paste(big.crop((0, 0, 500, min(bh, 355))), (0, max(0, (355 - bh) // 2)))
        canvas.save(os.path.join(out_dir, k + ".png"), optimize=True)
print(len(keys), "miniatures (jpg + png) dans", out_dir)
