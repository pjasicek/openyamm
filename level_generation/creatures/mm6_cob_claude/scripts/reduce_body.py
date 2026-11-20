"""Reduce the HD body (work/hd_base.blend, Meshy's even 20k remesh) before rigging: collapse decimation that keeps
sharp features at full density (vertices on edges folded more than SHARP_DEG: wing outline and struts, claws, horns,
spikes) and thins the smooth skin and membrane. UVs survive collapse decimation, so the Meshy textures still fit. (Decimate collapses only the vertex group;
inverted, the group is what it keeps.)
Cobra: the head (z above HEAD_Z, 1 m tall rig frame) is kept at full density too: fangs, eyes, head plates.
Usage: blender --background work/hd_base.blend --python scripts/reduce_body.py -- <target triangles> [out.blend]
Default output work/hd_reduced.blend; run on work/hd_base.blend from prepare_cob.py."""
import bpy, bmesh, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHARP_DEG = 60.0
HEAD_Z = 0.74
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
TARGET = int(args[0]) if args else 11000
OUT = args[1] if len(args) > 1 else os.path.join(HERE, 'work', 'hd_reduced.blend')

o = bpy.data.objects['Cobra']; me = o.data
bm = bmesh.new(); bm.from_mesh(me)
sharp = np.zeros(len(bm.verts))
for e in bm.edges:
    if len(e.link_faces) == 2:
        angle = math.degrees(e.calc_face_angle())
        for v in e.verts:
            sharp[v.index] = max(sharp[v.index], angle)
bm.free()
keep = o.vertex_groups.new(name='keep')
co = np.array([tuple(v.co) for v in me.vertices])
keep.add([int(i) for i in np.nonzero((sharp > SHARP_DEG) | (co[:, 2] > HEAD_Z))[0]], 1.0, 'REPLACE')


def triangles(ratio):
    m = o.modifiers.new('reduce', 'DECIMATE'); m.ratio = ratio; m.vertex_group = 'keep'; m.invert_vertex_group = True
    m.use_collapse_triangulate = True
    ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); e = ev.to_mesh()
    n = sum(len(p.vertices) - 2 for p in e.polygons)
    ev.to_mesh_clear(); o.modifiers.remove(m)
    return n


lo, hi = 0.05, 1.0
for _ in range(14):
    mid = (lo + hi) / 2
    if triangles(mid) > TARGET:
        hi = mid
    else:
        lo = mid
m = o.modifiers.new('reduce', 'DECIMATE'); m.ratio = lo; m.vertex_group = 'keep'; m.invert_vertex_group = True
m.use_collapse_triangulate = True
bpy.context.view_layer.objects.active = o
bpy.ops.object.modifier_apply(modifier=m.name)
o.vertex_groups.remove(o.vertex_groups['keep'])
print('REDUCED ratio', round(lo, 4), 'triangles', sum(len(p.vertices) - 2 for p in me.polygons), 'vertices', len(me.vertices))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
