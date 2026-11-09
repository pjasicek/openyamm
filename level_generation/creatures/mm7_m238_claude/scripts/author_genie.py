"""The genie's clips over the retargeted humanoid-set sources (IdleSrc = Unarmed Idle, AttackSrc = Unarmed Cast Dual
Summon 1, HitSrc = Unarmed Get Hit B1; G1 review/g1/G1.md). She has no legs: the pelvis floats at a steady hover
(HOVER above the rest, a +-BOB breath), the source legs are ignored (they carry no weight), and the vortex chain
(vortex.py) sways in every clip: per bone a rotation about the world X and Y axes, its amplitude growing toward the tip
with a phase lag down the chain (a soft chain), plus a trailing bend when she travels.
- FOLD (Standing, Walking, Fidget): both arms folded across the chest under the bust as in the native wa frames, by a
  two-bone IK in the chest frame (wrist targets beside the opposite elbow, elbows out and down); hands straight on the
  forearm; fingers keep the idle's.
- Standing: IdleSrc's upper body (breathing) + FOLD + hover + sway (its own length, a loop).
- Walking (1.2 s loop, the native walk is the same folded float): Standing + forward lean LEAN, head kept level, the
  vortex trailing back.
- Fidget (2.0 s): Standing + a head turn to each side and a small shrug (the native fidget keeps the arms folded).
- Attack (also cast and ranged): ease from Standing into AttackSrc, the source as far as its highest hands, a HOLD with
  the hands overhead (the native spark arc between them), then the rest and an ease back; the pelvis keeps the hover
  (its source drop and turn damped). IMPACT = the end of the hold (the release), printed for actors.yml.
- Hit: HitSrc with the hover kept, eased from and back to Standing.
- Death (native: a cloud bursts, she rises and vanishes, a lamp drops): arms up as in the cast, rise, a spin that speeds
  up while the whole body (B_Pelvis scale) shrinks away into the vortex; the lamp (bone 'Lamp', no parent, rest on the
  floor) appears at hip height and falls with gravity, bounces once and settles. Dead = the end (export_runtime.py).
  In every other clip the Lamp bone is scaled to LAMP_HIDE (model_hide_collapsed_meshes.py then hides that mesh).
Sockets 'Socket_Palm_L/R' (children of the hands, on the palm) carry the cast's glow; the release is between them.
Args: -- <in blend> <out blend>"""
import bpy, sys, os, math, json
import numpy as np
from mathutils import Matrix, Vector, Quaternion
src, out = sys.argv[sys.argv.index('--') + 1:]
E = lambda k, d: float(os.environ.get(k, d))
FPS = 30
HOVER, BOB, LEAN, HOLD = E('HOVER', 0.03), E('BOB', 0.015), E('LEAN', 15), E('HOLD', 0.25)
LAMP_HIDE = 1e-4
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
scene = bpy.context.scene; scene.render.fps = FPS
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']
VT = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'work', 'vortex.json')))
VORTEX = VT['bones']


def set_act(a):
    rig.animation_data_create(); rig.animation_data.action = a
    if a is not None and getattr(a, 'slots', None) is not None and len(a.slots):
        rig.animation_data.action_slot = a.slots[0]


# ---------------------------------------------------------------- extra bones: lamp and palm sockets
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones
LAMP_REST = Vector((0.10, -0.20, 0.0))
lb = eb.get('Lamp') or eb.new('Lamp'); lb.head = LAMP_REST; lb.tail = LAMP_REST + Vector((0, 0, 0.12)); lb.parent = None
lb.use_deform = True
for s in 'LR':
    h = eb[f'B_{s}_Hand'].head.copy(); m1 = eb[f'B_{s}_Finger2'].head.copy(); i1 = eb[f'B_{s}_Finger1'].head.copy()
    p4 = eb[f'B_{s}_Finger4'].head.copy()
    palm = (m1 - h).cross(i1 - p4).normalized()
    # the palm side faces the body in the A-pose rest (toward x = 0)
    if palm.x * (1 if s == 'L' else -1) > 0:
        palm = -palm
    c = h + (m1 - h) * 0.55 + palm * 0.02
    sb = eb.get(f'Socket_Palm_{s}') or eb.new(f'Socket_Palm_{s}')
    sb.head = c; sb.tail = c + palm * 0.05; sb.parent = eb[f'B_{s}_Hand']; sb.use_deform = False
