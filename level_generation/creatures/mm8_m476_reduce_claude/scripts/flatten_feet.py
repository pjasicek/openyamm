#!/usr/bin/env python3
"""MM6 Knight copy for the MM8 Troll (mesh node Troll; prints planted-frame tilt and sole spread). Level planted soles in idle clips (user: feet "not being idle on the ground flat"). Per foot, the sole is the
foot-weighted LOD0 vertices within SOLE_H of the foot's lowest bind-pose vertex; its plane normal and heel-to-toe axis
are fitted in the bind pose and carried in foot-bone space. Per frame of each listed clip, the foot bone (and its toe)
is rotated about the ankle around the heel-to-toe axis only, removing the sideways roll (heel/toe pitch, e.g. a
toe pivot in Hit, stays), weighted by how planted the foot is (lowest sole point below PLANT_LO: full, above PLANT_HI:
none). B_Pelvis then moves vertically so the lowest planted sole keeps its original height. Only the foot rotation and
pelvis translation channels change.
Clips as name:mode, mode full (roll and pitch: idle stances) or roll (default).
Usage: flatten_feet.py <in.glb> <out.glb> [clips, default Standing:full,Fidget:full] [--measure]"""
import struct
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402

SOLE_H, PLANT_LO, PLANT_HI = 0.02, 0.03, 0.08
FEET = ('B_L_Foot', 'B_R_Foot')
CT = {5126: ('f', 4), 5125: ('I', 4), 5123: ('H', 2), 5121: ('B', 1)}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


def acc(doc, b, i):
    a = doc['accessors'][i]; v = doc['bufferViews'][a['bufferView']]; f, s = CT[a['componentType']]; n = NC[a['type']]
    off = v.get('byteOffset', 0) + a.get('byteOffset', 0); stride = v.get('byteStride', s * n)
    out = np.zeros((a['count'], n), {'f': np.float32, 'I': np.uint32, 'H': np.uint16, 'B': np.uint8}[f])
    for k in range(a['count']):
        out[k] = struct.unpack_from('<' + f * n, b, off + k * stride)
    if a.get('normalized') and f != 'f':
        out = out / float(np.iinfo(out.dtype).max)
    return out


