import sys, numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, sys.path[0])
from pglb import load, lod0_body
g, m, names = load(sys.argv[1])
prim, dom = lod0_body(m)
P = prim['positions']
inv = {v: k for k, v in names.items()}
sel = np.isin(dom, [names['B_Head'], names['B_Neck']])
print('head/neck verts', sel.sum())
H = P[dom == names['B_Head']]
print('B_Head verts bounds', H.min(0).round(3), H.max(0).round(3))
N = P[dom == names['B_Neck']]
print('B_Neck verts bounds', N.min(0).round(3), N.max(0).round(3))
W = m.world({})
for b in ('B_Head', 'B_Neck', 'B_Spine2', 'B_L_Clavicle', 'B_L_UpperArm', 'B_L_Hand', 'B_R_Hand'):
    print(b, W[names[b]][:3, 3].round(3))
# plots: side (z right, y up), front (x right, y up), top (x right, z up)
cols = {names['B_Head']: (255, 200, 60), names['B_Neck']: (80, 200, 255)}
def plot(ax, ay, fn, box):
    im = Image.new('RGB', (800, 800), (30, 30, 30)); d = ImageDraw.Draw(im)
    (x0, x1), (y0, y1) = box
    for v, j in zip(P, dom):
        if v[1] < 1.3: continue
        c = cols.get(j, (110, 110, 110))
        px = (v[ax] - x0) / (x1 - x0) * 800; py = 800 - (v[ay] - y0) / (y1 - y0) * 800
        d.point((px, py), fill=c)
    # grid every 0.05
    for t in np.arange(-1, 3, 0.05):
        px = (t - x0) / (x1 - x0) * 800; py = 800 - (t - y0) / (y1 - y0) * 800
        d.line([(px, 0), (px, 4)], fill=(255, 255, 255)); d.line([(0, py), (4, py)], fill=(255, 255, 255))
        if abs(t*10 - round(t*10)) < 1e-6:
            d.text((px, 6), f'{t:.1f}', fill=(255,255,255)); d.text((6, py), f'{t:.1f}', fill=(255,255,255))
    im.save(fn)
out = sys.argv[2]
plot(2, 1, out + '_side.png', ((-0.5, 0.3), (1.3, 2.1)))
plot(0, 1, out + '_front.png', ((-0.4, 0.4), (1.3, 2.1)))
