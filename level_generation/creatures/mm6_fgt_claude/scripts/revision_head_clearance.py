"""Apply the existing Claude head-clearance solver to the revised death pose, preserving every other channel."""
from pathlib import Path
import bpy,sys,math,numpy as np
from mathutils import Vector,Matrix
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'))
from g6_head_clearance import Clearance
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_revision1.blend'))
scene=bpy.context.scene;rig=bpy.data.objects['Rig'];names=[b.name for b in rig.pose.bones]
CL=Clearance(bpy.data.objects['Body']);DEPTH=.003;W_=rig.matrix_world

def write(name,frames):
 act=bpy.data.actions[name];set_act(act);prev={}
 for i,pose in enumerate(frames):
  for n in ['B_Neck','B_Head']:
   q,l=pose[n];pb=rig.pose.bones[n]
   if n in prev and q.dot(prev[n])<0:q=-q
   prev[n]=q.copy();pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=i)
 for layer in act.layers:
  for strip in layer.strips:
   for cb in strip.channelbags:
    for fc in cb.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
 set_act(None)

def set_act(a):
    rig.animation_data_create(); rig.animation_data.action = a
    if a is not None and getattr(a, 'slots', None) is not None and len(a.slots):
        rig.animation_data.action_slot = a.slots[0]

def sample(act, f):
    set_act(act); scene.frame_set(int(f), subframe=f - int(f))
    return {n: (rig.pose.bones[n].rotation_quaternion.copy(), rig.pose.bones[n].location.copy()) for n in names}

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
        turn_world(f'B_{side}_Clavicle', (sh - cl).cross(Vector((0, 0, 1))).normalized(), -c[1])   # + lifts
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
    CAP = np.radians([15, 0, 0, 10]); COST = np.array([1.0, 0.7, 2.0, 1.5]); STEP = math.radians(2.5)
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

head_fix('Death')
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_revision1.blend'))
