"""Staff bone (Bone01) relative to the R hand over every frame of every MM9 clip: is the staff rigid in the hand?
Args: <mm9 glb>"""
import bpy, sys
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=argv[0])
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
hand = arm.pose.bones['Bip01 R Hand']; st = arm.pose.bones['Bone01']
for act in bpy.data.actions:
    arm.animation_data.action = act
    try:
        arm.animation_data.action_slot = act.slots[0]
    except Exception:
        pass
    f0, f1 = act.frame_range
    rels = []
    for f in range(int(f0), int(f1) + 1, 2):
        sc.frame_set(f)
        r = hand.matrix.inverted() @ st.matrix
        rels.append((f, r.to_translation().copy(), r.to_quaternion().copy(), (arm.matrix_world @ st.head).copy()))
    t0, q0 = rels[0][1], rels[0][2]
    dt = max((r[1] - t0).length for r in rels); dq = max(q0.rotation_difference(r[2]).angle for r in rels)
    print('STAFF', act.name, 'frames', len(rels), 'max dT %.3f m, max dRot %.1f deg' % (dt, dq * 57.3), 'rel0', tuple(round(x, 3) for x in t0), 'low z', round(min(r[3].z for r in rels), 3))
