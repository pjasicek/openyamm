"""(Bigfoot copy of the Gezzampt's, with the Lesser Demon's snap of protected points to the imported vertices; no ear bones,
so the ear-tip block finds nothing. Gezzampt copy of the Troglodyte's build_lods.py: node Gezzampt, prims Bigfoot_A/BigfootHead_A; tips = ear tips (Ponytail2)
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
node = next(n for n in d['nodes'] if n.get('name') == 'Bigfoot' and 'mesh' in n)
pr = {p['material']: p for p in bglbio.prims(d, bytes(b), node['mesh'])}
limbs = pr['Bigfoot_A']['POSITION'].astype(np.float64); head = pr['BigfootHead_A']['POSITION'].astype(np.float64)
top = max(limbs[:, 1].max(), head[:, 1].max())
keep = [limbs[limbs[:, 1] < limbs[:, 1].min() + SOLE], limbs[limbs[:, 1] > top - TOP], head[head[:, 1] > top - TOP]]
# the corpse's floor contact: vertices within LIE m of the floor at the end of Death and Death2 and in Dead (rest positions)
sys.path.insert(0, str(HERE.parents[1] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
m = Model(Glb(src)); LIE = float(os.environ.get('LIE', '0.01'))
for clip in ('Death', 'Death2', 'Dead'):
    t = m.clip_times(clip)[-1]
    for k, (posed, _) in enumerate(m.skinned_positions(m.world(m.sample(clip, t)))[:3]):
        rest = bglbio.prims(d, bytes(b), node['mesh'])[k]['POSITION'].astype(np.float64)
        keep.append(rest[posed[:, 1] < LIE])
# tips: the ear tips (vertices farthest from the Ponytail1/2 joint among those it weights > 0.5) and the rest-pose extremes of
# both primitives along each axis (fists, hooves, horn tips, the crest)
TIPS = int(os.environ.get('TIPS', '3'))
skin = d['skins'][node['skin']]; jn = [d['nodes'][j]['name'] for j in skin['joints']]
ibm = G.acc(d, bytes(b), skin['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1)
hp = pr['BigfootHead_A']; Jh, Wh = hp['JOINTS_0'], hp['WEIGHTS_0'].astype(np.float64); ntip = 0
for k, name in enumerate(jn):
    if not name.endswith(('Ponytail1', 'Ponytail2')):      # one ear each
        continue
    w = (Wh * (Jh == k)).sum(1); sel = np.flatnonzero(w > 0.5)
    if not len(sel):
        continue
    j0 = np.linalg.inv(ibm[k])[:3, 3]
    far = sel[np.argsort(-np.linalg.norm(head[sel] - j0, axis=1))[:TIPS]]
    keep.append(head[far]); ntip += len(far); print('EAR', name, head[far].round(3).tolist())
# hoof outline (e57: LOD3's collapsed hoof heel went 2 cm under the floor in Dead): the extremes of each hoof (Foot weight > 0.5)
lp = pr['Bigfoot_A']; Jl, Wl = lp['JOINTS_0'], lp['WEIGHTS_0'].astype(np.float64)
for k, name in enumerate(jn):
    if not name.endswith(' Foot'):
        continue
    sel = np.flatnonzero((Wl * (Jl == k)).sum(1) > 0.5)
    for ax in range(3):
        o = sel[np.argsort(limbs[sel, ax])]; keep += [limbs[o[:TIPS]], limbs[o[-TIPS:]]]; ntip += 2 * TIPS
for X in (limbs, head):
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
o = bpy.data.objects['Bigfoot']; Wv = [o.matrix_world @ v.co for v in o.data.vertices]
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
RAT = tuple(float(x) for x in os.environ.get('LOD_RATIOS', '0.5,0.2,0.075').split(','))
generate(Path(src).resolve(), Path(dst).resolve(), 'Bigfoot', ratios=RAT, max_influences=4, protected_points=pts)
