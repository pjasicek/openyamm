"""Close-up of an axe GLB's grip band (work/grip_blender.npy), textured and clay: review/props/grip_<label>[_clay].png.
Usage: blender -b -P grip_close.py -- <glb> <label>"""
import os, sys, math, bpy, numpy as np
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
glb, label = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
for o in bpy.data.objects:
    if o.type == 'MESH' and 'LOD' in o.name: o.hide_render = True
g = Vector(np.load(os.path.join(HERE, 'work', 'grip_blender.npy')).tolist())
sc = bpy.context.scene; sc.render.resolution_x = sc.render.resolution_y = 500
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 0.16
cam.location = g + Vector((0.4, -0.4, 0.05)); cam.rotation_euler = (g - cam.location).to_track_quat('-Z', 'Z').to_euler()
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sc.collection.objects.link(sun); sun.data.energy = 3
sun.rotation_euler = (math.radians(50), 0, math.radians(30))
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
for engine, suf in (('BLENDER_EEVEE', ''), ('BLENDER_WORKBENCH', '_clay')):
    sc.render.engine = engine
    if suf:
        sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.show_cavity = True
    sc.render.filepath = os.path.join(HERE, 'review', 'props', f'grip_{label}{suf}.png'); bpy.ops.render.render(write_still=True)
print('GRIP', label)
