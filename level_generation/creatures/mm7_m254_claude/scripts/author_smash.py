"""m254 golem: authored double-fist smash arms over the planted, front-faced axe chop (natm rule "no clip fits -> mocap
body + authored blow"). The set's 2HandAxeAttack5 gives the trunk, head, pelvis sink and leg effort; its arms hold an
axe handle beside the right side of the head with the forearms crossed in front of the face, which the native
m254aa..ah never shows. The native raises BOTH arms straight up over the head, then smashes both fists down in front
of the body with a crouch, holds, and recovers.

Per frame of <Action> the wrist targets are set in the CHEST frame (origin between the shoulders; x toward the
character's left, y forward (-Y world at rest), z up along the neck) and the arms are solved with armik.solve (elbow
plane from a pole, hand world rotation with a straight wrist and the palms facing each other):
  frame 0 ......... the clip's own wrists (its first pose, = Standing after the plant)
  RAISE (17) ...... overhead: wrists 7 cm from the midline, 2 cm behind the shoulders, 47 cm above them (arms almost
                    straight), elbows out; held to HOLD_UP (20)
  HIT (25) ........ both fists in front of the belly: 6 cm from the midline, 40 cm forward, 25 cm below the shoulders,
                    elbows out and down; the downswing eases IN (accelerates) like a falling hammer
  held to HOLD (37), then back onto the clip's own wrists by the end (the clip recovers to its guard; clip_timing.py
  then blends it out to Standing).
Trunk: the chest leans back LEAN_UP deg at the raise and forward LEAN_HIT deg at the hit (about B_Spine1/B_Spine2),
on top of the clip's own trunk.
Args: -- <in blend> <out blend> <Action>"""
import bpy, sys, os, math, json
import numpy as np
from mathutils import Vector, Matrix, Quaternion
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import armik
a = sys.argv[sys.argv.index('--') + 1:]
src, out, act_name = a[0], a[1], a[2]
P = json.loads(os.environ.get('SMASH', '{}'))
RAISE, HOLD_UP, HIT, HOLD = P.get('raise', 17), P.get('hold_up', 20), P.get('hit', 25), P.get('hold', 37)
UP = Vector(P.get('up', (0.11, 0.03, 0.46)))         # (lateral, forward, up) in the chest frame; 0.07 pressed the arms on the crown
LOW = Vector(P.get('low', (0.11, 0.40, -0.25)))     # fists side by side (0.06/0.085 pressed them 3 cm into each other)
LEAN_UP, LEAN_HIT = math.radians(P.get('lean_up', 6)), math.radians(P.get('lean_hit', 12))
KEEP_LEAN = P.get('keep_lean', 0.4)                   # as clip_timing.py's LEAN_KEEP for the slash
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
scene = bpy.context.scene; rig = bpy.data.objects['Rig']
act = bpy.data.actions[act_name]
names = [b.name for b in rig.data.bones]
nf = int(act.frame_range[1]) + 1
WM = lambda n: rig.matrix_world @ rig.pose.bones[n].matrix


def use(x):
    rig.animation_data_create(); rig.animation_data.action = x
    if x is not None and getattr(x, 'slots', None) is not None and len(x.slots):
        rig.animation_data.action_slot = x.slots[0]


def smooth(x):
    x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)


# rest hand frame: finger direction and the palm normal (the A-pose palms face the thighs, i.e. the midline)
use(None)
for pb in rig.pose.bones:
    pb.matrix_basis = Matrix()
bpy.context.view_layer.update()
REST = {}
for sd, sg in (('L', 1), ('R', -1)):
    H = WM(f'B_{sd}_Hand'); f = (WM(f'B_{sd}_Finger2').translation - H.translation).normalized()
    n = Vector((-sg, 0, 0)); n = (n - f * n.dot(f)).normalized()
    REST[sd] = (f, n, H.to_3x3().normalized())


def basis(f, n):
    return Matrix((f, n, f.cross(n))).transposed()


def chest():
    """Heading frame at the shoulders: x toward the character's left (shoulder line, horizontal), z world up,
    y = x cross z = forward (-Y at rest)."""
    l, r = WM('B_L_UpperArm').translation, WM('B_R_UpperArm').translation
    o = (l + r) / 2; x = l - r; x.z = 0.0; x.normalize(); z = Vector((0, 0, 1))
    return o, x, x.cross(z).normalized(), z


def sample(f):
    use(act); scene.frame_set(f)
    return {n: (rig.pose.bones[n].rotation_quaternion.copy(), rig.pose.bones[n].location.copy()) for n in names}


poses = [sample(f) for f in range(nf)]
own = []                                               # the clip's own wrists in its chest frame
for f in range(nf):
    use(act); scene.frame_set(f)
    o, x, y, z = chest()
    own.append({sd: Vector(((WM(f'B_{sd}_Hand').translation - o).dot(x), (WM(f'B_{sd}_Hand').translation - o).dot(y),
                            (WM(f'B_{sd}_Hand').translation - o).dot(z))) for sd in 'LR'})


