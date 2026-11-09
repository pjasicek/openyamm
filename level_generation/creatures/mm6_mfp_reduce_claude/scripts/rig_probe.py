"""Cutpurse rig facts: Knife/Socket parents, rest positions, which bones each clip animates, Knife joint world
position per clip (first/mid/last) and its distance to the right hand."""
import bpy, sys
glb = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=glb)
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
for n in ('Knife', 'Socket_Knife_Tip', 'B_R_Hand', 'B_Pelvis', 'B_Spine'):
    b = arm.data.bones[n]; print('BONE', n, 'parent', b.parent.name if b.parent else None, 'head', [round(x, 3) for x in (arm.matrix_world @ b.head_local)])
sc = bpy.context.scene
for act in bpy.data.actions:
    arm.animation_data.action = act
    if len(act.slots): arm.animation_data.action_slot = act.slots[0]
    bones = sorted({fc.data_path.split('"')[1] for fc in getattr(act, 'fcurves', []) if '"' in fc.data_path}) if hasattr(act, 'fcurves') else []
    if not bones:
        try:
            bones = sorted({fc.data_path.split('"')[1] for l in act.layers for s in l.strips for cb in s.channelbags for fc in cb.fcurves if '"' in fc.data_path})
        except Exception as e: bones = [str(e)]
    f0, f1 = act.frame_range; out = []
    for f in (f0, (f0 + f1) / 2, f1):
        sc.frame_set(int(f)); k = arm.matrix_world @ arm.pose.bones['Knife'].head; h = arm.matrix_world @ arm.pose.bones['B_R_Hand'].head
        out.append(f"f{int(f)} knife {[round(x, 2) for x in k]} d_hand {round((k - h).length, 3)}")
    print('ACT', act.name, act.frame_range[:], 'bones', len(bones), 'knife' if 'Knife' in bones else 'no-knife-keys', ' | '.join(out))
