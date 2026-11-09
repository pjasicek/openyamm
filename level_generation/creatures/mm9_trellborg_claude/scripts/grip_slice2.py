"""Sections of the fist across the grip axis from work/hand_rest.npz, cyan = handle. Arg: out.png"""
import json, sys, numpy as np
from PIL import Image, ImageDraw
g = json.load(open('scripts/grip.json')); G, kn = np.array(g['G']), np.array(g['kn']); kn /= np.linalg.norm(kn)
T = np.load('work/hand_rest.npz')['T']; W = np.array(json.load(open('work/hands_v1.json'))['frames']['R']['W'])
e2 = W - G; e2 -= kn * (e2 @ kn); e2 /= np.linalg.norm(e2); e1 = np.cross(e2, kn)
S = 1900; R = .0255; im = Image.new('RGB', (2000, 500), (20, 20, 24)); d = ImageDraw.Draw(im)
for k, a in enumerate((-.06, -.02, .02, .06)):
    ox, oy = 250 + 500 * k, 170
    def Pt(p): q = p - G; return (ox + (q @ e1) * S, oy + (q @ e2) * S)
    s = (T - G) @ kn - a
    for t, x in zip(T, s):
        pts = [t[i] + (t[(i + 1) % 3] - t[i]) * x[i] / (x[i] - x[(i + 1) % 3]) for i in range(3) if x[i] * x[(i + 1) % 3] < 0]
        if len(pts) == 2: d.line([Pt(pts[0]), Pt(pts[1])], fill=(240, 200, 120), width=2)
    d.ellipse([ox - R * S, oy - R * S, ox + R * S, oy + R * S], outline=(90, 220, 255), width=2)
    d.text((ox - 230, 8), f'axial {a:+.2f}, wrist is down', fill=(255, 255, 255))
im.save(sys.argv[1])
