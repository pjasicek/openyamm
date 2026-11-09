"""Deformation-aware reduction of the 20k sea serpent (as mm6_cob_claude): the mesh is decimated while posed in a tight
S wave (every ring curved), each vertex's rest position carried as an interpolated point attribute and restored after.
Rest-pose decimation removes the rings of the straight column, and the slivers fold when the body bends. Edges folded
more than SHARP_DEG (spike and claw tips, teeth, crest) keep full density; protecting the whole head kept a third of
the mesh (teeth, claws, crown) at full density and floored the result at 13.8k.
Run on work/rig_20k.blend (rig_seas.py on hd_base):
  blender --background work/rig_20k.blend --python scripts/reduce_bent.py -- <target triangles> <out.blend>"""
import bpy, bmesh, math, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_seas as A

args = sys.argv[sys.argv.index('--') + 1:]
TARGET, OUT = int(args[0]), args[1]
SHARP_DEG = 90.0
mesh = bpy.data.objects['Seas']
rest = np.array([tuple(v.co) for v in mesh.data.vertices])
# bent pose: a tight side-to-side S wave up the column with a forward bend, so every ring is curved
P = A.curve(pitch=A.profile(0.5), side=A.wave(0.5, 0.0, 0.45, 0.3))
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
keep.add([int(i) for i in np.nonzero(sharp > SHARP_DEG)[0]], 1.0, 'REPLACE')
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
for o in (mesh, bpy.data.objects['Seas_Rig']):
    bpy.data.objects.remove(o, do_unlink=True)
work.name = me.name = 'Seas'
for p in me.polygons:
    p.use_smooth = True
print('REDUCED_BENT triangles', sum(len(p.vertices) - 2 for p in me.polygons), 'vertices', len(me.vertices))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
