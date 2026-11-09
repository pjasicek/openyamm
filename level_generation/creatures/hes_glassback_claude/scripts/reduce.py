"""LOD0 reduction (game asset guidelines: silhouette first, flat areas cut): edit-mode collapse decimation per region,
UVs and weights interpolated. The head set (faces with 'head') keeps HEAD_RATIO, the body BODY_RATIO; the faces on the
head/body border are left alone so the neck seam keeps its vertices. Args: -- <in> <out> [body ratio] [head ratio]"""
import bpy, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
a = sys.argv[sys.argv.index('--') + 1:]
src, dst = a[:2]
BODY = float(a[2]) if len(a) > 2 else 0.42
HEAD = float(a[3]) if len(a) > 3 else 0.7
bpy.ops.wm.open_mainfile(filepath=C.path(src))
mesh = bpy.data.objects[C.MESH]; me = mesh.data
before = len(me.polygons)
for o in bpy.data.objects:
    o.select_set(o == mesh)
bpy.context.view_layer.objects.active = mesh


def select(want_head):
    hd = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hd)
    vh = np.zeros(len(me.vertices), np.int32); vb = np.zeros(len(me.vertices), np.int32)
    for p in me.polygons:
        for v in p.vertices:
            (vh if hd[p.index] else vb)[v] = 1
    border = vh & vb
    bpy.ops.object.mode_set(mode='OBJECT')
    for p in me.polygons:
        p.select = bool(hd[p.index]) == want_head and not any(border[v] for v in p.vertices)
    for v in me.vertices:
        v.select = False
    for e in me.edges:
        e.select = False
    for p in me.polygons:
        if p.select:
            for v in p.vertices:
                me.vertices[v].select = True
    bpy.ops.object.mode_set(mode='EDIT')


for want_head, ratio in ((False, BODY), (True, HEAD)):
    select(want_head)
    bpy.ops.mesh.decimate(ratio=ratio)
    bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.quads_convert_to_tris(quad_method='SHORTEST_DIAGONAL', ngon_method='BEAUTY')
bpy.ops.object.mode_set(mode='OBJECT')
hd = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hd)
print('REDUCED faces', before, '->', len(me.polygons), 'head', int(hd.sum()))
bpy.ops.wm.save_as_mainfile(filepath=C.path(dst))
