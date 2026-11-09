"""Front / back / side renders of GLBs at a clip frame. Usage: blender -b -P shots.py -- <label=glb,...> <clip:frame> <out dir>"""
import os, sys, bpy
from mathutils import Vector
args = sys.argv[sys.argv.index('--') + 1:]; out = args[2]; os.makedirs(out, exist_ok=True)
VIEWS = {'front': (0, -1, .1), 'back': (0, 1, .15), 'side': (1, -.25, .1), 'q34': (.7, -.7, .2)}
for item in args[0].split(','):
    label, glb = item.split('=')
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    for o in meshes:
        if 'LOD' in o.name or 'Shadow' in o.name:
            o.hide_render = True
    clip, frame = args[1].split(':'); rig.animation_data.action = bpy.data.actions[clip]; sc.frame_set(int(frame))
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = 2.0; sc.render.resolution_x = 400; sc.render.resolution_y = 480
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs['Color'].default_value = (.33, .34, .37, 1)
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3.5; sc.collection.objects.link(sun); sun.rotation_euler = (0.8, 0, -0.6)
    sc.view_settings.view_transform = 'Standard'; sc.render.engine = 'BLENDER_EEVEE'
    c = Vector((0, 0, .9))
    for v, d in VIEWS.items():
        cam.location = c + Vector(d).normalized() * 5; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.clip_end = 20
        sc.render.filepath = os.path.join(out, f'{label}_{v}.png'); bpy.ops.render.render(write_still=True)
print('SHOTS done')
