"""Render work/<name>_tex.blend with the Meshy retexture's base colour (workbench, texture colour, flat studio light):
34, front, left, back, right, top. Args: -- <name> <out prefix>"""
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
name, prefix = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', f'{name}_tex.blend'))
obj = bpy.data.objects[name]
mat = bpy.data.materials.new('tex'); mat.use_nodes = True
tex = mat.node_tree.nodes.new('ShaderNodeTexImage')
tex.image = bpy.data.images.load(os.path.join(HERE, 'meshy', obj.get('retexture', f'{name}_retexture_v1'), 'texture_urls_0_base_color.png'))
mat.node_tree.links.new(tex.outputs['Color'], mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
obj.data.materials.clear(); obj.data.materials.append(mat)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'TEXTURE'
scene.render.resolution_x, scene.render.resolution_y = 700, 700
scene.render.film_transparent = False
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
scene.collection.objects.link(cam); scene.camera = cam
cam.data.type = 'ORTHO'
co = np.array([v.co[:] for v in obj.data.vertices])
lo, hi = Vector(co.min(0)), Vector(co.max(0)); centre = (lo + hi) / 2; size = max(hi - lo)
cam.data.ortho_scale = size * 1.1
for view, (az, el) in {'34': (-35, 15), 'front': (0, 0), 'left': (-90, 0), 'back': (180, 0), 'right': (90, 0),
                       'top': (0, 89)}.items():
    a, e = math.radians(az), math.radians(el)
    d = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
    cam.location = centre + d * size * 3
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = f'{prefix}_{view}.png'
    bpy.ops.render.render(write_still=True)
