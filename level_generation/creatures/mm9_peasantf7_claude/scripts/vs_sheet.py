"""MM9 vs ours sheet: rows per tier: MM9 render (work/refs/mm9_<t>_<view>.png) next to our viewer shot (review/shots/fin<t>_<view>.png) for
front / quarter / side / back. Args: <out png> <tiers e.g. ab>"""
import sys
from PIL import Image, ImageDraw
out, tiers = sys.argv[1], sys.argv[2]; C = 320
views = [('front', 'front'), ('q34', 'q34'), ('left', 'side'), ('back', 'back')]
S = Image.new('RGB', (C * 8, C * len(tiers) + 22), (28, 28, 28)); d = ImageDraw.Draw(S)
def sq(p):
    im = Image.open(p).convert('RGB'); w, h = im.size; c = min(w, h); return im.crop(((w - c) // 2, (h - c) // 2, (w - c) // 2 + c, (h - c) // 2 + c)).resize((C, C), Image.LANCZOS)
for r, t in enumerate(tiers):
    for k, (mv, ov) in enumerate(views):
        S.paste(sq(f'work/refs/mm9_{t}_{mv}.png'), (2 * k * C, 22 + r * C)); S.paste(sq(f'review/shots/fin{t}_{ov}.png'), ((2 * k + 1) * C, 22 + r * C))
for k, (mv, _) in enumerate(views): d.text((2 * k * C + 4, 5), f'MM9 {mv}', fill=(255, 255, 0)); d.text(((2 * k + 1) * C + 4, 5), f'ours {mv}', fill=(255, 255, 0))
S.save(out); print('SHEET', out)
