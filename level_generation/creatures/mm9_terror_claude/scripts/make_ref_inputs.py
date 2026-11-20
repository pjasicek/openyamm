"""Assemble the Codex inputs from the MM9 renders: views strip (q34, front, left, back, right), skin x4, top view,
tier q34 sheet. Args: project_dir skin_png tiers(comma, e.g. t1,t2)"""
import sys, os
from PIL import Image
P, skin, tiers = sys.argv[1], sys.argv[2], sys.argv[3].split(',')
R = os.path.join(P, 'work/refs'); out = os.path.join(P, 'references_hd'); os.makedirs(out, exist_ok=True)
views = ['q34', 'front', 'left', 'back', 'right']
ims = [Image.open(f'{R}/t1_{v}.png').convert('RGB') for v in views]
s = Image.new('RGB', (640 * 5, 640))
for k, im in enumerate(ims):
    s.paste(im, (640 * k, 0))
s.save(f'{out}/mm9_views_tier1.png')
Image.open(f'{R}/t1_top.png').convert('RGB').save(f'{out}/mm9_top_tier1.png')
sk = Image.open(skin).convert('RGB')
sk.resize((512, 512), Image.LANCZOS).save(f'{out}/mm9_skin_tier1_x4.png')
t = Image.new('RGB', (640 * len(tiers), 640))
for k, n in enumerate(tiers):
    t.paste(Image.open(f'{R}/{n}_q34.png').convert('RGB'), (640 * k, 0))
t.save(f'{out}/mm9_tiers_q34.png')
print('ok')