bpy.ops.object.mode_set(mode='OBJECT')
names = [b.name for b in rig.data.bones]


def snapshot(act, f):
    for pb in rig.pose.bones:                                  # bones the action does not key (vortex, lamp, sockets)
        pb.matrix_basis.identity()                             # would otherwise keep the previous frame's pose
    set_act(act); scene.frame_set(int(f), subframe=f - int(f))
    snap = {pb.name: pb.matrix_basis.copy() for pb in rig.pose.bones}
    set_act(None)                                              # later pose edits must not be re-evaluated away
    return snap


def apply(snap):
    for pb in rig.pose.bones:
        if pb.name in snap:
            pb.matrix_basis = snap[pb.name].copy()
        else:
            pb.matrix_basis.identity()
    bpy.context.view_layer.update()


def lerp_snap(a, b, t):
    out = {}
    for n in a:
        la, ra, sa = a[n].decompose(); lb_, rb, sb_ = b[n].decompose()
        out[n] = Matrix.LocRotScale(la.lerp(lb_, t), ra.slerp(rb, t), sa.lerp(sb_, t))
    return out


def W(n):
    return rig.matrix_world @ rig.pose.bones[n].matrix


def rot_world(n, deg, axis):
    if abs(deg) < 1e-6:
        return
    bpy.context.view_layer.update()
    pb = rig.pose.bones[n]; M = rig.matrix_world @ pb.matrix; h = M.translation.copy()
    R = Matrix.Rotation(math.radians(deg), 4, Vector(axis))
    pb.matrix = rig.matrix_world.inverted() @ (Matrix.Translation(h) @ R @ Matrix.Translation(-h) @ M)


def aim(n, target_dir):
    """turn bone n (about its head, the least) so its +Y points along target_dir (world)"""
    bpy.context.view_layer.update()
    pb = rig.pose.bones[n]; M = rig.matrix_world @ pb.matrix; h = M.translation.copy()
    cur = (M.to_3x3() @ Vector((0, 1, 0))).normalized()
    q = cur.rotation_difference(target_dir.normalized())
    pb.matrix = rig.matrix_world.inverted() @ (Matrix.Translation(h) @ q.to_matrix().to_4x4() @ Matrix.Translation(-h) @ M)


IDLE, ATK, HIT = bpy.data.actions['IdleSrc'], bpy.data.actions['AttackSrc'], bpy.data.actions['HitSrc']
for pb in rig.pose.bones:
    pb.rotation_mode = 'QUATERNION'
REST_PEL = rig.data.bones['B_Pelvis'].head_local.copy()
Pel_rest_inv = rig.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted()
CH_REST = rig.data.bones['B_Spine2'].matrix_local.copy()
# folded-arm wrist targets and elbow hints in the REST chest frame (character faces -Y, her right = -X)
UA = {s: (rig.data.bones[f'B_{s}_Forearm'].head_local - rig.data.bones[f'B_{s}_UpperArm'].head_local).length for s in 'LR'}
FA = {s: (rig.data.bones[f'B_{s}_Hand'].head_local - rig.data.bones[f'B_{s}_Forearm'].head_local).length for s in 'LR'}
SH = {s: rig.data.bones[f'B_{s}_UpperArm'].head_local.copy() for s in 'LR'}
FOLD_Z = E('FOLD_Z', -0.14); FOLD_Y = E('FOLD_Y', -0.31)   # under the bust as wa0; G6: y -0.22 put the left forearm 6 cm into the waist
# her right forearm on top (closer to the chest front), the left under it
WR = {'R': Vector((0.04, FOLD_Y - 0.01, SH['R'].z + FOLD_Z + 0.025)), 'L': Vector((-0.04, FOLD_Y + 0.01, SH['L'].z + FOLD_Z - 0.025))}
PB, PD = E('POLE_BACK', -0.15), E('POLE_DOWN', 0.3)    # elbows out and slightly forward (G6)
POLE = {'R': Vector((-1.0, PB, -PD)), 'L': Vector((1.0, PB, -PD))}
CH_INV = CH_REST.inverted()
WR_CH = {s: CH_INV @ WR[s] for s in 'LR'}
POLE_CH = {s: CH_INV.to_3x3() @ POLE[s] for s in 'LR'}


