#!/usr/bin/env python3
"""Spine-chain, beard and braid weights of the MM7 Dwarf m190 (follow-up to the anim stream's Hit fix, 2026-11-11).

    reweight_trunk.py <in.glb> <out.glb> [--labels <out.npz>] [--beard H,N,S] [--opt key=value ...]

Why: the Meshy skin put the chest, upper back, beard and braids on B_Spine (plus clavicles, head and even the thighs
at the beard tip); B_Spine1 and B_Spine2 carried no weight at all and B_Neck almost none. Any clip that bends
Spine1/Spine2 or turns the head moved the shoulders and head over a chest and beard that stayed with B_Spine, and the
surface between them folded (the beard crumpled at the throat in Attack, Fidget, Death and Hit).

What changes with the defaults (the accepted configuration; only vertices of the torso shell - torso, head, face,
beard, back hair, collar -, the braid shells and the shoulder guards; arms, hands, legs, skirts, helmet, horns, eyes
and buckle keep their weights exactly):
- Chest and back: the B_Spine weight (Spine1/Spine2 had none) is spread over B_Spine, B_Spine1 and B_Spine2 by height
  with linear tents between the bone midpoints (Spine 0.785, Spine1 0.868, Spine2 0.935 m; all B_Spine below 0.785,
  all B_Spine2 above 0.935). Pelvis, neck, head, clavicle, upper-arm and thigh weights are kept: moving them as well
  (the first trials, `--opt` keys arm/clav/clav_low/clav_high/thigh/chain_only/keep_pelvis) made the waist and the
  shoulder blades worse.
- Beard and braids: the chin on the head, the rest riding with the chest under it. Head 1 at the jaw (y >= 1.0 m),
  blending by 0.86 m (`beard_y`) to the mix --beard (Head, Neck, chest; default 0.1 / 0.1 / 0.8), where the chest
  share uses the B_Spine/B_Spine1/B_Spine2 tents at the beard's own height (`beard_chest`). So the beard turns and
  nods with the chin over the throat and lies on the chest like cloth below it. A beard on the head and neck as one
  rigid mass (the first trials: Head 0.55, Neck 0.25, Spine2 0.20 below 0.88 m) lifted off the chest whenever the head
  tilted back (Fidget, the Hit recoil) and opened a gap to the belly at its tip.
  The beard is the torso shell's head-texture part in front (z > 0) below 1.06 m (with the left braid, which is welded
  into that shell), plus the separate braid shells.
- The beard's border is blended into the chest over eight averaging rings of the welded LOD0 surface (beardness
  0..1, `rings`); no beardness on the belly below 0.70-0.80 m round the beard tip (`b_low`), where the chest stays on
  its own weights.
- At most as many influences as the primitive has slots (4 on LOD0, LOD2, LOD3; 8 on LOD1), renormalised.
LOD1..3 and the shadow meshes take the labels (shell class and beardness) of the nearest LOD0 vertex and the same
rules on their own weights. The mesh, UVs, normals, skins, inverse binds and clips are not touched.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
import glb_pose  # noqa: E402

CHAIN = [('B_Pelvis', 0.70), ('B_Spine', 0.785), ('B_Spine1', 0.868), ('B_Spine2', 0.935), ('B_Neck', 0.99),
         ('B_Head', 1.04)]
MID_X = -0.009  # the spine chain's x
TORSO, BRAID, GUARD, OTHER = 1, 2, 3, 0


def smoothstep(x, a, b):
    t = np.clip((np.asarray(x, float) - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def weld_components(P, T):
    key = np.round(P / 1e-5).astype(np.int64)
    _, wid = np.unique(key, axis=0, return_inverse=True)
    wid = wid.ravel()
    e = np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
    n = wid.max() + 1
    A = coo_matrix((np.ones(len(e)), (wid[e[:, 0]], wid[e[:, 1]])), shape=(n, n)).tocsr()
    A = ((A + A.T) > 0).astype(float)
    _, lab = connected_components(A, directed=False)
    return wid, lab[wid], A


def lod0_labels(g):
    """Shell class and beardness per LOD0 vertex."""
    prim = g.json['meshes'][0]['primitives'][0]
    P = g.accessor(prim['attributes']['POSITION']).astype(np.float64)
    T = g.accessor(prim['indices']).astype(np.int64).reshape(-1, 3)
    uv = g.accessor(prim['attributes']['TEXCOORD_0'])
    wid, comp, A = weld_components(P, T)
    head_uv = uv[:, 0] > 0.51
    sizes = np.bincount(comp)
    torso = int(np.argmax(sizes))
    cls = np.full(len(P), OTHER)
    cls[comp == torso] = TORSO
    for c in range(len(sizes)):
        s = comp == c
        if c == torso:
            continue
        lo, hi = P[s, 1].min(), P[s, 1].max()
        if head_uv[s].all() and lo < 0.85:
            cls[s] = BRAID  # braid shells and braid ends (helmet, horns and eyes start above 1.09 m)
        elif not head_uv[s].any() and 0.74 < lo < 0.76 and 0.95 < hi < 1.0:
            cls[s] = GUARD  # shoulder guards and their rims
    beard = (cls == TORSO) & head_uv & (P[:, 2] > 0.0) & (P[:, 1] < 1.06)
    # beardness over the welded torso surface: 1 on the beard, averaging rings into the chest
    nw = wid.max() + 1
    bw = np.zeros(nw)
    np.maximum.at(bw, wid, beard.astype(float))
    torso_w = np.zeros(nw, bool)
    torso_w[wid[cls == TORSO]] = True
    At = A.multiply(torso_w[:, None]).multiply(torso_w[None, :]).tocsr()
    deg = np.asarray(At.sum(1)).ravel()
    inside = bw > 0
    for _ in range(int(OPT['rings'][0])):
        bw = np.where(torso_w, (At @ bw + bw) / (deg + 1), 0.0)
        if OPT['b_inside']:
            bw = np.where(inside, bw, 0.0)
    b = bw[wid]
    if OPT['b_low']:  # no beard share on the belly round the beard tip
        b = np.where(beard, b, b * smoothstep(P[:, 1], *OPT['b_low']))
    if OPT['b_tip']:  # the very tip of the beard lies on the belt
        b = np.where(beard, b * smoothstep(P[:, 1], *OPT['b_tip']), b)
    b[cls == BRAID] = 1.0
    b[(cls != TORSO) & (cls != BRAID)] = 0.0
    return P, cls, np.clip(b, 0, 1), beard


OPT = {'arm': None, 'clav': None, 'clav_low': None, 'clav_high': None, 'thigh': None, 'neck_x': (0.07, 0.13),
       'chain_only': (1,), 'keep_pelvis': (1,), 'rings': (8,), 'b_inside': None, 'b_low': (0.70, 0.80), 'b_tip': None,
       'beard_y': (0.86, 1.0), 'sigma': None, 'beard_chest': (1,)}


def rule(P, Wf, cls, b, idx, beard_mix):
    """New dense weights (n, joints) for the affected vertices; Wf is the old dense weights."""
    x, y = P[:, 0], P[:, 1]
    W = Wf.copy()
    pool = np.zeros(len(P))
    for side, sgn in (('L', 1.0), ('R', -1.0)):
        sx = sgn * (x - MID_X)
        f_arm = smoothstep(sx, *OPT['arm']) if OPT['arm'] else np.ones(len(P))
        for nm in (f'B_{side}_UpperArm', f'B_{side}_UpperArmTwist'):
            k = idx[nm]
            pool += W[:, k] * (1 - f_arm)
            W[:, k] *= f_arm
        f_cl = np.ones(len(P))
        if OPT['clav']:
            f_cl *= smoothstep(sx, *OPT['clav'])
        if OPT['clav_low']:
            f_cl *= smoothstep(y, *OPT['clav_low'])
        if OPT['clav_high']:
            f_cl *= 1 - smoothstep(y, *OPT['clav_high'])
        k = idx[f'B_{side}_Clavicle']
        pool += W[:, k] * (1 - f_cl)
        W[:, k] *= f_cl
        k = idx[f'B_{side}_Thigh']
        f_th = 1 - smoothstep(y, *OPT['thigh']) if OPT['thigh'] else np.ones(len(P))
        pool += W[:, k] * (1 - f_th)
        W[:, k] *= f_th
    chain = CHAIN[:4] if OPT['chain_only'] else CHAIN
    lo = 1 if OPT['keep_pelvis'] else 0
    for nm, _ in chain[lo:]:
        pool += W[:, idx[nm]]
        W[:, idx[nm]] = 0.0
    heights = np.array([h for _, h in chain])
    tent = np.zeros((len(P), len(CHAIN)))
    for i in range(lo, len(chain)):
        e = np.zeros(len(chain) - lo)
        e[i - lo] = 1.0
        tent[:, i] = np.interp(y, heights[lo:], e)
    if OPT['sigma']:  # wider blend: Gaussian of the clamped height round each knot, normalised
        yc = np.clip(y, heights[lo], heights[-1])[:, None]
        g_ = np.exp(-0.5 * ((yc - heights[None, lo:]) / OPT['sigma'][0]) ** 2)
        g_ /= g_.sum(1, keepdims=True)
        tent[:, lo:len(chain)] = g_
    # Neck/Head share only near the midline below the jaw; the rest to Spine2
    g = 1 - smoothstep(np.abs(x - MID_X), *OPT['neck_x'])
    g = np.maximum(g, smoothstep(y, 0.98, 1.04))
    moved = (tent[:, 4] + tent[:, 5]) * (1 - g)
    tent[:, 4] *= g
    tent[:, 5] *= g
    tent[:, 3] += moved
    torso_w = W.copy()
    for i, (nm, _) in enumerate(CHAIN):
        torso_w[:, idx[nm]] += pool * tent[:, i]
    # beard / braid mass
    hb, nb, cb = beard_mix
    s = smoothstep(y, *OPT['beard_y'])
    beard_w = np.zeros_like(W)
    beard_w[:, idx['B_Head']] = s + (1 - s) * hb
    beard_w[:, idx['B_Neck']] = (1 - s) * nb
    if OPT['beard_chest']:  # the rest rides with the chest under it (Spine/Spine1/Spine2 tents at its height)
        for i, (nm, _) in enumerate(CHAIN[1:4], start=1):
            beard_w[:, idx[nm]] += (1 - s) * cb * tent[:, i] / np.maximum(tent[:, 1:4].sum(1), 1e-9)
    else:
        beard_w[:, idx['B_Spine2']] = (1 - s) * cb
    out = (1 - b)[:, None] * torso_w + b[:, None] * beard_w
    affected = (cls == TORSO) | (cls == BRAID) | (cls == GUARD)
    out[~affected] = Wf[~affected]
    return out, affected


def prune(Wd, slots):
    order = np.argsort(-Wd, axis=1)[:, :slots]
    w = np.take_along_axis(Wd, order, axis=1)
    w[w < 1e-4] = 0.0
    w /= np.maximum(w.sum(1, keepdims=True), 1e-12)
    order = np.where(w > 0, order, 0)
    return order, w


def write_accessor(g, index, values):
    acc = g.json['accessors'][index]
    view = g.json['bufferViews'][acc['bufferView']]
    dtype = {5121: np.uint8, 5123: np.uint16, 5126: np.float32}[acc['componentType']]
    width = {'VEC4': 4}[acc['type']]
    start = view.get('byteOffset', 0) + acc.get('byteOffset', 0)
    stride = view.get('byteStride', 0) or np.dtype(dtype).itemsize * width
    assert stride == np.dtype(dtype).itemsize * width, 'interleaved accessors are not supported'
    data = np.ascontiguousarray(values, dtype=dtype)
    assert data.shape == (acc['count'], width)
    g.bin[start:start + data.nbytes] = data.tobytes()
    if 'min' in acc:
        acc['min'] = data.min(0).tolist()
        acc['max'] = data.max(0).tolist()


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('input')
    p.add_argument('output')
    p.add_argument('--beard', default='0.1,0.1,0.8')
    p.add_argument('--labels')
    p.add_argument('--opt', action='append', default=[], help="override a fade, e.g. arm=none, clav=-0.03,0.0")
    a = p.parse_args()
    for o in a.opt:
        k, v = o.split('=')
        OPT[k] = None if v == 'none' else tuple(float(t) for t in v.split(','))
    beard_mix = [float(v) for v in a.beard.split(',')]
    g = glb_pose.Glb(a.input)
    doc = g.json
    joints = doc['skins'][0]['joints']
    names = [doc['nodes'][j]['name'] for j in joints]
    idx = {n: i for i, n in enumerate(names)}
    P0, cls0, b0, beard0 = lod0_labels(g)
    tree = cKDTree(P0)
    if a.labels:
        np.savez(a.labels, cls=cls0, b=b0, beard=beard0)
    report = []
    for mi, mesh in enumerate(doc['meshes']):
        for prim in mesh['primitives']:
            at = prim['attributes']
            if 'JOINTS_0' not in at:
                continue
            P = g.accessor(at['POSITION']).astype(np.float64)
            sets = [k for k in ('0', '1') if f'JOINTS_{k}' in at]
            Js = [g.accessor(at[f'JOINTS_{k}']).astype(np.int64) for k in sets]
            Ws = [g.accessor(at[f'WEIGHTS_{k}']).astype(np.float64) for k in sets]
            J, Wt = np.concatenate(Js, 1), np.concatenate(Ws, 1)
            Wf = np.zeros((len(P), len(names)))
            for k in range(J.shape[1]):
                np.add.at(Wf, (np.arange(len(P)), J[:, k]), Wt[:, k])
            Wf /= np.maximum(Wf.sum(1, keepdims=True), 1e-12)
            if mi == 0:
                cls, b = cls0, b0
            else:
                d, n = tree.query(P)
                cls, b = cls0[n], b0[n]
                cls = np.where(d < 0.02, cls, OTHER)
            new, affected = rule(P, Wf, cls, b, idx, beard_mix)
            order, w = prune(new, J.shape[1])
            keep = ~affected
            order[keep], w[keep] = J[keep], Wt[keep]  # untouched vertices keep their exact slots
            for si, k in enumerate(sets):
                write_accessor(g, at[f'JOINTS_{k}'], order[:, 4 * si:4 * si + 4])
                write_accessor(g, at[f'WEIGHTS_{k}'], w[:, 4 * si:4 * si + 4])
            report.append(f'{mesh.get("name")}: {int(affected.sum())} of {len(P)} vertices reweighted')
    g.write(a.output)
    print('\n'.join(report))


if __name__ == '__main__':
    main()
