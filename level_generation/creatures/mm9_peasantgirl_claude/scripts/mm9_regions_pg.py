#!/usr/bin/env python3
"""MM9 skin texels by body region (PeasantGirl, from PeasantF5's mm9_regions.py): each PEASANTGIRL2 triangle rasterised into the 128 skin
with a label from its bones and bind position (soles at 0). Labels: 1 bodice, 2 skirt, 3 sleeve, 4 hair, 5 apron, 7 face/neck skin,
8 hand, 9 shoe/leg. Writes work/mm9_regions.npy and review/mm9_regions.png (the three skins with the labels tinted). Project folder."""
import sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, '../claude_shared/floor')
from glb_pose import Glb, Model
m = Model(Glb('source/mm9/pg2/pg2.glb')); doc = m.glb.json; jn = [doc['nodes'][j]['name'] for j in doc['skins'][0]['joints']]; g = m.glb
S = 128; LAB = np.zeros((S, S), int)
for node in doc['nodes']:
    if 'mesh' not in node or 'skin' not in node: continue
    pr = doc['meshes'][node['mesh']]['primitives'][0]; A = pr['attributes']
    pos = g.accessor(A['POSITION']).astype(float); P = np.c_[pos[:, 0], -pos[:, 2], pos[:, 1]] + [0, 0, 0.4797]
    tri = g.accessor(pr['indices']).astype(int).reshape(-1, 3); J = g.accessor(A['JOINTS_0']).astype(int); W = g.accessor(A['WEIGHTS_0'])
    uv = g.accessor(A['TEXCOORD_0']).astype(float)
    dom = np.array([jn[J[i][np.argmax(W[i])]] for i in range(len(pos))])
    im = Image.new('I', (S, S), 0); dr = ImageDraw.Draw(im)
    for t in tri:
        c = P[t].mean(0); bones = list(dom[t]); b = max(set(bones), key=bones.count)
        if any('Finger' in x or x.endswith('Hand') for x in bones): l = 8
        elif any(k in b for k in ('Calf', 'Foot', 'Toe')): l = 9
        elif any(k in b for k in ('UpperArm', 'Forearm')): l = 3
        elif b in ('Bip01 Head', 'Bip01 Ponytail1', 'Bip01 Ponytail11'): l = 7 if (c[1] < -0.05 and c[2] > 1.05) else 4
        elif b == 'Bip01 Neck': l = 7 if c[2] > 0.99 else 1
        elif c[2] > 0.70: l = 1
        elif c[1] < -0.06 and c[2] > 0.25 and abs(c[0]) < 0.12: l = 5
        else: l = 2
        dr.polygon([(float(uv[i, 0] * S), float(uv[i, 1] * S)) for i in t], fill=l)
    a = np.asarray(im); LAB[a > 0] = a[a > 0]
np.save('work/mm9_regions.npy', LAB)
COL = np.array([[0, 0, 0], [255, 0, 0], [0, 200, 0], [0, 0, 255], [255, 200, 0], [255, 255, 255], [0, 255, 255], [255, 0, 255], [255, 128, 0], [90, 60, 30]])
out = []
for t in ('pg2', 'pg3', 'pg1e'):
    sk = np.asarray(Image.open(f'source/mm9/{t}/skins/{t}.png').convert('RGB'), float)
    out.append((sk * 0.55 + COL[LAB] * 0.45 * (LAB > 0)[..., None] + sk * 0.45 * (LAB == 0)[..., None]).astype('u1'))
Image.fromarray(np.concatenate(out, 1)).resize((S * 3 * 4, S * 4), Image.NEAREST).save('review/mm9_regions.png')
print({k: int((LAB == k).sum()) for k in range(10)})