def fold(weight=1.0):
    """two-bone IK of both arms to the folded targets carried by the posed chest; weight blends from the current arm"""
    if weight <= 0:
        return
    bpy.context.view_layer.update()
    C = W('B_Spine2')
    for s in 'LR':
        S = W(f'B_{s}_UpperArm').translation.copy()
        cur_wrist = W(f'B_{s}_Hand').translation.copy()
        T = (C @ WR_CH[s]).lerp(cur_wrist, 1 - weight) if weight < 1 else C @ WR_CH[s]
        pole = (C.to_3x3() @ POLE_CH[s]).normalized()
        a, b = UA[s], FA[s]; dv = T - S; d = min(dv.length, a + b - 1e-4); u = dv.normalized()
        v = (pole - u * pole.dot(u)).normalized()
        ca = (a * a + d * d - b * b) / (2 * a * d); sa = math.sqrt(max(0.0, 1 - ca * ca))
        El = S + (u * ca + v * sa) * a
        aim(f'B_{s}_UpperArm', El - S)
        bpy.context.view_layer.update()
        aim(f'B_{s}_Forearm', (S + u * d) - W(f'B_{s}_Forearm').translation)
        rig.pose.bones[f'B_{s}_Hand'].rotation_quaternion = Quaternion()   # straight on the forearm


def hover(t, period, extra=Vector((0, 0, 0)), keep_xy=0.0, src_loc=None):
    """pelvis location: the rest height + HOVER + a breath, plus `extra` (world); keep_xy of the source's own offset"""
    pb = rig.pose.bones['B_Pelvis']
    world = Vector((0, 0, HOVER + BOB * math.sin(2 * math.pi * t / period))) + extra
    if src_loc is not None:
        sw = rig.data.bones['B_Pelvis'].matrix_local.to_3x3() @ src_loc
        world += Vector((sw.x * keep_xy, sw.y * keep_xy, 0))
    pb.location = Pel_rest_inv @ world


def sway(t, period, trail=0.0, amp=4.0, speed=1.0):
    """per bone rotations that accumulate down the chain: the tip bends ~trail + amp degrees in total"""
    n = len(VORTEX); wsum = sum((i + 1) / n for i in range(n))
    for i, bn in enumerate(VORTEX):
        k = (i + 1) / n / wsum
        ph = 2 * math.pi * speed * t / period - 0.55 * i
        rot_world(bn, trail * k + amp * k * math.sin(ph), (1, 0, 0))
        rot_world(bn, 0.7 * amp * k * math.cos(ph), (0, 1, 0))


LAMP_R = None


def lamp(scale=LAMP_HIDE, loc=Vector((0, 0, 0)), rot=Quaternion()):
    """loc and rot in world axes (the Lamp bone's rest +Y points up, so its local axes differ)"""
    R = rig.data.bones['Lamp'].matrix_local.to_3x3()
    pb = rig.pose.bones['Lamp']; pb.rotation_mode = 'QUATERNION'
    pb.scale = (scale, scale, scale); pb.location = R.inverted() @ loc
    pb.rotation_quaternion = (R.inverted() @ rot.to_matrix() @ R).to_quaternion()


def key(act, f):
    for pb in rig.pose.bones:
        pb.rotation_mode = 'QUATERNION'
        pb.keyframe_insert('rotation_quaternion', frame=f); pb.keyframe_insert('location', frame=f)
        pb.keyframe_insert('scale', frame=f)


