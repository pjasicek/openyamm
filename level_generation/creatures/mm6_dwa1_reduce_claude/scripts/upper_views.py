"""Front upper-body renders of a viewer GLB at clip frames (camera like the viewer screenshot: front, slightly right).
Usage: blender -b -P upper_views.py -- <glb|blend> <label> <clip:frame,...>  -> review/arm/<label>_<clip><f>_upper.png"""
import bpy, sys, os
from mathutils import Vector
glb, label, spec = sys.argv[sys.argv.index('--') + 1:][:3]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); out = os.path.join(HERE, 'review/arm'); os.makedirs(out, exist_ok=True)
if glb.endswith('.blend'):
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(glb))
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.name != 'Body': o.hide_render = True
    for o in [o for o in bpy.data.objects if o.type in ('CAMERA', 'LIGHT')]: bpy.data.objects.remove(o)
else:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
sc = bpy.context.scene
for o in bpy.data.objects:
    if o.type == 'MESH' and ('LOD' in o.name or 'Shadow' in o.name): o.hide_render = True
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
sc.render.resolution_x = sc.render.resolution_y = 500
try: sc.render.engine = 'BLENDER_EEVEE_NEXT'
except TypeError: sc.render.engine = 'BLENDER_EEVEE'
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND').inputs[0].default_value = (0.4, 0.42, 0.45, 1)
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sc.collection.objects.link(sun); sun.data.energy = 3
sun.rotation_euler = (0.6, 0.0, 0.3)
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.lens = 50
for cf in spec.split(','):
    clip, f = cf.split(':'); act = bpy.data.actions[clip]; rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    sc.frame_set(int(f))
    t = rig.matrix_world @ rig.pose.bones['B_Spine2'].head + Vector((-.1, 0, .15)) + Vector([float(x) for x in os.environ.get('UV_OFF', '0,0,0').split(',')])
    cam.location = t + Vector([float(x) for x in os.environ.get('UV_DIR', '-.25,-1,.25').split(',')]).normalized() * float(os.environ.get('UV_DIST', '1.3'))
    cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(out, f'{label}_{clip}{f}_upper.png'); bpy.ops.render.render(write_still=True)
