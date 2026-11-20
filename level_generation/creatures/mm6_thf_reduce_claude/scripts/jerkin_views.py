"""Close renders for the jerkin and the daggers: Standing front of the lower torso, and the Attack at mid-thrust.
Usage: blender -b -P jerkin_views.py -- <glb> <label> -> review/tex/<label>_{jerkin,daggers}.png"""
import bpy, math, os, sys
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
glb, label = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
sc = bpy.context.scene; rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.type = 'ORTHO'
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3; sun.rotation_euler = (math.radians(45), 0, math.radians(20)); sc.collection.objects.link(sun)
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs['Color'].default_value = (.35, .35, .38, 1)
sc.view_settings.view_transform = 'Standard'; sc.render.resolution_x = sc.render.resolution_y = 500; sc.render.engine = 'BLENDER_EEVEE'
for name, clip, frac, cz, size in [('jerkin', 'Standing', 0.0, 0.92, 0.55), ('daggers', 'Attack', 0.6, 1.05, 0.9),
                                  ('lowjerkin', 'Standing', 0.0, 0.86, 0.22), ('sleeve', 'Standing', 0.0, 1.05, 0.3)]:
    act = bpy.data.actions[clip]; rig.animation_data.action = act
    if act.slots: rig.animation_data.action_slot = act.slots[0]
    f0, f1 = act.frame_range; sc.frame_set(int(f0 + (f1 - f0) * frac))
    c = Vector((0.2 if name == 'sleeve' else 0, -0.1 if name == 'daggers' else 0, cz)); dv = Vector((0.25, -1, 0.1)).normalized()
    cam.location = c + dv * 5; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.ortho_scale = size
    sc.render.filepath = os.path.join(HERE, 'review', 'tex', f'{label}_{name}.png'); bpy.ops.render.render(write_still=True)
    if name == 'daggers':                                           # close-up of the right dagger, two angles
        pb = rig.pose.bones['DaggerR']
        c = rig.matrix_world @ ((pb.head + pb.tail) / 2)
        for k, dv in enumerate((Vector((0.3, -1, 0.3)), Vector((-0.8, -0.6, 0.5)))):
            dv.normalize(); cam.location = c + dv * 3; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
            cam.data.ortho_scale = 0.32
            sc.render.filepath = os.path.join(HERE, 'review', 'tex', f'{label}_dagger{k}.png'); bpy.ops.render.render(write_still=True)
