"""Frontal and three-quarter face close-ups (Standing frame 0). Usage: blender -b -P face_front.py -- <glb> <label>"""
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
hb = rig.pose.bones['Head']; c = rig.matrix_world @ (hb.head * 0.55 + hb.tail * 0.45)
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.type = 'ORTHO'
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3; sun.rotation_euler = (math.radians(50), 0, math.radians(200)); sc.collection.objects.link(sun)
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs['Color'].default_value = (.35, .35, .38, 1)
sc.view_settings.view_transform = 'Standard'; sc.render.resolution_x = sc.render.resolution_y = 450; sc.render.engine = 'BLENDER_EEVEE'
os.makedirs(os.path.join(HERE, 'review', 'face'), exist_ok=True)
# facing from the rig's headfront bone (in front of the face)
fwd = (rig.matrix_world @ rig.pose.bones['headfront'].head) - (rig.matrix_world @ hb.head); fwd.z = 0; fwd.normalize()
side = fwd.cross(Vector((0, 0, 1)))
for view, dv in [('front', fwd + Vector((0, 0, 0.05))), ('q34', fwd * 0.75 + side * 0.65 + Vector((0, 0, 0.1)))]:
    dv.normalize(); cam.location = c + dv * 2; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.ortho_scale = .24
    sc.render.filepath = os.path.join(HERE, 'review', 'face', f'{label}_{view}.png'); bpy.ops.render.render(write_still=True)
