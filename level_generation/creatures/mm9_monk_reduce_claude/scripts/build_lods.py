"""tools/build_actor_lods.py (its default ratios and 4 influences, as the Monk was built: ../mm9_monk_claude/scripts/rebuild.sh)
with protected points (Lesser Demon copy, snap fix): the floor contact (vertices within SOLE m of the rest floor), the hood tip
(within TOP of the highest point) and the corpse contact (posed within LIE of the floor at the end of Death and Death2 and in Dead).
Blender's glTF import moves vertices by up to ~1.3e-5 m and the tool matches points to 1e-5 m, so each point is replaced by
the Blender world position of the imported vertex nearest to it (within 1e-4) before generate().
Usage: blender -b -P build_lods.py -- <lod0.glb> <out.glb>"""
import os, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / 'tools')); sys.path.insert(0, str(HERE))
from build_actor_lods import generate  # noqa: E402
import glbpack as G, bglbio  # noqa: E402
src, dst = sys.argv[sys.argv.index('--') + 1:][:2]
NODE = 'Monk'
SOLE = float(os.environ.get('SOLE', '0.006')); TOP = float(os.environ.get('TOP', '0.004')); LIE = float(os.environ.get('LIE', '0.01'))
d, b = G.read(src)
node = next(n for n in d['nodes'] if n.get('name') == NODE and 'mesh' in n)
prs = bglbio.prims(d, bytes(b), node['mesh'])
allp = np.vstack([p['POSITION'].astype(np.float64) for p in prs])
keep = [allp[allp[:, 1] < allp[:, 1].min() + SOLE], allp[allp[:, 1] > allp[:, 1].max() - TOP]]
print('PROTECTED by rule (soles, hood tip)', [len(k) for k in keep])
sys.path.insert(0, str(HERE.parents[1] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
m = Model(Glb(src))
for clip in ('Death', 'Death2', 'Dead'):
    t = m.clip_times(clip)[-1]
    posed = [p for p, _ in m.skinned_positions(m.world(m.sample(clip, t)))[:len(prs)]]
    low = min(float(p[:, 1].min()) for p in posed)
    for k, p in enumerate(posed):
        rest = prs[k]['POSITION'].astype(np.float64)
        keep.append(rest[p[:, 1] < low + LIE])
print('PROTECTED corpse', [len(k) for k in keep[2:]])
pts = np.unique(np.vstack(keep).astype(np.float32), axis=0)
import bpy  # noqa: E402
from mathutils.kdtree import KDTree  # noqa: E402
bpy.ops.import_scene.gltf(filepath=str(Path(src).resolve()))
o = bpy.data.objects[NODE]; W = [o.matrix_world @ v.co for v in o.data.vertices]
kd = KDTree(len(W)); [kd.insert(w, i) for i, w in enumerate(W)]; kd.balance()
mapped = []
for x, y, z in pts:
    co, i, dist = kd.find((float(x), float(-z), float(y)))
    if dist < 1e-4:
        mapped.append(tuple(co))
print('SNAP protected mapped', len(mapped), 'of', len(pts))
pts = list({tuple(round(c, 7) for c in p): p for p in mapped}.values())
bpy.ops.wm.read_factory_settings(use_empty=True)
print('PROTECTED points', len(pts))
generate(Path(src).resolve(), Path(dst).resolve(), NODE, max_influences=4, protected_points=pts)