def build(name, n_frames, pose_fn):
    act = bpy.data.actions.get(name)
    if act is not None:
        bpy.data.actions.remove(act)
    act = bpy.data.actions.new(name); act.use_fake_user = True
    frames = []
    for f in range(n_frames):
        pose_fn(f / FPS)
        frames.append({pb.name: (pb.rotation_quaternion.copy(), pb.location.copy(), pb.scale.copy()) for pb in rig.pose.bones})
    set_act(act)
    prev = {}
    for f, fr in enumerate(frames):
        for pb in rig.pose.bones:
            q, l, s = fr[pb.name]
            if pb.name in prev and q.dot(prev[pb.name]) < 0:
                q = -q
            prev[pb.name] = q
            pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = q; pb.location = l; pb.scale = s
        key(act, f)
    set_act(None)
    print('CLIP', name, 'frames', n_frames, 's', round((n_frames - 1) / FPS, 3))
    return act


n_idle = int(IDLE.frame_range[1] - IDLE.frame_range[0])
IDLE_T = n_idle / FPS


def standing_pose(t, fold_w=1.0):
    f = IDLE.frame_range[0] + (t * FPS) % n_idle
    snap = snapshot(IDLE, f); apply(snap)
    hover(t, IDLE_T)
    bpy.context.view_layer.update()
    fold(fold_w)
    lamp()


def standing(t):
    standing_pose(t); sway(t, IDLE_T, amp=10.0)


build('Standing', n_idle + 1, standing)
STAND0 = None
standing(0.0); bpy.context.view_layer.update()
STAND0 = {pb.name: pb.matrix_basis.copy() for pb in rig.pose.bones}

WALK_T = 1.2


def walking(t):
    standing_pose(t * IDLE_T / WALK_T)
    hover(t, WALK_T / 2)
    rot_world('B_Pelvis', LEAN, (1, 0, 0))
    rot_world('B_Neck', -0.5 * LEAN, (1, 0, 0)); rot_world('B_Head', -0.4 * LEAN, (1, 0, 0))
    bpy.context.view_layer.update(); fold(1.0)
    sway(t, WALK_T, trail=22.0, amp=10.0)


build('Walking', int(WALK_T * FPS) + 1, walking)
FID_T = 2.0


def ss(x):
    x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)


def fidget(t):
    standing_pose(t)
    u = t / FID_T
    yaw = 28 * math.sin(2 * math.pi * u) * math.sin(math.pi * u)
    rot_world('B_Spine2', 0.25 * yaw, (0, 0, 1)); rot_world('B_Head', 0.75 * yaw, (0, 0, 1))
    shrug = 6 * math.sin(math.pi * ss(u * 2 - 0.5)) if 0.25 < u < 0.75 else 0.0
    for s, sg in (('L', -1), ('R', 1)):
        rot_world(f'B_{s}_Clavicle', sg * shrug, (0, 1, 0))
    bpy.context.view_layer.update(); fold(1.0)
    sway(t, IDLE_T, amp=10.0)


build('Fidget', int(FID_T * FPS) + 1, fidget)

# ---------------------------------------------------------------- attack / cast
a0, a1 = int(ATK.frame_range[0]), int(ATK.frame_range[1])
hz = []
for f in range(a0, a1 + 1):
    apply(snapshot(ATK, f)); hz.append(W('B_L_Hand').translation.z + W('B_R_Hand').translation.z)
k_top = a0 + int(np.argmax(hz))
LEAD_IN, BLEND_OUT = 0.15, 0.3
nl, nh, nb = int(LEAD_IN * FPS), int(HOLD * FPS), int(BLEND_OUT * FPS)
src_frames = list(range(a0, k_top + 1)) + [k_top] * nh + list(range(k_top + 1, a1 + 1))
total = nl + len(src_frames) + nb
IMPACT = (nl + (k_top - a0) + nh) / FPS


def damp_pelvis(snap, keep=0.5):
    q = snap['B_Pelvis'].to_quaternion(); l = snap['B_Pelvis'].translation.copy()
    snap['B_Pelvis'] = Matrix.LocRotScale(Vector((0, 0, 0)), Quaternion().slerp(q, keep), Vector((1, 1, 1)))
    return l


