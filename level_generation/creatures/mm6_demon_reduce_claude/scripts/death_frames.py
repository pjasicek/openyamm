"""Death clip frames and the Dead hold of a viewer GLB from the side and three-quarter: review/death/<label>_*.png.
Usage: blender -b -P death_frames.py -- <glb> <label>"""
import os, sys, math, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
glb, label = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
sc = bpy.context.scene; sc.render.fps = 24
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 2.6
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3
sun.rotation_euler = (math.radians(40), 0, math.radians(-25)); sc.collection.objects.link(sun)
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (.35, .35, .38, 1)
sc.view_settings.view_transform = 'Standard'; sc.render.resolution_x = sc.render.resolution_y = 420
sc.render.engine = 'BLENDER_EEVEE'
out = os.path.join(HERE, 'review', 'death'); os.makedirs(out, exist_ok=True)
c = Vector((0, 0, .7))
for clip, times in [('Death', [0, .25, .375, .5, .75, 1.0, 1.25]), ('Dead', [.5])]:
    rig.animation_data.action = bpy.data.actions[clip]
    for t in times:
        sc.frame_set(int(round(t * 24)))
        for view, d in {'side': (0, -1, .15), 'q34': (.7, -.7, .3)}.items():
            dv = Vector(d).normalized(); cam.location = c + dv * 6
            cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
            sc.render.filepath = os.path.join(out, f'{label}_{clip}_{t:.3f}_{view}.png'); bpy.ops.render.render(write_still=True)
