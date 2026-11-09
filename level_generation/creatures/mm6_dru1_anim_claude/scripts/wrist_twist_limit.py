"""Limit the hand's twist about the forearm axis in one clip (run after the retarget, before twist_bones.py): the
Mixamo punch's left guard hand pronates up to 118 deg against the forearm (the retarget moves Mixamo's forearm roll
into the hand); the accepted druidess clips stay under 45 deg (trace_attack.py baseline), beyond that the forearm skin
wraps. dq = hand rotation relative to the forearm (from rest), twist about the forearm segment (twist_bones.py rule);
the excess over TW_MAX (default 40 deg) is turned back about that axis, so the palm turns less and the swing stays.
SW_MAX (deg, off by default; round 3 magic blast: 40) also limits the swing (the hand bending against the forearm, the
rest of the relative rotation after the twist): the 2H Magic Attack 01 push bends both palms back 56-65 deg and opened
the wrist seam 6-8 mm in trace_attack.py; the swing is slerped back to SW_MAX, the twist kept.
Args: -- <in blend> <out blend> <clip> [side ...]"""
import bpy, sys, os, math
from mathutils import Vector, Quaternion
a = sys.argv[sys.argv.index('--') + 1:]
src, out, clip, sides = a[0], a[1], a[2], a[3:] or ['L', 'R']
TW = math.radians(float(os.environ.get('TW_MAX', '40')))
SW = math.radians(float(os.environ['SW_MAX'])) if os.environ.get('SW_MAX') else None
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene
act = bpy.data.actions[clip]; rig.animation_data_create(); rig.animation_data.action = act
if getattr(act, 'slots', None) is not None and len(act.slots):
    rig.animation_data.action_slot = act.slots[0]


def twist_about(q, axis):
    v = Vector((q.x, q.y, q.z)); t = 2 * math.atan2(v.dot(axis), q.w)
    return (t + math.pi) % (2 * math.pi) - math.pi


f0, f1 = (int(x) for x in act.frame_range)
worst = {s: [0.0, 0.0, 0.0, 0.0] for s in sides}
for f in range(f0, f1 + 1):
    sc.frame_set(f)
    for s in sides:
        fb, hb = rig.data.bones[f'B_{s}_Forearm'], rig.data.bones[f'B_{s}_Hand']
        fp, hp = rig.pose.bones[f'B_{s}_Forearm'], rig.pose.bones[f'B_{s}_Hand']
        seg = (fb.matrix_local.inverted() @ hb.head_local).normalized()
        rel = (fp.matrix.inverted() @ hp.matrix).to_quaternion()
        rest_rel = (fb.matrix_local.inverted() @ hb.matrix_local).to_quaternion()
        tw = twist_about(rel @ rest_rel.inverted(), seg)
        worst[s][0] = max(worst[s][0], abs(math.degrees(tw)))
        ex = tw - max(-TW, min(TW, tw))
        if abs(ex) > 1e-6:
            M = fp.matrix @ Quaternion(seg, -ex).to_matrix().to_4x4() @ (fp.matrix.inverted() @ hp.matrix)
            hp.rotation_mode = 'QUATERNION'; hp.matrix = M; bpy.context.view_layer.update()
            hp.keyframe_insert('rotation_quaternion', frame=f)
        if SW is not None:
            local = fp.matrix.inverted() @ hp.matrix; rel = local.to_quaternion()
            d = rel @ rest_rel.inverted(); tq = Quaternion(seg, twist_about(d, seg)); sw = d @ tq.inverted()
            ang = 2 * math.acos(min(1.0, abs(sw.w)))
            worst[s][2] = max(worst[s][2], math.degrees(ang))
            if ang > SW:
                sw = Quaternion().slerp(sw if sw.w >= 0 else -sw, SW / ang)
                M = (sw @ tq @ rest_rel).to_matrix().to_4x4(); M.translation = local.translation
                hp.rotation_mode = 'QUATERNION'; hp.matrix = fp.matrix @ M; bpy.context.view_layer.update()
                hp.keyframe_insert('rotation_quaternion', frame=f)
            d = (fp.matrix.inverted() @ hp.matrix).to_quaternion() @ rest_rel.inverted()
            sw = d @ Quaternion(seg, twist_about(d, seg)).inverted()
            worst[s][3] = max(worst[s][3], math.degrees(2 * math.acos(min(1.0, abs(sw.w)))))
        rel = (fp.matrix.inverted() @ hp.matrix).to_quaternion()
        worst[s][1] = max(worst[s][1], abs(math.degrees(twist_about(rel @ rest_rel.inverted(), seg))))
rig.animation_data.action = None
for s, (b, c, sb, sc_) in worst.items():
    print(f'WRISTTWIST {clip} {s}: max {b:.1f} -> {c:.1f} deg (limit {math.degrees(TW):.0f})'
          + (f', swing {sb:.1f} -> {sc_:.1f} deg (limit {math.degrees(SW):.0f})' if SW is not None else ''))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
