"""tools/build_actor_lods.py (its default ratios and 4 influences, as the Lesser Demon was built: rebuild.sh) with protected
points (MM8 batch lesson; Dwarf horn tips): the floor contact (vertices within SOLE m of the rest floor), the top (within TOP of
the highest point: back spikes), the thin tips that set the silhouette (horn tips: head vertices beyond 90 % of the horn span;
talon tips and the tail tip: the vertex of each talon/tail piece farthest from its root), and the corpse contact (posed within
LIE of the floor at the end of Death and in Dead). Usage: blender -b -P build_lods.py -- <lod0.glb> <out.glb>"""
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
node = next(n for n in d['nodes'] if n.get('name') == 'LesserDemon' and 'mesh' in n)
prs = bglbio.prims(d, bytes(b), node['mesh']); pr = {p['material']: p for p in prs}
body = pr['LesserDemon']['POSITION'].astype(np.float64); head = pr['LesserDemonHead']['POSITION'].astype(np.float64)
allp = np.vstack([body, head]); keep = [body[body[:, 1] < body[:, 1].min() + SOLE], allp[allp[:, 1] > allp[:, 1].max() - TOP]]
hx = np.abs(head[:, 0]); keep.append(head[hx > hx.max() - 0.01])   # outer horn curl (within 1 cm of the span)
horn_up = head[(hx > 0.3) & (head[:, 1] > np.percentile(head[hx > 0.3, 1], 95))]; keep.append(horn_up)
# talon and tail tips: farthest vertex of each thin piece from the body centre line, per side
# (talons lie along x in the bind pose: per talon piece, its vertices within 5 mm of its outermost |x|)
Tb = pr['LesserDemon']['T']; _, tp = np.unique(np.round(body, 6), axis=0, return_inverse=True); tp = tp.reshape(-1); TT = tp[Tb]
lab = np.arange(tp.max() + 1)   # connected pieces by label propagation (Blender's Python has no scipy)
while True:
    m_ = np.minimum(np.minimum(lab[TT[:, 0]], lab[TT[:, 1]]), lab[TT[:, 2]]); old = lab.copy()
    for k in range(3): np.minimum.at(lab, TT[:, k], m_)
    lab = lab[lab]
    if (lab == old).all(): break
vl = lab[tp]
for c in np.unique(vl):
    pv = body[vl == c]
    if len(pv) < 300 and np.abs(pv[:, 0]).min() > 1.1:
        keep.append(pv[np.abs(pv[:, 0]) > np.abs(pv[:, 0]).max() - 0.005])
keep.append(body[body[:, 2] < body[:, 2].min() + 0.01])          # tail tip (the arrowhead behind)
print('PROTECTED by rule', [len(k) for k in keep])
sys.path.insert(0, str(HERE.parents[1] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
m = Model(Glb(src))
for clip in ('Death', 'Dead'):
    t = m.clip_times(clip)[-1]
    for k, (posed, _) in enumerate(m.skinned_positions(m.world(m.sample(clip, t)))[:2]):
        rest = prs[k]['POSITION'].astype(np.float64)
        keep.append(rest[posed[:, 1] < posed[:, 1].min() + LIE])
print('PROTECTED corpse', [len(k) for k in keep[-4:]])
pts = np.unique(np.vstack(keep).astype(np.float32), axis=0)
# Blender's glTF import re-bases this skinned mesh under its rig (local z = y - 1.368 through the bind matrices), and its world
# positions differ from the GLB's by up to 1.3e-5 m; the tool matches points to 1e-5 m, so the plain (x, -z, y) points matched
# nothing (the first builds protected nothing: LOD3 stood 8 cm up in Standing). Each point is replaced by the Blender world
# position of the imported vertex nearest to it (within 1e-4), then the import is cleared for generate().
import bpy  # noqa: E402
from mathutils.kdtree import KDTree  # noqa: E402
bpy.ops.import_scene.gltf(filepath=str(Path(src).resolve()))
o = bpy.data.objects['LesserDemon']; W = [o.matrix_world @ v.co for v in o.data.vertices]
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
generate(Path(src).resolve(), Path(dst).resolve(), 'LesserDemon', max_influences=4, protected_points=pts)
