"""Authored ghost motion over the retargeted upper bodies (retarget_mixamo.py: Standing Zombie Idle, Walking Zombie
Walk, Attack Zombie Attack, Hit Zombie Reaction Hit, Fidget Zombie Scream; Death starts from Zombie Idle).
The ghost has no legs: the leg bones are reset to rest (they carry no weight), the pelvis floats at its rest height
(the lowest shred tip just above the floor) with a slow bob, and the robe moves on its chains (robe_rig.py), each
chain segment rotated relative to its rest about the lateral (pitch, + = hem swings back) and forward (roll, + = hem
swings toward +X) axes. Waves travel down each chain (phase lag LAG per segment, a phase per column and layer).
- Standing: the idle at its own length, bob +-BOB, a slow sway of the hem.
- Walking (native wa..wh, 1.0 s): the flight swoop: the body pitched FLY_PITCH forward about the pelvis, the head
  raised to look ahead, the arms reaching forward (Zombie Walk's arms at its first frame plus a little of their swing),
  the robe trailing back (each segment TRAIL deg more, so the hem streams nearly horizontal) with a travelling wave of
  +-WAVE deg on the native 1.0 s cycle, and the body rising on the gather (+-4 cm).
- Attack (native aa..ah, 1.0 s, MM7 applies the blow when the animation has played): the source window starts
  ATT_LEAD s before the claw (the fastest downward hand speed after the arms' highest point) and runs ATT_TAIL s after
  it; the body arches back with the raise and lunges forward ATT_LUNGE m with a FLY_PITCH/2 pitch at the claw, the robe
  lagging. IMPACT is printed for the binding.
- Hit (native 0.75 s): the first HIT_LEN s of the recoil; the robe jolts back.
- Fidget: Zombie Scream at its own length (arms flung wide), the robe flaring.
- Death (native da..dd + xa): authored, DEATH_LEN s: the arms rise, then the empty robe collapses straight down: the
  pelvis sinks to the floor, the spine curls forward, the head drops, the arms fall outward onto the floor and the
  robe chains fold outward into a heap (L/R columns out to the sides, front/back layers forward/back); a floor rule per
  frame raises the pelvis until no bone vertex and lifts the chains until no cloth vertex is under the floor.
Every one-shot clip eases from and to Standing frame 0 (BLEND s). Args: -- <in blend> <out blend>"""
import bpy, sys, os, math
import numpy as np
from mathutils import Matrix, Vector, Quaternion
src, out = sys.argv[sys.argv.index('--') + 1:]
E = lambda k, d: float(os.environ.get(k, d))
FPS = 30
BOB, LAG, WAVE, TRAIL = E('BOB', 0.025), E('LAG', 0.9), E('WAVE', 9), E('TRAIL', 16)
FLY_PITCH, ATT_LEAD, ATT_TAIL, ATT_LUNGE = E('FLY_PITCH', 35), E('ATT_LEAD', 1.0), E('ATT_TAIL', 0.7), E('ATT_LUNGE', 0.22)
HIT_LEN, DEATH_LEN, BLEND = E('HIT_LEN', 0.8), E('DEATH_LEN', 2.2), E('BLEND', 0.2)
HOVER = E('HOVER', 0.035)
HEAD_KEEP = E('HEAD_KEEP', 0.5)
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
scene = bpy.context.scene; scene.render.fps = FPS; scene.render.fps_base = 1
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
ROBE = sorted(b.name for b in rig.data.bones if b.name.startswith('Robe_'))
LEGS = [b.name for b in rig.data.bones if any(k in b.name for k in ('Thigh', 'Calf', 'Foot', 'Toe'))]
NSEG = max(int(n.rsplit('_', 1)[1]) for n in ROBE)
REST = {n: rig.data.bones[n].matrix_local.to_3x3() for n in ROBE}
cl = np.zeros(len(me.vertices), np.int32); me.attributes['cloth'].data.foreach_get('value', cl)
CLOTH = np.where(cl == 1)[0]; BONE = np.where(cl == 0)[0]
deps = bpy.context.evaluated_depsgraph_get()


