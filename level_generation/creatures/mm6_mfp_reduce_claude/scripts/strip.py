"""Stitch cand_sheet.py / render_attack_glb.py frames into review/attack/<tag>.png, one row per camera.
Usage: [CAMS=front,side] strip.py tag [tag ...]"""
import glob, os, sys
from PIL import Image, ImageDraw
D = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'review', 'attack')
for an in sys.argv[1:]:
    rows = [r for r in (sorted(glob.glob(f'{D}/_{an}_{c}_*.png')) for c in os.environ.get('CAMS', 'front,side').split(',')) if r]
    W, H = Image.open(rows[0][0]).size; s = Image.new('RGB', (W * len(rows[0]), H * len(rows)))
    for j, r in enumerate(rows):
        for i, f in enumerate(r): s.paste(Image.open(f).convert('RGB'), (i * W, j * H)); os.remove(f)
    ImageDraw.Draw(s).text((6, 6), an, fill=(255, 255, 0)); s.save(f'{D}/{an}.png')
