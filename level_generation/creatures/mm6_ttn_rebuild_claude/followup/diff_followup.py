#!/usr/bin/env python3
"""What the follow-up (clean fists) changed against the installed hands rebuild (exit 1 on anything unintended).
Must hold: node names, every node TRS except the 30 finger nodes' rest (graft rest at hand_tris 1900), skin joint
order and the original joints' inverse binds; every non-finger animation channel's data; materials; LOD0 body
vertices (those of the pre-rebuild GLB without hand/finger weight; the graft's wrist stub is hand) identical
(position, UV, joints, weights; normals within 5e-3) apart from the restored bracer faces;
image pixels outside the hand rectangles. Reported: finger channels changed per clip, LOD triangle counts.
Usage: diff_followup.py <installed.glb> <new.glb>"""
import io, json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
import glb_pose as gp
HERE = Path(__file__).resolve().parents[1]
A, B = gp.Glb(sys.argv[1]), gp.Glb(sys.argv[2]); bad = []
na = [n.get('name') for n in A.json['nodes']]; nb = [n.get('name') for n in B.json['nodes']]
finger = lambda n: n and 'Hand' in n and n[-1].isdigit()
if na != nb:
    bad.append('node names')
for x, y, n in zip(A.json['nodes'], B.json['nodes'], na):
    if not finger(n) and any(not np.allclose(x.get(k, d), y.get(k, d), atol=1e-6)
                             for k, d in (('translation', [0, 0, 0]), ('rotation', [0, 0, 0, 1]), ('scale', [1, 1, 1]))):
        bad.append(f'node TRS {n}')
ja, jb = A.json['skins'][0]['joints'], B.json['skins'][0]['joints']
if ja != jb:
    bad.append('skin joints')
ia = A.accessor(A.json['skins'][0]['inverseBindMatrices']); ib = B.accessor(B.json['skins'][0]['inverseBindMatrices'])
for k, j in enumerate(ja):
    if not finger(na[j]) and not np.allclose(ia[k], ib[k], atol=1e-6):
        bad.append(f'inverse bind {na[j]}')
for an, bn in zip(A.json['animations'], B.json['animations']):
    changed = []
    for ca, cb in zip(an['channels'], bn['channels']):
        node = na[ca['target']['node']]
        if ca['target'] != cb['target']:
            bad.append(f"{an['name']} channel order"); break
        sa, sb = an['samplers'][ca['sampler']], bn['samplers'][cb['sampler']]
        same = np.array_equal(A.accessor(sa['input']), B.accessor(sb['input'])) and \
            np.allclose(A.accessor(sa['output']), B.accessor(sb['output']), atol=1e-6)
        if not same:
            (changed if finger(node) else bad).append(node if finger(node) else f"{an['name']} {node}")
    print(f"{an['name']:10s} finger channels changed {len(changed)}")
if json.dumps(A.json['materials']) != json.dumps(B.json['materials']):
    bad.append('materials')


def lod0(g):
    p = g.json['meshes'][0]['primitives'][0]; at = p['attributes']; names = [n.get('name') for n in g.json['nodes']]
    joints = [names[j] for j in g.json['skins'][0]['joints']]
    J = g.accessor(at['JOINTS_0']).astype(int); W = g.accessor(at['WEIGHTS_0'])
    hand = np.array([any('Hand' in joints[J[i][k]] and W[i][k] > 0 for k in range(4)) for i in range(len(J))])
    return {k: g.accessor(at[k]) for k in ('POSITION', 'NORMAL', 'TEXCOORD_0', 'JOINTS_0', 'WEIGHTS_0')}, hand
va, ha = lod0(A); vb, hb = lod0(B)
# the graft's wrist stub (inside the bracer) carries only forearm weights: body = vertices of the pre-rebuild GLB
v0, _ = lod0(gp.Glb(HERE / 'work/before_rebuild/mm6_ttn.glb'))
ha = ha | (cKDTree(v0['POSITION']).query(va['POSITION'])[0] > 1e-6)
key = lambda v, m: np.concatenate([v['POSITION'][m], v['TEXCOORD_0'][m] * 0.01], 1)   # seam copies differ by UV
d, i = cKDTree(key(vb, np.ones(len(hb), bool))).query(key(va, ~ha))
miss = int((d > 1e-6).sum()); other = 0; ok = d <= 1e-6
for k, tol in (('NORMAL', 5e-3), ('JOINTS_0', 0), ('WEIGHTS_0', 1e-5)):   # normals: float re-export noise < 0.3 deg
    other += int((~np.isclose(va[k][~ha][ok].astype(float), vb[k][i[ok]].astype(float), atol=tol).all(1)).sum())
print(f'LOD0 body vertices {int((~ha).sum())}: missing {miss}, attribute differences {other}')
if miss or other:
    bad.append('LOD0 non-hand vertices')
rects = json.load(open(HERE / 'scripts/graft_ttn.json'))['rects']


def images(g):
    out = {}
    for im in g.json['images']:
        v = g.json['bufferViews'][im['bufferView']]; o = v.get('byteOffset', 0)
        out[im.get('name')] = np.asarray(Image.open(io.BytesIO(bytes(g.bin[o:o + v['byteLength']]))))
    return out
xa, xb = images(A), images(B)
for name, a in xa.items():
    b = xb.get(name)
    if b is None or a.shape != b.shape:
        print(f'image {name}: {"missing" if b is None else "resized"}'); continue
    diff = (a != b).reshape(a.shape[0], a.shape[1], -1).any(-1)
    if 'lod' in name.lower():
        print(f'image {name}: changed {int(diff.sum())} px (far-LOD bake)'); continue
    inside = np.zeros_like(diff)
    for x0, y0, w, h in rects.values():
        inside[y0:y0 + h, x0:x0 + w] = True
    print(f'image {name}: changed {int(diff.sum())} px, outside the hand rectangles {int((diff & ~inside).sum())}')
    if (diff & ~inside).any():
        bad.append(f'pixels outside the hand rectangles in {name}')
tri = lambda g: [sum(len(g.accessor(p['indices'])) // 3 for p in m['primitives']) for m in g.json['meshes'] if 'Shadow' not in m['name']]
print('LOD triangles', tri(A), '->', tri(B))
print('UNEXPECTED:', ', '.join(sorted(set(bad))) or 'none')
sys.exit(1 if bad else 0)