def set_act(a):
    rig.animation_data_create(); rig.animation_data.action = a
    if a is not None and getattr(a, 'slots', None) is not None and len(a.slots):
        rig.animation_data.action_slot = a.slots[0]


def snapshot(act, f):
    set_act(act); scene.frame_set(int(f), subframe=float(f) - int(f))
    return {pb.name: pb.matrix_basis.copy() for pb in rig.pose.bones}


def apply_snap(sn):
    for pb in rig.pose.bones:
        pb.matrix_basis = sn[pb.name].copy() if pb.name in sn else Matrix()


def blend_snap(a, b, t):
    out = {}
    for n in a:
        la, ra, sa = a[n].decompose(); lb, rb, sb = b[n].decompose()
        out[n] = Matrix.LocRotScale(la.lerp(lb, t), ra.slerp(rb, t), sa.lerp(sb, t))
    return out


def rot_world(name, deg, axis=(1, 0, 0), pivot=None):
    bpy.context.view_layer.update()
    pb = rig.pose.bones[name]
    M = rig.matrix_world @ pb.matrix
    h = M.translation.copy() if pivot is None else Vector(pivot)
    R = Matrix.Rotation(math.radians(deg), 4, Vector(axis))
    pb.matrix = rig.matrix_world.inverted() @ (Matrix.Translation(h) @ R @ Matrix.Translation(-h) @ M)


def move_world(name, d):
    bpy.context.view_layer.update()
    pb = rig.pose.bones[name]
    M = rig.matrix_world @ pb.matrix
    M = Matrix.Translation(Vector(d)) @ M
    pb.matrix = rig.matrix_world.inverted() @ M


GRAV = E('GRAV', 0.85)


def robe(fn):
    """fn(col, layer, seg) -> (pitch, roll) degrees, segment-local (they add up down the chain). The first segment
    first undoes GRAV of the pelvis's world rotation, so the robe hangs from the world (gravity), not from a hunched
    or pitched pelvis; the authored angles then act about the world axes."""
    bpy.context.view_layer.update()
    Pw = rig.pose.bones['B_Pelvis'].matrix.to_3x3().normalized(); Pr = rig.data.bones['B_Pelvis'].matrix_local.to_3x3().normalized()
    D = (Pw @ Pr.inverted()).to_quaternion()
    Dc = Quaternion().slerp(D.inverted(), GRAV).to_matrix()
    for n in ROBE:
        c, l, i = n[5], n[6], int(n.rsplit('_', 1)[1])
        p, r = fn(c, l, i)
        R = Matrix.Rotation(math.radians(p), 3, 'X') @ Matrix.Rotation(math.radians(r), 3, 'Y')
        pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'
        if i == 1:                     # child world = D @ B_rest @ basis; want D^(1-GRAV) @ R @ B_rest
            pb.rotation_quaternion = (REST[n].inverted() @ Dc @ R @ REST[n]).to_quaternion()
        else:
            pb.rotation_quaternion = (REST[n].inverted() @ R @ REST[n]).to_quaternion()


PH = {'L': 0.0, 'C': 1.7, 'R': 3.4}; PHL = {'F': 0.0, 'B': 0.9}
SGN = {'L': 1.0, 'C': 0.0, 'R': -1.0}


def flutter(t, T, amp=4.0, k=1):
    w = 2 * math.pi * k / T
    return lambda c, l, i: (amp * (0.4 + 0.2 * i) * math.sin(w * t - LAG * i + PH[c] + PHL[l]),
                            0.6 * amp * (0.3 + 0.2 * i) * math.sin(w * t * 0.7 - LAG * i + PH[c] * 1.3))


