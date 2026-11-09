#!/usr/bin/env python3
"""Cords on the robe: MM9's Y chains are keyed for MM9's thin robe, so in Running, Death and the bends a cord sinks behind our cloth. Per key, per chain, top link down: the least turn of a link that brings its end joint out of the robe by CLEAR (signed distance to the posed outer robe); the turn is held by a running maximum and Gaussian on the clip's keys, faded at clip ends for one-shots, never per frame.
Args: <in glb> <out glb>"""
import sys, json
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from scipy.ndimage import gaussian_filter1d, maximum_filter1d
from pygltflib import GLTF2
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
from glb_pose import Glb, Model, matrix_quaternion
from detached_parts_audit import closest_on_triangles
IN, OUT = sys.argv[1:3]; CLEAR = 0.022; SIG = 0.05; LOOPS = ('Standing', 'Walking', 'Running', 'Backpedal', 'BackpedalRun')
m = Model(Glb(IN)); doc = m.glb.json; names = [n.get('name') for n in doc['nodes']]; ix = {n: i for i, n in enumerate(names)}
prims = [p for p in m.primitives if p['node'] == m.primitives[0]['node']]; n_p = len(prims); jn = [names[j] for j in m.joints]
J = np.vstack([p['joints'] for p in prims]); W = np.vstack([p['weights'] for p in prims])
sk = [i for i, n in enumerate(jn) if n.startswith('X') and 'half' not in n]; sw = (np.isin(J, sk) * W).sum(1)
offs = np.cumsum([0] + [len(p['positions']) for p in prims]); tri = np.vstack([np.asarray(p['triangles']).reshape(-1, 3) + o for p, o in zip(prims, offs)])
def allpos(w): return np.concatenate([r[0] for r in m.skinned_positions(w)][:n_p])
R0 = allpos(m.world({})); c0 = R0[tri].mean(1); n0 = np.cross(R0[tri[:, 1]] - R0[tri[:, 0]], R0[tri[:, 2]] - R0[tri[:, 0]]); rad = c0.copy(); rad[:, 1] = 0
F = np.where((sw[tri] > 0.3).all(1) & ((n0 * rad).sum(1) > 0))[0]
tr0 = R0[tri[F]]; nn = np.cross(tr0[:, 1] - tr0[:, 0], tr0[:, 2] - tr0[:, 0]); test = tr0.mean(1) - nn / np.maximum(np.linalg.norm(nn, axis=1, keepdims=True), 1e-12) * 0.01
class Surf:
    def __init__(s, P):
        s.tr = P[tri[F]]; s.c = s.tr.mean(1); n = np.cross(s.tr[:, 1] - s.tr[:, 0], s.tr[:, 2] - s.tr[:, 0]); s.n = n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12); s.k = cKDTree(s.c)
    def sd(s, Q):
        Q = np.atleast_2d(Q); _, ids = s.k.query(Q, k=6); best = np.full(len(Q), 1e9); sd = np.zeros(len(Q)); nr = np.zeros((len(Q), 3))
        for k in range(6):
            i = ids[:, k]; q, _ = closest_on_triangles(Q, s.tr[i, 0], s.tr[i, 1], s.tr[i, 2]); d = np.linalg.norm(q - Q, axis=1); u = d < best
            best[u] = d[u]; sd[u] = ((Q - q) * s.n[i])[u].sum(1); nr[u] = s.n[i][u]
        return sd, nr, best
s0 = Surf(R0); SGN = -1.0 if np.median(s0.sd(test[:200])[0]) > 0 else 1.0; print('SGN', SGN)
g = GLTF2().load(IN); blob = bytearray(g.binary_blob())
def view(i, n):
    x = g.accessors[i]; v = g.bufferViews[x.bufferView]; o = (v.byteOffset or 0) + (x.byteOffset or 0)
    return np.frombuffer(blob, 'f4', x.count * n, o).reshape(x.count, n).copy(), o
def qmul(p, q):
    x1, y1, z1, w1 = p.T; x2, y2, z2, w2 = q.T
    return np.c_[w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2]
def rodr(v):
    a = np.linalg.norm(v)
    if a < 1e-9: return np.eye(3)
    k = v / a; K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]]); return np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * K @ K
