import sys, numpy as np
from PIL import Image, ImageDraw
d = np.load(sys.argv[1] + '.npz', allow_pickle=False); out = sys.argv[1]
bv, bt, mv, mt = d['bv'], d['bt'], d['mv'], d['mt']; names = list(d['names']); par = list(d['par']); pos = d['pos']
sc = 420; W = 1000; H = 900
def proj(p, view):
    if view == 0: x, y = p[..., 0], p[..., 2]
    else: x, y = p[..., 1], p[..., 2]
    return np.stack([W / 2 + x * sc, H - 30 - y * sc], -1)
ims = []
for view in (0, 1):
    a = Image.new('L', (W, H), 0); ad = ImageDraw.Draw(a)
    for t in bt: ad.polygon([tuple(q) for q in proj(bv[t[:3]], view)], fill=255)
    b = Image.new('L', (W, H), 0); bd = ImageDraw.Draw(b)
    for t in mt: bd.polygon([tuple(q) for q in proj(mv[t[:3]], view)], fill=255)
    ia, ib = np.array(a), np.array(b)
    im = Image.fromarray(np.stack([ib, ia, (ia // 2 + ib // 2)], -1)); dr = ImageDraw.Draw(im)
    P = proj(pos, view)
    for i, n in enumerate(names):
        if par[i] in names:
            j = names.index(par[i]); dr.line([tuple(P[i]), tuple(P[j])], fill=(255, 255, 0), width=2)
    ims.append(im)
s = Image.new('RGB', (W * 2, H)); s.paste(ims[0], (0, 0)); s.paste(ims[1], (W, 0)); s.save(out)
