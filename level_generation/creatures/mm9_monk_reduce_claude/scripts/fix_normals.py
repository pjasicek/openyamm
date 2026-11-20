#!/usr/bin/env python3
"""LOD0 normals of the reduced Monk the way its own build made them (../mm9_monk_claude/scripts/build_glb.py): every
candidate vertex that is a source vertex (same material, position and UV within 1e-5) takes the installed normal byte
for byte; every new vertex takes build_glb's rule on the reduced mesh: area-weighted face normals merged by position,
and on the robe three rounds of neighbour averaging along the surface. Blender's export normals are discarded.
The MonkHead primitive is restored from the installed file byte for byte (attributes and indices; it is kept whole).
Usage: fix_normals.py <source.glb> <in.glb> <out.glb>   (also: --selftest <source.glb>)"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
KEEP = ['MonkHead']


def robe_vertices(P, T, S):
    """robe vertices of a Monk_A primitive: faces whose nearest source face (rest centroid) is a robe face"""
    g = np.load(HERE / 'work' / 'glb_parts.npz'); names = [str(x) for x in g['names']]
    sT = S['Monk_A']['T']; sc = S['Monk_A']['P'][sT].mean(1); srobe = g['part'][:len(sT)] == names.index('robe')
    _, nn = cKDTree(sc).query(P[T].mean(1)); fr = srobe[nn]
    m = np.zeros(len(P), bool); m[np.unique(T[fr])] = True
    return m


def rule(P, T, robe):
    fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
    key = np.round(P, 5); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
    nw = inv.max() + 1; Ns = np.zeros((nw, 3))
    for c in range(3):
        np.add.at(Ns, inv[T[:, c]], fn)
    ed = np.vstack([inv[T[:, [0, 1]]], inv[T[:, [1, 2]]], inv[T[:, [2, 0]]]])
    robew = np.zeros(nw, bool); robew[inv[robe]] = True
    unit = lambda x: x / np.maximum(np.linalg.norm(x, axis=1, keepdims=True), 1e-12)
    for _ in range(3):
        Ac = np.zeros((nw, 3)); cnt = np.zeros(nw)
        np.add.at(Ac, ed[:, 0], unit(Ns[ed[:, 1]])); np.add.at(cnt, ed[:, 0], 1)
        np.add.at(Ac, ed[:, 1], unit(Ns[ed[:, 0]])); np.add.at(cnt, ed[:, 1], 1)
        Nw = unit(Ns); Nw[robew] = (Nw + Ac / np.maximum(cnt, 1)[:, None])[robew]; Ns = Nw
    return unit(Ns[inv])


if sys.argv[1] == '--selftest':
    doc, binary, nd, S = glbio.load(sys.argv[2])
    s = S['Monk_A']; N = rule(s['P'], s['T'], robe_vertices(s['P'], s['T'], S))
    dev = np.degrees(np.arccos(np.clip((N * s['N']).sum(1), -1, 1)))
    print('SELFTEST Monk_A rule vs installed deg: median', round(float(np.median(dev)), 3), 'p99',
          round(float(np.percentile(dev, 99)), 2), 'max', round(float(dev.max()), 2), '>2deg', int((dev > 2).sum()), 'of', len(dev))
    sys.exit()

src, inp, out = (Path(a) for a in sys.argv[1:4])
sdoc, sbin, snd, S = glbio.load(src); doc, binary, nd, C = glbio.load(inp); binary = bytearray(binary)
c = C['Monk_A']; s = S['Monk_A']
N = rule(c['P'], c['T'], robe_vertices(c['P'], c['T'], S))
hits = cKDTree(s['P']).query_ball_point(c['P'], 1e-5); copied = 0
for i, h in enumerate(hits):
    h = [j for j in h if np.abs(s['UV'][j] - c['UV'][i]).max() < 1e-5]
    if h:
        j = max(h, key=lambda j: float(s['N'][j] @ N[i])); N[i] = s['N'][j]; copied += 1
acc = doc['accessors'][c['prim']['attributes']['NORMAL']]
c['prim']['attributes']['NORMAL'] = glbio.append_accessor(doc, binary, acc, N.astype('<f4').tobytes())
print('NORMALS Monk_A vertices', len(N), 'installed normal kept', copied, 'rule', len(N) - copied)
# the installed encoding (u16 joints, u32 indices; Blender wrote u8/u16): build_actor_lods merges the shadow primitives
# and needs every primitive's attributes encoded alike
ja = dict(doc['accessors'][c['prim']['attributes']['JOINTS_0']], componentType=5123)
c['prim']['attributes']['JOINTS_0'] = glbio.append_accessor(doc, binary, ja, c['J'].astype('<u2').tobytes())
ia = dict(doc['accessors'][c['prim']['indices']], componentType=5125)
c['prim']['indices'] = glbio.append_accessor(doc, binary, ia, c['T'].reshape(-1).astype('<u4').tobytes())
for name in KEEP:
    sp, cp = S[name]['prim'], C[name]['prim']
    assert len(S[name]['T']) - len(C[name]['T']) in range(0, 30), f'{name} was not kept whole'
    cp['attributes'] = {k: glbio.append_accessor(doc, binary, sdoc['accessors'][i], glbio.accessor_bytes(sdoc, sbin, i))
                        for k, i in sp['attributes'].items()}
    cp['indices'] = glbio.append_accessor(doc, binary, sdoc['accessors'][sp['indices']], glbio.accessor_bytes(sdoc, sbin, sp['indices']))
    print('KEPT PRIMITIVE', name, 'installed bytes,', len(S[name]['T']), 'triangles')
glbio.write_glb(out, doc, bytes(binary))
