import bpy, sys, os, math, json
import numpy as np
from mathutils import Quaternion, Vector, Matrix
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPS = 30
LEAD = 0.15                     # ready pause (2026-10-11 slash: 0.15 s puts its slice at the native 0.75 s wind-up)
TWIST_FREE, TWIST_MAX = math.radians(25), math.radians(45)
SPINE = ('B_Spine', 'B_Spine1', 'B_Spine2')
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'rig_grip.blend'))
scene = bpy.context.scene; scene.render.fps = FPS; scene.render.fps_base = 1
rig = bpy.data.objects['Rig']
names = [b.name for b in rig.data.bones]


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



# Native ranged action: reach/nock/draw followed by the locally owned recoil.
def blend(a,b,t):
    return {n:(a[n][0].slerp(b[n][0],t),a[n][1].lerp(b[n][1],t)) for n in names}
for suffix in ('','Full'):
    a=bpy.data.actions['Draw'+suffix]; b=bpy.data.actions['Release'+suffix]
    frames=[sample(a,f) for f in range(int(a.frame_range[1])+1)]
    second=[sample(b,f) for f in range(int(b.frame_range[1])+1)]
    for f in range(4):
        second[f]=blend(frames[-1],second[f],smooth((f+1)/4))
    write('Attack'+suffix,frames+second[1:])

# ---------------------------------------------------------------- partial leg motion on planted clips
# The planted attack and battle cry (retarget_mixamo.py :plant) froze the legs (user: "some leg movement?"). The chain
# also retargets them unplanted (<name>Full: the source's lunge/stagger, pelvis up to ~25 cm lower). Pelvis (location
# and rotation) and leg bones take LEG_KEEP of the unplanted motion; the upper body stays as planted relative to the
# pelvis, except B_Spine, which keeps its planted WORLD orientation (the trunk stays upright; only hips and legs move).
# Then the pelvis moves vertically so the lowest foot point (ankle or toe against its rest height) lifts as
# LEG_KEEP of the unplanted clip's - feet stay on the floor.
LEAN_KEEP = {'Attack': 1.0}      # the slash leans the trunk 31-40 deg forward throughout (fencing hunch); walk/run 3-6
LEG_KEEP = 0.2                  # 0.35 of the slash's fencing crouch straddled the feet and tipped the trunk forward
LEGS = [n for n in names if any(t in n for t in ('Thigh', 'Calf', 'Foot', 'Toe'))]
FEET = ('B_L_Foot', 'B_R_Foot', 'B_L_Toe0', 'B_R_Toe0')
PEL_REST = rig.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted()


def foot_lift_of(act, f):
    set_act(act); scene.frame_set(int(f), subframe=f - int(f))
    return min((rig.matrix_world @ rig.pose.bones[n].head).z - REST_FOOT[n] for n in FEET)


set_act(None)
for pb in rig.pose.bones:
    pb.matrix_basis = Matrix()
