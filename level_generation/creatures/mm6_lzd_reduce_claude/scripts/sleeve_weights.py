#!/usr/bin/env python3
"""Tunic sleeves that follow the upper arms. Round 6 weights both sleeves fully to B_Spine2 out to the cuff while the
arm skin is an open tube starting inside the sleeve (about 40 % / 50 % along the right / left upper arm); in the
draw the right arm slid out and the sleeve showed its open, empty end (user, Attack frame 15 from behind).
Per side, in the bind pose, on the tunic piece (pieces with at least three non-arm vertices within RADIUS of the
upper-arm axis past s 0.4; pauldrons and straps keep their weights), every non-arm-skin vertex takes
    (1 - f) * own weights + f * weights of the nearest arm-skin vertex,
f = smoothstep((s - S0) / (S1 - S0)) * smoothstep((RADIUS + FALL - r) / FALL), smoothed SMOOTH times over the welded
surface, with s along the upper arm (shoulder joint 0, elbow 1) and r the distance from its axis; S1 is capped at
LEAD before the tube's open end (5th percentile of the arm skin's s). The sleeve blends off the chest across the
shoulder like shoulder skin and moves with the tube. A blend held off until s 0.45 stretched the back of the sleeve
into a flat sheet in the draw (`review/back/sleeve_zoom.png`); a hard radius edge stretched short edges 5-7x.
Applied to every colour and shadow mesh (top eight influences, renormalised). Usage: sleeve_weights.py <in> <out>"""
import struct, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402
import os
RADIUS, LEAD = float(os.environ.get('SLEEVE_R', '0.14')), 0.05
FALL, SMOOTH = float(os.environ.get('SLEEVE_FALL', '0.05')), int(os.environ.get('SLEEVE_SMOOTH', '4'))
S0, S1 = float(os.environ.get('SLEEVE_S0', '-0.05')), float(os.environ.get('SLEEVE_S1', '0.2'))
doc, binary = read_glb(Path(sys.argv[1])); binary = bytearray(binary)
node = next(n for n in doc['nodes'] if n.get('name') == 'Lizard'); skin = doc['skins'][node['skin']]
names = [doc['nodes'][i]['name'] for i in skin['joints']]; J = len(names)
CODES = {5121: ('B', 1, 255.), 5123: ('H', 2, 65535.), 5125: ('I', 4, 1.), 5126: ('f', 4, 1.)}


def view(ai):
    a = doc['accessors'][ai]; v = doc['bufferViews'][a['bufferView']]; code, size, scale = CODES[a['componentType']]
    k = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[a['type']]
    assert v.get('byteStride', size * k) == size * k, 'interleaved accessor'
    off = v.get('byteOffset', 0) + a.get('byteOffset', 0)
    return off, code, a['count'], k, scale


def get(ai):
    off, code, n, k, scale = view(ai)
    x = np.array(struct.unpack_from(f'<{n * k}{code}', binary, off), float).reshape(n, k)
    return x / scale if code != 'f' and doc['accessors'][ai].get('normalized') else x


def put(ai, x):
    off, code, n, k, scale = view(ai)
    if code != 'f':
        x = np.rint(x * scale) if doc['accessors'][ai].get('normalized') else np.rint(x)
        vals = [int(v) for v in x.reshape(-1)]
    else:
        vals = [float(v) for v in x.reshape(-1)]
    struct.pack_into(f'<{n * k}{code}', binary, off, *vals)


