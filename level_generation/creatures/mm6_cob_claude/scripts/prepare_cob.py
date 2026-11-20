"""Import the four-view Meshy cobra (meshy/hd_multiview_v1), weld UV-seam splits (one closed mesh; UVs stay per
corner), drop stray pieces smaller than 1% of the mesh, and move it into the rig frame: raised head height 1.0 m, ground
at z 0, the raised neck at the origin, head facing -Y, the ground body extending toward +Y. Saves work/hd_base.blend
(object 'Cobra') and copies the Meshy textures to textures/hd_*.png.
The direction is detected: the end of the long horizontal axis whose vertices reach highest is the head end."""
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
ext = co.max(0) - co.min(0)
# glTF import is Z-up after conversion; the long axis is the larger of X/Y
long_axis = 0 if ext[0] >= ext[1] else 1
lo, hi = co[:, long_axis].min(), co[:, long_axis].max()
near_lo = co[co[:, long_axis] < lo + 0.15 * (hi - lo)]
near_hi = co[co[:, long_axis] > hi - 0.15 * (hi - lo)]
head_at_hi = near_hi[:, 2].max() > near_lo[:, 2].max()
# rotate so the long axis is Y and the head end is at -Y
angle = {(0, True): -math.pi / 2, (0, False): math.pi / 2, (1, True): math.pi, (1, False): 0.0}[(long_axis, head_at_hi)]
mesh.matrix_world = Matrix.Rotation(angle, 4, 'Z') @ mesh.matrix_world
bpy.ops.object.transform_apply(rotation=True)
co = np.array([tuple(v.co) for v in mesh.data.vertices])
s = 1.0 / (co[:, 2].max() - co[:, 2].min())
mesh.scale = (s, s, s); bpy.ops.object.transform_apply(scale=True)
co = np.array([tuple(v.co) for v in mesh.data.vertices])
raised = co[co[:, 2] > co[:, 2].min() + 0.6]
mesh.location = (-raised[:, 0].mean(), -raised[:, 1].mean(), -co[:, 2].min())
bpy.ops.object.transform_apply(location=True)
mesh.name = mesh.data.name = 'Cobra'
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