bpy.context.view_layer.update()
REST_FOOT = {n: (rig.matrix_world @ rig.pose.bones[n].head).z for n in FEET}
for nm in ('Attack', 'Fidget'):
    full = bpy.data.actions.get(nm + 'Full')
    if full is None:
        continue
    planted = bpy.data.actions[nm]
    n = int(planted.frame_range[1])
    poses = []
    for f in range(n + 1):
        pp, pf = sample(planted, f), sample(full, f)
        pose = dict(pp)
        for b in ['B_Pelvis'] + LEGS:
            q0, q1 = pp[b][0], pf[b][0]
            if q0.dot(q1) < 0:
                q1 = -q1
            pose[b] = (q0.slerp(q1, LEG_KEEP), pp[b][1].lerp(pf[b][1], LEG_KEEP))
        poses.append(pose)
    tmp = write(nm + 'Tmp', poses)
    worst = 0.0
    for f, pose in enumerate(poses):
        dz = LEG_KEEP * foot_lift_of(full, f) - foot_lift_of(tmp, f)
        q, l = pose['B_Pelvis']; pose['B_Pelvis'] = (q, l + PEL_REST @ Vector((0, 0, dz)))
        worst = max(worst, abs(dz))
    bpy.data.actions.remove(tmp); bpy.data.actions.remove(full)
    # Foot targets: the blended ankles carry the source's own foot pops (the slash's right ankle jumps ~10 cm sideways
    # for two frames where its step starts; user: right foot jiggles). Per axis a 5-frame median removes pops, then a
    # Gaussian (sigma 1.5 frames) smooths; foot rotations are window-averaged. Two-bone IK puts each ankle on its
    # target (knee bend plane kept), the foot takes the smoothed world rotation.
    def apply(pose):
        set_act(None)
        for b, (q, l) in pose.items():
            pb = rig.pose.bones[b]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = q; pb.location = l
        bpy.context.view_layer.update()
    WM = lambda b: rig.matrix_world @ rig.pose.bones[b].matrix
    ank = {sd: [] for sd in 'LR'}; frot = {sd: [] for sd in 'LR'}
    for pose in poses:
        apply(pose)
        for sd in 'LR':
            m = WM(f'B_{sd}_Foot'); ank[sd].append(np.array(m.translation)); frot[sd].append(m.to_quaternion())
    nf = len(poses)
    gk = np.exp(-0.5 * (np.arange(-4, 5) / 1.5) ** 2); gk /= gk.sum()
    tgt, trot = {}, {}
    for sd in 'LR':
        A = np.array(ank[sd])
        med = np.array([np.median(A[max(0, i - 2):i + 3], axis=0) for i in range(nf)])
        pad = np.concatenate([np.repeat(med[:1], 4, 0), med, np.repeat(med[-1:], 4, 0)])
        tgt[sd] = [Vector(sum(gk[j] * pad[i + j] for j in range(9))) for i in range(nf)]
        qs = frot[sd]; out = []
        for i in range(nf):
            acc = Quaternion((0, 0, 0, 0))
            for j in range(-2, 3):
                q = qs[min(max(i + j, 0), nf - 1)]
                acc = acc + (q if q.dot(qs[i]) >= 0 else -q) * float(np.exp(-0.5 * (j / 1.0) ** 2))
            out.append(acc.normalized())
        trot[sd] = out
    # Steps instead of gliding: a foot stays at home (frame 0) until its smoothed target leaves by > STEP_MIN, steps
    # (STEP_FRAMES, sine lift STEP_LIFT) onto its target at the blow frame, holds it, and steps home over the last
    # STEP_FRAMES + 2 frames; a foot that never leaves by STEP_MIN stays planted at home.
    STEP_MIN, STEP_FRAMES, STEP_LIFT, STEP_MAX = 0.03, 6, 0.03, 0.15
    set_act(planted); scene.frame_set(0)                     # home = the Standing foot (planted frame 0)
    HOME = {sd: (WM(f'B_{sd}_Foot').translation.copy(), WM(f'B_{sd}_Foot').to_quaternion()) for sd in 'LR'}
    set_act(None)
    plan = {}
    for sd in 'LR':
        home = HOME[sd][0]
        off = [(t - home).length for t in tgt[sd]]
        if max(off) <= STEP_MIN:
            continue
        km = int(np.argmax(off))
        hold = sum((tgt[sd][i] for i in range(max(0, km - 3), min(nf, km + 4))), Vector()) / len(range(max(0, km - 3), min(nf, km + 4)))
        dv = hold - home; dv.z = 0.0
        if dv.length > STEP_MAX:
            dv *= STEP_MAX / dv.length
        plan[sd] = (next(i for i in range(nf) if off[i] > STEP_MIN), home + dv)
    # one foot in the air at a time: the second step starts when the first has landed; returns in reverse order
    order = sorted(plan, key=lambda sd: plan[sd][0])
    back_end = nf - 1
    for rank, sd in enumerate(order):
        k0 = plan[sd][0] if rank == 0 else max(plan[sd][0], plan[order[0]][0] + STEP_FRAMES)
        b1 = back_end - rank * STEP_FRAMES if len(order) > 1 else back_end
        b0 = b1 - STEP_FRAMES
        plan[sd] = (k0, plan[sd][1], b0, b1)
    for sd in 'LR':
        home, hq = HOME[sd]
        if sd not in plan:
            tgt[sd] = [home.copy() for _ in range(nf)]; trot[sd] = [hq.copy() for _ in range(nf)]
            continue
        k0, hold, b0, b1 = plan[sd]
        nt = []
        for i in range(nf):
            if i <= k0 or i >= b1:
                u, a_, b_ = 0.0, home, hold
            elif i < k0 + STEP_FRAMES:
                u, a_, b_ = (i - k0) / STEP_FRAMES, home, hold
            elif i < b0:
                u, a_, b_ = 1.0, home, hold
            else:
                u, a_, b_ = (i - b0) / (b1 - b0), hold, home
            p_ = a_.lerp(b_, smooth(u)); p_.z = home.z + (STEP_LIFT * math.sin(math.pi * u) if 0 < u < 1 else 0.0)
            nt.append(p_)
        tgt[sd], trot[sd] = nt, [hq.copy() for _ in range(nf)]
        print(f'STEP {nm} {sd}: out {k0}-{k0 + STEP_FRAMES}, hold {100 * (hold - home).length:.1f} cm from home, back {b0}-{b1}')
    jump = max((tgt[sd][i] - Vector(ank[sd][i])).length for sd in 'LR' for i in range(nf))
    print(f'FEET {nm}: largest ankle correction {100 * jump:.1f} cm')
    def aim(bone, direction):
        pb = rig.pose.bones[bone]; M = WM(bone); cur = (M.to_3x3() @ Vector((0, 1, 0))).normalized()
        R = cur.rotation_difference(direction.normalized()).to_matrix().to_4x4()
        t = M.translation.copy(); M = R @ M; M.translation = t
        pb.matrix = rig.matrix_world.inverted() @ M; bpy.context.view_layer.update()
    TOE_DIR = {}
    set_act(planted); scene.frame_set(0)
    for sd in 'LR':
        d = WM(f'B_{sd}_Toe0').translation - WM(f'B_{sd}_Foot').translation; d.z = 0.0; TOE_DIR[sd] = d.normalized()
    set_act(None)
    for f, pose in enumerate(poses):
        apply(pose)
        for sd in 'LR':
            th, ca, ft = f'B_{sd}_Thigh', f'B_{sd}_Calf', f'B_{sd}_Foot'
            H = WM(th).translation; K = WM(ca).translation; A0 = WM(ft).translation
            a, b = (K - H).length, (A0 - K).length
            T = tgt[sd][f]; d = min((T - H).length, (a + b) * 0.999); u = (T - H).normalized()
            # knee over the toes: the bend plane comes from the foot's forward (ankle -> toe, constant home rotation);
            # the blended knee carried the source's pop (thigh turned 7-8 deg in one viewer frame; user: thigh jiggles)
            fwd = (TOE_DIR[sd] - u * TOE_DIR[sd].dot(u))
            v = fwd.normalized() if fwd.length > 1e-6 else Vector((0, -1, 0))
            ca_ = (a * a + d * d - b * b) / (2 * a * d)
            Kn = H + a * (u * ca_ + v * math.sqrt(max(0.0, 1 - ca_ * ca_)))
            aim(th, Kn - H); aim(ca, T - WM(ca).translation)
            pb = rig.pose.bones[ft]; M = trot[sd][f].to_matrix().to_4x4(); M.translation = WM(ft).translation
            pb.matrix = rig.matrix_world.inverted() @ M; bpy.context.view_layer.update()
            for bn in (th, ca, ft):
                pose[bn] = (rig.pose.bones[bn].rotation_quaternion.copy(), pose[bn][1])
    for f, pose in enumerate(poses):
        set_act(planted); scene.frame_set(f)
        spine_world = (rig.matrix_world @ rig.pose.bones['B_Spine'].matrix).copy()
        set_act(None)
        for b, (q, l) in pose.items():
            pb = rig.pose.bones[b]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = q; pb.location = l
        bpy.context.view_layer.update()
        pb = rig.pose.bones['B_Spine']
        M = spine_world.copy(); M.translation = (rig.matrix_world @ pb.matrix).translation
        pb.matrix = rig.matrix_world.inverted() @ M
        bpy.context.view_layer.update()
        if nm in LEAN_KEEP:
            # trunk lean (spine -> neck, sagittal; the character faces -Y): keep LEAN_KEEP of it, pivot at B_Spine
            P = lambda b: rig.matrix_world @ rig.pose.bones[b].head
            d = P('B_Neck') - P('B_Spine'); lean = math.atan2(-d.y, d.z)
            M = rig.matrix_world @ pb.matrix; t = M.translation.copy()
            M = Matrix.Rotation(-(1 - LEAN_KEEP[nm]) * lean, 4, 'X') @ M; M.translation = t
            pb.matrix = rig.matrix_world.inverted() @ M
            bpy.context.view_layer.update()
        pose['B_Spine'] = (pb.rotation_quaternion.copy(), pose['B_Spine'][1])
    write(nm, poses)
    drop = []
    act = bpy.data.actions[nm]
    for f in range(n + 1):
        set_act(act); scene.frame_set(f); drop.append((rig.matrix_world @ rig.pose.bones['B_Pelvis'].head).z)
    print(f'LEGS {nm}: {LEG_KEEP:.2f} of the unplanted leg motion, floor fix max {100 * worst:.1f} cm, pelvis range '
          f'{100 * (max(drop) - min(drop)):.1f} cm')
