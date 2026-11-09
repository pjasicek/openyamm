"""hkr: the demon's tail (Bone_020 at the pelvis -> Bone_015 at the tip) moves in every clip instead of trailing as a
rigid stick. Per frame, bones root to tip, a world rotation about each bone's head on top of the clip's pose:
- sway: side to side about (bone direction x world X), amplitude SWAY[clip] x (0.5 + 0.18 k) deg for bone k, phase
  lagging 0.55 rad per bone, CYCLES[clip] whole cycles per clip (loops stay seamless; one-shot clips use a half sine
  that is 0 at both ends);
- lift: about world X (the tail's root raised behind), LIFT[clip] deg on the root, a quarter of it on the others,
  plus a pitch bob at twice the sway rate (BOB deg);
- floor: if a bone's tip falls below FLOOR (3 cm), the bone turns up by the smallest rotation that puts it there
  (the lying death drapes the tail along the floor instead of through it);
- legs: if a tail joint is closer than CLEAR (9 cm) to a thigh/calf bone segment, the tail turns away from it (the
  running leg's back kick).
Keys every frame; quaternions sign-continuous. Args: -- <in> <out> <Action> [...]"""
import bpy, sys, os, math
from mathutils import Vector, Quaternion, Matrix
a = sys.argv[sys.argv.index('--') + 1:]
src, out, acts = a[0], a[1], a[2:]
TAIL = ['Bone_020', 'Bone_019', 'Bone_018', 'Bone_017', 'Bone_016', 'Bone_015']
SWAY = {'Standing': 3.0, 'Walking': 7.0, 'Running': 9.0, 'Attack': 3.0, 'Hit': 8.0, 'Fidget': 4.0, 'Death': 0.0}
CYCLES = {'Standing': 1, 'Walking': 1, 'Running': 1, 'Attack': 1, 'Hit': 0.5, 'Fidget': 1, 'Death': 0}
LIFT = {'Running': 14.0, 'Walking': 4.0, 'Attack': 3.0}
BOB = {'Walking': 2.0, 'Running': 3.0}
FLOOR, CLEAR = float(os.environ.get('FLOOR', '0.03')), float(os.environ.get('CLEAR', '0.09'))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene; AW = rig.matrix_world; AWi = AW.inverted()
X = Vector((1, 0, 0)); UP = Vector((0, 0, 1))
LEGS = [(f'B_{s}_{a_}', f'B_{s}_{b_}') for s in 'LR' for a_, b_ in (('Thigh', 'Calf'), ('Calf', 'Foot'))]


def seg_dist(p, a_, b_):
    ab = b_ - a_; t = max(0.0, min(1.0, (p - a_).dot(ab) / ab.length_squared)); q = a_ + ab * t
    return (p - q).length, q


def world(n):
    return AW @ rig.pose.bones[n].matrix


def set_world_rot(n, R):
    M = world(n); new = (R @ M.to_3x3()).to_4x4(); new.translation = M.translation
    rig.pose.bones[n].matrix = AWi @ new; bpy.context.view_layer.update()


rep = {}
for name in acts:
    act = bpy.data.actions[name]; rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range); T = max(1, f1 - f0)
    sway, cyc, lift, bob = SWAY.get(name, 3.0), CYCLES.get(name, 1), LIFT.get(name, 0.0), BOB.get(name, 0.0)
    keys = {}; lowest = 9.0; nearest = 9.0
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        for n in TAIL:
            pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = Quaternion()
        bpy.context.view_layer.update()
        u = (f - f0) / T
        legs = [(world(x).translation, world(y).translation) for x, y in LEGS]
        for k, n in enumerate(TAIL):
            if cyc >= 1:
                s_ = math.sin(2 * math.pi * cyc * u - 0.55 * k)
            else:
                s_ = math.sin(math.pi * u) * math.cos(0.55 * k)
            M = world(n); d = (M.to_3x3() @ Vector((0, 1, 0))).normalized()
            ax = d.cross(X); ax = ax.normalized() if ax.length > 1e-6 else Vector((0, 0, 1))
            R = Quaternion(ax, math.radians(sway * (0.5 + 0.18 * k) * s_)).to_matrix()
            lp = (lift if k == 0 else lift * 0.25) + bob * math.sin(4 * math.pi * cyc * u - 0.55 * k) * (1 if cyc >= 1 else 0)
            # +X rotation turns a backward-down tail (+Y, -Z) upward
            R = Matrix.Rotation(math.radians(lp), 3, X) @ R if lp else R
            set_world_rot(n, R)
            M = world(n); head = M.translation; L = rig.data.bones[n].length
            tip = head + (M.to_3x3() @ Vector((0, 1, 0))).normalized() * L
            if tip.z < FLOOR:                                     # turn up just enough
                d = (tip - head).normalized(); want_z = max(-1.0, min(1.0, (FLOOR - head.z) / L))
                hz = Vector((d.x, d.y, 0)); hz = hz.normalized() if hz.length > 1e-6 else Vector((0, 1, 0))
                d2 = hz * math.sqrt(max(0.0, 1 - want_z * want_z)) + UP * want_z
                set_world_rot(n, d.rotation_difference(d2).to_matrix())
            M = world(n); tip = M.translation + (M.to_3x3() @ Vector((0, 1, 0))).normalized() * L
            for la, lb in legs:                                    # away from the legs
                dist, q = seg_dist(tip, la, lb)
                if dist < CLEAR:
                    d = (tip - M.translation).normalized(); push = (tip - q); push.z = 0
                    if push.length < 1e-6: continue
                    d2 = (tip + push.normalized() * (CLEAR - dist) - M.translation).normalized()
                    set_world_rot(n, d.rotation_difference(d2).to_matrix())
                    M = world(n); tip = M.translation + (M.to_3x3() @ Vector((0, 1, 0))).normalized() * L
            lowest = min(lowest, tip.z)
            nearest = min([nearest] + [seg_dist(tip, la, lb)[0] for la, lb in legs])
        keys[f] = {n: rig.pose.bones[n].rotation_quaternion.copy() for n in TAIL}
    prev = {}
    for f, kv in keys.items():
        for n, q in kv.items():
            if n in prev and q.dot(prev[n]) < 0: q = -q
            prev[n] = q; pb = rig.pose.bones[n]; pb.rotation_quaternion = q; pb.keyframe_insert('rotation_quaternion', frame=f)
    rep[name] = (round(lowest * 100, 1), round(nearest * 100, 1))
    print('TAIL', name, 'lowest tail joint cm', rep[name][0], 'nearest to a leg bone cm', rep[name][1])
rig.animation_data.action = None
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
