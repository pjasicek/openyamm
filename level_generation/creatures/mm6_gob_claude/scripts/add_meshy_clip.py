"""Add one clip from a Meshy animation GLB (same Meshy skeleton as rig_v1) to the Meshy-based goblin rig.
Bones copy Meshy's world rotations directly (identical rest joints), the hips copy position; the sword stays in the
solved right fist, the left hand is a loose fist. Args: glb clip_name [source_action_substring]."""
import bpy, os, sys
from mathutils import Matrix, Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[sys.argv.index('--') + 1:]
glb, name = args[0], args[1]
want = args[2].lower() if len(args) > 2 else None
rig = bpy.data.objects['Peasant_Rig']; scene = bpy.context.scene
MAP = {'Hips': 'Hips', 'Spine02': 'Spine', 'Spine01': 'Spine1', 'Spine': 'Spine2', 'neck': 'Neck', 'Head': 'Head'}
for side in ('Left', 'Right'):
    for b in ('Shoulder', 'Arm', 'ForeArm', 'Hand', 'UpLeg', 'Leg', 'Foot', 'ToeBase'):
        MAP[side + b] = side + b
before = set(bpy.data.objects); before_act = set(bpy.data.actions)
bpy.ops.import_scene.gltf(filepath=glb)
objs = [o for o in bpy.data.objects if o not in before]
marm = next(o for o in objs if o.type == 'ARMATURE')
acts = [a for a in bpy.data.actions if a not in before_act]
src = next(a for a in acts if want is None or want in a.name.lower())
src_name = src.name
marm.animation_data.action = src
f0, f1 = (int(round(x)) for x in src.frame_range)
frames = []
for f in range(f0, f1 + 1):
    scene.frame_set(f)
    frames.append({k: marm.matrix_world @ marm.pose.bones[k].matrix for k in MAP})
for o in objs:
    bpy.data.objects.remove(o, do_unlink=True)
for a in acts:
    bpy.data.actions.remove(a)
import author_clips as A
import posing as P
inv = rig.matrix_world.inverted()
order = [b.name for b in rig.data.bones]
back = {('mixamorig:' + v): k for k, v in MAP.items()}
out = []
A.PREV_WRIST.clear()
for k, fm in enumerate(frames):
    rig.animation_data.action = None
    P.reset(rig)
    for n in order:
        if n not in back:
            continue
        pb = rig.pose.bones[n]; m = fm[back[n]]
        loc, rot, _ = m.decompose()
        head = inv @ loc if n == 'mixamorig:Hips' else pb.head.copy()
        pb.matrix = Matrix.LocRotScale(head, rig.matrix_world.to_quaternion().inverted() @ rot, Vector((1, 1, 1)))
        bpy.context.view_layer.update()
    for side in ('Left', 'Right'):
        A.limit_wrist(side)
    P.curl_hand(rig, 'Right', 80, thumb=35)
    A.wrap_grip('Right'); A.wrap_thumb('Right')
    P.curl_hand(rig, 'Left', 30, thumb=12)
    for side in ('Left', 'Right'):
        A.PREV_WRIST[side] = A.wrist_relative(side)
    out.append((k + 1, A.capture()))
old = bpy.data.actions.get(name)
if old:
    bpy.data.actions.remove(old)
A.write_action(name, out, loop=False)
rig.animation_data.action = bpy.data.actions['Standing']
bpy.ops.wm.save_mainfile()
print('ADDED', name, 'from', src_name, len(frames), 'frames')
