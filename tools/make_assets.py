#!/usr/bin/env python3
"""Génère l'icône (src/thumbnail.jpg, 200x200) et l'image d'accueil (src/splash.jpg, 787x554) de l'extension.
Nécessite Pillow et la police Inter ; à relancer seulement si l'identité visuelle change."""
import os
import sys

from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skyline as sk  # noqa: E402

NAVY, SKY, ICE = (8, 8, 102), (56, 189, 245), (181, 204, 232)
FONT = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"


def gradient(size, c1, c2):
    w, h = size
    im = Image.new("RGB", size)
    d = ImageDraw.Draw(im)
    for y in range(h):
        t = y / max(1, h - 1)
        d.line([(0, y), (w, y)], fill=tuple(round(c1[i] + (c2[i] - c1[i]) * t) for i in range(3)))
    return im


# Icône : trois blocs empilés sur fond dégradé
icon = gradient((200, 200), NAVY, (11, 58, 156))
d = ImageDraw.Draw(icon)
for i, (w, col) in enumerate([(120, SKY), (140, ICE), (100, (255, 255, 255))]):
    y = 38 + i * 42
    d.rounded_rectangle([100 - w // 2, y, 100 + w // 2, y + 32], radius=10, fill=col)
icon.save(os.path.join(sk.ROOT, "src", "thumbnail.jpg"), quality=90)

# Image d'accueil : titre + mosaïque de miniatures
splash = gradient((787, 554), NAVY, SKY)
d = ImageDraw.Draw(splash)
d.text((40, 32), "Skyline Blocks", font=ImageFont.truetype(FONT, 46), fill="white")
d.text((42, 92), "Ready-made blocks for Mobirise 6", font=ImageFont.truetype(FONT, 20), fill=ICE)
keys = ["sk-hero1", "sk-pricing1", "sk-schedule1", "sk-faq1", "sk-tiers1", "sk-cards1"]
tw, th, gap = 225, 150, 18
for i, k in enumerate(keys):
    t = Image.open(os.path.join(sk.ROOT, "tools", "thumbs", k + ".jpg")).convert("RGB")
    t = t.resize((tw, round(t.height * tw / t.width))).crop((0, 0, tw, th))
    x, y = 40 + (i % 3) * (tw + gap), 150 + (i // 3) * (th + gap)
    shadow = Image.new("RGBA", (tw + 40, th + 40), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle([20, 24, tw + 20, th + 24], radius=14, fill=(0, 0, 40, 110))
    splash.paste(shadow.filter(ImageFilter.GaussianBlur(8)), (x - 20, y - 20), shadow.filter(ImageFilter.GaussianBlur(8)))
    mask = Image.new("L", (tw, th), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, tw, th], radius=14, fill=255)
    splash.paste(t, (x, y), mask)
splash.save(os.path.join(sk.ROOT, "src", "splash.jpg"), quality=88)
print("assets écrits dans src/")