SH_X = 0.2                                           # shoulder half-width for the arcs (chest frame)
MID = Vector(P.get('mid', (0.24, 0.40, -0.05)))
ARC = Vector(P.get('arc', (0.13, 0.50, 0.20)))       # the downswing passes well in front of the face and the nemes lappets        # arms rising forward in front of the chest on the way up
KEYS = [(0, 'own', 'smooth'), (P.get('mid_f', 7), MID, 'smooth'), (RAISE, UP, 'smooth'), (HOLD_UP, UP, 'hold'),
        (P.get('arc_f', 23), ARC, 'fall'), (HIT, LOW, 'lin'), (HOLD, LOW, 'hold'), (None, 'own', 'smooth')]
# weights (overhead share, hit share) for the trunk lean at each key
WK = {0: (0, 0), 1: (0.4, 0), 2: (1, 0), 3: (1, 0), 4: (0.3, 0.5), 5: (0, 1), 6: (0, 1), 7: (0, 0)}


def key_vec(k, f, sd):
    v = KEYS[k][1]; sg = 1 if sd == 'L' else -1
    return own[f][sd] if isinstance(v, str) else Vector((sg * v.x, v.y, v.z))


def target(f, sd):
    sg = 1 if sd == 'L' else -1
    fr = [k[0] if k[0] is not None else nf - 1 for k in KEYS]
    k = max(i for i in range(len(KEYS) - 1) if fr[i] <= f) if f < fr[-1] else len(KEYS) - 2
    f0, f1 = fr[k], fr[k + 1]; u = (f - f0) / max(f1 - f0, 1); u = min(max(u, 0.0), 1.0)
    mode = KEYS[k + 1][2]
    w = u ** 1.6 if mode == 'fall' else (1.0 if mode == 'hold' else (u if mode == 'lin' else smooth(u)))
    a_, b_ = key_vec(k, f, sd), key_vec(k + 1, f, sd)
    sh = Vector((sg * SH_X, 0, 0)); d0, d1 = a_ - sh, b_ - sh
    d = d0.normalized().slerp(d1.normalized(), w) * (d0.length * (1 - w) + d1.length * w)
    wu = WK[k][0] * (1 - w) + WK[k + 1][0] * w; wh = WK[k][1] * (1 - w) + WK[k + 1][1] * w
    return sh + d, wu, wh


rep = []
for f in range(nf):
    use(None)
    for n, (q, l) in poses[f].items():
        pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = q; pb.location = l
    bpy.context.view_layer.update()
    # trunk: keep KEEP_LEAN of the clip's own forward lean change (spine -> neck against frame 0), then lean back at the
    # raise and forward at the hit, pivoting at B_Spine about the world X axis (the faced clip looks along -Y)
    d = WM('B_Neck').translation - WM('B_Spine').translation; lean_src = math.atan2(-d.y, d.z)
    if f == 0:
        LEAN0 = lean_src
    _, wu, wh = target(f, 'L')
    rot = -(1 - KEEP_LEAN) * (lean_src - LEAN0) - LEAN_UP * wu + LEAN_HIT * wh
    M = WM('B_Spine'); t = M.translation.copy(); M = Matrix.Rotation(rot, 4, 'X') @ M; M.translation = t
    armik.set_world(rig, 'B_Spine', M)
    o, x, y, z = chest()
    for sd, sg in (('L', 1), ('R', -1)):
        c, wu_, wh_ = target(f, sd)
        T = o + x * c.x + y * c.y + z * c.z
        S = WM(f'B_{sd}_UpperArm').translation
        lat = x * sg
        # elbows: back while the arms hang, out and up overhead, out and down at the hit
        pole = S + lat * 0.30 + y * -0.25 * (1 - wu_) * (1 - wh_) + (z * 0.15 - y * 0.10) * wu_ + (y * 0.10 - z * 0.25) * wh_
        armik.solve(rig, sd, T, pole=pole)
        E, Wr = WM(f'B_{sd}_Forearm').translation, WM(f'B_{sd}_Hand').translation
        fdir = (Wr - E).normalized(); n = -lat; n = (n - fdir * n.dot(fdir)).normalized()
        f0, n0, H0 = REST[sd]
        H = basis(fdir, n) @ basis(f0, n0).transposed() @ H0
        reach = armik.solve(rig, sd, T, pole=pole, hand_rot=H)
        if f in (RAISE, HIT):
            rep.append(f'{sd}@{f} reach {reach:.2f} miss {100 * (WM(f"B_{sd}_Hand").translation - T).length:.1f} cm')
    poses[f] = {n: (rig.pose.bones[n].rotation_quaternion.copy(), rig.pose.bones[n].location.copy()) for n in names}
# write back (clip_timing.py's writer: sign-continuous quaternions, pelvis location only)
use(None)
old = bpy.data.actions.get(act_name)
if old:
    bpy.data.actions.remove(old)
new = bpy.data.actions.new(act_name); new.use_fake_user = True; use(new)
prev = {}
for f, pose in enumerate(poses):
    for n, (q, l) in pose.items():
        pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'
        if n in prev and q.dot(prev[n]) < 0:
            q = -q
        prev[n] = q
        pb.rotation_quaternion = q; pb.location = l
        pb.keyframe_insert('rotation_quaternion', frame=f)
        if n == 'B_Pelvis':
            pb.keyframe_insert('location', frame=f)
new.use_frame_range = True; new.frame_start, new.frame_end = 0, nf - 1
use(None)
print('SMASH authored arms', act_name, nf, 'frames;', '; '.join(rep))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
