#!/usr/bin/env python3
"""Side by side and overlay of a pose preview with the x2 sprite. Usage: overlay.py <sprite.png> <preview.png> <out>"""
import sys

from PIL import Image

sprite = Image.open(sys.argv[1]).convert('RGBA')
preview = Image.open(sys.argv[2]).convert('RGBA').resize(sprite.size)
back = Image.new('RGBA', sprite.size, (40, 40, 48, 255))
mix = back.copy(); mix.alpha_composite(sprite)
ghost = preview.copy(); ghost.putalpha(preview.split()[3].point(lambda a: a * 0.6))
mix.alpha_composite(ghost)
a = back.copy(); a.alpha_composite(sprite)
b = back.copy(); b.alpha_composite(preview)
sheet = Image.new('RGB', (sprite.width * 3 + 20, sprite.height), (255, 255, 255))
for k, im in enumerate((a, b, mix)):
    sheet.paste(im.convert('RGB'), (k * (sprite.width + 10), 0))
sheet = sheet.resize((sheet.width * 2, sheet.height * 2))
sheet.save(sys.argv[3])
