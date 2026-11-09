#!/usr/bin/env python3
"""Club rebuilt low-poly (prio-1 relaxed set: simple rigid props are rebuilt, not decimated). The installed club is
../mm9_trellborg_claude/scripts/make_club.py's lathe (19 stations x 14 sides) plus six iron nails, placed by an affine map
(fitted here from work/club.npz to the installed primitive, residual < 1e-6 m). The rebuild uses the same stations minus the
two that lie on a straight line (grip middle -0.635, head middle 0.22) and SIDES sides on the old corner radius (the new
ring inscribed in the same circle), and make_club's own cylinder UVs (u linear in the angle, v linear in t), so the
installed club maps are used unchanged (no bake needed). Nails: vertices, normals, UVs and triangles byte for byte.
Normals: angle-weighted smooth per vertex, seam unmerged, as installed (selftest printed). Weights: Yclub 1.0 as installed.
Usage: club_rebuild.py <in.glb> <out.glb>"""
import os, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
SIDES = int(os.environ.get('SIDES', 10)); DROP = [-0.635, 0.22]
src, out = sys.argv[1:3]
doc, binary, nd, PR = glbio.load(src, 'Trellborg'); binary = bytearray(binary)
c = PR['TrellborgClub']; z = np.load(HERE.parent / 'mm9_trellborg_claude/work/club.npz')
A = np.c_[z['V'], np.ones(len(z['V']))]; X = np.linalg.lstsq(A, c['P'], rcond=None)[0]
assert np.abs(A @ X - c['P']).max() < 1e-5
assert np.abs(c['UV'][:, 0] - z['UV'][:, 0]).max() < 1e-6 and np.abs(c['UV'][:, 1] - (1 - z['UV'][:, 1])).max() < 1e-6
GR = 0.0255
ST = [(-0.893, 0.0, 0.010, 0.010), (-0.875, 0.0, 0.034, 0.034), (-0.84, 0.0, 0.043, 0.043), (-0.80, 0.0, 0.040, 0.040), (-0.765, 0.0, 0.031, 0.031), (-0.72, 0.0, GR, GR), (-0.635, 0.0, GR, GR),
      (-0.55, 0.0, GR, GR), (-0.50, 0.0, 0.034, 0.034), (-0.44, 0.0, 0.043, 0.047), (-0.30, 0.012, 0.070, 0.082), (-0.16, 0.035, 0.096, 0.118), (-0.08, 0.055, 0.112, 0.136), (0.05, 0.06, 0.116, 0.138),
      (0.22, 0.06, 0.118, 0.138), (0.37, 0.06, 0.118, 0.136), (0.415, 0.056, 0.090, 0.104), (0.445, 0.05, 0.040, 0.046), (0.457, 0.05, 0.006, 0.006)]
N0 = 14; TMIN, TMAX = ST[0][0], ST[-1][0]
nlathe = len(ST) * (N0 + 1); flathe = (len(ST) - 1) * N0 * 2
assert len(c['T']) == flathe + 72 and len(c['P']) == nlathe + 54


def lathe(stations, n, k):
    V, UV, F = [], [], []
    for s in stations:
        for j in range(n + 1):
            a = 2 * np.pi * j / n
            V.append((s[0], s[1] + s[2] * k * np.cos(a), s[3] * k * np.sin(a)))
            UV.append((0.5 * j / n * 0.97 + 0.005, 1 - (0.02 + 0.96 * (s[0] - TMIN) / (TMAX - TMIN))))
    for r in range(len(stations) - 1):
        for j in range(n):
            a, b = r * (n + 1) + j, (r + 1) * (n + 1) + j
            F += [(a, a + 1, b + 1), (a, b + 1, b)]
    return np.array(V), np.array(UV), np.array(F)


def smooth(P, T):
    # the installed lathe: Blender's angle-weighted smooth normals, the u seam (j = 0 and j = n) not merged (selftest 0.02 deg)
    tri = P[T]; fn = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]); fn /= np.linalg.norm(fn, axis=1)[:, None]
    Ns = np.zeros((len(P), 3))
    for k in range(3):
        a, b = tri[:, (k + 1) % 3] - tri[:, k], tri[:, (k + 2) % 3] - tri[:, k]
        w = np.arccos(np.clip((a * b).sum(1) / np.linalg.norm(a, axis=1) / np.linalg.norm(b, axis=1), -1, 1))
        np.add.at(Ns, T[:, k], fn * w[:, None])
    return Ns / np.maximum(np.linalg.norm(Ns, axis=1, keepdims=True), 1e-12)


# selftest: the rule on the installed lathe
dev = np.degrees(np.arccos(np.clip((smooth(c['P'][:nlathe], c['T'][:flathe]) * c['N'][:nlathe]).sum(1), -1, 1)))
print('SELFTEST lathe normals rule vs installed deg: median', round(float(np.median(dev)), 2), 'p99', round(float(np.percentile(dev, 99)), 2), 'max', round(float(dev.max()), 2))
st = [s for s in ST if s[0] not in DROP]
k = float(os.environ.get('RADK', 1.0))  # 1.0: vertices on the old circumcircle (1.025 kept the mid-face radius but put the club 4.6 mm under the floor in Death)
V, UV, F = lathe(st, SIDES, k)
Pn = np.c_[V, np.ones(len(V))] @ X
Nn = smooth(Pn, F)
nails = slice(nlathe, None)
P2 = np.vstack([Pn, c['P'][nails]]); N2 = np.vstack([Nn, c['N'][nails]]); UV2 = np.vstack([UV, c['UV'][nails]])
T2 = np.vstack([F, c['T'][flathe:] - nlathe + len(V)])
J2 = np.repeat(c['J'][:1], len(P2), 0); W2 = np.repeat(c['W'][:1], len(P2), 0)
p = c['prim']; acc = lambda i: doc['accessors'][i]


def put(sem, arr_, dtype):
    a = dict(acc(p['attributes'][sem])); a['count'] = len(arr_)
    if sem == 'POSITION': a['min'] = arr_.min(0).tolist(); a['max'] = arr_.max(0).tolist()
    else: a.pop('min', None); a.pop('max', None)
    p['attributes'][sem] = glbio.append_accessor(doc, binary, a, np.ascontiguousarray(arr_.astype(dtype)).tobytes())


put('POSITION', P2, '<f4'); put('NORMAL', N2, '<f4'); put('TEXCOORD_0', UV2, '<f4')
jt = {5121: 'u1', 5123: '<u2'}[acc(p['attributes']['JOINTS_0'])['componentType']]; put('JOINTS_0', J2, jt)
put('WEIGHTS_0', W2, {5126: '<f4', 5121: 'u1', 5123: '<u2'}[acc(p['attributes']['WEIGHTS_0'])['componentType']] if acc(p['attributes']['WEIGHTS_0'])['componentType'] == 5126 else '<f4')
ia = dict(acc(p['indices'])); ia['count'] = T2.size; ia.pop('min', None); ia.pop('max', None)
ict = 5125 if len(P2) > 65535 else ia['componentType']; ia['componentType'] = ict
p['indices'] = glbio.append_accessor(doc, binary, ia, T2.reshape(-1).astype({5123: '<u2', 5125: '<u4'}[ict]).tobytes())
glbio.write_glb(Path(out), doc, bytes(binary))
print('CLUB', len(c['T']), '->', len(T2), 'triangles,', len(c['P']), '->', len(P2), 'vertices; sides', SIDES, 'stations', len(st), 'radius x', round(k, 4))
