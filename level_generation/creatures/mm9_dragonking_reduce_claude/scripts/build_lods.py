"""(Dragon King copy of the Troglodyte/Highwayman build_lods.py: node DragonKing, all three primitives.)
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
node = next(n for n in d['nodes'] if n.get('name') == 'DragonKing' and 'mesh' in n)
plist = bglbio.prims(d, bytes(b), node['mesh'])
allp = [p['POSITION'].astype(np.float64) for p in plist]
P = np.vstack(allp)
floor = P[:, 1].min(); top = P[:, 1].max()
keep = [P[P[:, 1] < floor + SOLE], P[P[:, 1] > top - TOP]]
# the corpse's floor contact: vertices within LIE m of the floor at the end of Death and in Dead (rest positions)
sys.path.insert(0, str(HERE.parents[1] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
m = Model(Glb(src)); LIE = float(os.environ.get('LIE', '0.01'))
for clip in ('Death', 'Dead'):
    t = m.clip_times(clip)[-1]
    posed = m.skinned_positions(m.world(m.sample(clip, t)))
    lo = min(pz[:, 1].min() for pz, _ in posed)
    for k, (pz, _) in enumerate(posed[:3]):
        keep.append(allp[k][pz[:, 1] < lo + LIE])
# the rest-pose extremes along each axis (wing tips, tail tip, arm-head snouts)
TIPS = int(os.environ.get('TIPS', '3')); ntip = 0
for ax in range(3):
    o = np.argsort(P[:, ax]); keep += [P[o[:TIPS]], P[o[-TIPS:]]]; ntip += 2 * TIPS
print('TIP points', ntip)
pts = np.unique(np.vstack(keep).astype(np.float32), axis=0)
# LOD-protection trap (REDUCTION_BRIEF_20261104, mm9_lesserdemon_reduce_claude/scripts/build_lods.py): Blender's glTF import
# moves vertices by ~1e-5 m and build_actor_lods.py matches protected points to 1e-5 m, so plain (x, -z, y) points can match
# nothing. Each point becomes the world position of the imported vertex nearest to it.
import bpy  # noqa: E402
from mathutils.kdtree import KDTree  # noqa: E402
bpy.ops.import_scene.gltf(filepath=str(Path(src).resolve()))
o = bpy.data.objects['DragonKing']; Wv = [o.matrix_world @ v.co for v in o.data.vertices]
kd = KDTree(len(Wv)); [kd.insert(w, i) for i, w in enumerate(Wv)]; kd.balance()
mapped = []; worst = 0.0
for x, y, z in pts:
    co, i, dist = kd.find((float(x), float(-z), float(y)))
    if dist < 1e-4:
        mapped.append(tuple(co)); worst = max(worst, dist)
print('PROTECTED mapped', len(mapped), 'of', len(pts), 'worst offset', worst)
pts = list({tuple(round(c, 7) for c in p): p for p in mapped}.values())
bpy.ops.wm.read_factory_settings(use_empty=True)
print('PROTECTED points', len(pts))
generate(Path(src).resolve(), Path(dst).resolve(), 'DragonKing', ratios=(0.5, 0.18, 0.06), max_influences=4, protected_points=pts)
