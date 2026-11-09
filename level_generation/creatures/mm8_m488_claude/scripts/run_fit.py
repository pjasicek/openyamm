"""Running fit (bar1 review rounds 1-2, 2026-10-13: Mixamo Standard Run as the run, NOT crouched - the retarget's floor
correction put the pelvis ~19 cm low). natm review 1 (2026-10-14): the first fit replaced the legs with sine-lift foot
paths and read as "fast walking" - the feet now follow the SOURCE's own ankle paths (heel kick, knee drive, toe-off),
taken relative to the source pelvis, forward travel scaled to STRIDE, absolute heights kept, knees bent in the
source's own leg plane, the source foot rotation kept. Keeps the retargeted upper body/sway; replaces pelvis height:
- pelvis height = the original FBX hip bob (half-cycle averaged, smoothed, amplitude x0.45) anchored at PEL_MIN of the
  Standing pelvis height; pelvis x/y at Standing's (in place) with a small sway;
- feet: each foot a STANCE fraction on the floor travelling the STRIDE backwards at constant speed, then a Hermite
  return with a sine lift and toe-down pitch; two-bone IK with the knee bending over the toes;
- trunk lean set to LEAN deg forward (B_Spine about the lateral axis), keeping the source's twist/sway.
Writes the Running action in place (30 fps keys, cyclic: last = first). Args: -- <in blend> <out blend>"""
import bpy, sys, os, math, json
import numpy as np
from mathutils import Matrix, Vector, Quaternion
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import armik
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; scene = bpy.context.scene
STRIDE = float(os.environ.get('RUN_STRIDE', '1.8')); STANCE = 0.36; PEL_MIN = 0.92; LEAN = 13.0; LIFT = 0.22; BOB = 0.05


def set_act(a):
    rig.animation_data_create(); rig.animation_data.action = a
    if a is not None and len(a.slots): rig.animation_data.action_slot = a.slots[0]


set_act(bpy.data.actions['Standing']); scene.frame_set(0)
st_pel = armik.W(rig, 'B_Pelvis').translation.copy()
FEET = {sd: armik.W(rig, f'B_{sd}_Foot').copy() for sd in 'LR'}
TOES = {sd: armik.W(rig, f'B_{sd}_Toe0').translation.copy() for sd in 'LR'}
HEAD_FWD = armik.W(rig, 'B_Head').to_3x3().normalized().inverted() @ Vector((0, -1, 0))   # head-local forward at Standing
set_act(None)
# original FBX hip height profile
before_o, before_a = set(bpy.data.objects), set(bpy.data.actions)
bpy.ops.import_scene.fbx(filepath='/home/pjasicek/github/OpenYAMM/anim_library/mixamo/Standard Run.fbx')
srcarm = next(o for o in set(bpy.data.objects) - before_o if o.type == 'ARMATURE')
hips = next(b.name for b in srcarm.data.bones if b.name.endswith('Hips'))
s0, s1 = srcarm.animation_data.action.frame_range
zs = []
for f in range(int(s0), int(s1)):
    scene.frame_set(f); zs.append((srcarm.matrix_world @ srcarm.pose.bones[hips].head).z)
