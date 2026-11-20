"""UV check of work/<name>_uv.blend: the layout as a PNG and checker-textured views (stretch, density).
Args: -- <name> <out prefix>"""
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
name, prefix = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', f'{name}_uv.blend'))
obj = bpy.data.objects[name]
for o in bpy.context.scene.objects:
    o.select_set(o is obj)
bpy.context.view_layer.objects.active = obj
import numpy as np
uv = obj.data.uv_layers.active.data
np.save(prefix + '_uvtris.npy', np.array([[uv[li].uv[:] for li in p.loop_indices[:3]] for p in obj.data.polygons]))
img = bpy.data.images.new('checker', 2048, 2048)
img.generated_type = 'UV_GRID'
mat = bpy.data.materials.new('chk')
mat.use_nodes = True
tex = mat.node_tree.nodes.new('ShaderNodeTexImage'); tex.image = img
mat.node_tree.links.new(tex.outputs['Color'], mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
obj.data.materials.clear(); obj.data.materials.append(mat)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'TEXTURE'
scene.render.resolution_x = scene.render.resolution_y = 800
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
scene.collection.objects.link(cam); scene.camera = cam
pts = [Vector(c) for c in obj.bound_box]
lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
centre, size = (lo + hi) / 2, max(hi - lo)
cam.data.type = 'ORTHO'; cam.data.ortho_scale = size * 1.1
for view, (az, el) in {'34': (-35, 15), 'back34': (150, 20)}.items():
    a, e = math.radians(az), math.radians(el)
    d = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
    cam.location = centre + d * size * 3
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = f'{prefix}_chk_{view}.png'
    bpy.ops.render.render(write_still=True)
print('UVCHECK', prefix)
