"""The MM9 shield in its own frame: long axis tip -> top, half widths from MM9's vertices, made symmetric. Writes work/shield_frame.json and the outline template references_shield/outline.png (1024x1536, 1 m = 1100 px, tip down). Run with the gltf venv, project folder."""
import json
import numpy as np
from PIL import Image, ImageDraw
P = np.unique(np.load('work/shield_verts.npy').astype(float).round(4), axis=0)     # glTF axes, true-handed
c = P.mean(0); w, V = np.linalg.eigh(np.cov((P - c).T)); V = V[:, ::-1]
a1, a2, a3 = V.T
if a3[0] < 0: a3 = -a3
Q = (P - c) @ V
tip = P[np.argsort((P - c) @ a1)[:4]].mean(0)
top = P[np.argmax((P - c) @ a1)]
L = top - tip; length = np.linalg.norm(L); L /= length
n = a3 - L * (a3 @ L); n /= np.linalg.norm(n)
W = np.cross(n, L)
Sv = (P - tip) @ L; Wv = (P - tip) @ W; Nv = (P - tip) @ n
plate = np.abs(Nv - np.median(Nv)) < 0.05
st = []
for s0 in (0.0, 0.40, 1.0, 1.26):
    m = plate & (np.abs(Sv - s0) < 0.09)
    st.append((round(float(Sv[m].mean()), 3), round(float(0.5 * (Wv[m].max() - Wv[m].min())), 3), round(float(0.5 * (Wv[m].max() + Wv[m].min())), 3)))
print('STATIONS', st, 'length', round(length, 3))
hand = P[Nv < np.median(Nv) - 0.03]
print('HANDLE', hand.mean(0).round(3), 'plate n', np.round([Nv[plate].min(), Nv[plate].max()], 3), 'handle n', np.round(Nv[~plate].min(), 3))
mid = tip + W * np.mean([x[2] for x in st[:4]])
json.dump(dict(tip=mid.tolist(), L=L.tolist(), W=W.tolist(), n=n.tolist(), length=length, stations=st, handle=hand.mean(0).tolist(), plate_n=float(np.median(Nv[plate]))), open('work/shield_frame.json', 'w'), indent=0)
PX = 1100
im = Image.new('RGBA', (1024, 1536), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
x0, y0 = 512, 1536 - 45
pts = [(st[0][0], st[0][1]), (st[1][0], st[1][1]), (st[2][0], st[2][1]), (st[3][0], st[3][1]), (length, 0.0)]
poly = [(x0 + w_ * PX, y0 - s * PX) for s, w_ in pts] + [(x0 - w_ * PX, y0 - s * PX) for s, w_ in pts[::-1][1:]]
d.polygon(poly, fill=(235, 235, 235, 255))
im.save('references_shield/outline.png')
print('OUTLINE', [(round(a), round(b)) for a, b in poly])
