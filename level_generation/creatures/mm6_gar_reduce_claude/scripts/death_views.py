"""Death collapse (mid Death) and settled rubble (Dead) renders of a viewer GLB, three-quarter view from above.
Usage: blender -b -P death_views.py -- <glb> <label>"""
import os, sys, math, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
glb, label = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
sc = bpy.context.scene; rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3
sun.rotation_euler = (math.radians(40), 0, math.radians(-25)); sc.collection.objects.link(sun)
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (.35, .35, .38, 1)
sc.view_settings.view_transform = 'Standard'; sc.render.resolution_x = sc.render.resolution_y = 600
sc.render.engine = 'BLENDER_EEVEE'
for name, act, frame, size, height in [('collapse', 'Death', 8, 3.2, 1.2), ('settled', 'Dead', 0, 2.4, 0.1)]:
    rig.animation_data.action = bpy.data.actions[act]; sc.frame_set(frame)
    c = Vector((0, 0, height))
    dv = Vector((.6, -.6, .5)).normalized()
    cam.location = c + dv * 6; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.ortho_scale = size
    sc.render.filepath = os.path.join(HERE, 'review/close', f'{label}_{name}.png'); bpy.ops.render.render(write_still=True)
