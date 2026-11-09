"""Clip timing for the engine's action events (playbook "Clip timing"): <in blend> -> <out blend> (goblin).
- Attack: a ready pause of LEAD seconds (ease from the Standing pose into the attack's first pose, with a slight
  coil: the chest turned 6 deg toward the sword side) before the source attack at its own
  speed. The blow (peak sword-tip speed of the built clip) then lands near 0.6 s, so the engine's fit of [0, impact]
  to the native 0.75 s action stretches it only ~1.2x. Prints IMPACT for actors.yml `events: attack_melee`.
- Fidget: the native fidget is 0.625 s and the engine cuts fidget at the native length, so the 1.0 s sword raise was
  cut mid-move. New fidget = Standing with the head/neck (and 40 % of the upper chest) of the set's head-shake clip
  (RelaxNo, 0.7 s) layered as local deltas from its first frame, resampled to FIDGET_LEN.
Goblin changes: the Cast clip (left-hand thrust, source peak hand speed at 0.25 s) gets the same kind of ready pause
and prints CAST_IMPACT (peak left-hand speed); the fidget is authored from the native study (gobfi: a small chest and
shoulder rise and release, no head turn) instead of the barbarian's head shake.
Args: -- <in blend> <out blend>"""
import bpy, sys, os, math, json
import numpy as np
from mathutils import Quaternion, Vector, Matrix
SRC_BLEND, OUT_BLEND = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPS = 30
LEAD = 0.4                           # SwordAttackR6 blow at 0.28 s -> ~0.68 s (R4, a lunging stab, was replaced)
CAST_LEAD = 0.4                      # ArmedCastLAttack1 thrust at 0.25 s -> ~0.65 s
FIDGET_LEN = 0.75                    # native gobfi: six 125 ms frames
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(SRC_BLEND))
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


# ---------------------------------------------------------------- upright Standing
# The source idle is a deep guard crouch (posed height 1.47 m against the 1.71 m walk): in game the 3D goblins stood
# visibly shorter than the upright native stand (gobsta). Legs (thighs, calves, feet) are eased STRAIGHTEN of the way
# toward the upright bind pose, the pelvis is lowered/raised so the lowest foot joint stays where it was; spine and arms
# keep the source motion.
STRAIGHTEN = 0.6
LEGS = [f'B_{s_}_{b}' for s_ in 'LR' for b in ('Thigh', 'Calf', 'Foot')]
st = bpy.data.actions['Standing']; n_st0 = int(st.frame_range[1]); frames = []
for f in range(n_st0 + 1):
    pose = sample(st, f)
    set_act(st); scene.frame_set(f)
    low0 = min((rig.matrix_world @ rig.pose.bones[b].head).z for b in ('B_L_Foot', 'B_R_Foot', 'B_L_Toe0', 'B_R_Toe0'))
    set_act(None)
    for n in names:
        pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion, pb.location = pose[n]
        if n in LEGS:
            pb.rotation_quaternion = pose[n][0].slerp(Quaternion(), STRAIGHTEN)
    bpy.context.view_layer.update()
    low1 = min((rig.matrix_world @ rig.pose.bones[b].head).z for b in ('B_L_Foot', 'B_R_Foot', 'B_L_Toe0', 'B_R_Toe0'))
    pel = rig.pose.bones['B_Pelvis']
    m = rig.matrix_world @ pel.matrix; m.translation.z -= (low1 - low0)
    pel.matrix = rig.matrix_world.inverted() @ m; bpy.context.view_layer.update()
    frames.append({n: (rig.pose.bones[n].rotation_quaternion.copy(), rig.pose.bones[n].location.copy()) for n in names})
write('Standing', frames)
print('STANDING legs straightened', STRAIGHTEN, 'pelvis raised (frame 0) cm', round((low0 - low1) * 100, 1))

# ---------------------------------------------------------------- attack with a ready pause
atk = bpy.data.actions['Attack']; st = bpy.data.actions['Standing']
n_atk = int(atk.frame_range[1]); n_lead = int(round(LEAD * FPS))
s0, a0 = sample(st, 0), sample(atk, 0)
frames = []
for i in range(n_lead):
    u = smooth(i / n_lead); coil = math.sin(math.pi * u) * 0.8 + u * 0.2            # coil peaks then holds a little
    pose = {}
    for n in names:
        q = s0[n][0].slerp(a0[n][0], u); l = s0[n][1].lerp(a0[n][1], u)
        if n == 'B_Spine2':
            q = q @ Quaternion((0, 1, 0), math.radians(-6) * coil)
        pose[n] = (q, l)
    frames.append(pose)
for f in range(n_atk + 1):
    frames.append(sample(atk, f))
new_atk = write('Attack', frames)
# blow = peak tip speed of the Sword bone tip in the new clip
set_act(new_atk)
G = json.load(open(os.path.join(HERE, 'work', 'grip_pose.json')))
tips = []
for f in range(len(frames)):
    scene.frame_set(f)
    M = rig.matrix_world @ rig.pose.bones['B_R_Hand'].matrix          # the Sword bone is added at export
    c = M @ Vector(G['handle_centre_hand_local']); ax = (M.to_3x3() @ Vector(G['handle_axis_hand_local'])).normalized()
    tips.append(np.array(c + ax * 0.8))
sp = np.linalg.norm(np.diff(np.array(tips), axis=0), axis=1)
k = int(np.argmax(sp)); impact = (k + 0.5) / FPS
set_act(None)
print(f'ATTACK {len(frames) / FPS:.3f} s (lead {n_lead / FPS:.3f} s), blow at {impact:.3f} s -> wind-up stretch '
      f'{0.75 / impact:.2f}x; IMPACT {impact:.3f}')