for o in set(bpy.data.objects) - before_o: bpy.data.objects.remove(o, do_unlink=True)
for a in set(bpy.data.actions) - before_a: bpy.data.actions.remove(a)
scene.render.fps = 30; scene.render.fps_base = 1
bob = np.array(zs); bob = (bob + np.roll(bob, len(bob) // 2)) / 2; bob = (np.roll(bob, 1) + 2 * bob + np.roll(bob, -1)) / 4
bob = (bob - bob.min()) / max(1e-6, (bob.max() - bob.min())) * BOB           # source timing/shape
run = bpy.data.actions['Running']; n = int(run.frame_range[1])                 # 22 intervals
ncyc = len(bob)
SRCP = []                                                              # source pelvis, ankles, knees, foot rotations
for f in range(n + 1):
    set_act(run); scene.frame_set(f)
    SRCP.append({'P': armik.W(rig, 'B_Pelvis').translation.copy(),
                 **{sd: (armik.W(rig, f'B_{sd}_Foot').translation.copy(), armik.W(rig, f'B_{sd}_Calf').translation.copy(),
                         armik.W(rig, f'B_{sd}_Thigh').translation.copy(), armik.W(rig, f'B_{sd}_Foot').to_3x3().normalized())
                    for sd in 'LR'}})
set_act(None)
# source stride: planted-foot backward speed x cycle time
vy = []
for sd in 'LR':
    A = np.array([tuple(x[sd][0]) for x in SRCP]); z = A[:, 2]; low = z < z.min() + 0.015
    vy.append(np.median(np.gradient(A[:, 1])[low]) * 30)
src_stride = float(np.mean(vy)) * n / 30
KY = STRIDE / max(src_stride, 1e-3)
print('RUNFIT source stride', round(src_stride, 3), 'm -> scale', round(KY, 3))
# constant yaw from the source foot onto the home foot, measured over the stance frames (foot low) where the foot is
# nearly level (a per-frame yaw flipped 60-100 deg when the foot pointed down at toe-off)
YAWFIX = {}
for sd in 'LR':
    hp = FEET[sd].translation; fwd_h = TOES[sd] - hp; yh = math.atan2(fwd_h.x, -fwd_h.y)
    zs = [x[sd][0].z for x in SRCP]; zmin = min(zs); ys = []
    for x in SRCP:
        if x[sd][0].z < zmin + 0.02:
            fw = x[sd][3] @ (FEET[sd].to_3x3().normalized().inverted() @ fwd_h)
            ys.append(math.atan2(fw.x, -fw.y))
    YAWFIX[sd] = yh - float(np.median(ys))
print('RUNFIT foot yaw fix deg', {k: round(math.degrees(v), 1) for k, v in YAWFIX.items()})
body = bpy.data.objects['Body']; vgn = [g.name for g in body.vertex_groups]
FOOTV = {sd: np.array([sum(e.weight for e in v.groups if vgn[e.group] in (f'B_{sd}_Foot', f'B_{sd}_Toe0')) > 0.5 for v in body.data.vertices]) for sd in 'LR'}
floor_fix = []
poses = []
for f in range(n):
    set_act(run); scene.frame_set(f)
    snap = {pb.name: pb.matrix_basis.copy() for pb in rig.pose.bones}
    set_act(None)
    for pb in rig.pose.bones: pb.matrix_basis = snap[pb.name]
    bpy.context.view_layer.update()
    Mp = armik.W(rig, 'B_Pelvis')
    Mp.translation = Vector((st_pel.x + 0.012 * math.sin(2 * math.pi * f / n), st_pel.y,
                             st_pel.z * PEL_MIN + float(np.interp(f * ncyc / n, np.arange(ncyc + 1), np.r_[bob, bob[0]]))))
    armik.set_world(rig, 'B_Pelvis', Mp)
    d = armik.W(rig, 'B_Neck').translation - armik.W(rig, 'B_Spine').translation
    lean = math.atan2(-d.y, d.z)
    M = armik.W(rig, 'B_Spine'); t = M.translation.copy(); M = Matrix.Rotation(math.radians(LEAN) - lean, 4, 'X') @ M; M.translation = t
    armik.set_world(rig, 'B_Spine', M)
    # level the gaze: the source runner looks ahead through a 25-30 deg lean; after the lean change the face pointed up
    hf = armik.W(rig, 'B_Head').to_3x3() @ HEAD_FWD
    pitch_up = math.atan2(hf.z, math.hypot(hf.x, hf.y)) + math.radians(4)           # aim 4 deg below level
    lat = Vector((hf.y, -hf.x, 0)).normalized()                                      # head's right-hand lateral axis
    for b_, share in (('B_Neck', 0.5), ('B_Head', 1.0)):
        cur = armik.W(rig, 'B_Head').to_3x3() @ HEAD_FWD
        pu = math.atan2(cur.z, math.hypot(cur.x, cur.y)) + math.radians(4)
        M = armik.W(rig, b_); t = M.translation.copy()
        M = Matrix.Rotation(-pu * share, 4, lat) @ M; M.translation = t; armik.set_world(rig, b_, M)
    Pn = armik.W(rig, 'B_Pelvis').translation.copy(); src = SRCP[f]

    def solve_leg(sd, lift=0.0):
        A, K, Hs, Rf = src[sd]
        home = FEET[sd]; hp = home.translation
        target = Vector((hp.x, Pn.y + (A.y - src['P'].y) * KY, A.z + lift))
        th, ca, ft = f'B_{sd}_Thigh', f'B_{sd}_Calf', f'B_{sd}_Foot'
        H = armik.W(rig, th).translation; K_ = armik.W(rig, ca).translation; A_ = armik.W(rig, ft).translation
        a_, b_ = (K_ - H).length, (A_ - K_).length
        dist = min((target - H).length, (a_ + b_) * 0.999); u_ = (target - H).normalized()
        su = (A - Hs).normalized(); kv = (K - Hs) - su * (K - Hs).dot(su)
        fw = kv.normalized() if kv.length > 0.01 else Vector((0, -1, 0))
        vv = (fw - u_ * fw.dot(u_)).normalized()
        c = (a_ * a_ + dist * dist - b_ * b_) / (2 * a_ * dist)
        Kn = H + a_ * (u_ * c + vv * math.sqrt(max(0, 1 - c * c)))
        for bone, direction in ((th, Kn - H), (ca, None)):
            M = armik.W(rig, bone); cur = (armik.W(rig, ca if bone==th else ft).translation-M.translation).normalized()
            if direction is None: direction = (H + u_ * dist) - M.translation
            R = cur.rotation_difference(direction.normalized()).to_matrix(); t = M.translation.copy()
            M = R.to_4x4() @ M; M.translation = t; armik.set_world(rig, bone, M)
        R = Matrix.Rotation(YAWFIX[sd], 3, 'Z') @ Rf                     # one constant yaw per foot (per-frame flipped)
        armik.set_world(rig, ft, armik.rot_world(armik.W(rig, ft), R))
        rig.pose.bones[f'B_{sd}_Toe0'].matrix_basis = Matrix(); bpy.context.view_layer.update()
    lift = {'L': 0.0, 'R': 0.0}
    for it in range(3):
        for sd in 'LR':
            solve_leg(sd, lift[sd])
        ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); mm = ev.to_mesh()
        zz = np.array([(body.matrix_world @ v.co).z for v in mm.vertices]); ev.to_mesh_clear()
        low = {sd: float(zz[FOOTV[sd]].min()) for sd in 'LR'}
        if min(low.values()) > -0.003:
            break
        for sd in 'LR':
            if low[sd] < -0.003:
                lift[sd] += -low[sd]
    floor_fix.append(max(lift.values()))
    # arms out a little (clear the hips / skirt), the carry step solves the spear arm later
    for sd, sign in (('L', -1), ('R', 1)):
        M = armik.W(rig, f'B_{sd}_UpperArm'); t = M.translation.copy()
        M = Matrix.Rotation(sign * math.radians(7), 4, 'Y') @ M; M.translation = t
        armik.set_world(rig, f'B_{sd}_UpperArm', M)
    poses.append({pb.name: (pb.rotation_quaternion.copy(), pb.location.copy()) for pb in rig.pose.bones})
poses.append(poses[0])
bpy.data.actions.remove(run)
act = bpy.data.actions.new('Running'); act.use_fake_user = True; set_act(act)
prev = {}
for f, pose in enumerate(poses):
    for nme, (q, l) in pose.items():
        pb = rig.pose.bones[nme]; pb.rotation_mode = 'QUATERNION'
        if nme in prev and q.dot(prev[nme]) < 0: q = -q
        prev[nme] = q; pb.rotation_quaternion = q; pb.location = l
        pb.keyframe_insert('rotation_quaternion', frame=f)
        if nme == 'B_Pelvis': pb.keyframe_insert('location', frame=f)
act.use_frame_range = True; act.frame_start, act.frame_end = 0, n
set_act(None)
print(f'RUNFIT floor lift max {max(floor_fix) * 100:.1f} cm; frames {n + 1}, stride {STRIDE} m, stance {STANCE}, pelvis {PEL_MIN * 100:.0f}% of Standing + bob {BOB * 100:.0f} cm, lean {LEAN} deg')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
