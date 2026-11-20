"""Right-arm close-ups of a viewer GLB over a clip: textured renders looking at the elbow and the hand from the
front-right. Usage: blender -b -P arm_views.py -- <glb> <label> <clip> <frame,...>  -> review/arm/<label>_<clip><f>_{elbow,hand}.png"""
import bpy, sys, os
from mathutils import Vector
glb, label, clip, frames = sys.argv[sys.argv.index('--') + 1:][:4]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); out = os.path.join(HERE, 'review/arm'); os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
sc = bpy.context.scene
for o in bpy.data.objects:
    if o.type == 'MESH' and ('LOD' in o.name or 'Shadow' in o.name): o.hide_render = True
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
act = bpy.data.actions[clip]; rig.animation_data.action = act
if len(act.slots): rig.animation_data.action_slot = act.slots[0]
sc.render.resolution_x = sc.render.resolution_y = 500
try: sc.render.engine = 'BLENDER_EEVEE_NEXT'
except TypeError: sc.render.engine = 'BLENDER_EEVEE'
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND').inputs[0].default_value = (0.4, 0.42, 0.45, 1)
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sc.collection.objects.link(sun); sun.data.energy = 3
sun.rotation_euler = (0.6, 0.0, 0.3)
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.lens = 50
pb = rig.pose.bones
for f in [int(x) for x in frames.split(',')]:
    sc.frame_set(f)
    for spot, bone, dist in (('elbow', 'B_R_Forearm', .55), ('hand', 'B_R_Hand', .38)):
        t = rig.matrix_world @ (pb[bone].head if spot == 'elbow' else (pb[bone].head + pb[bone].tail) / 2)
        cam.location = t + Vector([float(x) for x in os.environ.get('ARM_DIR', '-.35,-.85,.25').split(',')]).normalized() * dist
        cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(out, f'{label}_{clip}{f}_{spot}.png'); bpy.ops.render.render(write_still=True)
