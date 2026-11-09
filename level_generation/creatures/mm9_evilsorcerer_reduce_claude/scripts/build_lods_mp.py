"""(Evil Sorcerer copy of the Imp's: node Sorcerer, prims SorcererUp_A/SorcererLow_A/SorcererHead, no ear block, no tip file;
rest floor = the lowest vertex of every primitive, top = the crown.) (Imp copy (imp-reduce-20261104): + claw, horn and tail tips, ratios 0.5/0.18/0.06 as the Imp was built.
Bigfoot copy of the Gezzampt's, with the Lesser Demon's snap of protected points to the imported vertices; no ear bones,
so the ear-tip block finds nothing. Gezzampt copy of the Troglodyte's build_lods.py: node Gezzampt, prims Imp_A/ImpHead_A; tips = ear tips (Ponytail2)
and the rest-pose extremes of both primitives: fists, hooves, horn tips, crest.)
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
node = next(n for n in d['nodes'] if n.get('name') == 'Sorcerer' and 'mesh' in n)
PRS = bglbio.prims(d, bytes(b), node['mesh']); XS = [p['POSITION'].astype(np.float64) for p in PRS]
top = max(X[:, 1].max() for X in XS); low = min(X[:, 1].min() for X in XS)
keep = [X[X[:, 1] < low + SOLE] for X in XS] + [X[X[:, 1] > top - TOP] for X in XS]
# the corpse's floor contact: vertices within LIE m of the floor at the end of Death and Death2 and in Dead (rest positions)
sys.path.insert(0, str(HERE.parents[1] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
m = Model(Glb(src)); LIE = float(os.environ.get('LIE', '0.01'))
for clip in os.environ.get('CORPSE_CLIPS', 'Death,Death2,Dead').split(','):  # sorcerer: Dead only (Death2 ends 12 cm under the floor)
    t = m.clip_times(clip)[-1]
    for k, (posed, _) in enumerate(m.skinned_positions(m.world(m.sample(clip, t)))[:3]):
        rest = bglbio.prims(d, bytes(b), node['mesh'])[k]['POSITION'].astype(np.float64)
        keep.append(rest[posed[:, 1] < LIE])
TIPS = int(os.environ.get('TIPS', '3')); ntip = 0
for X in XS:
    for ax in range(3):
        o = np.argsort(X[:, ax]); keep += [X[o[:TIPS]], X[o[-TIPS:]]]; ntip += 2 * TIPS
print('TIP points', ntip)
pts = np.unique(np.vstack(keep).astype(np.float32), axis=0)
# LOD-protection trap (REDUCTION_BRIEF_20261104, mm9_lesserdemon_reduce_claude/scripts/build_lods.py): Blender's glTF import
# re-bases the skinned mesh and moves vertices by ~1e-5 m, and build_actor_lods.py matches protected points to 1e-5 m, so
# plain (x, -z, y) points can match nothing. Each point becomes the world position of the imported vertex nearest to it.
import bpy  # noqa: E402
from mathutils.kdtree import KDTree  # noqa: E402
bpy.ops.import_scene.gltf(filepath=str(Path(src).resolve()))
o = bpy.data.objects['Sorcerer']; Wv = [o.matrix_world @ v.co for v in o.data.vertices]
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
RAT = tuple(float(x) for x in os.environ.get('LOD_RATIOS', '0.5,0.18,0.06').split(','))
generate(Path(src).resolve(), Path(dst).resolve(), 'Sorcerer', ratios=RAT, max_influences=4, protected_points=pts)
