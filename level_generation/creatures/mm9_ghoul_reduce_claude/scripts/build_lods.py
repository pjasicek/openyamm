"""(Ghoul copy of the Troglodyte's copy of the Highwayman's build_lods.py: node Ghoul, prims Ghoul_A/GhoulHead_A; claw tips per
digit chain, since the Ghoul's distal bones weight almost nothing.)
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
node = next(n for n in d['nodes'] if n.get('name') == 'Ghoul' and 'mesh' in n)
pr = {p['material']: p for p in bglbio.prims(d, bytes(b), node['mesh'])}
limbs = pr['Ghoul_A']['POSITION'].astype(np.float64); head = pr['GhoulHead_A']['POSITION'].astype(np.float64)
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
# claw tips (Troglodyte, a55: LOD3 lost 9 cm of the right hand's claws, picking bounds 0.454 against 0.583 m): per finger tip
# bone (Finger12/22/32) and toe, the TIPS vertices farthest from the bone's rest joint among the vertices it weights > 0.5
TIPS = int(os.environ.get('TIPS', '3'))
skin = d['skins'][node['skin']]; jn = [d['nodes'][j]['name'] for j in skin['joints']]
ibm = G.acc(d, bytes(b), skin['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1)
bp = pr['Ghoul_A']; Jb, Wb = bp['JOINTS_0'], bp['WEIGHTS_0'].astype(np.float64); ntip = 0
chains = {}
for k, name in enumerate(jn):
    if 'Finger' in name:
        chains.setdefault(name[:name.index('Finger') + 7], []).append(k)     # 'Bip01 L Finger1' + its 11/12
    elif name.endswith('Toe0'):
        chains[name] = [k]
for ch, ks in chains.items():
    w = sum((Wb * (Jb == k)).sum(1) for k in ks); sel = np.flatnonzero(w > 0.5)
    if not len(sel):
        continue
    j0 = np.linalg.inv(ibm[ks[0]])[:3, 3]
    far = sel[np.argsort(-np.linalg.norm(limbs[sel] - j0, axis=1))[:TIPS]]
    keep.append(limbs[far]); ntip += len(far)
# and the rest-pose extremes of the body along each axis (a55: LOD3 tail tip 1.4 cm shorter)
for ax in range(3):
    o = np.argsort(limbs[:, ax]); keep += [limbs[o[:TIPS]], limbs[o[-TIPS:]]]; ntip += 2 * TIPS
print('TIP points', ntip)
pts = np.unique(np.vstack(keep).astype(np.float32), axis=0)
# (brief, Lesser Demon lesson) Blender's glTF import re-bases this skinned mesh under its rig (the Ghoul: local z = y - 1.109) and
# its world positions differ from the GLB's by ~1e-5 m, while the tool matches points to 1e-5 m: each point is replaced by the
# Blender world position of the imported vertex nearest to it (within 1e-4), then the import is cleared for generate().
import bpy  # noqa: E402
from mathutils.kdtree import KDTree  # noqa: E402
bpy.ops.import_scene.gltf(filepath=str(Path(src).resolve()))
o = bpy.data.objects['Ghoul']; Wv = [o.matrix_world @ v.co for v in o.data.vertices]
kd = KDTree(len(Wv)); [kd.insert(w, i) for i, w in enumerate(Wv)]; kd.balance()
mapped = []
for x, y, z in pts:
    co, i, dist = kd.find((float(x), float(-z), float(y)))
    if dist < 1e-4:
        mapped.append(tuple(co))
print('PROTECTED mapped', len(mapped), 'of', len(pts))
pts = list({tuple(round(c, 7) for c in p): p for p in mapped}.values())
bpy.ops.wm.read_factory_settings(use_empty=True)
print('PROTECTED points', len(pts))
generate(Path(src).resolve(), Path(dst).resolve(), 'Ghoul', ratios=(0.5, 0.18, 0.06), max_influences=4, protected_points=pts)
