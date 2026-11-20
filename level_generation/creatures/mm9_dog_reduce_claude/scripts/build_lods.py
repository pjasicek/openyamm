"""Dog copy (2026-11-05, from mm9_ram_reduce_claude): node Dog, tips XtailC,Xearpiv,Xearpiv1, paw extremes, no horn primitive; corpse contact of Death and Dead.
Ram LODs (Cow copy, 2026-11-05: tail tip Xtail, ear tips, hoof extremes; the horn primitive's tips and extremes too). Cow LODs (Terror copy; tassel tip, ear tips, hoof extremes instead of tentacle/toe tips): tools/build_actor_lods.py (4 influences; ratios LOD_RATIOS, default the tool's 0.5 / 0.18 / 0.06 as the Terror
was built) with protected points (Lesser Demon copy, mm9_lesserdemon_reduce_claude/scripts/build_lods.py): the floor contact
(vertices within SOLE m of the rest floor), the top (within TOP m of the highest point: horn tentacle tips), the tentacle tips
(per last chain bone Bone07/16/11/19/24/33: its TIPS vertices farthest from the joint among those it weights > 0.5), the toe claw
tips (per foot/toe bone the extremes along each axis), the rest-pose extremes of the mesh along each axis, and the corpse contact
(posed within LIE of the lowest point at the end of Death, Death2 and in Dead).
Trap (brief): Blender's import moves vertices by ~1e-5 m and the tool matches points to 1e-5 m, so each point is replaced by the
Blender world position of the imported vertex nearest to it first. Usage: blender -b -P build_lods.py -- <lod0.glb> <out.glb>"""
import os, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / 'tools')); sys.path.insert(0, str(HERE))
from build_actor_lods import generate  # noqa: E402
import glbpack as G, bglbio  # noqa: E402
src, dst = sys.argv[sys.argv.index('--') + 1:][:2]
SOLE = float(os.environ.get('SOLE', '0.006')); TOP = float(os.environ.get('TOP', '0.004')); LIE = float(os.environ.get('LIE', '0.01'))
TIPS = int(os.environ.get('TIPS', '3'))
d, b = G.read(src)
node = next(n for n in d['nodes'] if n.get('name') == 'Dog' and 'mesh' in n)
prs = bglbio.prims(d, bytes(b), node['mesh']); pr = prs[0]
X = pr['POSITION'].astype(np.float64); Jv, Wv = pr['JOINTS_0'], pr['WEIGHTS_0'].astype(np.float64)
keep = [X[X[:, 1] < X[:, 1].min() + SOLE], X[X[:, 1] > X[:, 1].max() - TOP]]
skin = d['skins'][node['skin']]; jn = [d['nodes'][j]['name'] for j in skin['joints']]
ibm = G.acc(d, bytes(b), skin['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1)
for name in ('XtailC', 'Xearpiv', 'Xearpiv1'):   # tail tip, ear tips
    k = jn.index(name); sel = np.flatnonzero((Wv * (Jv == k)).sum(1) > 0.5)
    j0 = np.linalg.inv(ibm[k])[:3, 3]
    keep.append(X[sel[np.argsort(-np.linalg.norm(X[sel] - j0, axis=1))[:TIPS]]])
for name in ('Xffoot', 'Xffoot01', 'Xbfoot', 'Xbfoot01'):   # hoof extremes
    sel = np.flatnonzero((Wv * (Jv == jn.index(name))).sum(1) > 0.5)
    for ax in range(3):
        o = sel[np.argsort(X[sel, ax])]; keep += [X[o[:TIPS]], X[o[-TIPS:]]]
for ax in range(3):
    o = np.argsort(X[:, ax]); keep += [X[o[:TIPS]], X[o[-TIPS:]]]
print('PROTECTED by rule', sum(len(k) for k in keep))
sys.path.insert(0, str(HERE.parents[1] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
m = Model(Glb(src))
for clip in ('Death', 'Dead'):
    t = m.clip_times(clip)[-1]
    posed = m.skinned_positions(m.world(m.sample(clip, t)))[0][0]
    keep.append(X[posed[:, 1] < posed[:, 1].min() + LIE])
pts = np.unique(np.vstack(keep).astype(np.float32), axis=0)
import bpy  # noqa: E402
from mathutils.kdtree import KDTree  # noqa: E402
bpy.ops.import_scene.gltf(filepath=str(Path(src).resolve()))
o = bpy.data.objects['Dog']; W = [o.matrix_world @ v.co for v in o.data.vertices]
kd = KDTree(len(W)); [kd.insert(w, i) for i, w in enumerate(W)]; kd.balance()
mapped = []; worst = 0.0
for x, y, z in pts:
    co, i, dist = kd.find((float(x), float(-z), float(y)))
    worst = max(worst, dist)
    if dist < 1e-4:
        mapped.append(tuple(co))
print('PROTECTED mapped', len(mapped), 'of', len(pts), 'worst snap', worst)
pts = list({tuple(round(c, 7) for c in p): p for p in mapped}.values())
bpy.ops.wm.read_factory_settings(use_empty=True)
print('PROTECTED points', len(pts))
RAT = tuple(float(x) for x in os.environ.get('LOD_RATIOS', '0.5,0.18,0.06').split(','))
generate(Path(src).resolve(), Path(dst).resolve(), 'Dog', ratios=RAT, max_influences=4, protected_points=pts)
