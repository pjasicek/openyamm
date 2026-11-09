"""Meshy v3 return -> work/body.blend: one mesh 'Glassback', forward -Y (rotated +90 deg about Z), the body widened
x1.12 (the concept's broad barrel), scaled so the back stands 1.2 m (tier A shoulder, design brief), grounded, centred
in x; specks under 10 vertices deleted (the two eyeballs stay as their own pieces)."""
import bpy, os, sys, math
import bmesh
from mathutils import Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
WIDEN, HEIGHT = 1.12, 1.2
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=C.path('meshy/body_geometry_v3/model_urls_glb.glb'))
mesh = next(o for o in bpy.data.objects if o.type == 'MESH')
for o in list(bpy.data.objects):
    if o is not mesh:
        bpy.data.objects.remove(o, do_unlink=True)
mesh.parent = None
mesh.matrix_world = Matrix.Rotation(math.radians(90), 4, 'Z') @ mesh.matrix_world
bpy.context.view_layer.objects.active = mesh
mesh.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
me = mesh.data
xs = [v.co.x for v in me.vertices]; zs = [v.co.z for v in me.vertices]
cx = (max(xs) + min(xs)) / 2; z0 = min(zs); s = HEIGHT / (max(zs) - z0)
for v in me.vertices:
    v.co.x = (v.co.x - cx) * WIDEN * s
    v.co.y *= s
    v.co.z = (v.co.z - z0) * s
bm = bmesh.new(); bm.from_mesh(me)
islands = []
seen = set()
for v in bm.verts:
    if v in seen:
        continue
    stack = [v]; isl = []; seen.add(v)
    while stack:
        a = stack.pop(); isl.append(a)
        for e in a.link_edges:
            b = e.other_vert(a)
            if b not in seen:
                seen.add(b); stack.append(b)
    islands.append(isl)
kill = [v for isl in islands if len(isl) < 10 for v in isl]
bmesh.ops.delete(bm, geom=kill, context='VERTS')
bm.to_mesh(me); bm.free()
mesh.name = me.name = C.MESH
for p in me.polygons:
    p.use_smooth = True
me.materials.clear()
print('PREP verts', len(me.vertices), 'tris', sum(len(p.vertices) - 2 for p in me.polygons), 'deleted', len(kill))
bpy.ops.wm.save_as_mainfile(filepath=C.path('work/body.blend'))
