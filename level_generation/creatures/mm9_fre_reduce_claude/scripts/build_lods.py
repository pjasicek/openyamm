"""tools/build_actor_lods.py (default ratios, 4 influences, as Fre was built: build_runtime_fre.sh) with protected points
(brief: the LOD-protection snap trap, mm9_lesserdemon_reduce_claude/scripts/build_lods.py): the floor contact (vertices within SOLE m
of the rest floor), the crown (vertices within TOP m of the top) and the corpse contact (posed within LIE m of the floor at the end of
Death and in Dead). Each point is snapped to the Blender world position of the nearest imported vertex (the tool matches to 1e-5 m;
the import moves vertices by up to 1.3e-5 m). Usage: blender -b -P build_lods.py -- <lod0.glb> <out.glb>"""
import os, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / 'tools')); sys.path.insert(0, str(HERE))
from build_actor_lods import generate  # noqa: E402
import glbpack as G, bglbio  # noqa: E402
src, dst = sys.argv[sys.argv.index('--') + 1:][:2]
SOLE = float(os.environ.get('SOLE', '0.006')); TOP = float(os.environ.get('TOP', '0.004')); LIE = float(os.environ.get('LIE', '0.01'))
d, b = G.read(src)
node = next(n for n in d['nodes'] if n.get('name') == 'Fre' and 'mesh' in n)
prs = bglbio.prims(d, bytes(b), node['mesh']); pr = {p['material']: p for p in prs}
body = pr['Fre']['POSITION'].astype(np.float64)
allp = np.vstack([p['POSITION'] for p in prs]).astype(np.float64)
keep = [body[body[:, 1] < body[:, 1].min() + SOLE], allp[allp[:, 1] > allp[:, 1].max() - TOP]]
print('PROTECTED by rule', [len(k) for k in keep])
sys.path.insert(0, str(HERE.parents[1] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
m = Model(Glb(src))
for clip in ('Death', 'Dead'):
    t = m.clip_times(clip)[-1]
    for k, (posed, _) in enumerate(m.skinned_positions(m.world(m.sample(clip, t)))[:3]):
        rest = prs[k]['POSITION'].astype(np.float64)
        keep.append(rest[posed[:, 1] < posed[:, 1].min() + LIE])
print('PROTECTED corpse', [len(k) for k in keep[-6:]])
pts = np.unique(np.vstack(keep).astype(np.float32), axis=0)
# the tool refuses a point shared by coincident vertices with other skin weights (F1's split seams): leave those out
VP = np.vstack([p['POSITION'] for p in prs]).astype(np.float64)
VW = np.vstack([np.c_[p['JOINTS_0'].astype(np.float64), np.round(p['WEIGHTS_0'].astype(np.float64), 4)] for p in prs])
near = [np.flatnonzero(np.linalg.norm(VP - q, axis=1) < 2e-5) for q in pts.astype(np.float64)]   # Blender's Python has no scipy
ok = np.array([len({tuple(r) for r in VW[n]}) == 1 for n in near])
print('PROTECTED dropped (coincident with other weights)', int((~ok).sum()))
pts = pts[ok]
import bpy  # noqa: E402
from mathutils.kdtree import KDTree  # noqa: E402
bpy.ops.import_scene.gltf(filepath=str(Path(src).resolve()))
o = bpy.data.objects['Fre']; W = [o.matrix_world @ v.co for v in o.data.vertices]
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
generate(Path(src).resolve(), Path(dst).resolve(), 'Fre', max_influences=4, protected_points=pts)
