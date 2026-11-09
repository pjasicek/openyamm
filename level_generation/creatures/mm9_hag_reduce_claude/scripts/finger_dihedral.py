#!/usr/bin/env python3
"""Finger facet check (Kira r8 measure: one smooth cut of the MPFB fingers took the finger dihedrals from p50 20 / p90 45 deg to
11 / 26 deg, the user's "faceted fingers"): dihedral angles between edge-adjacent finger faces (faces of the hand pieces whose
dominant joint is a finger bone; edges welded by position) of the LOD0 Kira primitive, plus the finger-face count and each
fingertip's distance from its distal joint (every finger kept at full length). Usage: finger_dihedral.py <glb> [...]"""
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
FING = ('Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky')
for path in sys.argv[1:]:
    doc, binary, nd, D = glbio.load(path, 'Hag')
    jn = [doc['nodes'][j]['name'] for j in doc['skins'][nd['skin']]['joints']]
    fj = np.array([any(t in x for t in FING) for x in jn])
    P, T, J, W = D['Hag']['P'], D['Hag']['T'], D['Hag']['J'], D['Hag']['W']
    dom = J[np.arange(len(J)), W.argmax(1)]
    f = fj[dom[T]].all(1); TF = T[f]
    _, w = np.unique(P.round(6), axis=0, return_inverse=True); w = w.ravel(); TT = w[TF]
    n = np.cross(P[TF[:, 1]] - P[TF[:, 0]], P[TF[:, 2]] - P[TF[:, 0]]); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-20)
    ed = {}
    for i, t in enumerate(TT):
        for a, b in ((0, 1), (1, 2), (2, 0)):
            ed.setdefault((min(t[a], t[b]), max(t[a], t[b])), []).append(i)
    ang = np.array([np.degrees(np.arccos(np.clip(n[v[0]] @ n[v[1]], -1, 1))) for v in ed.values() if len(v) == 2])
    ibm = np.array(glbio.arr(doc, binary, doc['skins'][nd['skin']]['inverseBindMatrices'])).reshape(-1, 4, 4).transpose(0, 2, 1)
    jp = np.linalg.inv(ibm)[:, :3, 3]; used = np.unique(T)
    tips = []
    for s in 'LR':
        for fn in ('Thumb3', 'Index3', 'Middle3', 'Ring3', 'Pinky3'):
            ji = jn.index(f'Bip01 {s} {fn}'); vs = used[dom[used] == ji]
            tips.append(round(float(np.linalg.norm(P[vs] - jp[ji], axis=1).max() * 1000), 2) if len(vs) else -1)
    print(f'{Path(path).name}: finger faces {int(f.sum())}, dihedral p50 {np.percentile(ang, 50):.1f} p90 {np.percentile(ang, 90):.1f} '
          f'max {ang.max():.1f} deg; tip reach mm L/R thumb..pinky {tips}')
