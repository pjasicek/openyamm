"""Gold trim faces of the dwarf's cloth (hem/sleeve zigzag bands, buckle): body-atlas faces whose base colour is gold
(hue 30-60 deg, saturation > .35, value > .45) at more than half of 7 samples, grown by one face ring.
-> work/trim.npy"""
import numpy as np, colorsys
from PIL import Image
T = '../mm6_dwa1_codex/textures/'
body = np.asarray(Image.open(T + 'dwa1_basecolor_1k.png').convert('RGB'), np.float32) / 255
d = np.load('work/mesh_in.npz'); wuv = d['wuv'].reshape(-1, 3, 2); faces = d['faces']
hs = np.load('work/headset.npy'); cls = np.load('work/classes.npy')
c = wuv.mean(1, keepdims=True); pts = np.concatenate([wuv, c, (wuv + c) / 2], 1)
gold = np.zeros(len(wuv), bool)
for i, p in enumerate(pts):
    if hs[i]: continue
    n = 0
    for u, v in p:
        r, g, b = body[int(np.clip((1 - v) * 1024, 0, 1023)), int(np.clip(u * 2080, 0, 1023))]
        h, s, val = colorsys.rgb_to_hsv(r, g, b)
        n += 30 / 360 < h < 60 / 360 and s > .35 and val > .45
    gold[i] = n >= 4
# grow one ring by shared vertices
vmask = np.zeros(faces.max() + 1, bool); vmask[faces[gold].ravel()] = True
ring = vmask[faces].any(1) & ~hs
np.save('work/trim.npy', ring)
print('gold', int(gold.sum()), 'with ring', int(ring.sum()), 'by class', {int(k): int((ring & (cls == k)).sum()) for k in np.unique(cls)})