ibm = get(skin['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1)  # column-major
jpos = np.array([np.linalg.inv(m)[:3, 3] for m in ibm])
arm_ids = {s: [i for i, n in enumerate(names) if n.startswith(f'B_{s}_') and ('Arm' in n or 'Forearm' in n)] for s in 'LR'}
done = set(); report = []
meshes = [node['mesh']] + doc['meshes'][node['mesh']]['extras']['openyamm_lods'] + doc['meshes'][node['mesh']]['extras']['openyamm_shadow_lods']
for mi in meshes:
    for prim in doc['meshes'][mi]['primitives']:
        at = prim['attributes']; key = (at['POSITION'], at['WEIGHTS_0'])
        if key in done: continue
        done.add(key)
        P = get(at['POSITION']); n = len(P); W = np.zeros((n, J))
        sets = [s for s in ('0', '1') if 'JOINTS_' + s in at]
        for s in sets:
            jj, ww = get(at['JOINTS_' + s]).astype(int), get(at['WEIGHTS_' + s])
            np.add.at(W, (np.repeat(np.arange(n), 4), jj.reshape(-1)), ww.reshape(-1))
        F = get(prim['indices']).astype(int).reshape(-1, 3)
        _, weld = np.unique(np.round(P, 5), axis=0, return_inverse=True); weld = weld.reshape(-1)
        r = np.r_[F[:, 0], F[:, 1], F[:, 2], np.arange(n)]; c = np.r_[F[:, 1], F[:, 2], F[:, 0], n + weld]
        lab = connected_components(coo_matrix((np.ones(len(r)), (r, c)), shape=(n + weld.max() + 1,) * 2), directed=False)[1][:n]
        new = W.copy(); changed = 0
        for side in 'LR':
            sh, el = jpos[names.index(f'B_{side}_UpperArm')], jpos[names.index(f'B_{side}_Forearm')]
            ax = el - sh; L = np.linalg.norm(ax); ax /= L
            d = P - sh; s = d @ ax / L; rad = np.linalg.norm(d - np.outer(d @ ax, ax), axis=1)
            armw = W[:, arm_ids[side]].sum(1); skinv = armw >= .5
            tube = skinv & (rad < RADIUS) & (s > .1)
            if not tube.any(): continue
            s_tube = np.percentile(s[tube], 5)
            cand = (~skinv) & (rad < RADIUS + FALL) & (s > S0) & (s < 1.1)
            pc, cnt = np.unique(lab[cand & (s > .4) & (rad < RADIUS)], return_counts=True); pieces = pc[cnt >= 3]
            if os.environ.get('SLEEVE_DEBUG'):
                for q in pieces: print('  mesh', mi, 'piece', side, q, (lab == q).sum(), 'verts')
            area = (~skinv) & np.isin(lab, pieces)
            if not area.any(): continue
            t = np.clip((s - S0) / (min(S1, s_tube - LEAD) - S0), 0, 1)
            u = np.clip((RADIUS + FALL - rad) / FALL, 0, 1)
            f = np.where(area & (s > S0) & (s < 1.1), t * t * (3 - 2 * t) * u * u * (3 - 2 * u), 0.)
            # smooth f over the welded surface of the piece: no hard edge between moved and kept vertices
            g = weld; A = coo_matrix((np.ones(3 * len(F)), (g[np.r_[F[:, 0], F[:, 1], F[:, 2]]], g[np.r_[F[:, 1], F[:, 2], F[:, 0]]])),
                                     shape=(g.max() + 1,) * 2).tocsr(); A = ((A + A.T) > 0).astype(float)
            fw = np.zeros(g.max() + 1); np.maximum.at(fw, g, f); inside = np.zeros(g.max() + 1, bool); inside[g[area]] = True
            deg = np.asarray(A.sum(1)).ravel()
            for _ in range(SMOOTH):
                fw = np.where(inside, .5 * fw + .5 * (A @ fw) / np.maximum(deg, 1), 0)
            f = np.where(area, fw[g], 0.); sel = f > 1e-4
            near = np.flatnonzero(skinv)[cKDTree(P[skinv]).query(P[sel])[1]]
            new[sel] = (1 - f[sel])[:, None] * W[sel] + f[sel][:, None] * W[near]; changed += int(sel.sum())
            if mi == node['mesh']: report.append(f'{side}: s_tube {s_tube:.2f}, {int(sel.sum())} sleeve vertices')
        # top eight, renormalised, back into the two sets
        order = np.argsort(-new, axis=1)[:, :4 * len(sets)]; vals = np.take_along_axis(new, order, 1)
        vals /= vals.sum(1, keepdims=True)
        for k, s in enumerate(sets):
            jj, ww = order[:, 4 * k:4 * k + 4], vals[:, 4 * k:4 * k + 4]
            jj = np.where(ww > 0, jj, 0)
            put(at['JOINTS_' + s], jj.astype(float)); put(at['WEIGHTS_' + s], ww)
        if changed: report.append(f'mesh {mi} prim: {changed} vertices reweighted')
print('\n'.join(report)); write_glb(Path(sys.argv[2]), doc, binary)
