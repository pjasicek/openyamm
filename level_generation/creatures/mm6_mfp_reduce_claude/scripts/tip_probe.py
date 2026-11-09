"""Per-frame knife numbers for an action: tip forward (-Y) / height / lateral, tip speed (m/s), knife direction
(pitch: + up, yaw: 0 = forward), right-hand height, pelvis height. Args: -- <blend> <action> [step]"""
import bpy, sys, math
a = sys.argv[sys.argv.index('--') + 1:]; bpy.ops.wm.open_mainfile(filepath=a[0])
rig = bpy.data.objects['Rig']; sc = bpy.context.scene; act = bpy.data.actions[a[1]]; step = int(a[2]) if len(a) > 2 else 1
rig.animation_data_create(); rig.animation_data.action = act
if len(act.slots): rig.animation_data.action_slot = act.slots[0]
P = lambda n: rig.matrix_world @ rig.pose.bones[n].head
prev = None
for f in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1, step):
    sc.frame_set(f); t = P('Socket_Knife_Tip'); k = P('Knife'); d = (t - k).normalized()
    sp = (t - prev).length * 30 / step if prev is not None else 0; prev = t.copy()
    print(f'F {f:3d} tip fwd {-t.y:5.2f} h {t.z:4.2f} lat {t.x:5.2f} v {sp:4.1f} | knife pitch {math.degrees(math.asin(max(-1, min(1, d.z)))):5.0f} yaw {math.degrees(math.atan2(d.x, -d.y)):5.0f} | hand h {P("B_R_Hand").z:4.2f} pelvis {P("B_Pelvis").z:4.2f}')
