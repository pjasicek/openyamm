"""Fly frame 0 head close-ups of a viewer GLB from five directions (side, below, above, both ends).
Usage: blender -b -P head_closeups.py -- <glb> <label> -> review/compare/close_<label>_<dir>.png"""
import bpy, math, os, sys
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
glb, label = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
sc = bpy.context.scene; rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
act = bpy.data.actions['Fly']; rig.animation_data.action = act
if act.slots: rig.animation_data.action_slot = act.slots[0]
sc.frame_set(0)
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.type = 'ORTHO'
for rot in ((40, 0, -25), (-50, 0, 150)):
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 2.2
    sun.rotation_euler = tuple(math.radians(a) for a in rot); sc.collection.objects.link(sun)
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs['Color'].default_value = (.35, .35, .38, 1)
sc.view_settings.view_transform = 'Standard'; sc.render.resolution_x = sc.render.resolution_y = 450; sc.render.engine = 'BLENDER_EEVEE'
pb = rig.pose.bones
c = rig.matrix_world @ ((pb['Head'].head + pb['Mouth'].tail) / 2)
for name, dv in [('sideA', Vector((1, 0, .1))), ('sideB', Vector((-1, 0, .1))), ('below', Vector((0.05, 0, -1))),
                 ('above', Vector((0.05, 0, 1))), ('endP', Vector((0, 1, .1))), ('endN', Vector((0, -1, .1)))]:
    dv.normalize(); cam.location = c + dv * 3; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.ortho_scale = .38
    sc.render.filepath = os.path.join(HERE, 'review', 'compare', f'close_{label}_{name}.png'); bpy.ops.render.render(write_still=True)
