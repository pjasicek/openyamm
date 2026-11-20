"""Wyrde copy (node Wyrde, prims Wyrde_YOUNG / WyrdeHead, clips Death and Dead) of the Thrall's build_lods.py.
tools/build_actor_lods.py (default ratios 0.5 / 0.18 / 0.06, 4 influences, as the model was built) with the floor contact
and the crown as protected points (MM8 batch lesson; mm9_banshee_reduce_claude/scripts/build_lods.py): the boot-sole vertices
within SOLE m of the rest floor and the head-set vertices within TOP m of the top. Without them LOD3 of the reduced model
stood 1.1 cm above the floor in Standing and sank 2.5 cm in Dead (installed LOD3: 0.35 / 1.5 cm); the corpse contact
vertices (posed within LIE of the floor at the end of Death, Death2 and in Dead) are protected too.
Usage: blender -b -P build_lods.py -- <lod0.glb> <out.glb>"""
import os, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / 'tools')); sys.path.insert(0, str(HERE))
from build_actor_lods import generate  # noqa: E402
import glbpack as G, bglbio  # noqa: E402
src, dst = sys.argv[sys.argv.index('--') + 1:][:2]
SOLE = float(os.environ.get('SOLE', '0.006')); TOP = float(os.environ.get('TOP', '0.004'))
d, b = G.read(src)
node = next(n for n in d['nodes'] if n.get('name') == 'Wyrde' and 'mesh' in n)
pr = {p['material']: p for p in bglbio.prims(d, bytes(b), node['mesh'])}
limbs = pr['Wyrde_YOUNG']['POSITION'].astype(np.float64); head = pr['WyrdeHead']['POSITION'].astype(np.float64)
keep = [limbs[limbs[:, 1] < limbs[:, 1].min() + SOLE], head[head[:, 1] > head[:, 1].max() - TOP]]
# the corpse's floor contact: vertices within LIE m of the floor at the end of Death and Death2 and in Dead (rest positions)
sys.path.insert(0, str(HERE.parents[1] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
m = Model(Glb(src)); LIE = float(os.environ.get('LIE', '0.01'))
for clip in ('Death', 'Dead'):
    t = m.clip_times(clip)[-1]
    for k, (posed, _) in enumerate(m.skinned_positions(m.world(m.sample(clip, t)))[:2]):
        rest = bglbio.prims(d, bytes(b), node['mesh'])[k]['POSITION'].astype(np.float64)
        keep.append(rest[posed[:, 1] < LIE])
pts = np.unique(np.vstack(keep).astype(np.float32), axis=0)
# Wyrde (PeasantF6 fix): drop points shared by coincident vertices of one primitive with different skin weights (the tool refuses them;
# e.g. skirt/lining hem): such a point cannot pin one weight set
bad = np.zeros(len(pts), bool)
for p_ in bglbio.prims(d, bytes(b), node['mesh']):
    X = p_['POSITION'].astype(np.float64); JW = np.c_[p_['JOINTS_0'].astype(np.float64), np.round(p_['WEIGHTS_0'].astype(np.float64), 4)]
    for k, q in enumerate(pts.astype(np.float64)):
        ids = np.flatnonzero(np.abs(X - q).max(1) < 2e-5)
        if len(ids) > 1 and len({tuple(JW[i]) for i in ids}) > 1:
            bad[k] = True
print('PROTECTED dropped (coincident, other weights)', int(bad.sum()))
pts = pts[~bad]
# LOD-protection snap (mm9_lesserdemon_reduce_claude): Blender's import moves vertices by up to ~1.3e-5 m and the tool matches
# points to 1e-5 m, so each point becomes the Blender world position of the imported vertex nearest to it (within 1e-4)
import bpy  # noqa: E402
from mathutils.kdtree import KDTree  # noqa: E402
bpy.ops.import_scene.gltf(filepath=str(Path(src).resolve()))
o = bpy.data.objects['Wyrde']; W = [o.matrix_world @ v.co for v in o.data.vertices]
kd = KDTree(len(W)); [kd.insert(w, i) for i, w in enumerate(W)]; kd.balance()
mapped = []
for x, y, z in pts:
    co, i, dist = kd.find((float(x), float(-z), float(y)))
    if dist < 1e-4:
        mapped.append(tuple(co))
print('PROTECTED mapped', len(mapped), 'of', len(pts))
pts = list({tuple(round(c, 7) for c in p): p for p in mapped}.values())
bpy.ops.wm.read_factory_settings(use_empty=True)
print('PROTECTED points', len(pts))
generate(Path(src).resolve(), Path(dst).resolve(), 'Wyrde', ratios=(0.5, 0.18, 0.06), max_influences=4, protected_points=pts)
