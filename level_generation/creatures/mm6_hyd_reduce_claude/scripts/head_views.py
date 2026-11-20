"""Close renders of each hydra head (Standing frame 0): side and three-quarter, textured.
Usage: blender -b -P head_views.py -- <glb> <label>  -> review/close/<label>_head<N>_<view>.png"""
import os, sys, math, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
glb, label = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
sc = bpy.context.scene; rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
rig.animation_data.action = bpy.data.actions['Standing']; sc.frame_set(0)
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3
sun.rotation_euler = (math.radians(40), 0, math.radians(-25)); sc.collection.objects.link(sun)
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (.35, .35, .38, 1)
sc.view_settings.view_transform = 'Standard'; sc.render.resolution_x = sc.render.resolution_y = 500
sc.render.engine = 'BLENDER_EEVEE'
for n in range(1, 6):
    b = rig.pose.bones[f'Head{n}']
    c = rig.matrix_world @ ((b.head + b.tail) / 2)
    for view, d in {'side': (0, -1, .15), 'q34': (.7, -.7, .25)}.items():
        # the hydra faces +X in the GLB (yaw_offset -90 deg)
        dv = Vector((-d[1], d[0], d[2])).normalized() if view == 'q34' else Vector((0, -1, .15)).normalized()
        cam.location = c + dv * 3; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        cam.data.ortho_scale = .22
        sc.render.filepath = os.path.join(HERE, 'review/close', f'{label}_head{n}_{view}.png'); bpy.ops.render.render(write_still=True)
