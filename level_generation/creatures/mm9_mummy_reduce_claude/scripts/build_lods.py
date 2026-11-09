"""tools/build_actor_lods.py (its default ratios and 4 influences, as the Mummy was built: ../mm9_mummy_claude/scripts/rebuild.sh)
with protected points (MM8 batch lesson), from the Lesser Demon's copy: the floor contact (vertices within SOLE m of the rest
floor), the top (head-set vertices within TOP of the highest point) and the corpse contact (posed within LIE of the floor at the
end of Death, Death2 and in Dead, Dead2). Each point is snapped to the nearest vertex of Blender's import first: the tool matches
points to 1e-5 m and the import moves vertices by ~1.3e-5 m (Lesser Demon: nothing protected, LOD3 stood 8 cm up).
Env LOD_BODY / LOD_HEAD: per-material LOD1-3 ratios (default the tool's 0.5,0.18,0.06).
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
NODE = 'Mummy'
d, b = G.read(src)
node = next(n for n in d['nodes'] if n.get('name') == NODE and 'mesh' in n)
prs = bglbio.prims(d, bytes(b), node['mesh']); pr = {p['material']: p for p in prs}
body = pr['Mummy']['POSITION'].astype(np.float64); head = pr['MummyHead']['POSITION'].astype(np.float64)
# the floor of the body: the lowest vertex not on the band/strip bones (the band's rest vertices hang lower, -0.17 m)
names = [d['nodes'][j]['name'] for j in d['skins'][0]['joints']]
stripj = np.array([n.startswith('Xband') or n.startswith('Xstrip') for n in names])
pb = pr['Mummy']; onstrip = (pb['WEIGHTS_0'].astype(np.float64) * stripj[pb['JOINTS_0'].astype(int)]).sum(1) > 0
fl = body[~onstrip, 1].min()
keep = [body[(body[:, 1] >= fl - 1e-6) & (body[:, 1] < fl + SOLE)], head[head[:, 1] > head[:, 1].max() - TOP]]
print('PROTECTED by rule', [len(k) for k in keep], 'floor', round(float(fl), 4))
sys.path.insert(0, str(HERE.parents[1] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
m = Model(Glb(src))
for clip in ('Death', 'Dead', 'Death2', 'Dead2'):
    if clip not in m.clips:
        continue
    t = m.clip_times(clip)[-1]
    for k, (posed, _) in enumerate(m.skinned_positions(m.world(m.sample(clip, t)))[:2]):
        rest = prs[k]['POSITION'].astype(np.float64)
        keep.append(rest[posed[:, 1] < posed[:, 1].min() + LIE])
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
print('PROTECTED mapped', len(mapped), 'of', len(pts))
pts = list({tuple(round(c, 7) for c in p): p for p in mapped}.values())
bpy.ops.wm.read_factory_settings(use_empty=True)
print('PROTECTED points', len(pts))
# per-material ratios (LOD_BODY, LOD_HEAD): after the cut the exact face set is half of LOD0, so the default 0.5/0.18/0.06 of the
# whole would leave the body 195 triangles at LOD3 (installed 371) and fold the band strip under the floor in Death (-7 cm)
rb = tuple(float(x) for x in os.environ.get('LOD_BODY', '0.5,0.18,0.06').split(','))
rh = tuple(float(x) for x in os.environ.get('LOD_HEAD', '0.5,0.18,0.06').split(','))
print('LOD ratios body', rb, 'head', rh)
generate(Path(src).resolve(), Path(dst).resolve(), NODE, max_influences=4, protected_points=pts,
         material_ratios={'Mummy': rb, 'MummyHead': rh})
