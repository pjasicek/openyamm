"""Per-face material class of the dwarf from the Codex class maps (1 skin, 2 hair/beard, 6 eyes, 8 cloth/leather,
9 metal, 10 wood): majority of samples at the corners and centre in the 2080x1024 runtime atlas (body 0-1023,
head 1056-2079). -> work/classes.npy."""
import numpy as np
from PIL import Image
T = '../mm6_dwa1_codex/textures/'
body = np.array(Image.open(T + 'dwa1_material_classes_1k.png')); head = np.array(Image.open(T + 'dwa1_head_material_classes_1k.png'))
if body.ndim == 3: body = body[..., 0]
if head.ndim == 3: head = head[..., 0]
d = np.load('work/mesh_in.npz'); wuv = d['wuv'].reshape(-1, 3, 2)
pts = np.concatenate([wuv, wuv.mean(1, keepdims=True), (wuv + wuv.mean(1, keepdims=True)) / 2], 1)
cls = np.zeros(len(wuv), int)
for i, p in enumerate(pts):
    px = p[:, 0] * 2080; py = (1 - p[:, 1]) * 1024
    vals = []
    for x, y in zip(px, py):
        yi = int(np.clip(y, 0, 1023))
        if x >= 1056: vals.append(head[yi, int(np.clip(x - 1056, 0, 1023))])
        else: vals.append(body[yi, int(np.clip(x, 0, 1023))])
    vals = [v for v in vals if v] or [0]
    cls[i] = np.bincount(vals).argmax()
np.save('work/classes.npy', cls)
hs = np.load('work/headset.npy')
for c in np.unique(cls): print('class', c, 'faces', int((cls == c).sum()), 'headset', int((hs & (cls == c)).sum()))