def q2m(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def m2q(m):
    t = np.trace(m)
    if t > 0:
        s = np.sqrt(t + 1) * 2; q = [(m[2, 1] - m[1, 2]) / s, (m[0, 2] - m[2, 0]) / s, (m[1, 0] - m[0, 1]) / s, s / 4]
    else:
        i = int(np.argmax(np.diag(m))); j, k = (i + 1) % 3, (i + 2) % 3
        s = np.sqrt(1 + m[i, i] - m[j, j] - m[k, k]) * 2; q = [0, 0, 0, 0]
        q[i] = s / 4; q[j] = (m[j, i] + m[i, j]) / s; q[k] = (m[k, i] + m[i, k]) / s; q[3] = (m[k, j] - m[j, k]) / s
    q = np.array(q); return q / np.linalg.norm(q)


def trs(t, r, s):
    m = np.eye(4); m[:3, :3] = q2m(r) * s; m[:3, 3] = t; return m


def align(a, b):
    """Rotation matrix taking unit vector a onto unit vector b."""
    v = np.cross(a, b); c = float(a @ b)
    if np.linalg.norm(v) < 1e-9:
        return np.eye(3)
    k = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + k + k @ k / (1 + c)


def about(axis, ang):
    k = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.eye(3) + np.sin(ang) * k + (1 - np.cos(ang)) * k @ k


def roll_fix(n, f):
    """Rotation about the heel-to-toe axis f taking the sole normal n into the vertical plane through f."""
    f = f / np.linalg.norm(f); up = np.array([0., 1., 0.])
    a = n - (n @ f) * f; u = up - (up @ f) * f
    if np.linalg.norm(a) < 1e-6 or np.linalg.norm(u) < 1e-6:
        return 0.0
    a /= np.linalg.norm(a); u /= np.linalg.norm(u)
    return float(np.arctan2(np.cross(a, u) @ f, a @ u))


def slerp_id(m, w):
    """Rotation m scaled to fraction w of its angle."""
    ang = np.arccos(np.clip((np.trace(m) - 1) / 2, -1, 1))
    if ang < 1e-6:
        return np.eye(3)
    axis = np.array([m[2, 1] - m[1, 2], m[0, 2] - m[2, 0], m[1, 0] - m[0, 1]]) / (2 * np.sin(ang))
    a = ang * w; k = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.eye(3) + np.sin(a) * k + (1 - np.cos(a)) * k @ k


args = [a for a in sys.argv[1:] if not a.startswith('--')]; measure = '--measure' in sys.argv
src, dst = Path(args[0]), Path(args[1]); clips = dict((c.split(':') + ['roll'])[:2] for c in (args[2] if len(args) > 2 else 'Standing:full,Fidget:full').split(','))
doc, b = read_glb(src); b = bytearray(b)
nodes = doc['nodes']; names = [n.get('name') for n in nodes]
parent = {c: i for i, n in enumerate(nodes) for c in n.get('children', [])}
skin = doc['skins'][0]; joints = skin['joints']; ibm = acc(doc, b, skin['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1)
mesh_node = next(n for n in nodes if n.get('name') == 'Troll'); prim = doc['meshes'][mesh_node['mesh']]['primitives'][0]
pos = acc(doc, b, prim['attributes']['POSITION']).astype(np.float64)
jw = [(acc(doc, b, prim['attributes'][f'JOINTS_{k}']), acc(doc, b, prim['attributes'][f'WEIGHTS_{k}']))
      for k in range(2) if f'JOINTS_{k}' in prim['attributes']]
sole = {}
for foot in FEET:
    fi = names.index(foot); toe = names.index(foot.replace('Foot', 'Toe0'))
    wsum = sum(((np.isin(np.array(joints)[j.astype(int)], [fi, toe])) * w).sum(1) for j, w in jw)
    vs = pos[wsum > .5]; low = vs[:, 1].min(); pts = vs[vs[:, 1] < low + SOLE_H]
    c = pts.mean(0); vt = np.linalg.svd(pts - c)[2]; n = vt[2] if vt[2][1] > 0 else -vt[2]; fwd = vt[0]
    j = joints.index(fi); R0 = ibm[j][:3, :3]
    local = R0 @ n; local /= np.linalg.norm(local); flocal = R0 @ fwd; flocal /= np.linalg.norm(flocal)
    sole[foot] = (fi, (ibm[j] @ np.append(pts, np.ones((len(pts), 1)), 1).T).T[:, :3], local, flocal)
    print('SOLE', foot, len(pts), 'points, bind normal', n.round(3), 'tilt %.1f deg' % np.degrees(np.arccos(n[1])))


def globals_at(anim, f):
    loc = {i: (np.array(n.get('translation', [0, 0, 0]), float), np.array(n.get('rotation', [0, 0, 0, 1]), float),
               np.array(n.get('scale', [1, 1, 1]), float)) for i, n in enumerate(nodes)}
    for ch in anim['channels']:
        i = ch['target']['node']; p = ch['target']['path']
        if p not in ('translation', 'rotation', 'scale'):
            continue
        v = sample(anim, ch['sampler'], times[anim['name']][f], p); t, r, s = loc[i]
        loc[i] = (v if p == 'translation' else t, v if p == 'rotation' else r, v if p == 'scale' else s)
    g = {}

    def G(i):
        if i not in g:
            m = trs(*loc[i]); g[i] = (G(parent[i]) @ m) if i in parent else m
        return g[i]
    return G, loc


cache, times, master = {}, {}, {}
for anim in doc['animations']:
    for si, s in enumerate(anim['samplers']):
        cache[(anim['name'], si)] = (acc(doc, b, s['input'])[:, 0].astype(np.float64), acc(doc, b, s['output']).astype(np.float64))
    master[anim['name']] = max((s['input'] for s in anim['samplers']), key=lambda i: doc['accessors'][i]['count'])
    times[anim['name']] = acc(doc, b, master[anim['name']])[:, 0].astype(np.float64)


def sample(anim, si, t, path):
    ts, vs = cache[(anim['name'], si)]
    k = int(np.searchsorted(ts, t, 'right')) - 1
    if k < 0:
        return vs[0]
    if k >= len(ts) - 1:
        return vs[-1]
    u = (t - ts[k]) / (ts[k + 1] - ts[k]); a, c = vs[k], vs[k + 1]
    if path == 'rotation':
        c = c if a @ c >= 0 else -c; q = a * (1 - u) + c * u; return q / np.linalg.norm(q)
    return a * (1 - u) + c * u

for anim in doc['animations']:
    nframes = len(times[anim['name']])
    edit = anim['name'] in clips and not measure
    rot_ch = {ch['target']['node']: ch['sampler'] for ch in anim['channels'] if ch['target']['path'] == 'rotation'}
    tr_ch = {ch['target']['node']: ch['sampler'] for ch in anim['channels'] if ch['target']['path'] == 'translation'}
    pelvis = names.index('B_Pelvis')
    stats = {f: [] for f in FEET}
    new = {f: np.array([sample(anim, rot_ch[sole[f][0]], t_, 'rotation') for t_ in times[anim['name']]]) for f in FEET}
    hips = np.array([sample(anim, tr_ch[pelvis], t_, 'translation') for t_ in times[anim['name']]])
    for f in range(nframes):
        G, loc = globals_at(anim, f)
        old_low, new_low = [], []
        for foot, (fi, pts, nloc, floc) in sole.items():
            M = G(fi); S = M[:3, :3] / np.linalg.norm(M[:3, :3], axis=0)
            nw = S @ nloc; fw = S @ floc
            hts = ((M[:3, :3] @ pts.T).T + M[:3, 3])[:, 1]; low = hts.min()
            tilt = np.degrees(np.arccos(np.clip(nw[1], -1, 1))); roll = np.degrees(roll_fix(nw, fw))
            stats[foot].append((tilt, low, abs(roll), hts.max() - low))
            if not edit:
                continue
            w = float(np.clip((PLANT_HI - low) / (PLANT_HI - PLANT_LO), 0, 1))
            if clips[anim['name']] == 'full':
                C = slerp_id(align(nw / np.linalg.norm(nw), np.array([0., 1., 0.])), w)
            else:
                C = about(fw / np.linalg.norm(fw), np.radians(roll) * w)
            Rg = C @ S
            P = G(parent[fi])[:3, :3]; P = P / np.linalg.norm(P, axis=0)
            q = m2q(P.T @ Rg); q = q if q @ new[foot][f] >= 0 else -q
            new[foot][f] = q
            if w > .5:
                old_low.append(low); new_low.append(((C @ M[:3, :3] @ pts.T).T + M[:3, 3])[:, 1].min())
        if edit and old_low:
            hips[f, 1] -= min(new_low) - min(old_low)
    for foot in FEET:
        a = np.array(stats[foot])
        pl = a[:, 1] < PLANT_LO  # planted frames
        print(f"{anim['name']:9s} {foot}: tilt max {a[:, 0].max():5.1f} mean {a[:, 0].mean():5.1f}, roll max {a[:, 2].max():5.1f} deg, lowest sole {a[:, 1].min() * 100:5.1f}"
              f" .. {a[:, 1].max() * 100:5.1f} cm; planted frames {int(pl.sum())}/{len(a)}"
              + (f" tilt {a[pl, 0].mean():4.1f} deg, sole spread {a[pl, 3].mean() * 100:4.1f} cm" if pl.any() else '')
              + ('  -> levelled' if edit else ''))
    if edit:
        outs = [(rot_ch[sole[foot][0]], new[foot]) for foot in FEET] + [(tr_ch[pelvis], hips)]
        for si, arr in outs:
            data = arr.astype(np.float32).tobytes()
            while len(b) % 4:
                b.append(0)
            doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(b), 'byteLength': len(data)}); b += data
            doc['accessors'].append({'bufferView': len(doc['bufferViews']) - 1, 'componentType': 5126,
                                     'count': nframes, 'type': 'VEC4' if arr.shape[1] == 4 else 'VEC3'})
            anim['samplers'][si].update(output=len(doc['accessors']) - 1, input=master[anim['name']], interpolation='LINEAR')
if not measure:
    doc['buffers'][0]['byteLength'] = len(b)
    write_glb(dst, doc, bytes(b)); print('WROTE', dst)
