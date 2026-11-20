#!/usr/bin/env python3
"""Fix two source-animation faults of the Wasp in a game GLB, in place, touching only these keys (every other clip's
data stays byte-identical; the clips keep their key times, 48 Hz):

Death, frames 25-34: the left wing swung down through vertical during the roll, so the build's floor lock raised the
Root (thorax 34.6 cm at frame 26 -> 54.7 cm at 30 -> 14.4 cm at 34, 16.4 cm in one frame). The four wing bones now
turn in one eased move from their frame-22 pose to the frame-34 landing pose (speeds matched at both ends), and the Root height follows a monotonic
Hermite fall from frame 25 (its value and speed) to frame 34 (the landing height, speed zero). Frames that would
put a body or prop vertex under the floor (2 mm) are raised just enough, kept monotonic; frames 34-42 and Dead are
unchanged.

Attack, frames 47-60 (recovery, after the 0.875 s impact at frame 42): Hand_L's turn (30 degrees in one frame at
54-55) is respread along its own path by cumulative angle (a Hermite in path length that keeps the incoming and
outgoing speeds); frames 47 and 60 unchanged.

Evaluation is plain glTF FK + linear blend skinning in numpy (the sword and shield as rigid children of their
joints). Usage: fix_clips.py <game.glb> <sword.glb> <shield.glb>   (rewrites <game.glb>; prints the checks)"""
import json
import struct
import sys
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation, Slerp

glb_path, sword_path, shield_path = (Path(a) for a in sys.argv[1:4])
FLOOR = 0.002


def read(path):
    raw = bytearray(path.read_bytes()); n = struct.unpack_from('<I', raw, 12)[0]
    return json.loads(raw[20:20 + n]), raw, 28 + n


def acc_view(doc, raw, base, i):
    a = doc['accessors'][i]; bv = doc['bufferViews'][a['bufferView']]
    comp = {5126: np.float32, 5123: np.uint16, 5121: np.uint8, 5125: np.uint32}[a['componentType']]
    k = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[a['type']]
    off = base + bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    assert bv.get('byteStride', np.dtype(comp).itemsize * k) == np.dtype(comp).itemsize * k
    return off, comp, k, a['count']


def get(doc, raw, base, i):
    off, comp, k, cnt = acc_view(doc, raw, base, i)
    return np.frombuffer(bytes(raw[off:off + cnt * k * np.dtype(comp).itemsize]), comp).reshape(cnt, k).copy()


def put(doc, raw, base, i, arr):
    off, comp, k, cnt = acc_view(doc, raw, base, i)
    data = np.ascontiguousarray(arr, comp).reshape(cnt, k).tobytes(); raw[off:off + len(data)] = data


