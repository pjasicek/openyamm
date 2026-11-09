"""Print world head positions of key bones of a GLB at rest and at POSE=action@frame."""
import bpy, sys, os
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=argv[0])
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
if os.environ.get('POSE'):
    name, frame = os.environ['POSE'].split('@')
    act = bpy.data.actions[name]
    arm.animation_data.action = act
    try:
        arm.animation_data.action_slot = act.slots[0]
    except Exception:
        pass
    sc.frame_set(int(float(frame)))
print('ACTIONS', [(a.name, a.frame_range[:]) for a in bpy.data.actions])
for pb in arm.pose.bones:
    if any(k in pb.name for k in argv[1].split(',')):
        print('BONE', pb.name, tuple(round(x, 3) for x in (arm.matrix_world @ pb.head)))
