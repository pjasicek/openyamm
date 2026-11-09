#!/usr/bin/env python3
"""Fix pass, step 1: chart-guarded pose-aware half-edge collapse of every bone piece on its own (2026-11-04).

The first pass (MeshLab texture-aware quadric per piece) let 75 LOD0 faces reach off the painted UV charts (UV audit) and was
rolled back. Here each decimation group of work/fix/glb_sets.npz (one bone piece, or the cranium dome) is cut with mpqem.Prim
(the Imp's copy: every output vertex is an installed GLB vertex, collapses scored over every clip at 10 Hz plus a position+UV
rest quadric with texture weight MP_W5, texture guard on both tiers' base colours, chart guard MP_CHART: a collapse is refused
if any sample of a new face's UV triangle lands off the installed charts, seam slides when MP_SEAMS=1).
One Prim per piece is run down 0.9, 0.8 ... 0.3 and every step is measured at rest against the source piece: two-way
point-to-surface max and mean (pymeshlab Hausdorff), volume ratio (closed pieces) and the growth of its rest gap to each
neighbouring piece (any primitive, the dagger included).
Writes work/fix/sweep.json {group: {cat, n, rows: [[ratio, faces, max mm, mean mm, volume, gap mm]]}} and
work/fix/sweep_T.npz (g<group>_r<NN>: the step's triangles as GLB vertex indices of the group's primitive).
Usage (meshlab venv): MP_CHART=1 MP_AUDIT=1 MP_W5=4 MP_SEAMS=1 [MP_CONTACT=0.004] [SFX=_x] mp_pieces.py
(MP_AUDIT runs reduction_uv_audit's own chart test, off and cross, on every new face: zero tolerance)
(MP_CONTACT locks every vertex closer than that to a neighbouring piece: the joint contacts)"""
import json
import os
import sys
from pathlib import Path

import numpy as np
import pymeshlab as ml
from scipy.spatial import cKDTree
from scipy import ndimage
from PIL import Image

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import mpqem as M  # noqa: E402
from glb_pose import Glb, Model  # noqa: E402  (mpqem put claude_shared/floor on the path)
import bglbio as glbio  # noqa: E402

RATIOS = [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3]
NEAR = 0.005
glb_path = HERE / 'before' / 'mm9_skeleton.glb'
sets = np.load(HERE / 'work' / 'fix' / 'glb_sets.npz')
plan = json.load(open(HERE / 'work' / 'group_plan.json'))
g = Glb(str(glb_path)); model = Model(g)
doc, binary = glbio.read(glb_path)
node = next(n for n in doc['nodes'] if n.get('name') == 'Skel' and 'mesh' in n)
prims = glbio.prims(doc, binary, node['mesh'])
poses = []
for clip in model.clips:
    t1 = model.clip_times(clip)[-1]
    for t in np.append(np.arange(0, t1, 1 / M.HZ), t1):
        poses.append([p for p, _ in model.skinned_positions(model.world(model.sample(clip, t)))])
print('POSES', len(poses), flush=True)
if os.environ.get('MP_CHART', '0') == '1':
    M.CHART.update(M.chart_masks(prims)); print('CHART masks', list(M.CHART), flush=True)
if os.environ.get('MP_AUDIT', '0') == '1':   # the UV audit's chart test inside every collapse (no 'cross' escapes either)
    sys.path.insert(0, str(HERE.parent / 'claude_shared'))
    import reduction_uv_audit as RA  # noqa: E402
    for pr in prims:
        M.AUDIT[pr['material']] = RA.Charts([(pr['TEXCOORD_0'].astype(np.float64), pr['T'])], (2048, 2048), 2)
    print('AUDIT charts', list(M.AUDIT), flush=True)
tl = json.loads((HERE / 'work' / 'fix' / 'tex_list.json').read_text())
TEX = {k: [ndimage.gaussian_filter(np.asarray(Image.open(HERE / 'work' / f).convert('RGB'), np.float32), (1.5, 1.5, 0))
           for f in v] for k, v in tl.items()}
nf = [len(pr['T']) for pr in prims]; off = np.cumsum([0] + nf)
# every source face in GLB space with its piece, for the gap test
allF = np.concatenate([pr['T'] + 0 for pr in prims]); allP = [pr['POSITION'].astype(np.float64) for pr in prims]
comp = sets['comp']; prim_of = sets['prim']; group = sets['group']; lining = sets['lining']
fpos = [allP[prim_of[f]][allF[f]] for f in range(len(allF))]
fpos = np.stack(fpos)                                                  # (F, 3, 3)
vtree = cKDTree(fpos.reshape(-1, 3))


def mesh(tris):
    v = tris.reshape(-1, 3); u, inv = np.unique(np.round(v, 7), axis=0, return_inverse=True)
    return ml.Mesh(u, inv.reshape(-1, 3).astype(np.int32))