def lowest(ids):
    bpy.context.view_layer.update(); deps.update()
    ev = body.evaluated_get(deps); m = ev.to_mesh()
    z = min((body.matrix_world @ m.vertices[int(i)].co).z for i in ids[::3])
    ev.to_mesh_clear()
    return z


def finish(sn_list, name, extra):
    """sn_list: per-frame body snapshots; extra(i, t, n) applies the authored layer and robe for frame i. Poses are
    built with no action assigned (a depsgraph update cannot overwrite them), then keyed into a new action."""
    set_act(None)
    n = len(sn_list); poses = []
    for i, sn in enumerate(sn_list):
        base(sn)
        extra(i, i / FPS, n)
        bpy.context.view_layer.update()
        poses.append({pb.name: pb.matrix_basis.copy() for pb in rig.pose.bones})
    act = bpy.data.actions.new(name + '_ghost'); act.use_fake_user = True
    set_act(act)
    prev = {}
    for i, P_ in enumerate(poses):
        for pb in rig.pose.bones:
            l, q, sc_ = P_[pb.name].decompose()
            if pb.name in prev and q.dot(prev[pb.name]) < 0:
                q = -q
            prev[pb.name] = q
            pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = q; pb.location = l
            pb.keyframe_insert('rotation_quaternion', frame=i); pb.keyframe_insert('location', frame=i)
    set_act(None)
    old = bpy.data.actions.get(name)
    if old is not None:
        bpy.data.actions.remove(old)
    act.name = name
    return act


def base(sn):
    """a body snapshot with the legs at rest and the hover: the source pelvis keeps its rotation but floats at its
    rest height + HOVER (the retarget dropped it with the source's knees); the authored layer adds the rest"""
    apply_snap(sn)
    for lg in LEGS:
        rig.pose.bones[lg].matrix_basis = Matrix()
    pb = rig.pose.bones['B_Pelvis']; l_, q_, s_ = pb.matrix_basis.decompose()
    pb.matrix_basis = Matrix.LocRotScale(Vector((0, 0, 0)), q_, s_)
    # the skull sits in a cowl, not on a skin neck: the source's neck and head bend is damped to HEAD_KEEP (Zombie
    # Scream bent them ~60 deg and stretched the hood; user review 2026-10-20)
    for n_ in ('B_Neck', 'B_Head'):
        pn = rig.pose.bones[n_]; l_, q_, s_ = pn.matrix_basis.decompose()
        pn.matrix_basis = Matrix.LocRotScale(l_, Quaternion().slerp(q_, HEAD_KEEP), s_)
    move_world('B_Pelvis', (0, 0, HOVER))


def source_frames(name, f0=None, f1=None):
    a = bpy.data.actions[name]; s0, s1 = int(a.frame_range[0]), int(a.frame_range[1])
    f0 = s0 if f0 is None else f0; f1 = s1 if f1 is None else f1
    return [snapshot(a, f) for f in np.arange(f0, f1 + 1e-6, 1.0)]


WK0 = snapshot(bpy.data.actions['Walking'], 0)
ARMS = [n for n in WK0 if any(k in n for k in ('Clavicle', 'UpperArm', 'Forearm', 'Hand', 'Finger'))]
ARM_MIX = E('ARM_MIX', 0.7)


def stand_arms(sn):
    """the native holds the claws before the waist; Zombie Idle's arms hang into the robe: ARM_MIX of the walk's
    reaching arms"""
    out = dict(sn)
    for k in ARMS:
        out[k] = blend_snap({k: sn[k]}, {k: WK0[k]}, ARM_MIX)[k]
    return out


STAND0 = stand_arms(snapshot(bpy.data.actions['Standing'], 0))
for lg in LEGS:
    STAND0[lg] = Matrix()


def with_blends(frames, bin_=BLEND, bout=BLEND):
    n = len(frames); bi, bo = int(bin_ * FPS), int(bout * FPS)
    out = []
    for i, sn in enumerate(frames):
        w = 1.0
        if i < bi:
            w = i / bi
        if i > n - 1 - bo:
            w = min(w, (n - 1 - i) / bo)
        w = w * w * (3 - 2 * w)
        out.append(blend_snap(STAND0, sn, w))
    return out


