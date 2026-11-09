"""Import the four-view Meshy sea serpent (meshy/hd_multiview_v1), weld UV-seam splits, drop stray pieces smaller than
1% of the mesh, and move it into the rig frame: 1.0 m tall, the flat bottom (waterline) at z 0 centred on the origin,
the arched head toward -Y. Saves work/hd_base.blend (object 'Seas') and copies the Meshy textures to
textures/hd_*.png."""
import bpy, bmesh, os, shutil, math
import numpy as np
from mathutils import Matrix

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(HERE, 'meshy', 'hd_multiview_v1')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(SRC, 'model_urls_glb.glb'))
mesh = next(o for o in bpy.data.objects if o.type == 'MESH')
for o in list(bpy.data.objects):
    if o is not mesh:
        bpy.data.objects.remove(o, do_unlink=True)
mesh.parent = None
bpy.context.view_layer.objects.active = mesh; mesh.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bm = bmesh.new(); bm.from_mesh(mesh.data)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
# drop tiny loose islands (Meshy specks)
bm.verts.ensure_lookup_table()
seen = set(); islands = []
for v in bm.verts:
    if v.index in seen:
        continue
    stack = [v]; isl = []; seen.add(v.index)
    while stack:
        a = stack.pop(); isl.append(a)
        for e in a.link_edges:
            b = e.other_vert(a)
            if b.index not in seen:
                seen.add(b.index); stack.append(b)
    islands.append(isl)
keep = max(len(i) for i in islands) * 0.01
dropped = [v for isl in islands if len(isl) < keep for v in isl]
bmesh.ops.delete(bm, geom=dropped, context='VERTS')
bm.to_mesh(mesh.data); bm.free()
print('ISLANDS', len(islands), 'dropped verts', len(dropped))

co = np.array([tuple(v.co) for v in mesh.data.vertices])
# glTF import is Z-up after conversion; the head is where the top of the body arches to: rotate it to -Y
zmin, zmax = co[:, 2].min(), co[:, 2].max()
top = co[co[:, 2] > zmax - 0.2 * (zmax - zmin)].mean(0); base = co[co[:, 2] < zmin + 0.1 * (zmax - zmin)].mean(0)
lean = top[:2] - base[:2]
angle = -math.pi / 2 - math.atan2(lean[1], lean[0])      # rotation about Z that maps the lean direction onto -Y
mesh.matrix_world = Matrix.Rotation(angle, 4, 'Z') @ mesh.matrix_world
bpy.ops.object.transform_apply(rotation=True)
co = np.array([tuple(v.co) for v in mesh.data.vertices])
s = 1.0 / (co[:, 2].max() - co[:, 2].min())
mesh.scale = (s, s, s); bpy.ops.object.transform_apply(scale=True)
co = np.array([tuple(v.co) for v in mesh.data.vertices])
base = co[co[:, 2] < co[:, 2].min() + 0.08]
mesh.location = (-(base[:, 0].min() + base[:, 0].max()) / 2, -(base[:, 1].min() + base[:, 1].max()) / 2, -co[:, 2].min())
bpy.ops.object.transform_apply(location=True)
mesh.name = mesh.data.name = 'Seas'
for p in mesh.data.polygons:
    p.use_smooth = True
os.makedirs(os.path.join(HERE, 'textures'), exist_ok=True)
for k in ('base_color', 'normal', 'roughness', 'metallic'):
    f = os.path.join(SRC, f'texture_urls_0_{k}.png')
    if os.path.exists(f):
        shutil.copy(f, os.path.join(HERE, 'textures', f'hd_{k}.png'))
co = np.array([tuple(v.co) for v in mesh.data.vertices])
print('HD BASE verts', len(co), 'tris', sum(len(p.vertices) - 2 for p in mesh.data.polygons), 'bbox', co.min(0).round(3),
      co.max(0).round(3))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'hd_base.blend'))
