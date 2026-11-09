import bpy,sys,os,math,json,numpy as np
from mathutils import Vector,Matrix,Quaternion
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/motion_carry_fixed.blend'))
rig=bpy.data.objects['Rig'];scene=bpy.context.scene;names=[b.name for b in rig.data.bones]
def set_act(a):
    rig.animation_data_create(); rig.animation_data.action = a
    if a is not None and getattr(a, 'slots', None) is not None and len(a.slots):
        rig.animation_data.action_slot = a.slots[0]


def sample(act, f):
    set_act(act); scene.frame_set(int(f), subframe=f - int(f))
    return {n: (rig.pose.bones[n].rotation_quaternion.copy(), rig.pose.bones[n].location.copy()) for n in names}


def segment_axis(j, child):
    b, c = rig.data.bones[j], rig.data.bones[child]
    return (b.matrix_local.to_3x3().inverted() @ (c.head_local - b.head_local)).normalized()


TWIST_AXES = {'B_Spine': segment_axis('B_Spine', 'B_Spine1'), 'B_Spine1': segment_axis('B_Spine1', 'B_Spine2'),
              'B_Spine2': segment_axis('B_Spine2', 'B_Neck'), 'B_Neck': segment_axis('B_Neck', 'B_Head')}


def split_twist(q, axis):
    """q = swing @ twist about the bone-local axis; returns (swing, twist angle)."""
    t = 2 * math.atan2(Vector((q.x, q.y, q.z)).dot(axis), q.w)
    t = (t + math.pi) % (2 * math.pi) - math.pi
    return q @ Quaternion(axis, t).inverted(), t


def limit_spine_twist(pose):
    parts = {j: split_twist(pose[j][0], TWIST_AXES[j]) for j in TWIST_AXES}
    total = sum(parts[j][1] for j in SPINE)
    if abs(total) <= TWIST_FREE:
        return pose, total, total
    span = TWIST_MAX - TWIST_FREE
    limited = math.copysign(TWIST_FREE + span * math.tanh((abs(total) - TWIST_FREE) / span), total)
    k = limited / total
    for j in SPINE:
        swing, t = parts[j]; pose[j] = (swing @ Quaternion(TWIST_AXES[j], t * k), pose[j][1])
    swing, t = parts['B_Neck']; pose['B_Neck'] = (swing @ Quaternion(TWIST_AXES['B_Neck'], t + total - limited),
                                                  pose['B_Neck'][1])
    return pose, total, limited


def smooth(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def write(name, frames):
    old = bpy.data.actions.get(name)
    if old:
        bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name); act.use_fake_user = True; set_act(act)
    prev = {}
    for i, pose in enumerate(frames):
        for n, (q, l) in pose.items():
            pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'
            if n in prev and q.dot(prev[n]) < 0:
                q = -q
            prev[n] = q
            pb.rotation_quaternion = q; pb.location = l
            pb.keyframe_insert('rotation_quaternion', frame=i)
            if n == 'B_Pelvis':
                pb.keyframe_insert('location', frame=i)
    act.use_frame_range = True; act.frame_start, act.frame_end = 0, len(frames) - 1
    set_act(None)
    return act


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from g6_head_clearance import Clearance
DEPTH = 0.003
CL = Clearance(bpy.data.objects['Body'])
W_ = rig.matrix_world
_b = bpy.data.objects['Body']; _hv = [v.co for v in _b.data.vertices if v.co.z > rig.data.bones['B_Head'].head_local.z and v.co.y < -0.08]
FACE_C = sum(_hv, Vector()) / max(len(_hv), 1)                     # rest face centre (front of the head)


def turn_world(n, axis, ang):
    pb = rig.pose.bones[n]; m = W_ @ pb.matrix; h = m.translation.copy()
    pb.matrix = W_.inverted() @ (Matrix.Translation(h) @ Matrix.Rotation(ang, 4, axis) @ Matrix.Translation(-h) @ m)
    bpy.context.view_layer.update()


