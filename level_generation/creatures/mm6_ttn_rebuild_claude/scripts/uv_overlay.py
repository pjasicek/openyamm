"""Draw the LOD0 UV layout on the base colour atlas; faces whose vertices are mostly weighted to the hands in colour."""
import sys, numpy as np
from PIL import Image, ImageDraw
d = np.load(sys.argv[1]); img = Image.open(sys.argv[2]).convert('RGB'); out = sys.argv[3]
names = list(d['names']); W, H = img.size
uv = d['uv']; idx = d['idx'].reshape(-1, 3); j = d['j']; w = d['w']
def share(bone):
    b = names.index(bone); return ((j == b) * w).sum(1)
lh, rh = share('LeftHand'), share('RightHand')
dr = ImageDraw.Draw(img)
occ = Image.new('L', (W, H), 0); do = ImageDraw.Draw(occ)
for t in idx:
    pts = [(uv[k][0] * W, uv[k][1] * H) for k in t]
    do.polygon(pts, fill=255)
    if lh[t].mean() > 0.5: dr.polygon(pts, outline=(0, 255, 0))
    elif rh[t].mean() > 0.5: dr.polygon(pts, outline=(255, 0, 255))
img.save(out); occ.save(out.replace('.png', '_occ.png'))
o = np.array(occ) > 0
print('occupied body half', o[:, :1024].mean(), 'head half', o[:, 1056:].mean())
for nm, s in (('L', lh), ('R', rh)):
    sel = [t for t in idx if s[t].mean() > 0.5]
    u = np.array([uv[k] for t in sel for k in t])
    print(nm, 'faces', len(sel), 'uv bbox', u.min(0).round(3), u.max(0).round(3))
