#!/usr/bin/env python3
"""Body faces the Imp's attachments sit on (imp-reduce-20261104): the trident (mm9_imp_trident.glb, rigid on Yweaponbase)
against the right fist, and the shin wraps (mm9_imp_wrapl/wrapr.glb, rigid on Xwrap L/R) against the calves. Each attachment
is posed on its joint's world matrix at FPS (default 24) samples of every clip; a body face (LOD0 Imp_A primitive) whose posed centroid comes
within C m (default 1.5 cm) of the attachment's surface (vertices and face centres) in any sample is kept exactly.
Writes work/keep_extra_grip.npy, keep_extra_wrap.npy and keep_extra_shaft.npy (left-hand faces within CONTACT_SHAFT, 7 cm) (one entry per GLB face of both LOD0 primitives)."""
import os, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE / 'scripts'))
from glb_pose import Glb, Model  # noqa: E402
import bglbio as gb  # noqa: E402
C = float(os.environ.get('CONTACT', '0.015')); C_GRIP = float(os.environ.get('CONTACT_GRIP', '0.025')); NT = int(os.environ.get('NT', '6'))
FPS = float(os.environ.get('FPS', '24'))   # n80: Hit2 frame 30 (between the 6 samples) put the trident 6 cm 'inside' the left fingers
SRC = HERE.parents[2] / 'assets_source/worlds/mm9/models'
m = Model(Glb(str(HERE / 'before' / 'mm9_imp.glb')))
nm = [n.get('name') for n in m.glb.json['nodes']]
imp_node = next(i for i, n in enumerate(m.glb.json['nodes']) if n.get('name') == 'Imp' and 'mesh' in n)
pidx = [i for i, p in enumerate(m.primitives) if p['node'] == imp_node]
assert len(pidx) == 2
nB = len(m.primitives[pidx[0]]['triangles']); nH = len(m.primitives[pidx[1]]['triangles'])


def attachment(name):
    doc, b = gb.read(SRC / f'mm9_imp_{name}.glb')
    n = next(n for n in doc['nodes'] if 'mesh' in n); p = gb.prims(doc, b, n['mesh'])[0]
    P = p['POSITION'].astype(float); T = p['T']
    pts = np.r_[P, P[T].mean(1)]
    if name == 'trident':   # the long shaft faces have no interior points: a line of 240 samples (as blade_gate.py)
        ax = np.linalg.svd(P - P.mean(0))[2][0]; t_ = P @ ax; e0, e1 = P[t_.argmin()], P[t_.argmax()]
        pts = np.r_[pts, e0 + np.outer(np.linspace(0, 1, 240), e1 - e0)]
    return n['name'], np.c_[pts, np.ones(len(pts))]


out = {}
# shaft: left-hand faces within C_SHAFT of the trident (n80: in Hit2 frames 28-31 the shaft passes 3.8-5 cm from the left
# fingers; the cut fingers turned blade_gate's nearest-face sign test into a 6 cm false 'inside' reading, winding number 0.01)
jn_ = [nm[j] for j in m.joints]; P0 = m.primitives[pidx[0]]
dom_ = np.array(jn_)[P0['joints'][np.arange(len(P0['positions'])), P0['weights'].argmax(1)]]
lh_ = np.array([('L Hand' in x or 'L Finger' in x) for x in dom_])[np.asarray(P0['triangles'])].any(1)
rh_ = np.array([('R Hand' in x or 'R Finger' in x) for x in dom_])[np.asarray(P0['triangles'])].any(1)
C_SHAFT = float(os.environ.get('CONTACT_SHAFT', '0.07'))
for key, names, C in (('grip', ['trident'], C_GRIP), ('wrap', ['wrapl', 'wrapr'], C), ('shaft', ['trident'], C_SHAFT)):
    att = [attachment(a) for a in names]
    best = np.full(nB, 9.0)
    for clip in m.clips:
        ts = m.clip_times(clip)
        for t in (np.arange(ts[0], ts[-1] + 1e-6, 1 / FPS) if FPS else np.linspace(ts[0], ts[-1], NT)):
            w = m.world(m.sample(clip, t))
            P, T = m.skinned_positions(w)[pidx[0]]
            cen = P[T].mean(1)
            for jn, H in att:
                pts = (H @ w[nm.index(jn)].T)[:, :3]
                d, _ = cKDTree(pts).query(cen); best = np.minimum(best, d)
    k = best < C
    if key == 'shaft':
        k &= lh_
    if key == 'grip':      # the fist only (with the shaft samples, faces along the shaft's path would join)
        k &= rh_
    print(key, 'body faces within', C, 'm:', int(k.sum()), 'closest', round(float(best.min()) * 1000, 2), 'mm')
    np.save(HERE / 'work' / f'keep_extra_{key}.npy', np.r_[k, np.zeros(nH, bool)])
