"""Standing frame 0 front, back and three-quarter of a viewer GLB, plus a face close-up.
Usage: blender -b -P tier_views.py -- <glb> <label> -> review/tex/<label>_<view>.png"""
import bpy, math, os, sys
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
glb, label = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
sc = bpy.context.scene; rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
act = bpy.data.actions['Standing']; rig.animation_data.action = act
if act.slots: rig.animation_data.action_slot = act.slots[0]
sc.frame_set(0)
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.type = 'ORTHO'
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3; sun.rotation_euler = (math.radians(45), 0, math.radians(20)); sc.collection.objects.link(sun)
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs['Color'].default_value = (.35, .35, .38, 1)
sc.view_settings.view_transform = 'Standard'; sc.render.resolution_x = sc.render.resolution_y = 520; sc.render.engine = 'BLENDER_EEVEE'
os.makedirs(os.path.join(HERE, 'review', 'tex'), exist_ok=True)
for view, dv, size, cz in [('front', Vector((0, -1, .1)), 1.85, .82), ('back', Vector((0, 1, .1)), 1.85, .82),
                           ('q34', Vector((.7, -.7, .15)), 1.85, .82), ('torso', Vector((0, -1, .05)), .75, 1.1),
                           ('chest', Vector((0, -1, .05)), .42, 1.08), ('legs', Vector((.4, -1, .1)), .8, .35),
                           ('backtorso', Vector((0, 1, .05)), .75, 1.1)]:
    c = Vector((0, 0, cz)); dv.normalize(); cam.location = c + dv * 5; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.ortho_scale = size
    sc.render.filepath = os.path.join(HERE, 'review', 'tex', f'{label}_{view}.png'); bpy.ops.render.render(write_still=True)
