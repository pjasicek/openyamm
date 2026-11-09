"""Per-face labels of the rest mesh (work/mesh_in.npz): dominant-bone region (hand = hand + finger weights > 0.5,
head, hair, arm, torso, tail) and base-colour class (gold by hue/saturation) -> work/face_info.npz; prints counts."""
import numpy as np
from PIL import Image
import colorsys
d = np.load('work/mesh_in.npz'); g = np.load('work/groups.npz'); W = g['W']; names = list(g['names'])
f, v = d['faces'], d['verts']; uv = d['wuv'].reshape(-1, 3, 2)
img = np.asarray(Image.open('work/basecolor.png').convert('RGB'), np.float32) / 255; H, Wd = img.shape[:2]
B = np.random.default_rng(1).dirichlet((1, 1, 1), 9)
u = np.einsum('sk,fkc->fsc', B, uv)
x = np.clip((u[..., 0] % 1) * Wd, 0, Wd - 1).astype(int); y = np.clip((1 - u[..., 1] % 1) * H, 0, H - 1).astype(int)
col = img[y, x]  # (F, 9, 3)
mx = col.max(-1); mn = col.min(-1); sat = (mx - mn) / np.maximum(mx, 1e-6)
hue = np.array([[colorsys.rgb_to_hsv(*c)[0] for c in fc] for fc in col])
gold_s = (hue > 0.10) & (hue < 0.18) & (sat > 0.55) & (mx > 0.55)
gold = gold_s.mean(1) > 0.5
idx = lambda pred: [i for i, n in enumerate(names) if pred(n)]
fingers = ('thumb', 'index', 'middle', 'ring', 'pinky')
hand = W[:, idx(lambda n: n.endswith('_Hand') or any(k in n for k in fingers))].sum(1)
head = W[:, idx(lambda n: n in ('Head',))].sum(1)
hair = W[:, idx(lambda n: n.startswith('Hair'))].sum(1)
arm = W[:, idx(lambda n: 'Arm' in n or 'Forearm' in n or 'Shoulder' in n)].sum(1)
tail = W[:, idx(lambda n: n.startswith('Serpent'))].sum(1)
fm = lambda a: a[f].mean(1)
region = np.full(len(f), 'torso', object)
region[fm(tail) > .5] = 'tail'; region[fm(arm) > .5] = 'arm'; region[fm(hair) > .5] = 'hair'
region[fm(head) > .5] = 'head'; region[fm(hand) > .5] = 'hand'
c = v[f].mean(1)
np.savez('work/face_info.npz', region=region.astype(str), gold=gold, centroid=c, hand=fm(hand), head=fm(head))
for r in np.unique(region):
    m = region == r; print(r, m.sum(), 'gold', (m & gold).sum())
print('gold total', gold.sum())