def attack(t):
    f = int(round(t * FPS))
    if f < nl:
        s1 = snapshot(ATK, a0); l = damp_pelvis(s1)
        snap = lerp_snap(STAND0, s1, ss(f / max(nl, 1)))
    elif f < nl + len(src_frames):
        snap = snapshot(ATK, src_frames[f - nl]); l = damp_pelvis(snap)
        if src_frames[f - nl] == k_top:                        # the hold: a small tremble of the raised hands
            pass
    else:
        s1 = snapshot(ATK, a1); l = damp_pelvis(s1)
        snap = lerp_snap(s1, STAND0, ss((f - nl - len(src_frames) + 1) / max(nb, 1)))
    apply(snap)
    hover(t, IDLE_T, src_loc=l if f >= nl else None, keep_xy=0.3)
    lamp(); sway(t, IDLE_T, amp=14.0, speed=1.5)


build('Attack', total, attack)
print('IMPACT attack/cast release', round(IMPACT, 3), 's of', round((total - 1) / FPS, 3), 's; hands highest at source frame', k_top)

# ---------------------------------------------------------------- hit
h0, h1 = int(HIT.frame_range[0]), int(HIT.frame_range[1])
HIN, HOUT = 3, 6
hit_total = HIN + (h1 - h0 + 1) + HOUT


def hit(t):
    f = int(round(t * FPS))
    if f < HIN:
        s1 = snapshot(HIT, h0); l = damp_pelvis(s1, 0.7); snap = lerp_snap(STAND0, s1, ss(f / HIN))
    elif f < HIN + (h1 - h0 + 1):
        snap = snapshot(HIT, h0 + f - HIN); l = damp_pelvis(snap, 0.7)
    else:
        s1 = snapshot(HIT, h1); l = damp_pelvis(s1, 0.7); snap = lerp_snap(s1, STAND0, ss((f - HIN - (h1 - h0 + 1) + 1) / HOUT))
    apply(snap); hover(t, IDLE_T, src_loc=l, keep_xy=0.5); lamp(); sway(t, IDLE_T, trail=-10.0, amp=16.0, speed=2.0)


build('Hit', hit_total, hit)

# ---------------------------------------------------------------- death and the lamp
DEATH_T = 2.0
UP = snapshot(ATK, k_top); damp_pelvis(UP)
G = 9.81
LAMP_APPEAR, LAMP_H = 0.55, REST_PEL.z + HOVER
t_fall = math.sqrt(2 * LAMP_H / G)


def death(t):
    if t < 0.35:
        snap = lerp_snap(STAND0, UP, ss(t / 0.35))
    else:
        snap = UP
    apply(snap)
    rise = 0.15 * ss(t / 0.35) + 0.25 * ss((t - 0.35) / 1.0)
    hover(t, IDLE_T, extra=Vector((0, 0, rise)))
    spin = 540 * ss((t - 0.3) / 1.1) ** 1.5 if t > 0.3 else 0.0
    rot_world('B_Pelvis', spin, (0, 0, 1))
    shrink = 1.0 - ss((t - 0.45) / 0.9)
    sc = max(shrink, 1e-4)
    rig.pose.bones['B_Pelvis'].scale = (sc, sc, sc)
    sway(t, IDLE_T, amp=30.0, speed=3.0)
    # the lamp: appears at hip height in front of her, falls, one small bounce, settles with a quarter turn
    if t < LAMP_APPEAR:
        lamp()
    else:
        u = t - LAMP_APPEAR
        h = max(0.0, LAMP_H - 0.5 * G * u * u) if u < t_fall else 0.02 * max(0.0, math.sin(math.pi * (u - t_fall) / 0.18)) if u < t_fall + 0.18 else 0.0
        yaw = math.radians(35) * ss(u / (t_fall + 0.2))
        tilt = math.radians(25) * math.sin(math.pi * min(u / t_fall, 1.0)) if u < t_fall else 0.0
        q = Quaternion((0, 0, 1), yaw) @ Quaternion((1, 0, 0), tilt)
        lamp(1.0, Vector((0, 0, h)), q)


build('Death', int(DEATH_T * FPS) + 1, death)
for a in ('IdleSrc', 'AttackSrc', 'HitSrc'):
    bpy.data.actions[a].use_fake_user = True
json.dump({'impact': IMPACT, 'attack_s': (total - 1) / FPS, 'lamp_rest': list(LAMP_REST), 'hover': HOVER},
          open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'work', 'clips.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
