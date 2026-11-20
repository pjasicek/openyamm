#!/usr/bin/env python3
"""Third pass review (2026-11-01): the corpse's mallet head lay 4.2 cm in its left thigh (Dead, Death's end). The mallet turns about the right
fist's grip point (Xbase's keys, in the hand's frame) by the least rotation, among the hand frame's axes and 5-60 deg, that takes it out of the
body in Dead; Dead takes it on every key, Death eases into it over its last RAMP seconds (Death ends on Dead's pose). Args: <in glb> <out glb>"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor')); sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from glb_pose import Glb, Model, matrix_quaternion
from detached_parts_audit import closest_on_triangles
from outer_surface import outer_faces
from pygltflib import GLTF2
IN, OUT = sys.argv[1:3]; RAMP = 0.6
HERE = Path(__file__).resolve().parents[1]
m = Model(Glb(IN)); d = m.glb.json; names = [n.get('name') for n in d['nodes']]; jn = [names[j] for j in m.joints]
P = m.primitives; USE = [k for k, pr in enumerate(P) if pr['node'] == P[0]['node'] and pr['skinned']]
tris, dom, off = [], [], 0
for k in USE:
    pr = P[k]; tris.append(pr['triangles'] + off); off += len(pr['positions'])
    dom.append(np.array([jn[pr['joints'][v][np.argmax(pr['weights'][v])]] for v in range(len(pr['positions']))]))
tris = np.concatenate(tris); dom = np.concatenate(dom)
mal = np.isin(dom, ['Xhammer', 'Xbase']); mv = np.where(mal)[0]; rarm = np.array([' R ' in x for x in dom])
skin = lambda w: np.concatenate([m.skinned_positions(w)[k][0] for k in USE])
body = np.where(~mal[tris].any(1) & ~rarm[tris].any(1))[0]; body = body[outer_faces(skin(m.world({})), tris, body)]
def depth(X):
    T = X[tris[body]]; a, b, c = T[:, 0], T[:, 1], T[:, 2]
    n = np.cross(b - a, c - a); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    pts = X[mv]; _, near = cKDTree((a + b + c) / 3).query(pts, k=24); rp = np.repeat(pts, near.shape[1], 0)
    q, _ = closest_on_triangles(rp, a[near.ravel()], b[near.ravel()], c[near.ravel()])
    dd = np.linalg.norm(rp - q, axis=1).reshape(near.shape); best = dd.argmin(1); rows = np.arange(len(pts))
    side = np.einsum('ij,ij->i', pts - q.reshape(*near.shape, 3)[rows, best], n[near[rows, best]])
    return float(np.where((side < 0) & (dd[rows, best] <= 0.08), -side, 0.0).max())
iH, iB = names.index('Bip01 R Hand'), names.index('Xbase')
Pz = json.load(open(HERE / 'work' / 'hand_poses.json')); B2G = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0.]])
lift = np.array(d['nodes'][names.index('MM9_Rig')].get('translation', [0, 0, 0]))
Gh = (np.linalg.inv(m.world({})[iH]) @ np.r_[B2G @ np.array(Pz['holeR']['G_turned_world']) + lift, 1])[:3]      # grip point, hand frame
def rodr(ax, a):
    K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]]); return np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * K @ K
def trs(t, q):
    x, y, z, w = q; R = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)], [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)], [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
    M = np.eye(4); M[:3, :3] = R; M[:3, 3] = t; return M
def turned(loc, R):
    """Xbase's local TRS turned about the grip point (Xbase's parent is the hand: its local frame is the hand frame)"""
    t, q = np.array(loc[0]), np.array(loc[1]); M = trs(t, q); A = np.eye(4); A[:3, :3] = R; A[:3, 3] = Gh - R @ Gh
    N = A @ M; return N[:3, 3], np.array(matrix_quaternion(N[:3, :3]))
base = m.sample('Dead', 0.0); d0 = depth(skin(m.world(base)))
best = (d0, None, 0.0)
for ax in np.eye(3):
    for sg in (1, -1):
        for ang in np.radians(np.arange(5, 61, 5)):
            R = rodr(ax * sg, ang); pose = dict(base); loc = pose.get(iB, m.rest[iB]); t, q = turned(loc, R)
            pose[iB] = [t, q] + list(loc[2:]); dp = depth(skin(m.world(pose)))
            if dp < best[0] - 1e-4 or (dp < 0.006 and best[0] < 0.006 and ang < best[2]): best = (dp, R, ang)
            if dp < 0.006: break
print('CORPSE mallet in body before cm', round(d0 * 100, 2), 'after', round(best[0] * 100, 2), 'turn deg', round(float(np.degrees(best[2])), 0))
g = GLTF2().load(IN); blob = bytearray(g.binary_blob())
def acc(i):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]; n = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[a.type]
    return np.frombuffer(bytes(blob), 'f4', a.count * n, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n).copy()
def put(i, arr):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]; off_ = (bv.byteOffset or 0) + (a.byteOffset or 0)
    blob[off_:off_ + arr.size * 4] = arr.astype('f4').tobytes()
if best[1] is not None:
    axis_ang = best[1]
    for an in g.animations:
        if an.name not in ('Dead', 'Death'): continue
        cr = next(c for c in an.channels if c.target.node == iB and c.target.path == 'rotation'); ct = next(c for c in an.channels if c.target.node == iB and c.target.path == 'translation')
        sr, st = an.samplers[cr.sampler], an.samplers[ct.sampler]; tr_, tt_ = acc(sr.input)[:, 0], acc(st.input)[:, 0]
        Q, T = acc(sr.output), acc(st.output); dur = max(tr_[-1], tt_[-1])
        wgt = lambda t: 1.0 if an.name == 'Dead' else float(np.clip((t - (dur - RAMP)) / RAMP, 0, 1)) ** 2 * (3 - 2 * float(np.clip((t - (dur - RAMP)) / RAMP, 0, 1)))
        # the partial turn: same axis, angle scaled by the weight; translation from the turned matrix at that angle
        w_, th_ = np.linalg.eig(axis_ang)[0], None
        ax_ = np.array([axis_ang[2, 1] - axis_ang[1, 2], axis_ang[0, 2] - axis_ang[2, 0], axis_ang[1, 0] - axis_ang[0, 1]]); ax_ /= np.linalg.norm(ax_)
        Qn, Tn = Q.copy(), T.copy()
        for k, t in enumerate(tr_):
            Tk = np.array([np.interp(t, tt_, T[:, i]) for i in range(3)])
            _, qn = turned((Tk, Q[k]), rodr(ax_, best[2] * wgt(t))); Qn[k] = qn
        for k, t in enumerate(tt_):
            qk = Q[min(np.searchsorted(tr_, t), len(Q) - 1)]
            tn, _ = turned((T[k], qk), rodr(ax_, best[2] * wgt(t))); Tn[k] = tn
        put(sr.output, Qn); put(st.output, Tn)
g.set_binary_blob(bytes(blob)); g.save(OUT)
