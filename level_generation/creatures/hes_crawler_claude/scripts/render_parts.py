"""Orthographic workbench renders of a GLB (or the master blend's mesh) with each connected part in its own colour
and a 5 cm grid. Args: -- <glb> <out prefix> [labels.npy]. Forward is whatever the file has (Meshy: +Z glTF)."""
import bpy, bmesh, os, sys, colorsys
import numpy as np
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]
src, prefix = a[0], a[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, src))
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
mesh = meshes[0]
zmin = min((mesh.matrix_world @ v.co).z for v in mesh.data.vertices)
mesh.location.z -= zmin
bpy.context.view_layer.update()
bm = bmesh.new(); bm.from_mesh(mesh.data); bm.verts.ensure_lookup_table()
label = -np.ones(len(bm.verts), int); k = 0
for v in bm.verts:
    if label[v.index] >= 0: continue
    st = [v]; label[v.index] = k
    while st:
        x = st.pop()
        for e in x.link_edges:
            w = e.other_vert(x)
            if label[w.index] < 0: label[w.index] = k; st.append(w)
    k += 1
mesh.data.materials.clear()
for i in range(k):
    m = bpy.data.materials.new(f'p{i}'); h = (i * 0.618) % 1
    m.diffuse_color = (*colorsys.hsv_to_rgb(h, 0.55, 0.9), 1); mesh.data.materials.append(m)
for p in mesh.data.polygons:
    p.material_index = int(label[p.vertices[0]])
co = np.array([tuple(mesh.matrix_world @ v.co) for v in mesh.data.vertices])
lo, hi = co.min(0), co.max(0); c = (lo + hi) / 2; ext = float((hi - lo).max()) * 1.15
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_cavity = True
sh.background_type = 'VIEWPORT'; sh.background_color = (0.85, 0.85, 0.83)
sc.render.resolution_x, sc.render.resolution_y = 900, 700
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = ext
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
VIEWS = {'front': (0, -1, 0), 'back': (0, 1, 0), 'left': (1, 0, 0), 'right': (-1, 0, 0), 'top': (0, 0, 1),
         'bottom': (0, 0, -1), 'quarter': (0.7, -0.7, 0.45)}
if len(a) > 2 and a[2] != 'all':
    VIEWS = {v: VIEWS[v] for v in a[2].split(',')}
if len(a) > 3:
    c = np.array([float(x) for x in a[3].split(',')]); ext = float(a[4]); cd.ortho_scale = ext
for name, d in VIEWS.items():
    d = Vector(d).normalized(); loc = Vector(c) + d * 5
    up = 'Y' if abs(d.z) < 0.9 else 'Y'
    fwd = -d; upw = Vector((0, 1, 0)) if abs(fwd.z) > 0.95 else Vector((0, 0, 1))
    right = fwd.cross(upw).normalized(); up = right.cross(fwd)
    R = Matrix((right, up, -fwd)).transposed().to_4x4()
    cam.matrix_world = Matrix.Translation(loc) @ R
    sc.render.filepath = os.path.join(HERE, f'{prefix}_{name}.png')
    bpy.ops.render.render(write_still=True)
print('PARTS', k, 'BBOX', lo.round(3), hi.round(3))