def head_fix(name):
    act = bpy.data.actions[name]; n_f = int(act.frame_range[1]); poses = [sample(act, f) for f in range(n_f + 1)]
    set_act(None)

    def apply(pose):
        for n in names:
            pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion, pb.location = pose[n]
        bpy.context.view_layer.update()

    def correct(side, c):
        # c = (chin up, clavicle down, upper arm down, head away) in radians. The chest twists and the raised upper arm
        # swings under the chin while the head pitches down onto it (it hits the deltoid more than the plate).
        # Directions verified one by one on the worst frames (a probe per component).
        P = lambda n: W_ @ rig.pose.bones[n].head
        lat = (P('B_L_UpperArm') - P('B_R_UpperArm')).normalized()
        cl, sh = P(f'B_{side}_Clavicle'), P(f'B_{side}_UpperArm')
        
        for shoulder_side in ('R','L'):
            cl2, sh2 = P(f'B_{shoulder_side}_Clavicle'), P(f'B_{shoulder_side}_UpperArm')
            turn_world(f'B_{shoulder_side}_Clavicle', (sh2-cl2).cross(Vector((0,0,1))).normalized(), -c[1])   # + lifts
        el, sh = P(f'B_{side}_Forearm'), P(f'B_{side}_UpperArm')
        arm_ax = (el - sh).cross(Vector((0, 0, 1)))
        if arm_ax.length > 1e-4:
            turn_world(f'B_{side}_UpperArm', arm_ax.normalized(), -c[2])                             # + lifts
        turn_world('B_Neck', lat, c[0] * 0.5); turn_world('B_Head', lat, c[0] * 0.5)                  # + chin up
        nk, hd, sh = P('B_Neck'), P('B_Head'), P(f'B_{side}_UpperArm')
        u = (hd - nk).normalized(); v = hd - sh; v = (v - u * v.dot(u)).normalized()
        turn_world('B_Neck', u.cross(v).normalized(), c[3])                                           # away

    # caps and visual costs: lowering the shoulder and arm in a follow-through reads better than a head looking up and
    # away (first version: chin up 30 + away 20 deg made the head look sideways at the sky); the arm stays a last resort
    # disabled (35 deg drove the forearm 5 cm and the blade 18 cm into the body, 15 deg still put the blade 2.8 cm into
    # the left thigh in the low sweep: g6_contacts / g6_sword_mesh)
    CAP = np.radians([20, 20, 0, 0]); COST = np.array([1.0, 0.7, 2.0, 1.5]); STEP = math.radians(2.5)
    cs, sides = [], []
    for pose in poses:
        apply(pose); r = CL.measure()
        c = np.zeros(4)
        if r[0] > DEPTH:
            depth = r[0]
            for _ in range(40):
                best = None
                for k in range(4):
                    if c[k] + STEP > CAP[k] + 1e-6:
                        continue
                    c2 = c.copy(); c2[k] += STEP
                    apply(pose); correct(r[2], c2); d2 = CL.measure()[0]
                    gain = (depth - d2) / COST[k]
                    if best is None or gain > best[2]:
                        best = (d2, k, gain)
                if best is None:
                    break
                c[best[1]] += STEP; depth = best[0]
                if depth <= DEPTH:
                    break
        cs.append(c); sides.append(r[2] if c.any() else None)
    C = np.array(cs); held = np.array([C[max(0, i - 2):i + 3].max(0) for i in range(len(C))])
    k = np.exp(-0.5 * (np.arange(-4, 5) / 1.5) ** 2); k /= k.sum()
    sm = np.maximum(np.stack([np.convolve(np.pad(held[:, j], 4, mode='edge'), k, mode='valid') for j in range(4)], 1), C)
    out, left = [], []
    for i, pose in enumerate(poses):
        apply(pose)
        if sm[i].any():
            sd = next((sides[j] for j in sorted(range(len(sides)), key=lambda j: abs(j - i)) if sides[j]), 'R')
            correct(sd, sm[i])
        left.append(CL.measure()[0])
        out.append({n: (rig.pose.bones[n].rotation_quaternion.copy(), rig.pose.bones[n].location.copy()) for n in names})
    write(name, out)
    mx = np.degrees(sm.max(0)).round().astype(int)
    print(f'HEADFIX {name}: frames corrected {int(sm.any(1).sum())} of {len(sm)}; max chin up {mx[0]}, clavicle down '
          f'{mx[1]}, arm down {mx[2]}, head away {mx[3]} deg; worst remaining depth {max(left) * 100:.1f} cm')



for nm in ('Fidget','Death'):head_fix(nm)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/motion_head_fixed.blend'))