doc, raw, base = read(glb_path)
nodes = doc['nodes']; name = [x.get('name') for x in nodes]; idx = {x: i for i, x in enumerate(name)}
parent = {c: i for i, x in enumerate(nodes) for c in x.get('children', [])}
body = nodes[idx['Wasp']]; prim = doc['meshes'][body['mesh']]['primitives'][0]; skin = doc['skins'][body['skin']]
joints = skin['joints']; ibm = get(doc, raw, base, skin['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1)
V = get(doc, raw, base, prim['attributes']['POSITION']); J = get(doc, raw, base, prim['attributes']['JOINTS_0']).astype(int)
Wt = get(doc, raw, base, prim['attributes']['WEIGHTS_0']).astype(np.float64)
if Wt.max() > 1.5:
    Wt /= 255.0 if Wt.max() <= 255 else 65535.0
props = {}
for p, joint in ((sword_path, 'Sword'), (shield_path, 'Shield')):
    pd, pr, pb = read(p); pn = next(x for x in pd['nodes'] if x.get('name') == joint)
    props[joint] = get(pd, pr, pb, pd['meshes'][pn['mesh']]['primitives'][0]['attributes']['POSITION'])


def clip_channels(clip):
    an = next(a for a in doc['animations'] if a['name'] == clip)
    ch = {}
    for c in an['channels']:
        s = an['samplers'][c['sampler']]
        ch[(name[c['target']['node']], c['target']['path'])] = s['output']
    times = get(doc, raw, base, an['samplers'][an['channels'][0]['sampler']]['input'])[:, 0]
    return ch, times


def trs_mats(ch, vals, n):
    """Local matrices per key for every node (channel values where animated, node defaults elsewhere)."""
    L = np.zeros((len(nodes), n, 4, 4))
    for i, x in enumerate(nodes):
        t = vals.get((name[i], 'translation'), np.tile(x.get('translation', [0, 0, 0]), (n, 1)))
        r = vals.get((name[i], 'rotation'), np.tile(x.get('rotation', [0, 0, 0, 1]), (n, 1)))
        s = vals.get((name[i], 'scale'), np.tile(x.get('scale', [1, 1, 1]), (n, 1)))
        M = np.zeros((n, 4, 4)); M[:, :3, :3] = Rotation.from_quat(r).as_matrix() * s[:, None, :]; M[:, :3, 3] = t; M[:, 3, 3] = 1
        L[i] = M
    return L


def world(L):
    Wm = np.zeros_like(L); done = [False] * len(nodes)

    def go(i):
        if done[i]:
            return Wm[i]
        Wm[i] = (go(parent[i]) @ L[i]) if i in parent else L[i]; done[i] = True
        return Wm[i]
    for i in range(len(nodes)):
        go(i)
    return Wm


def evaluate(vals, n, frames):
    """Per frame: thorax height, lowest body vertex, lowest prop vertex (glTF y up), body and prop vertices."""
    Wm = world(trs_mats(None, vals, n))
    out = []
    for f in frames:
        S = Wm[joints, f] @ ibm                      # joint skinning matrices
        Vh = np.c_[V, np.ones(len(V))]
        P = np.einsum('vk,vkij,vj->vi', Wt, S[J], Vh)[:, :3]
        pv = np.concatenate([(np.c_[pp, np.ones(len(pp))] @ Wm[idx[j], f].T)[:, :3] for j, pp in props.items()])
        out.append((Wm[idx['Thorax'], f][1, 3], P[:, 1].min(), pv[:, 1].min(), P, pv))
    return out


def load_vals(ch):
    return {k: get(doc, raw, base, a) for k, a in ch.items()}


# ---------------------------------------------------------------- Death
ch, times = clip_channels('Death'); n = len(times); vals = load_vals(ch); orig = {k: v.copy() for k, v in vals.items()}
F0, F1, W0 = 25, 34, 22
before = evaluate(orig, n, range(n))
smooth = lambda u: u * u * (3 - 2 * u)
for b in ('WingRoot_L', 'WingFlex_L', 'WingRoot_R', 'WingFlex_R'):
    # one eased turn from the frame-W0 pose to the landing pose (slerp path, Hermite in angle with the incoming and
    # outgoing speeds): a blend towards a held pose doubled the flap speed and then stopped dead
    q = vals[(b, 'rotation')]; Ra, Rb = Rotation.from_quat(q[W0]), Rotation.from_quat(q[F1])
    tot = (Ra.inv() * Rb).magnitude(); N = F1 - W0
    v_in = (Rotation.from_quat(q[W0 - 1]).inv() * Ra).magnitude(); v_out = (Rb.inv() * Rotation.from_quat(q[F1 + 1])).magnitude()
    u = np.linspace(0, 1, N + 1)
    sp = (-2 * u**3 + 3 * u**2) + ((u**3 - 2 * u**2 + u) * v_in * N + (u**3 - u**2) * v_out * N) / max(tot, 1e-9)
    sp = np.maximum.accumulate(np.clip(sp, 0, 1))
    path = Slerp([0, 1], Rotation.concatenate([Ra, Rb]))(sp).as_quat()
    path *= np.sign((path * q[W0:F1 + 1]).sum(1))[:, None]
    q[W0:F1 + 1] = path
rt = vals[('Root', 'translation')]
th0 = np.array([e[0] for e in before]); p0, p1 = th0[F0], th0[F1]; m0 = (th0[F0] - th0[F0 - 1]) * (F1 - F0); m1 = 0.0
target = th0.copy()
for f in range(F0, F1 + 1):
    u = (f - F0) / (F1 - F0)
    target[f] = (2 * u**3 - 3 * u**2 + 1) * p0 + (u**3 - 2 * u**2 + u) * m0 + (-2 * u**3 + 3 * u**2) * p1 + (u**3 - u**2) * m1
for it in range(6):
    cur = evaluate(vals, n, range(n)); th = np.array([e[0] for e in cur])
    rt[F0 + 1:F1, 1] += (target - th)[F0 + 1:F1]     # Root has no rotated parent: its y shifts the thorax 1:1
    cur = evaluate(vals, n, range(n)); low = np.array([min(e[1], e[2]) for e in cur]); th = np.array([e[0] for e in cur])
    need = np.where(low < FLOOR, th + (FLOOR - low), -np.inf)
    new = np.maximum(target, need)
    for f in range(F1 - 1, F0, -1):                  # monotonic fall: never below a later frame's height
        new[f] = max(new[f], new[f + 1])
    if np.allclose(new, target, atol=1e-5):
        break
    target = new
after = evaluate(vals, n, range(n))
th1 = np.array([e[0] for e in after]); lowb = np.array([e[1] for e in after]); lowp = np.array([e[2] for e in after])
for k in [('Root', 'translation')] + [(b, 'rotation') for b in ('WingRoot_L', 'WingFlex_L', 'WingRoot_R', 'WingFlex_R')]:
    put(doc, raw, base, ch[k], vals[k])
changed = sorted({k[0] for k in vals if not np.array_equal(vals[k], orig[k])})
print('DEATH changed', changed, 'frames', W0, '-', F1 - 1)
print('DEATH thorax cm before', np.round(th0[20:F1 + 2] * 100, 1).tolist())
print('DEATH thorax cm after ', np.round(th1[20:F1 + 2] * 100, 1).tolist())
print('DEATH max step cm before', round(float(np.abs(np.diff(th0)).max() * 100), 2), 'after', round(float(np.abs(np.diff(th1)).max() * 100), 2),
      '; rises in 25-34 after', int((np.diff(th1[F0:F1 + 1]) > 1e-5).sum()))
for b in ('WingRoot_L', 'WingFlex_L', 'WingRoot_R', 'WingFlex_R'):
    stp = lambda qq: np.degrees([(Rotation.from_quat(qq[i]).inv() * Rotation.from_quat(qq[i + 1])).magnitude() for i in range(n - 1)])
    print('DEATH', b, 'max step deg before', round(float(stp(orig[(b, 'rotation')]).max()), 1), 'after', round(float(stp(vals[(b, 'rotation')]).max()), 1))
print('DEATH lowest body / prop mm after', round(float(lowb.min() * 1000), 1), round(float(lowp.min() * 1000), 1),
      '(before', round(float(min(e[1] for e in before) * 1000), 1), round(float(min(e[2] for e in before) * 1000), 1), ')')
np.savez(Path(glb_path).parent.parent / 'work' / 'death_fix.npz', before=th0, after=th1, low_body=lowb, low_prop=lowp)

# ---------------------------------------------------------------- Attack
ch, times = clip_channels('Attack'); n = len(times); vals = load_vals(ch)
A0, A1 = 47, 60
q = vals[('Hand_L', 'rotation')]; R = Rotation.from_quat(q[A0:A1 + 1])
step = np.array([(R[i].inv() * R[i + 1]).magnitude() for i in range(len(R) - 1)]); cum = np.r_[0, np.cumsum(step)]
Rin = Rotation.from_quat(q[A0 - 1:A0 + 1]); v_in = (Rin[0].inv() * Rin[1]).magnitude(); v_out = step[-1]
u = np.linspace(0, 1, A1 - A0 + 1); N = A1 - A0       # Hermite in path length: the incoming and outgoing speeds kept
s_new = (-2 * u**3 + 3 * u**2) * cum[-1] + (u**3 - 2 * u**2 + u) * v_in * N + (u**3 - u**2) * v_out * N
assert np.all(np.diff(s_new) > 0)
res = []
for s in s_new:
    i = min(int(np.searchsorted(cum, s, side='right')) - 1, len(step) - 1); u = (s - cum[i]) / max(step[i], 1e-12)
    res.append(Slerp([0, 1], Rotation.concatenate([R[i], R[i + 1]]))([u])[0].as_quat())
res = np.array(res); res *= np.sign((res * q[A0:A1 + 1]).sum(1))[:, None]   # keep the source hemisphere
before_steps = np.degrees(step)
q[A0:A1 + 1] = res; put(doc, raw, base, ch[('Hand_L', 'rotation')], q)
R2 = Rotation.from_quat(q); after_steps = np.degrees([(R2[i].inv() * R2[i + 1]).magnitude() for i in range(n - 1)])
print('ATTACK Hand_L steps deg before', np.round(before_steps, 1).tolist())
print('ATTACK Hand_L steps deg after ', np.round(after_steps[A0:A1], 1).tolist(), 'max over clip', round(float(after_steps.max()), 1))
glb_path.write_bytes(bytes(raw))
print('WROTE', glb_path)
