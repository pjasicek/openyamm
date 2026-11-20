#!/usr/bin/env python3
"""Even out the Walking clip's vertical bob (MM8 Pirate, user: "a big jump in height when walking, frames 14-16").
The installed Walking pelvis sinks while both feet are planted (double support, the legs cannot reach both soles from a
higher hip) and then shoots up 7.5 cm in three 48 fps frames at each toe-off (frames 13-16 and 36-39; 11.7 cm range
per cycle). It is in the creature's motion from before the 2026-10-15 knee repair, not from the reduction.

New pelvis height: one periodic Gaussian pass over the original curve (two even bobs per cycle, no frame step),
lowered by smooth local dips wherever it would rise above the height from which both ankles are still reachable
(99.5 % of the leg length); loop continuity holds because every filter is periodic. Both legs are then
re-solved analytically (two-bone IK in the original knee plane) so every ankle keeps its original world path and every
foot its original world rotation: no foot slides, lifts or sinks. Only B_Pelvis translation and the thigh, calf and
foot rotations of Walking change; every other clip and channel is byte-identical.
Usage: smooth_walk_bob.py <in.glb> <out.glb> [sigma in 120 Hz samples, default 7]"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes, append_accessor  # noqa: E402

src, dst = Path(sys.argv[1]), Path(sys.argv[2]); SIGMA = float(sys.argv[3]) if len(sys.argv) > 3 else 7.0
doc, raw = read_glb(src); binary = bytearray(raw)
nodes = doc['nodes']; idx = {n.get('name'): i for i, n in enumerate(nodes)}
parent = {c: i for i, n in enumerate(nodes) for c in n.get('children', [])}
anim = next(a for a in doc['animations'] if a['name'] == 'Walking')
F = lambda a: np.frombuffer(accessor_bytes(doc, binary, a), '<f4').reshape(doc['accessors'][a]['count'], -1).astype(np.float64)
times = None; chan = {}
for ch in anim['channels']:
    s = anim['samplers'][ch['sampler']]; t = F(s['input']).ravel()
    chan[ch['target']['node'], ch['target']['path']] = (t, F(s['output']), ch)
    if len(t) > 2:
        times = t if times is None else times
T = len(times)
assert np.allclose(np.diff(times), times[1] - times[0], atol=1e-5), 'Walking keys are not uniform'


def qmat(q):
    x, y, z, w = q[..., 0], q[..., 1], q[..., 2], q[..., 3]
    return np.stack([np.stack([1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)], -1),
                     np.stack([2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)], -1),
                     np.stack([2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)], -1)], -2)


def matq(m):
    out = np.empty(m.shape[:-2] + (4,))
    for k, r in enumerate(m.reshape(-1, 3, 3)):
        tr = np.trace(r)
        if tr > 0:
            s = np.sqrt(tr + 1) * 2; q = [(r[2, 1] - r[1, 2]) / s, (r[0, 2] - r[2, 0]) / s, (r[1, 0] - r[0, 1]) / s, s / 4]
        else:
            i = int(np.argmax(np.diag(r))); j, kk = (i + 1) % 3, (i + 2) % 3
            s = np.sqrt(1 + r[i, i] - r[j, j] - r[kk, kk]) * 2; q = [0, 0, 0, (r[kk, j] - r[j, kk]) / s]
            q[i] = s / 4; q[j] = (r[j, i] + r[i, j]) / s; q[kk] = (r[kk, i] + r[i, kk]) / s
        out.reshape(-1, 4)[k] = q
    return out / np.linalg.norm(out, axis=-1, keepdims=True)


def value(i, path, default):
    if (i, path) not in chan:
        return np.broadcast_to(np.array(nodes[i].get(path, default), float), (T, len(default))).copy()
    t, v, _ = chan[i, path]
    if len(t) == T:
        return v.copy()
    if path == 'rotation':
        assert np.allclose(v, v[0], atol=1e-6), (nodes[i]['name'], 'animated rotation with other keys')
    return np.array([[np.interp(x, t, v[:, c]) for c in range(v.shape[1])] for x in times])


def world(i, local):
    m = local[i]
    while i in parent:
        i = parent[i]; m = local[i] @ m if i in local else m
    return m


def local_mats(over=None):
    L = {}
    for i in range(len(nodes)):
        r = qmat(value(i, 'rotation', [0, 0, 0, 1])) if not (over and (i, 'rotation') in over) else over[i, 'rotation']
        t = value(i, 'translation', [0, 0, 0]) if not (over and (i, 'translation') in over) else over[i, 'translation']
        s = value(i, 'scale', [1, 1, 1])
        m = np.zeros((T, 4, 4)); m[:, :3, :3] = r * s[:, None, :]; m[:, :3, 3] = t; m[:, 3, 3] = 1; L[i] = m
    return L


L0 = local_mats(); P = idx['B_Pelvis']
W = {n: world(idx[n], L0) for n in ['B_Pelvis'] + [f'B_{s}_{b}' for s in 'LR' for b in ('Thigh', 'Calf', 'Foot')]}
UP = 1  # glTF Y up; B_Pelvis's parent (Rig) has no transform
assert 'matrix' not in nodes[parent[P]] and not any(k in nodes[parent[P]] for k in ('translation', 'rotation', 'scale'))
pel = W['B_Pelvis'][:, UP, 3].copy()
legs = {}
for s in 'LR':
    H = W[f'B_{s}_Thigh'][:, :3, 3]; K = W[f'B_{s}_Calf'][:, :3, 3]; A = W[f'B_{s}_Foot'][:, :3, 3]
    l1 = np.linalg.norm(K - H, axis=1).mean(); l2 = np.linalg.norm(A - K, axis=1).mean()
    hor = np.linalg.norm(np.delete(A - H, UP, axis=1), axis=1); R = 0.995 * (l1 + l2)
    dzmax = (A[:, UP] - H[:, UP]) + np.sqrt(np.maximum(R * R - hor * hor, 0)) * 1.0
    legs[s] = (H, K, A, l1, l2, dzmax)
zmax = pel + np.minimum(legs['L'][5], legs['R'][5])  # highest pelvis from which both ankles are reachable
n = T - 1  # key T-1 repeats key 0 (loop)
assert np.allclose(pel[0], pel[-1], atol=1e-5)
k = np.exp(-0.5 * (np.arange(-4 * int(SIGMA) - 1, 4 * int(SIGMA) + 2) / SIGMA) ** 2); k /= k.sum()
smooth = lambda z: np.array([np.dot(k, z[(i + np.arange(len(k)) - len(k) // 2) % n]) for i in range(n)])
# one periodic smoothing pass of the original keeps the two bobs per cycle; where it rises above the reach limit,
# a smooth local dip (window-maximum of the excess, then smoothed) lowers it, repeated until it fits
z = smooth(pel[:n]); lim = zmax[:n]
for _ in range(100):
    over_ = np.maximum(z - lim, 0)
    if over_.max() < 1e-5:
        break
    w = int(SIGMA)
    z = z - smooth(np.array([over_[(i + np.arange(-w, w + 1)) % n].max() for i in range(n)])) * 1.2
znew = np.append(z, z[0]); dz = znew - pel
f48 = np.arange(0, round((times[-1] - times[0]) * 48) + 1) / 48 + times[0]
step48 = lambda zz: np.abs(np.diff(np.interp(f48, times, zz))).max()
print('PELVIS range %.4f-%.4f -> %.4f-%.4f m; largest 48 fps frame step %.4f -> %.4f m' % (
    pel.min(), pel.max(), znew.min(), znew.max(), step48(pel), step48(znew)))


def between(a, b):
    a = a / np.linalg.norm(a, axis=1, keepdims=True); b = b / np.linalg.norm(b, axis=1, keepdims=True)
    v = np.cross(a, b); c = np.einsum('ij,ij->i', a, b); vx = np.zeros((len(a), 3, 3))
    vx[:, 0, 1], vx[:, 0, 2], vx[:, 1, 0], vx[:, 1, 2], vx[:, 2, 0], vx[:, 2, 1] = -v[:, 2], v[:, 1], v[:, 2], -v[:, 0], -v[:, 1], v[:, 0]
    return np.eye(3) + vx + vx @ vx / (1 + c)[:, None, None]


rot = lambda m: m[:, :3, :3] / np.linalg.norm(m[:, :3, :3], axis=1, keepdims=True)
over = {}
ptrans = value(P, 'translation', [0, 0, 0]); ptrans[:, UP] += dz; over[P, 'translation'] = ptrans
Wp = rot(W['B_Pelvis'])
worst_reach = 0
for s in 'LR':
    H, K, A, l1, l2, _ = legs[s]
    H2 = H.copy(); H2[:, UP] += dz
    d = np.linalg.norm(A - H2, axis=1); worst_reach = max(worst_reach, (d / (l1 + l2)).max())
    u = (A - H2) / d[:, None]
    bend = (K - H) - np.einsum('ij,ij->i', K - H, u)[:, None] * u
    bend /= np.linalg.norm(bend, axis=1, keepdims=True)
    a = (l1 * l1 - l2 * l2 + d * d) / (2 * d); h = np.sqrt(np.maximum(l1 * l1 - a * a, 0))
    K2 = H2 + a[:, None] * u + h[:, None] * bend
    Wt = between(K - H, K2 - H2) @ rot(W[f'B_{s}_Thigh'])
    Wc = between(A - K, A - K2) @ rot(W[f'B_{s}_Calf'])
    Wf = rot(W[f'B_{s}_Foot'])
    over[idx[f'B_{s}_Thigh'], 'rotation'] = np.linalg.inv(Wp) @ Wt
    over[idx[f'B_{s}_Calf'], 'rotation'] = np.linalg.inv(Wt) @ Wc
    over[idx[f'B_{s}_Foot'], 'rotation'] = np.linalg.inv(Wc) @ Wf
# verify by FK: ankles and foot rotations unchanged, pelvis as planned
L1 = local_mats(over)
for s in 'LR':
    A1 = world(idx[f'B_{s}_Foot'], L1)[:, :3, 3]; err = np.linalg.norm(A1 - legs[s][2], axis=1).max()
    R1 = rot(world(idx[f'B_{s}_Foot'], L1)); rerr = np.abs(R1 - rot(W[f'B_{s}_Foot'])).max()
    print(f'LEG {s}: ankle path error {err * 1000:.3f} mm, foot rotation error {rerr:.2e}')
    assert err < 5e-4 and rerr < 1e-3
print('REACH worst %.3f of leg length' % worst_reach)
for (i, path), v in over.items():
    _, _, ch = chan[i, path]; s = anim['samplers'][ch['sampler']]
    if len(chan[i, path][0]) != T:
        s['input'] = next(anim['samplers'][c['sampler']]['input'] for (j, p), (t, _, c) in chan.items() if len(t) == T)
    out = matq(v) if path == 'rotation' else v
    if path == 'rotation':  # keep quaternion signs continuous
        for t in range(1, T):
            if np.dot(out[t], out[t - 1]) < 0:
                out[t] = -out[t]
    acc = dict(doc['accessors'][s['output']]); acc['count'] = T; acc.pop('min', None); acc.pop('max', None)
    s['output'] = append_accessor(doc, binary, acc, np.ascontiguousarray(out, '<f4').tobytes())
write_glb(dst, doc, bytes(binary))
np.save(dst.with_suffix('.pelvis.npy'), np.stack([times, pel, znew]))
print('WROTE', dst)
