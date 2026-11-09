"""PeasantF2 LODs: tools/build_actor_lods.py (default ratios 0.5 / 0.18 / 0.06, 4 influences, as build_runtime.sh built the
model) with protected points (MM8 batch lesson; mm9_lesserdemon_reduce_claude/scripts/build_lods.py, with its snap): the floor
contact (shoe vertices within SOLE m of the rest floor), the top (hair cap within TOP of the highest point), the braid tip
(braid vertices within 1 cm of its lowest end) and the corpse contact (posed within LIE of the lowest point at the end of
Death and in Dead). Blender's import moves vertices by up to ~1.3e-5 m and the tool matches to 1e-5 m, so every point is
replaced by the nearest imported vertex's world position (within 1e-4) first.
Usage: blender -b -P build_lods.py -- <lod0.glb> <out.glb>"""
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
NODE = 'PeasantF2'
node = next(n for n in d['nodes'] if n.get('name') == NODE and 'mesh' in n)
prs = bglbio.prims(d, bytes(b), node['mesh']); pr = {p['material']: p for p in prs}
body = pr['PeasantF2_A']['POSITION'].astype(np.float64); head = pr['PeasantF2Head']['POSITION'].astype(np.float64)
allp = np.vstack([body, head])
keep = [body[body[:, 1] < body[:, 1].min() + SOLE], allp[allp[:, 1] > allp[:, 1].max() - TOP]]
# braid tip: head vertices behind the neck (z < -0.1 in glTF: the braid hangs down the back) within 1 cm of the lowest one
br = head[head[:, 2] < head[:, 2].min() + 0.06]
keep.append(br[br[:, 1] < br[:, 1].min() + 0.01])
print('PROTECTED by rule', [len(k) for k in keep])
sys.path.insert(0, str(HERE.parents[1] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
m = Model(Glb(src))
for clip in ('Death', 'Dead'):
    t = m.clip_times(clip)[-1]
    sk = m.skinned_positions(m.world(m.sample(clip, t)))[:2]
    low = min(p[:, 1].min() for p, _ in sk)
    for k, (posed, _) in enumerate(sk):
        keep.append(prs[k]['POSITION'].astype(np.float64)[posed[:, 1] < low + LIE])
print('PROTECTED corpse', [len(k) for k in keep[-4:]])
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
print('PROTECTED mapped', len(mapped), 'of', len(pts))
pts = list({tuple(round(c, 7) for c in p): p for p in mapped}.values())
bpy.ops.wm.read_factory_settings(use_empty=True)
generate(Path(src).resolve(), Path(dst).resolve(), NODE, ratios=(0.5, 0.18, 0.06), max_influences=4, protected_points=pts)
