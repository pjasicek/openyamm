"""Copy the wing weights (piece 3 membrane, piece 4 wing bones) from a fresh build_wings_v2.py output onto a later
stage of the same mesh (2026-10-30 rework). The first wing build had no vertex groups for the wing bones, so most wing
vertices were left unweighted; the wing geometry is not touched by the later steps (reduce, head split, UVs, mirrored
arm head), so its vertices match the fresh build by position and only their weights are replaced, keeping the UVs
the retextures were painted on. Args: <fresh wings blend> <target blend> <out blend>"""
import bpy, sys
import numpy as np
from mathutils.kdtree import KDTree
a = sys.argv[sys.argv.index('--') + 1:]
SRC, DST, OUT = a
bpy.ops.wm.open_mainfile(filepath=DST)
with bpy.data.libraries.load(SRC) as (src, dst):
    dst.objects = ['Body']
fresh = dst.objects[0]
body = next(o for o in bpy.data.objects if o.type == 'MESH' and o.name == 'Body')
fm, tm = fresh.data, body.data
fp = np.zeros(len(fm.vertices), np.int32); fm.attributes['piece'].data.foreach_get('value', fp)
tp = np.zeros(len(tm.vertices), np.int32); tm.attributes['piece'].data.foreach_get('value', tp)
fw = [v for v in fm.vertices if fp[v.index] in (3, 4)]
kd = KDTree(len(fw))
for k, v in enumerate(fw):
    kd.insert(v.co, k)
kd.balance()
names = [g.name for g in fresh.vertex_groups]
for n in names:
    if n not in body.vertex_groups:
        body.vertex_groups.new(name=n)
tgt = [v for v in tm.vertices if tp[v.index] in (3, 4)]
worst, done = 0.0, 0
for v in tgt:
    co, k, d = kd.find(v.co)
    worst = max(worst, d)
    for g in list(v.groups):
        body.vertex_groups[g.group].remove([v.index])
    for g in fw[k].groups:
        body.vertex_groups[names[g.group]].add([v.index], g.weight, 'REPLACE')
    done += 1
unweighted = sum(1 for v in tgt if not v.groups)
bpy.data.objects.remove(fresh)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('WINGWEIGHTS', done, 'vertices, worst position match', round(worst, 6), 'm, unweighted after', unweighted)