set_act(None)


standing=sample(bpy.data.actions['Standing'],0)
# Gentle bow-side idle flourish; source Boost is retained without the strong backward bend.
boost=bpy.data.actions['Boost']
fidget=[blend(standing,sample(boost,f),0.28) for f in range(int(boost.frame_range[1])+1)]
write('Fidget',fidget)
# Fire Archer opens and extends the drawing hand for a palm-fired spell.
cast=[]
draw=bpy.data.actions['Draw']; target=sample(draw,draw.frame_range[1])
for f in range(37):
    t=smooth(f/15) if f<=18 else smooth((36-f)/18)
    pose=blend(standing,target,t)
    # A casting palm: open fingers, distinct from the nocked arrow release.
    for n in names:
        if n.startswith('B_R_Finger'):
            pose[n]=(Quaternion(),Vector())
    cast.append(pose)
write('Cast',cast)
for nm in ('Attack','Hit','Fidget','Cast','Death'):
    a=bpy.data.actions[nm]; nf=int(a.frame_range[1])+1
    poses=[sample(a,f) for f in range(nf)]
    for f in range(min(5,nf)):
        poses[f]=blend(standing,poses[f],smooth(f/4))
    if nm!='Death':
        for k in range(min(7,nf)):
            f=nf-1-k; poses[f]=blend(standing,poses[f],smooth(k/6))
    write(nm,poses)
write('Dead',[sample(bpy.data.actions['Death'],bpy.data.actions['Death'].frame_range[1])]*2)
keep={'Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget','Cast'}
for a in list(bpy.data.actions):
    if a.name not in keep:bpy.data.actions.remove(a)
set_act(bpy.data.actions['Standing']);scene.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE,'work','rig_clips.blend'))
print('CLIPS',[(a.name,list(a.frame_range)) for a in bpy.data.actions])
