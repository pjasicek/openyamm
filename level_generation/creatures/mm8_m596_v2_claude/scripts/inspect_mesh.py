"""Clay renders (front, three-quarter, side, back) and stats of one GLB mesh, flat and smooth shading.
Usage: blender -b -P inspect_mesh.py -- <glb rel. to project> <label>  -> review/inspect/<label>_*.png"""
import math, os, sys, bpy
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]; glb, label = a[0], a[1]
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(P, 'review', 'inspect'); os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=os.path.join(P, glb))
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
dg = bpy.context.evaluated_depsgraph_get()
pts = [o.matrix_world @ v.co for o in meshes for v in o.evaluated_get(dg).data.vertices]
lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
print('STATS', label, 'objects', len(meshes), 'tris', sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in meshes),
      'verts', len(pts), 'bounds', tuple(round(x, 3) for x in lo), tuple(round(x, 3) for x in hi))
mat = bpy.data.materials.new('clay'); mat.use_nodes = True
mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.75, .62, .68, 1)
mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = .45
for o in meshes:
    o.data.materials.clear(); o.data.materials.append(mat)
    for poly in o.data.polygons:
        poly.use_smooth = False
sc = bpy.context.scene; sc.render.engine = 'BLENDER_EEVEE'; sc.render.resolution_x = 640; sc.render.resolution_y = 800
sc.view_settings.view_transform = 'Standard'
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (.3, .31, .34, 1)
for ang, en in ((50, 3.0), (200, 1.2)):
    s = bpy.data.objects.new('S', bpy.data.lights.new('S', 'SUN')); s.data.energy = en; sc.collection.objects.link(s)
    s.rotation_euler = (math.radians(50), 0, math.radians(ang))
cam = bpy.data.objects.new('C', bpy.data.cameras.new('C')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; c = (lo + hi) / 2; size = max(hi - lo); cam.data.ortho_scale = size * 1.1
views = {'front': (0, -1, 0), 'quarter': (.7, -.7, .15), 'side': (1, 0, 0), 'back': (0, 1, 0)}
for name, d in views.items():
    d = Vector(d).normalized(); cam.location = c + d * size * 3
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(out, f'{label}_{name}.png'); bpy.ops.render.render(write_still=True)
