"""Join g1_preview.py tiles: review/g1/<set>.png with the clip names. Args: <set>"""
import json, os, sys
from PIL import Image, ImageDraw
d = json.load(open(f'review/g1/{sys.argv[1]}.json')); w, h = d['w'], d['h']
s = Image.new('RGB', (d['cols'] * w, d['rows'] * h)); dr = ImageDraw.Draw(s)
for r, c, f in d['tiles']:
    s.paste(Image.open(f).convert('RGB'), (c * w, r * h)); os.remove(f)
for r, lab in enumerate(d['labels']): dr.text((4, r * h + 4), lab, fill=(255, 255, 120))
s.save(f'review/g1/{sys.argv[1]}.png'); print('SHEET', sys.argv[1])