CH = [['Ytasspiv', 'YtassA', 'YtassB', 'YtassC', 'YtassD'], ['Ytasspiv01', 'YtassA01', 'YtassB01', 'YtassC01', 'YtassD01']]
tot = 0
for an in g.animations:
    if an.name == 'Dead': continue
    idx0 = ix['YtassA']; c0_ = next(c for c in an.channels if c.target.node == idx0 and c.target.path == 'rotation')
    ts, _ = view(an.samplers[c0_.sampler].input, 1); ts = ts[:, 0]
    for chain in CH:
        rv = np.zeros((len(ts), len(chain), 3)); need = False
        for k, t in enumerate(ts):
            w = m.world(m.sample(an.name, float(t))); s = Surf(allpos(w))
            pts = [w[ix[b]][:3, 3].copy() for b in chain]
            tip = pts[-1] + (pts[-1] - pts[-2]) * 0.8        # the knot's end
            P = pts + [tip]
            for i in range(len(chain)):
                for it in range(3):
                    cand = np.array([P[i] + (P[i + 1] - P[i]) * f for f in (0.5, 1.0)]); sd_, nr, dist = s.sd(cand); sd_ = sd_ * SGN; b_ = int(np.argmin(sd_))
                    sd = sd_[b_]; nv = nr[b_] * SGN; e = cand[b_]
                    if sd >= CLEAR or dist[b_] > 0.2: break
                    arm = e - P[i]; L = np.linalg.norm(arm); ang = min((CLEAR - sd) / max(L, 0.03), 0.7)
                    ax = np.cross(arm, nv); ax /= max(np.linalg.norm(ax), 1e-9); R = rodr(ax * ang)
                    for j in range(i + 1, len(P)): P[j] = P[i] + R @ (P[j] - P[i])
                    r = rodr(rv[k, i]); rn = R @ r
                    # keep as a rotation vector in world (small)
                    a_ = np.arccos(np.clip((np.trace(rn) - 1) / 2, -1, 1)); v_ = np.array([rn[2, 1] - rn[1, 2], rn[0, 2] - rn[2, 0], rn[1, 0] - rn[0, 1]]) / (2 * max(np.sin(a_), 1e-6))
                    rv[k, i] = v_ * a_; need = True
        if not need: continue
        tot += 1
        dt = float(np.median(np.diff(ts))); wn = max(int(round(0.1 / dt)) | 1, 3); loop = an.name in LOOPS
        mode = 'wrap' if loop else 'nearest'
        for i in range(len(chain)):
            for c in range(3):
                rv[:, i, c] = maximum_filter1d(np.maximum(rv[:, i, c], 0), wn, mode=mode) - maximum_filter1d(np.maximum(-rv[:, i, c], 0), wn, mode=mode)
        rv = gaussian_filter1d(rv, SIG / dt, axis=0, mode='wrap' if loop else 'nearest')
        if not loop:
            T = ts[-1]; e = np.clip(ts / 0.12, 0, 1); e = e * e * (3 - 2 * e)
            if an.name not in ('Death', 'Death2', 'CowerStart'):
                e = e * np.clip((T - ts) / 0.12, 0, 1)
            rv = rv * e[:, None, None]
        # apply: each link's world turn into its local rotation, top link first
        for i, b in enumerate(chain):
            nd = ix[b]; ch = next(c for c in an.channels if c.target.node == nd and c.target.path == 'rotation')
            Q, o = view(an.samplers[ch.sampler].output, 4); par = next(p for p, n in enumerate(doc['nodes']) if nd in n.get('children', []))
            Qn = Q.astype(float).copy()
            for k, t in enumerate(ts):
                w = m.world(m.sample(an.name, float(t))); Rp = w[par][:3, :3]; Rp = Rp / np.linalg.norm(Rp[:, 0])
                # upper links' turns act too: the local of this link turns in the (already turned) parent; small angles, the world vector is carried to the parent's frame
                v = Rp.T @ rv[k, i]; a = np.linalg.norm(v)
                if a < 1e-5: continue
                q = np.r_[v / a * np.sin(a / 2), np.cos(a / 2)]; Qn[k] = qmul(q[None], Qn[k:k + 1])[0]
            blob[o:o + Qn.size * 4] = Qn.astype('f4').tobytes()
g.set_binary_blob(bytes(blob)); g.save(OUT); print('CLOTH chains corrected', tot)
