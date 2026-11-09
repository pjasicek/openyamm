"""Import the Meshy mallet, report size and topology, render it from 4 sides (third pass). Args: <glb> <out prefix>"""
import bpy, sys, numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=a[0])
obs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
for o in obs:
    V = np.array([o.matrix_world @ v.co for v in o.data.vertices]); print('INSPECT', o.name, 'verts', len(V), 'faces', len(o.data.polygons), 'tris', sum(len(p.vertices) - 2 for p in o.data.polygons), 'bbox', V.min(0).round(3), V.max(0).round(3))
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.show_cavity = True; sh.color_type = 'SINGLE'
sc.render.resolution_x, sc.render.resolution_y = 600, 900
V = np.concatenate([np.array([o.matrix_world @ v.co for v in o.data.vertices]) for o in obs]); c = Vector((V.min(0) + V.max(0)) / 2); ext = float((V.max(0) - V.min(0)).max())
cam = bpy.data.objects.new('c', bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.type = 'ORTHO'; cam.data.ortho_scale = ext * 1.1
for n, d in {'x': (1, 0, 0), 'y': (0, 1, 0), 'z': (0, 0, 1), 'q': (1, 1, 0.5)}.items():
    d = Vector(d).normalized(); cam.location = c + d * 10; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[1]}_{n}.png'; bpy.ops.render.render(write_still=True)
