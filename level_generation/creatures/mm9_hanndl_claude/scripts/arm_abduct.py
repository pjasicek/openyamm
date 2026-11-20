#!/usr/bin/env python3
"""Hand off the tunic skirt in HANNDL.abc's own scene clips (2026-11-02): MM9's right hand rests at the thin MM9 hip, so
our fingers dip 2-3.5 cm into the HD tunic skirt; hand_rest.py (horizontal cast onto the trunk) and arm_clear.py do not
see the skirt. The upper arm is abducted by a constant DEG (eased in and out over EASE s at the clip's ends, so the clip
still starts and ends on Standing's arm), about the body's forward axis at the shoulder: no per-key solve, so no jitter.
Usage: arm_abduct.py <in glb> <out glb> --clip <role>:<side>:<deg>[:<ease s>] [...] [--ease 0.3]"""
import argparse, json, sys
import numpy as np
import pygltflib

ap = argparse.ArgumentParser(); ap.add_argument('src'); ap.add_argument('dst')
ap.add_argument('--clip', action='append', required=True); ap.add_argument('--ease', type=float, default=0.3)
o = ap.parse_args()
g = pygltflib.GLTF2().load(o.src); blob = bytearray(g.binary_blob())
names = {n.name: i for i, n in enumerate(g.nodes)}
parent = {c: i for i, n in enumerate(g.nodes) for c in (n.children or [])}


def qmul(a, b):
    x1, y1, z1, w1 = a; x2, y2, z2, w2 = b
    return np.array([w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
                     w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2])


def qmat(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def world(i):
    n = g.nodes[i]; R = qmat(n.rotation or [0, 0, 0, 1]); t = np.array(n.translation or [0, 0, 0], float)
    s = np.array(n.scale or [1, 1, 1], float)
    M = np.eye(4); M[:3, :3] = R * s; M[:3, 3] = t
    return world(parent[i]) @ M if i in parent else M


def acc_view(i):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]
    n = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[a.type]
    off = (bv.byteOffset or 0) + (a.byteOffset or 0)
    assert a.componentType == 5126 and (bv.byteStride in (None, 0, 4 * n))
    return off, a.count, n


rep = {}
for spec in o.clip:
    parts = spec.split(':'); role, side, deg = parts[:3]; deg = float(deg)
    ease = float(parts[3]) if len(parts) > 3 else o.ease          # optional per-clip ease (s)
    an = next(a for a in g.animations if a.name == role)
    ua, cl = names[f'Bip01 {side} UpperArm'], names[f'Bip01 {side} Clavicle']
    sh = world(ua)[:3, 3]; osh = world(names[f'Bip01 {"L" if side == "R" else "R"} UpperArm'])[:3, 3]
    hand = world(names[f'Bip01 {side} Hand'])[:3, 3]
    up = world(names['Bip01 Head'])[:3, 3] - world(names['Bip01 Spine'])[:3, 3]; up /= np.linalg.norm(up)
    lat = sh - osh; lat -= up * (lat @ up); lat /= np.linalg.norm(lat)
    F = np.cross(up, lat); F /= np.linalg.norm(F)
    Wc = world(cl)[:3, :3]; Wc = Wc / np.linalg.norm(Wc, axis=0)
    best = None
    for sgn in (1, -1):                      # the sign that moves the hand away from the midline
        a = np.radians(deg) * sgn; Dq = np.array([*(F * np.sin(a / 2)), np.cos(a / 2)])
        h2 = sh + qmat(Dq) @ (hand - sh)
        if best is None or (h2 - sh) @ lat > best[0]: best = ((h2 - sh) @ lat, sgn)
    axis_local = Wc.T @ F
    ch = next(c for c in an.channels if c.target.node == ua and c.target.path == 'rotation')
    smp = an.samplers[ch.sampler]
    toff, tn, _ = acc_view(smp.input); T = np.frombuffer(bytes(blob[toff:toff + 4 * tn]), np.float32)
    qoff, qn, _ = acc_view(smp.output); Q = np.frombuffer(bytes(blob[qoff:qoff + 16 * qn]), np.float32).reshape(qn, 4).copy()
    dur = T[-1] - T[0]
    for k in range(qn):
        t = T[k] - T[0]
        e = min(1.0, t / ease, (dur - t) / ease) if ease > 0 else 1.0
        e = max(0.0, e); e = e * e * (3 - 2 * e)
        a = np.radians(deg) * best[1] * e
        D = np.array([*(axis_local * np.sin(a / 2)), np.cos(a / 2)])
        Q[k] = qmul(D, Q[k]); Q[k] /= np.linalg.norm(Q[k])
    blob[qoff:qoff + 16 * qn] = Q.astype(np.float32).tobytes()
    rep[role] = {'side': side, 'deg': deg, 'keys': int(qn), 'sign': best[1]}
g.set_binary_blob(bytes(blob)); g.save(o.dst)
print('ABDUCT', json.dumps(rep))