def env(i, n, bi=BLEND, bo=BLEND):
    t = i / FPS; T = (n - 1) / FPS
    w = min(1.0, t / bi if bi else 1, (T - t) / bo if bo else 1)
    w = max(0.0, w)
    return w * w * (3 - 2 * w)


# ---------------------------------------------------------------- Standing
st = [stand_arms(x) for x in source_frames('Standing')]; TS = (len(st) - 1) / FPS


def st_extra(i, t, n):
    move_world('B_Pelvis', (0, 0, BOB * math.sin(2 * math.pi * 2 * t / TS)))
    robe(flutter(t, TS, 3.0, 2))


finish(st, 'Standing', st_extra)
print('CLIP Standing', len(st), 'frames')

# ---------------------------------------------------------------- Walking: the swoop
wk_src = bpy.data.actions['Walking']
wk = []
for i in range(31):
    sw = snapshot(wk_src, (i / 30) * 30)                          # the walk's first second: a little arm sway
    sn = {k: (blend_snap({k: WK0[k]}, {k: sw[k]}, 0.25)[k] if k in ARMS else STAND0[k]) for k in WK0}
    wk.append(sn)


def wk_extra(i, t, n):
    ph = 2 * math.pi * t / 1.0
    move_world('B_Pelvis', (0, 0, 0.04 * math.sin(ph)))
    rot_world('B_Pelvis', FLY_PITCH + 4 * math.sin(ph))
    for b_ in ('B_Spine1', 'B_Spine2'):
        rot_world(b_, -4)
    rot_world('B_Neck', -FLY_PITCH * 0.45); rot_world('B_Head', -FLY_PITCH * 0.35)
    robe(lambda c, l, k: (TRAIL * (0.6 + 0.5 * k) + WAVE * math.sin(ph - LAG * k + PH[c] * 0.3),
                          3 * math.sin(ph * 0.5 - LAG * k + PH[c])))


finish(wk, 'Walking', wk_extra)
print('CLIP Walking 31 frames (1.0 s loop)')

# ---------------------------------------------------------------- Attack: raise and claw
at_src = bpy.data.actions['Attack']; a0, a1 = int(at_src.frame_range[0]), int(at_src.frame_range[1])
hz, hv = [], []
set_act(at_src)
for f in range(a0, a1 + 1):
    scene.frame_set(f)
    hz.append(np.mean([(rig.matrix_world @ rig.pose.bones[f'B_{s}_Hand'].head).z for s in 'LR']))
hz = np.array(hz); top = int(np.argmax(hz))
vz = np.diff(hz); claw = top + int(np.argmin(vz[top:top + 40]))
s0 = max(a0, claw - int(ATT_LEAD * FPS)); s1 = min(a1, claw + int(ATT_TAIL * FPS))
at = with_blends(source_frames('Attack', s0, s1), 0.25, 0.3)
IMPACT = (claw - s0 + 0.5) / FPS
CL = claw - s0


def at_extra(i, t, n):
    e = env(i, n, 0.25, 0.3)
    k = math.exp(-((i - CL) / 6.0) ** 2)                       # lunge around the claw
    back = math.exp(-((i - (CL - 12)) / 8.0) ** 2)             # arch back with the raise
    move_world('B_Pelvis', (0, -ATT_LUNGE * k * e, 0.03 * back * e))
    rot_world('B_Pelvis', (FLY_PITCH * 0.5 * k - 10 * back) * e)
    robe(lambda c, l, s: (e * (TRAIL * 0.8 * k * (0.5 + 0.4 * s) - 6 * back) + 2 * math.sin(2 * math.pi * t - LAG * s + PH[c]),
                          e * SGN[c] * 6 * back))


