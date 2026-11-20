"""Deformation-aware reduction of the 20k cobra. Collapse decimation in the rest pose removes the ring loops along the
straight body and tail (cheap on a straight tube) and leaves long slivers that fold into a flat blade when the body
bends. Here the mesh is decimated while posed in a tight wave + coil + bent neck (every part curved), with each vertex's
rest position carried as a point attribute that the collapse interpolates; afterwards the rest positions are restored.
Sharp features and the head itself (z > HEAD_Z and y < HEAD_Y: snout, fangs, eyes) keep full density; the hood
flaps are a smooth surface whose scales live in the baked texture and normal map, so they are reduced like the body.
Run on work/rig_v1.blend built from work/hd_base.blend (rig_cob.py):
  blender --background work/rig_v1.blend --python scripts/reduce_bent.py -- <target triangles> <out.blend>"""
import bpy, bmesh, math, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_cob as A

args = sys.argv[sys.argv.index('--') + 1:]
TARGET, OUT = int(args[0]), args[1]
SHARP_DEG, HEAD_Z, HEAD_Y = 60.0, 0.74, -0.06
mesh = bpy.data.objects['Cobra']
rest = np.array([tuple(v.co) for v in mesh.data.vertices])
# bent pose: tight travelling wave on the tail, neck bent sideways and forward
nT = len(A.TAIL); v = np.cumsum(A.L[A.K - 1::-1])
kappa = 6.0 * np.sin(2 * math.pi * v / 0.55)
P = A.curve(neck_pitch=A.profile(0.6), neck_yaw=A.profile(0.5, 1.2), kappa=kappa, tail_heading=0.0)
A.apply(P); bpy.context.view_layer.update()
ev = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get())
posed = bpy.data.meshes.new_from_object(ev)
work = bpy.data.objects.new('Bent', posed); bpy.context.scene.collection.objects.link(work)
att = posed.attributes.new('rest_co', 'FLOAT_VECTOR', 'POINT'); att.data.foreach_set('vector', rest.ravel())
# keep group from the rest geometry (same vertex order)
bm = bmesh.new(); bm.from_mesh(mesh.data); sharp = np.zeros(len(rest))
for e in bm.edges:
    if len(e.link_faces) == 2:
        a = math.degrees(e.calc_face_angle())
        for x in e.verts:
            sharp[x.index] = max(sharp[x.index], a)
bm.free()
for g in list(work.vertex_groups):
    work.vertex_groups.remove(g)
keep = work.vertex_groups.new(name='keep')
head = (rest[:, 2] > HEAD_Z) & (rest[:, 1] < HEAD_Y)          # snout, fangs, eyes; the hood flaps are free
keep.add([int(i) for i in np.nonzero((sharp > SHARP_DEG) | head)[0]], 1.0, 'REPLACE')
for o in bpy.context.view_layer.objects:
    o.select_set(o is work)
bpy.context.view_layer.objects.active = work


def tris(ratio):
    m = work.modifiers.new('r', 'DECIMATE'); m.ratio = ratio; m.vertex_group = 'keep'; m.invert_vertex_group = True
    e = work.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
    n = sum(len(p.vertices) - 2 for p in e.polygons); work.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh_clear()
    work.modifiers.remove(m); return n


lo, hi = 0.05, 1.0
for _ in range(14):
    mid = (lo + hi) / 2
    lo, hi = (mid, hi) if tris(mid) <= TARGET else (lo, mid)
m = work.modifiers.new('r', 'DECIMATE'); m.ratio = lo; m.vertex_group = 'keep'; m.invert_vertex_group = True
bpy.ops.object.modifier_apply(modifier=m.name)
me = work.data
rc = np.zeros(len(me.vertices) * 3); me.attributes['rest_co'].data.foreach_get('vector', rc)
me.vertices.foreach_set('co', rc); me.attributes.remove(me.attributes['rest_co']); me.update()
work.vertex_groups.clear()
for o in (mesh, bpy.data.objects['Cobra_Rig']):
    bpy.data.objects.remove(o, do_unlink=True)
work.name = me.name = 'Cobra'
for p in me.polygons:
    p.use_smooth = True
print('REDUCED_BENT triangles', sum(len(p.vertices) - 2 for p in me.polygons), 'vertices', len(me.vertices))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
