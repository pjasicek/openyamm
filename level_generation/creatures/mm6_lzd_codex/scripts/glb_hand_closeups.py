"""Textured close-ups of both hands (or, with FOCUS=neck, the neck and shoulders) from the exported GLB (what the
viewer and game play), at listed clip times, four views around each. Args: -- <glb> <out prefix> clip:seconds [...]"""
import bpy, sys, os, math
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
glb, out, picks = a[0], a[1], a[2:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
for o in bpy.data.objects:
    if o.type == 'MESH' and ('LOD' in o.name or 'Shadow' in o.name):
        o.hide_render = True
sc = bpy.context.scene; common.workbench_clay(sc, textured=True)
for pk in picks:
    clip, t = pk.split(':')
    act = bpy.data.actions[clip]; arm.animation_data.action = act
    if len(act.slots):
        arm.animation_data.action_slot = act.slots[0]
    f = act.frame_range[0] + float(t) * sc.render.fps
    sc.frame_set(int(f), subframe=f - int(f))
    for s in (('N',) if os.environ.get('FOCUS') == 'neck' else 'RL'):
        if s == 'N':
            c = arm.matrix_world @ arm.pose.bones['B_Neck'].head
        else:
            h = arm.matrix_world @ arm.pose.bones[f'B_{s}_Hand'].head; k = arm.matrix_world @ arm.pose.bones[f'B_{s}_Finger2'].head
            c = (h + k) / 2
        for v, ang in (('a', 0), ('b', 90), ('c', 180), ('d', 270)):
            r = math.radians(ang); d = Vector((math.sin(r), -math.cos(r), 0.35)).normalized()
            cam = common.ortho_camera('c', c + d, (0, 0, 0), 0.6 if s == 'N' else 0.28); cam.rotation_mode = 'QUATERNION'
            cam.rotation_quaternion = (-d).to_track_quat('-Z', 'Y'); sc.camera = cam
            sc.render.resolution_x = sc.render.resolution_y = 300
            sc.render.filepath = f'{out}_{clip}{t}_{s}_{v}.png'; bpy.ops.render.render(write_still=True)
            bpy.data.objects.remove(cam)