finish(at, 'Attack', at_extra)
print(f'CLIP Attack {len(at)} frames, source {s0}..{s1}, arms highest at {top}, claw at {claw}; IMPACT {IMPACT:.3f}')

# ---------------------------------------------------------------- Hit
h_src = bpy.data.actions['Hit']
hit = with_blends(source_frames('Hit', 0, int(HIT_LEN * FPS)), 0.08, 0.25)


def hit_extra(i, t, n):
    e = env(i, n, 0.08, 0.25)
    k = math.exp(-((t - 0.2) / 0.12) ** 2)
    robe(lambda c, l, s: (-12 * k * (0.5 + 0.3 * s) * e, SGN[c] * 4 * k * e))


finish(hit, 'Hit', hit_extra)
print('CLIP Hit', len(hit), 'frames')

# ---------------------------------------------------------------- Fidget
fd = with_blends(source_frames('Fidget'), 0.3, 0.3); TF = (len(fd) - 1) / FPS


def fd_extra(i, t, n):
    e = env(i, n, 0.3, 0.3)
    flare = math.sin(math.pi * min(1, t / TF)) * e
    robe(lambda c, l, s: (flutter(t, TF, 5.0, 2)(c, l, s)[0] + (8 if l == 'B' else -8) * flare * 0.5,
                          flutter(t, TF, 5.0, 2)(c, l, s)[1] + SGN[c] * 10 * flare))


finish(fd, 'Fidget', fd_extra)
print('CLIP Fidget', len(fd), 'frames')

# ---------------------------------------------------------------- Death: the robe collapses
ND = int(DEATH_LEN * FPS) + 1
pel_z0 = (rig.matrix_world @ rig.data.bones['B_Pelvis'].head_local).z
dth = [dict(STAND0) for _ in range(ND)]
DROP = pel_z0 - 0.12
lifts = 0


def ss(x):
    x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)


def death_pose(i, t, n, k_extra=0.0, lift=0.0):
    rise = ss(t / 0.45) * (1 - ss((t - 0.7) / 0.6))            # arms up, then they fall
    fall = ss((t - 0.4) / 1.3)                                  # the collapse
    for s, sg in (('L', 1.0), ('R', -1.0)):
        rot_world(f'B_{s}_UpperArm', sg * (55 * rise - 35 * fall), axis=(0, 1, 0))
    rot_world('B_Pelvis', 30 * fall)
    rot_world('B_Spine', 35 * fall); rot_world('B_Spine1', 25 * fall); rot_world('B_Neck', 20 * fall)
    rot_world('B_Head', 15 * fall)
    move_world('B_Pelvis', (0, 0.05 * fall, -(DROP + HOVER) * fall + lift))
    k = min(1.0, fall + k_extra)
    robe(lambda c, l, sgm: (k * (50 if sgm == 1 else 12) * (1 if l == 'B' else -1) * (0.6 if c != 'C' else 1.0),
                            k * SGN[c] * (55 if sgm == 1 else 12)))


def dth_extra(i, t, n):
    global lifts
    death_pose(i, t, n)
    lift, kx = 0.0, 0.0
    if t > 0.4:
        zb = lowest(BONE)
        if zb < 0.0:
            lift = -zb; base(dth[i])
            death_pose(i, t, n, 0.0, lift); lifts += 1
        while lowest(CLOTH) < 0.003 and kx < 1.0:
            kx += 0.1; base(dth[i])
            death_pose(i, t, n, kx, lift); lifts += 1
        zc = lowest(CLOTH)
        if zc < 0.0:                                    # the fold alone cannot clear it: lift the whole heap
            lift += -zc + 0.003; base(dth[i])
            death_pose(i, t, n, kx, lift); lifts += 1


finish(dth, 'Death', dth_extra)
print('CLIP Death', ND, 'frames, floor-rule steps', lifts)
print('IMPACT', round(IMPACT, 3))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
