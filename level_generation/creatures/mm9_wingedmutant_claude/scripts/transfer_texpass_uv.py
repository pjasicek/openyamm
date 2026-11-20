"""Carry the texture quality pass UVs (2026-10-30) onto a rebuilt symmetric body: the body/wing UVMap that
retexture_v2 was painted on (uv_texpass.py) and the head HeadUV that resample_head.py carried the head paint into
(head_uv_texpass.py), both in work/uv_texpass2.blend. xatlas packing is not repeatable, so the UVs are copied face by
face (the target is triangulated exactly like the source by texpass_mesh.py; faces matched by centre, loops by
vertex position), as transfer_headuv.py did for the rework.
Args: -- <uv source blend (uv_texpass2)> <target blend (sym_v2 + HeadUV)> <out blend>"""
import bpy, sys, os
import numpy as np
from mathutils.kdtree import KDTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from texpass_mesh import mirror_triangulate, triangulate_head

a = sys.argv[sys.argv.index('--') + 1:]
SRC, TGT, OUT = a
LAYERS = ('UVMap', 'HeadUV')

bpy.ops.wm.open_mainfile(filepath=SRC)
me = bpy.data.objects['Body'].data
src = []
for p in me.polygons:
    co = np.array([tuple(me.vertices[v].co) for v in p.vertices])
    src.append((co, {n: np.array([tuple(me.uv_layers[n].data[li].uv) for li in p.loop_indices]) for n in LAYERS}))
tree = KDTree(len(src))
for i, (co, _) in enumerate(src):
    tree.insert(co.mean(0), i)
tree.balance()

bpy.ops.wm.open_mainfile(filepath=TGT)
body = bpy.data.objects['Body']
me = body.data
mirror_triangulate(me)
triangulate_head(me)
if len(me.polygons) != len(src):
    raise ValueError(f'face count {len(me.polygons)} != source {len(src)}')
for n in LAYERS:
    if n not in me.uv_layers:
        me.uv_layers.new(name=n)
worst_centre = worst_vertex = 0.0
for p in me.polygons:
    co = np.array([tuple(me.vertices[v].co) for v in p.vertices])
    _, j, dist = tree.find(co.mean(0))
    worst_centre = max(worst_centre, dist)
    sco, suv = src[j]
    for k, li in enumerate(p.loop_indices):
        m = int(np.argmin(np.linalg.norm(sco - co[k], axis=1)))
        worst_vertex = max(worst_vertex, float(np.linalg.norm(sco[m] - co[k])))
        for n in LAYERS:
            me.uv_layers[n].data[li].uv = tuple(suv[n][m])
if worst_vertex > 1e-4:
    raise ValueError(f'rebuilt geometry differs from the UV source: worst vertex {worst_vertex}')
me.uv_layers.active = me.uv_layers['UVMap']
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('TEXPASS-TRANSFER faces', len(me.polygons), 'worst centre', worst_centre, 'worst vertex', worst_vertex)