# ---------------------------------------------------------------- cast with a ready pause (left-hand thrust)
cst = bpy.data.actions['Cast']; n_c = int(cst.frame_range[1]); n_cl = int(round(CAST_LEAD * FPS))
c0 = sample(cst, 0); frames = []
for i in range(n_cl):
    u = smooth(i / n_cl)
    frames.append({n: (s0[n][0].slerp(c0[n][0], u), s0[n][1].lerp(c0[n][1], u)) for n in names})
for f in range(n_c + 1):
    frames.append(sample(cst, f))
# open casting hand (gob2 review 1): the source keeps the left hand a fist (fingers curled ~99 deg) and bends the wrist
# 55 deg through the thrust, which on the goblin read as a limp, bent claw. During the thrust the left wrist eases to
# straight (hand and its twist bone toward rest relative to the forearm) and the fingers open to the goblin's own open
# rest pose, keeping 15 % of the source; it eases back to the source over the recovery.
OPEN = [n for n in names if n.startswith('B_L_Finger')] + ['B_L_Hand', 'B_L_ForearmTwist']
for i, pose in enumerate(frames):
    ts = i / FPS - CAST_LEAD
    w = 0.85 * smooth((ts - 0.05) / 0.17) * (1 - smooth((ts - 0.62) / 0.3))
    for n in OPEN:
        q, l = pose[n]; pose[n] = (q.slerp(Quaternion(), w), l)
new_c = write('Cast', frames); set_act(new_c)
hp = []
for f in range(len(frames)):
    scene.frame_set(f); hp.append(np.array(rig.matrix_world @ rig.pose.bones['B_L_Hand'].head))
sp = np.linalg.norm(np.diff(np.array(hp), axis=0), axis=1)
k = int(np.argmax(sp[n_cl:])) + n_cl; cast_impact = (k + 0.5) / FPS
set_act(None)
print(f'CAST {len(frames) / FPS:.3f} s (lead {n_cl / FPS:.3f} s), release (peak left-hand speed) at {cast_impact:.3f} s; '
      f'CAST_IMPACT {cast_impact:.3f}')

# ---------------------------------------------------------------- fidget: native gobfi chest/shoulder rise
# a-c: chest rises/expands and the shoulders lift; c-e: release; f: back to ready (study: 0-3 deg body rotations)
n_st = int(st.frame_range[1]); n_f = int(round(FIDGET_LEN * FPS)); frames = []
W = rig.matrix_world
# world-space turns (bone-local axes differ per bone on the cloned frames: a local-X "pitch" on Spine2 was a side
# bend); +X is the character's left, the character faces -Y. Chest: lean back (about +X); shoulders: lift (about
# the forward axis, opposite signs per side)
# (a positive turn about +X tips the chest forward toward -Y; about -Y it lowers a +X shoulder; measured against
# Standing at the same frame)
TURNS = (('B_Spine1', Vector((1, 0, 0)), -1.5), ('B_Spine2', Vector((1, 0, 0)), -2.5),
         ('B_L_Clavicle', Vector((0, -1, 0)), 5.0), ('B_R_Clavicle', Vector((0, -1, 0)), -5.0),
         ('B_Neck', Vector((1, 0, 0)), 2.0))
for i in range(n_f + 1):
    u = i / n_f; b = math.sin(math.pi * min(1.0, u / 0.85)) ** 2            # rise to c (~0.3), release, settle by f
    pose = sample(st, i % (n_st + 1))
    set_act(None)                                                           # never pose with an action attached
    for n in names:
        pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion, pb.location = pose[n]
    bpy.context.view_layer.update()
    for n, ax_, deg in TURNS:
        pb = rig.pose.bones[n]; m = W @ pb.matrix; h = m.translation.copy()
        pb.matrix = W.inverted() @ (Matrix.Translation(h) @ Matrix.Rotation(math.radians(deg) * b, 4, ax_) @
                                    Matrix.Translation(-h) @ m)
        bpy.context.view_layer.update()
    frames.append({n: (rig.pose.bones[n].rotation_quaternion.copy(), rig.pose.bones[n].location.copy()) for n in names})
write('Fidget', frames)
print(f'FIDGET {n_f / FPS:.3f} s (native 0.75 s): Standing + chest/shoulder rise and release (gobfi)')
# ---------------------------------------------------------------- head clear of the shoulders
# gob2 review 2: in the attack's follow-through (0.70-1.0 s, after the blow) the source shrugs the right clavicle and
# the raised shoulder plate sank >= 5 cm into the jaw (the source mannequin has a long neck and no pauldrons); the
# cast's raised left arm and the fall did the same. Per frame one parameter t in 0..1 lifts the chin (neck + head
# extension, t x 35 deg), lowers the offending clavicle and swings that upper arm down (t x 25 deg each); the smallest t that leaves no head vertex more than 3 mm inside the shoulder geometry is found by
# bisection, then held over +-2 frames and smoothed. A sideways neck turn alone needed > 40 deg.
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
    CAP = np.radians([25, 25, 0, 12]); COST = np.array([1.0, 0.7, 2.0, 1.5]); STEP = math.radians(2.5)
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


for nm in ('Attack', 'Cast', 'Death'):
    head_fix(nm)
json.dump({'attack_impact_s': round(impact, 3), 'cast_impact_s': round(cast_impact, 3)},
          open(os.path.join(HERE, 'work', 'clip_timing.json'), 'w'))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(OUT_BLEND))