def two_way(a, b):
    ms = ml.MeshSet(); ms.add_mesh(mesh(a)); ms.add_mesh(mesh(b))
    x = ms.get_hausdorff_distance(sampledmesh=1, targetmesh=0, samplevert=True, sampleface=True, samplenum=3000)
    y = ms.get_hausdorff_distance(sampledmesh=0, targetmesh=1, samplevert=True, sampleface=True, samplenum=3000)
    return max(x['max'], y['max']) * 1000, max(x['mean'], y['mean']) * 1000


def gap(a, b):
    ms = ml.MeshSet(); ms.add_mesh(mesh(a)); ms.add_mesh(mesh(b))
    return ms.get_hausdorff_distance(sampledmesh=0, targetmesh=1, samplevert=True, sampleface=True, samplenum=4000)['min'] * 1000


def volume(tris):
    return float(np.einsum('ij,ij->i', tris[:, 0], np.cross(tris[:, 1], tris[:, 2])).sum() / 6)


def closed(T):
    e = np.sort(np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]), 1)
    _, c = np.unique(e, axis=0, return_counts=True)
    return int((c == 1).sum())


out, snaps = {}, {}
only = {int(x) for x in os.environ.get('ONLY', '').split(',') if x}
for gid in sorted(int(x) for x in np.unique(group[group > 0])):
    if only and gid not in only:
        continue
    gfaces = np.flatnonzero(group == gid); pi = int(prim_of[gfaces[0]]); assert (prim_of[gfaces] == pi).all()
    pr = prims[pi]; local = gfaces - off[pi]; T = pr['T'][local]
    P = pr['POSITION'].astype(np.float64)
    used = np.unique(T); remap = -np.ones(len(P), np.int64); remap[used] = np.arange(len(used))
    posed = np.stack([pz[pi][used] for pz in poses])
    src = P[T]
    # closedness by position (glTF splits vertices at UV seams)
    _, wid = np.unique(np.round(P[used], 6), axis=0, return_inverse=True); wid = wid.ravel()
    is_closed = closed(wid[remap[T]]) == 0
    svol = volume(src) if is_closed else 0.0
    # neighbouring pieces: source faces of other pieces with a vertex within NEAR of this piece
    own = set(np.unique(comp[gfaces]).tolist())
    hit = vtree.query_ball_point(P[used], NEAR)
    nb_faces = np.unique([int(i) // 3 for h in hit for i in h])
    nb = {}
    for f in nb_faces:
        if int(comp[f]) not in own and not lining[f]:
            nb.setdefault(int(comp[f]), None)
    nbf = {k: fpos[comp == k] for k in nb}
    g0 = {k: gap(src, v) for k, v in nbf.items()}
    # joint contacts (MP_CONTACT, metres): vertices this close to a neighbouring piece are locked, so a collapse cannot pull a
    # bone end back from its joint (the first pass opened the index knuckles 5.8 mm)
    lockv = None
    CONTACT = float(os.environ.get('MP_CONTACT', '0'))
    if CONTACT > 0 and nbf:
        nv = np.concatenate([v.reshape(-1, 3) for v in nbf.values()])
        lockv = cKDTree(nv).query(P[used])[0] < CONTACT
    prim = M.Prim(f"{pr['material']}/{gid}", P[used], pr['TEXCOORD_0'].astype(np.float64)[used], remap[T].copy(),
                  pr['JOINTS_0'][used], pr['WEIGHTS_0'].astype(np.float64)[used], posed, np.zeros(len(T), bool), lockv,
                  TEX.get(pr['material']), seams=os.environ.get('MP_SEAMS', '1') == '1')
    rows = []; log = []; prev = len(T)
    for r in RATIOS:
        t_, _ = prim.run(r, log)
        if len(t_) >= prev:                                      # stuck: no allowed collapse left
            break
        prev = len(t_)
        tris = P[used][t_]
        mx, mean = two_way(src, tris)
        vol = volume(tris) / svol if is_closed and svol else 1.0
        dg = max([gap(tris, v) - g0[k] for k, v in nbf.items()] or [0.0])
        rows.append([r, int(len(t_)), round(mx, 2), round(mean, 3), round(vol, 3), round(dg, 2)])
        snaps[f'g{gid}_r{int(round(r * 100))}'] = used[t_]
    base, cat, n = plan[str(gid)]
    out[gid] = dict(cat=cat, n=int(len(T)), prim=pi, closed=bool(is_closed), rows=rows)
    print(f'g{gid:3d} {cat:6s} {len(T):4d}', ' '.join(f'{x[0]:.1f}:{x[1]}f {x[2]:.1f}/{x[3]:.2f} v{x[4]:.2f} g{x[5]:.1f}' for x in rows),
          '|', log[-1].split(': ', 1)[1] if log else '', flush=True)
sfx = os.environ.get('SFX', '')
(HERE / 'work' / 'fix' / f'sweep{sfx}.json').write_text(json.dumps(out))
np.savez(HERE / 'work' / 'fix' / f'sweep_T{sfx}.npz', **snaps)
