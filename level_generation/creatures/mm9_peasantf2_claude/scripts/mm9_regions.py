#!/usr/bin/env python3
"""MM9 skin texels by body region, from MM9's own mesh: each PEASANTF5 triangle rasterised into the 256 skin with a label from its bones and
bind position. Labels: 1 bodice, 2 skirt, 3 sleeve, 4 scarf, 5 apron, 6 band, 7 face/skin, 8 hand, 9 shoe/leg, 10 ear.
Writes work/mm9_regions.npy and review/mm9_regions.png (skins A and B with the labels tinted). Project folder."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, '../claude_shared/floor')
from glb_pose import Glb, Model
m = Model(Glb('source/mm9/pf5b.glb')); doc = m.glb.json; jn = [doc['nodes'][j]['name'] for j in doc['skins'][0]['joints']]
g = m.glb
LAB = np.zeros((256, 256), int)
for node in doc['nodes']:
    if 'mesh' not in node or 'skin' not in node: continue
    pr = doc['meshes'][node['mesh']]['primitives'][0]; A = pr['attributes']
    pos = g.accessor(A['POSITION']).astype(float); P = np.c_[pos[:, 0], -pos[:, 2], pos[:, 1]] + [0, 0, 0.9297]
    tri = g.accessor(pr['indices']).astype(int).reshape(-1, 3); J = g.accessor(A['JOINTS_0']).astype(int); W = g.accessor(A['WEIGHTS_0'])
    uv = g.accessor(A['TEXCOORD_0']).astype(float)
    dom = np.array([jn[J[i][np.argmax(W[i])]] for i in range(len(pos))])
    im = Image.new('I', (256, 256), 0); dr = ImageDraw.Draw(im)
    for t in tri:
        c = P[t].mean(0); bones = set(dom[t]); b = max(bones, key=lambda x: list(dom[t]).count(x))
        if any('Finger' in x or x.endswith('Hand') for x in bones): l = 8
        elif any(x.startswith('xpony') for x in bones): l = 10
        elif any(k in b for k in ('Calf', 'Foot', 'Toe')): l = 9
        elif any(k in b for k in ('UpperArm', 'Forearm')): l = 3
        elif b in ('FHP Head', 'FHP Ponytail1', 'FHP Ponytail11', 'FHP Ponytail12', 'XCOM_Hair'):
            l = 7 if (c[1] < -0.06 and c[2] > 1.47) else 4
        elif b in ('FHP Neck',): l = 7
        elif c[2] > 1.13: l = 1
        elif c[2] > 1.06: l = 6
        elif c[1] < -0.06 and c[2] > 0.5 and abs(c[0]) < 0.16: l = 5
        else: l = 2
        dr.polygon([(float(uv[i, 0] * 256), float(uv[i, 1] * 256)) for i in t], fill=l)
    a = np.asarray(im); LAB[a > 0] = a[a > 0]
np.save('work/mm9_regions.npy', LAB)
COL = np.array([[0, 0, 0], [255, 0, 0], [0, 200, 0], [0, 0, 255], [255, 200, 0], [255, 255, 255], [0, 255, 255], [255, 0, 255], [255, 128, 0], [90, 60, 30], [128, 0, 255]])
out = []
for t in 'ab':
    sk = np.asarray(Image.open(f'source/mm9/skins/pf5{t}.png').convert('RGB'), float)
    out.append((sk * 0.55 + COL[LAB] * 0.45 * (LAB > 0)[..., None] + sk * 0.45 * (LAB == 0)[..., None]).astype('u1'))
Image.fromarray(np.concatenate(out, 1)).resize((1024, 512), Image.NEAREST).save('review/mm9_regions.png')
print({k: int((LAB == k).sum()) for k in range(11)})
