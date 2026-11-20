"""tools/build_actor_lods.py (its default ratios 0.5 / 0.18 / 0.06 and 4 influences, as build_runtime_v2.sh built the Honk) with
protected points: the floor contact (body vertices within SOLE m of the rest floor), the top of the goose hat (within TOP of
the highest point), the beak tip (goose vertices within BEAK m of the farthest forward point above 1.84 m) and the floor
contact of the fall and the corpse (posed within LIE of the lowest point every 0.1 s of Death, Death2, Dead and Dead2). Each point is snapped to the
Blender world position of the nearest imported vertex first (the Lesser Demon trap: build_actor_lods.py matches to 1e-5 m and
Blender's import moves vertices by ~1.3e-5 m, so plain points protected nothing).
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
BEAK = float(os.environ.get('BEAK', '0.004'))
d, b = G.read(src)
node = next(n for n in d['nodes'] if n.get('name') == 'HonkF' and 'mesh' in n)
prs = bglbio.prims(d, bytes(b), node['mesh']); pr = {p['material']: p for p in prs}
body = pr['HonkF_A']['POSITION'].astype(np.float64); head = pr['HonkFHead']['POSITION'].astype(np.float64)
allp = np.vstack([body, head])
keep = [body[body[:, 1] < body[:, 1].min() + SOLE], allp[allp[:, 1] > allp[:, 1].max() - TOP]]
goose = head[head[:, 1] > 1.84]
keep.append(goose[goose[:, 2] > goose[:, 2].max() - BEAK])
print('PROTECTED by rule', [len(k) for k in keep])
sys.path.insert(0, str(HERE.parents[1] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
m = Model(Glb(src))
for clip in ('Death', 'Death2', 'Dead', 'Dead2'):
    t1 = m.clip_times(clip)[-1]
    # every 0.1 s of the clip, not only its last frame: h70's first LOD3 sank to -3.65 cm in the fall (LOD0 -2.43)
    for t in np.append(np.arange(0, t1, 0.1), t1):
        sk = m.skinned_positions(m.world(m.sample(clip, float(t))))[:2]
        low = min(p[:, 1].min() for p, _ in sk)
        for k, (posed, _) in enumerate(sk):
            rest = prs[k]['POSITION'].astype(np.float64)
            keep.append(rest[posed[:, 1] < low + LIE])
print('PROTECTED corpse and fall', sum(len(k) for k in keep[3:]))
pts = np.unique(np.vstack(keep).astype(np.float32), axis=0)
import bpy  # noqa: E402
from mathutils.kdtree import KDTree  # noqa: E402
bpy.ops.import_scene.gltf(filepath=str(Path(src).resolve()))
o = bpy.data.objects['HonkF']; W = [o.matrix_world @ v.co for v in o.data.vertices]
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
generate(Path(src).resolve(), Path(dst).resolve(), 'HonkF', max_influences=4, protected_points=pts)
