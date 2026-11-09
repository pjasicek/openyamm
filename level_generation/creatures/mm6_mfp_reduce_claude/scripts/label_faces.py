"""Per-face labels of the source body for per-region budgets (work/mesh_in.npz order = loop triangles):
colour class from the base colour at the face's UV corners+centre (gold / dark hair / skin / other), dominant bone
(work/dom.npy), connected component size (work/comp.npy). Prints a table; saves work/labels.npz."""
import numpy as np, collections
from PIL import Image
d = np.load('work/mesh_in.npz'); dom = np.load('work/dom.npy'); comp = np.load('work/comp.npy')
img = np.asarray(Image.open('work/mfp_basecolor_head_atlas.png').convert('RGB')).astype(float) / 255
H, W = img.shape[:2]
wuv = d['wuv'].reshape(-1, 3, 2) % 1.0
pts = np.concatenate([wuv, wuv.mean(1, keepdims=True)], 1)
px = np.clip((pts[..., 0] * W).astype(int), 0, W - 1); py = np.clip(((1 - pts[..., 1]) * H).astype(int), 0, H - 1)
col = img[py, px].mean(1)
r, g, b = col.T; mx = col.max(1); mn = col.min(1); sat = (mx - mn) / np.maximum(mx, 1e-3)
gold = (r > .55) & (g > .45) & (b < .6 * g) & (sat > .3)
dark = mx < .16
headset = wuv.mean(1)[:, 0] > float(__import__("os").environ.get("HEAD_U", "0.795"))  # round 3: head set right of the 4096/5152 body block
size = np.bincount(comp)[comp]
head = dom == 'B_Head'
hand = np.array([('Hand' in n or 'Finger' in n) for n in dom])
braid = np.array([n.startswith('Braid') for n in dom])
print('faces', len(dom), 'headset', headset.sum(), 'head-bone', head.sum())
print('headset & gold', (headset & gold).sum(), 'dark', (headset & dark).sum(), 'other', (headset & ~gold & ~dark).sum())
print('body gold', (~headset & gold).sum())
for s in [50, 80, 100, 150]:
    print('small comps <=', s, (size <= s).sum())
print('hands', hand.sum(), 'braid', braid.sum(), 'braid comp', np.bincount(comp)[comp[braid]][:1])
print('headset bones', collections.Counter(dom[headset]).most_common(6))
np.savez('work/labels.npz', gold=gold, dark=dark, headset=headset, size=size, head=head, hand=hand, braid=braid)
