"""Face close-up comparison of the viewer shots (hf, hq; tiers; installed | pass) -> review/<out>.png. Usage: face_crops.py [out cmp_face] [tiers a,b,c]"""
import sys
from PIL import Image
import tp
out = sys.argv[1] if len(sys.argv) > 1 else 'cmp_face'
tiers = (sys.argv[2] if len(sys.argv) > 2 else ','.join(t.rsplit('_', 1)[1] for t in tp.CFG['tiers'])).split(',')
pre = next(iter(tp.CFG['tiers'])).rsplit('_', 1)[0]
R = tp.HERE / 'review'
rows = [[Image.open(R / 'shots' / s / f'{pre}_{t}_{v}.png') for s in ('before', 'tp')] for t in tiers for v in ('hf', 'hq')]
w, h = rows[0][0].size
cw, ch = int(w * 0.4), int(h * 0.9)
sheet = Image.new('RGB', (cw * 4, ch * len(tiers)))
for k, pair in enumerate(rows):
    for j, im in enumerate(pair):
        sheet.paste(im.crop((int(w * 0.3), 0, int(w * 0.3) + cw, ch)), (((k % 2) * 2 + j) * cw, (k // 2) * ch))
sheet.save(R / f'{out}.png')
print(R / f'{out}.png', sheet.size)
