#!/usr/bin/env python3
"""Keep the long band out of the leg skin: per clip, on the keys, the least rotation of the chain root Bone04 that lifts the deepest band point out of the thigh or calf, through a running maximum and a Gaussian
(circular on loops), capped. Chain below follows; the tip stays pinned on the forearm by its weights. Args: <in glb> <out glb> [iterations]"""
import sys
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter1d, maximum_filter1d
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model, quaternion_matrix, matrix_quaternion
from pygltflib import GLTF2
IN, OUT = sys.argv[1:3]; ITER = int(sys.argv[3]) if len(sys.argv) > 3 else 3
LOOPS = ('Standing', 'Walking', 'Running'); MARGIN = 0.012; CAP = np.radians(38)
def rv2mat(r):
    a = np.linalg.norm(r)
    if a < 1e-9: return np.eye(3)
    k = r / a; K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * K @ K
cur = IN
for it in range(ITER):
    m = Model(Glb(cur)); doc = m.glb.json; names = [n.get('name') for n in doc['nodes']]
    jn = [names[j] for j in m.joints]; P0 = m.primitives[0]; J, W = P0['joints'], P0['weights']; dom = J[np.arange(len(J)), W.argmax(1)]
    legs = [jn.index(f'Bip01 {s} {b}') for s in 'LR' for b in ('Thigh', 'Calf')]
    band = [jn.index(n) for n in ('Bone04', 'Bone05', 'Bone06', 'Bone07', 'Bone08', 'XstripTip')]; rootb = jn.index('XstripRoot')
    sv = np.isin(J, band).any(1); sv &= (W * (J == rootb)).sum(1) < 0.01
    allhelp = np.isin(J, band + [rootb, jn.index('XarmStrip'), jn.index('XthighStrip'), jn.index('Bone01'), jn.index('Bone02')]).any(1)
    vf = np.isin(dom, legs) & ~allhelp; F = P0['triangles'][vf[P0['triangles']].all(1)]
    nb, ns = names.index('Bone04'), names.index('Bip01 Spine1')
    g = GLTF2().load(cur); blob = bytearray(g.binary_blob())
    report = {}
    for ai, an in enumerate(g.animations):
        if an.name == 'Dead': pass
        ch = next(c for c in an.channels if c.target.node == nb and c.target.path == 'rotation')
        sm = an.samplers[ch.sampler]; ta = g.accessors[sm.input]; qa = g.accessors[sm.output]
        def view(acc, n):
            bv = g.bufferViews[acc.bufferView]; o = (bv.byteOffset or 0) + (acc.byteOffset or 0)
            return np.frombuffer(blob, 'f4', acc.count * n, o).reshape(acc.count, n), o
        ts, _ = view(ta, 1); ts = ts[:, 0].copy(); Q, qo = view(qa, 4); Q = Q.copy()
        need = np.zeros((len(ts), 3))
        worst = 0
        for k, t in enumerate(ts):
            w = m.world(m.sample(an.name, float(t))); Pz = m.skinned_positions(w)[0][0]
            A, B, C = Pz[F[:, 0]], Pz[F[:, 1]], Pz[F[:, 2]]
            n = np.cross(B - A, C - A); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
            samp = np.vstack([(A + B + C) / 3, (A * 2 + B + C) / 4, (A + B * 2 + C) / 4, (A + B + C * 2) / 4]); nn = np.tile(n, (4, 1))
            pts = Pz[sv]; d, f = cKDTree(samp).query(pts, distance_upper_bound=0.12); ok = np.isfinite(d)
            if not ok.any(): continue
            v = samp[f[ok]] - pts[ok]; dot = (v * nn[f[ok]]).sum(1); dist = d[ok]
            ins = dot > 0.7 * dist
            if not ins.any(): continue
            i = np.where(ok)[0][ins][dist[ins].argmax()]; depth = d[i]; worst = max(worst, depth)
            p = pts[i]; o = w[nb][:3, 3]; r = p - o; nrm = nn[f[i]]
            ax = np.cross(r, nrm); L = np.linalg.norm(ax)
            if L < 1e-6: continue
            ang = (depth + MARGIN) / max(np.linalg.norm(r), 0.1)
            # world rotation vector, stored in the Spine1 frame
            need[k] = w[ns][:3, :3].T @ (ax / L * ang)
        mode = 'wrap' if an.name in LOOPS else 'nearest'
        mag = np.linalg.norm(need, axis=1)
        for c in range(3):
            # running extreme by magnitude order: keep sign through a filter on the signed component's largest absolute value
            pos = maximum_filter1d(np.maximum(need[:, c], 0), 5, mode=mode); neg = maximum_filter1d(np.maximum(-need[:, c], 0), 5, mode=mode)
            need[:, c] = pos - neg
        need = gaussian_filter1d(need, 2.0, axis=0, mode=mode)
        for k in range(len(ts)):
            r = need[k]; a = np.linalg.norm(r)
            if a > CAP: r = r / a * CAP
            Rc = rv2mat(r)                         # in the Spine1 frame, applied to Bone04's local rotation
            Mq = quaternion_matrix(Q[k])
            q2 = matrix_quaternion(Rc @ Mq)
            Q[k] = q2
        for k in range(1, len(Q)):
            if Q[k] @ Q[k - 1] < 0: Q[k] *= -1
        blob[qo:qo + Q.nbytes] = Q.astype('f4').tobytes()
        report[an.name] = round(worst * 100, 1)
    print('ITER', it, report)
    g.set_binary_blob(bytes(blob)); g.save(OUT); cur = OUT
