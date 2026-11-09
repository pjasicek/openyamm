"""Render a GLB's mesh with faces touching an open boundary in red (per component colours). Args: glb outdir"""
import bpy, bmesh, sys, os
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=a[0])
ob = next(o for o in bpy.data.objects if o.type == 'MESH')
bm = bmesh.new(); bm.from_mesh(ob.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
mats = []
for c in [(0.75, 0.75, 0.75, 1), (1, 0.1, 0.1, 1)]:
    m = bpy.data.materials.new('m'); m.diffuse_color = c; mats.append(m)
ob.data.materials.clear(); [ob.data.materials.append(m) for m in mats]
for f in bm.faces:
    f.material_index = 1 if any(e.is_boundary for e in f.edges) else 0
bm.to_mesh(ob.data)
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.color_type = 'MATERIAL'; sc.display.shading.show_backface_culling = False
sc.render.resolution_x = sc.render.resolution_y = 500
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = 1.2
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
os.makedirs(a[1], exist_ok=True)
for v, d in {'left': (1, 0, 0), 'front': (0, -1, 0), 'below': (0, -0.3, -1), 'q34': (-1, -1.2, 0.5)}.items():
    d = Vector(d).normalized(); cam.location = d * 5
    cam.rotation_euler = (-cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(a[1], f'holes_{v}.png'); bpy.ops.render.render(write_still=True)
