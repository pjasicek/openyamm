"""tools/build_actor_lods.py (its default ratios and 4 influences, as the Clan Soldier was built: rebuild.sh) with protected points
(after mm9_lesserdemon_reduce_claude/scripts/build_lods.py, the snap fix): the floor contact (vertices within SOLE m of the rest
floor), the helmet top (within TOP of the highest point) and, with CORPSE=1, the corpse contact (posed within LIE of the lowest point at
the end of Death and in Dead). Every point is snapped to the Blender world position of the nearest imported vertex (the tool matches to 1e-5 m;
the import moves vertices by ~1.3e-5 m). Usage: blender -b -P build_lods.py -- <lod0.glb> <out.glb>"""
import os, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / 'tools')); sys.path.insert(0, str(HERE))
from build_actor_lods import generate  # noqa: E402
import glbpack as G, bglbio  # noqa: E402
src, dst = sys.argv[sys.argv.index('--') + 1:][:2]
NODE = 'ClanSoldier'
SOLE = float(os.environ.get('SOLE', '0.006')); TOP = float(os.environ.get('TOP', '0.004')); LIE = float(os.environ.get('LIE', '0.01'))
SEAMX = float(os.environ.get('SEAMX', '-1'))
d, b = G.read(src)
node = next(n for n in d['nodes'] if n.get('name') == NODE and 'mesh' in n)
prs = bglbio.prims(d, bytes(b), node['mesh'])
allp = np.vstack([p['POSITION'].astype(np.float64) for p in prs])
keep = [allp[allp[:, 1] < allp[:, 1].min() + SOLE], allp[allp[:, 1] > allp[:, 1].max() - TOP]]
print('PROTECTED by rule soles', len(keep[0]), 'top', len(keep[1]))
sys.path.insert(0, str(HERE.parents[1] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
m = Model(Glb(src))
# corpse contact (CORPSE=1, default): the Dead contact is the pants' back centre seam, whose sliver face (installed LOD0: 3 mm2 at
# rest, 299 mm2 in Death) these points carry into LOD1-3 (634 mm2 in Death). Excluding the seam (SEAMX=0.005) left no corpse point
# and LOD1-3 lay 1.5 cm above the floor in Dead, so the seam is protected (SEAMX=-1: no exclusion) and the sliver is reported
for clip in (('Death', 'Dead') if os.environ.get('CORPSE', '1') == '1' else ()):
    t = m.clip_times(clip)[-1]
    sp = m.skinned_positions(m.world(m.sample(clip, t)))[:len(prs)]
    low = min(posed[:, 1].min() for posed, _ in sp)
    for k, (posed, _) in enumerate(sp):
        rp = prs[k]['POSITION'].astype(np.float64)
        keep.append(rp[(posed[:, 1] < low + LIE) & (np.abs(rp[:, 0]) > SEAMX)])   # not on the centre seam (sliver, see above)
print('PROTECTED corpse', sum(len(k) for k in keep[2:]))
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
print('SNAP mapped', len(mapped), 'of', len(pts))
pts = list({tuple(round(c, 7) for c in p): p for p in mapped}.values())
bpy.ops.wm.read_factory_settings(use_empty=True)
print('PROTECTED points', len(pts))
generate(Path(src).resolve(), Path(dst).resolve(), NODE, max_influences=4, protected_points=pts)
