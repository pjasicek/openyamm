"""Behemoth clip finishing (playbook "Clip timing"), retargeted blend -> final clip set, keys at 30 fps.
- Attack: SwipeT (Mutant Swiping, chest turned onto the party) source 0.20-2.45 s. The wind-up (to 1.17 s: right arm
  raised overhead as in native m162nb, the left arm circling up from behind) plays WINDUP_SPEED x faster; the source's
  spin during the slam is replaced by a 0.25 s ease into its slam pose (1.45 s); the recovery runs at the source
  speed. The blow (impact) = the end of that ease, the left claws on the floor in front.
- Hit: zombie reaction hit, first HIT_LEN s, last 0.3 s eased into Standing frame 0.
- Death: Mixamo Zombie Dying, relative to its own first frame (staggers, falls flat on the face as the native corpse
  m162xa0; four forward deaths compared by corpse flatness), horizontal travel halved (corpse near the actor), eased in from Standing over 0.35 s (it starts upright).
- Dead: the last Death pose held 1 s.  Fidget: Mutant Roaring, eased in/out 0.3 s.
- Floor, per frame from the evaluated mesh: Standing/Attack/Hit/Fidget put the lowest SOLE vertex (feet/toes weight
  > 0.5) on z = 0; Death/Dead the lowest vertex of the whole body. Walking grounds its lowest sole too (one foot is always planted);
Running keeps its flight phases and is only lifted out of penetration (eased).
Writes work/clip_timing.json (impact times, durations). Args: -- <in blend> <out blend>"""
import bpy, sys, os, math, json
import numpy as np
from mathutils import Quaternion, Vector, Matrix
SRC_BLEND, OUT_BLEND = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPS = 30
WINDUP = (0.20, 1.17); RECOVER_END = 2.45; WINDUP_SPEED = 1.6; SRC_SLAM = 1.45
HIT_LEN = 1.10; DEATH_TRAVEL = 0.5
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(SRC_BLEND))
scene = bpy.context.scene; scene.render.fps = FPS; scene.render.fps_base = 1
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; names = [b.name for b in rig.data.bones]


def set_act(a):
    rig.animation_data_create(); rig.animation_data.action = a
    if a is not None and len(a.slots):
        rig.animation_data.action_slot = a.slots[0]


def sample(act, t):
    """pose (local quaternion + location per bone) of an action at time t seconds"""
    f = t * FPS
    set_act(act); scene.frame_set(int(math.floor(f)), subframe=f - math.floor(f))
    return {n: (rig.pose.bones[n].rotation_quaternion.copy(), rig.pose.bones[n].location.copy()) for n in names}


def blend(a, b, w):
    out = {}
    for n in names:
        qa, la = a[n]; qb, lb = b[n]
        if qa.dot(qb) < 0:
            qb = -qb
        out[n] = (qa.slerp(qb, w), la.lerp(lb, w))
    return out


def smooth(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def write(name, frames):
    old = bpy.data.actions.get(name)
    if old:
        bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name); act.use_fake_user = True; set_act(act); prev = {}
    for i, pose in enumerate(frames):
        for n, (q, l) in pose.items():
            pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'
            if n in prev and q.dot(prev[n]) < 0:
                q = -q
            prev[n] = q; pb.rotation_quaternion = q; pb.location = l
            pb.keyframe_insert('rotation_quaternion', frame=i)
            if n == 'B_Pelvis':
                pb.keyframe_insert('location', frame=i)
    act.use_frame_range = True; act.frame_start, act.frame_end = 0, len(frames) - 1
    set_act(None); return act


A = bpy.data.actions
stand0 = sample(A['Standing'], 0.0)
report = {}

# ---------------------------------------------------------------- Attack
# source spans: wind-up WINDUP (sped up), then the source spins a full turn while it slams (1.17-1.45 s; with the
# chest held on the party that whipped the trunk 1000 deg/s): replaced by a direct ease from the overhead pose to the
# slam pose in 0.25 s (0.15 s whipped the trunk at 600 deg/s; the curve still lands with speed), then the recovery at the source speed.
STRIKE = (WINDUP[1], 1.45, 0.25)
w_len = (WINDUP[1] - WINDUP[0]) / WINDUP_SPEED
total = w_len + STRIKE[2] + (RECOVER_END - STRIKE[1])
up_pose = sample(A['SwipeT'], STRIKE[0]); slam_pose = sample(A['SwipeT'], STRIKE[1])
n = int(round(total * FPS))
frames = []
for i in range(n + 1):
    t = i / FPS
    if t <= w_len:
        p = sample(A['SwipeT'], WINDUP[0] + t * WINDUP_SPEED)
    elif t <= w_len + STRIKE[2]:
        x = (t - w_len) / STRIKE[2]
        p = blend(up_pose, slam_pose, 0.5 * x ** 1.5 + 0.5 * smooth(x))
    else:
        p = sample(A['SwipeT'], STRIKE[1] + (t - w_len - STRIKE[2]))
    p = blend(stand0, p, smooth(t / 0.15))
    p = blend(p, stand0, smooth((t - (total - 0.2)) / 0.2))
    frames.append(p)
write('Attack', frames)
impact = w_len + STRIKE[2]
report['Attack'] = {'duration': round(n / FPS, 3), 'impact': round(impact, 3), 'source': 'Mutant Swiping (turn)',
                    'windup': list(WINDUP), 'windup_speed': WINDUP_SPEED, 'strike_ease': list(STRIKE),
                    'recovery_end': RECOVER_END}

# ---------------------------------------------------------------- Hit
n = int(round(HIT_LEN * FPS)); frames = []
for i in range(n + 1):
    t = i / FPS
    p = blend(stand0, sample(A['Hit'], t), smooth(t / 0.1))
    frames.append(blend(p, stand0, smooth((t - (HIT_LEN - 0.3)) / 0.3)))
write('Hit', frames)
report['Hit'] = {'duration': round(n / FPS, 3)}

# ---------------------------------------------------------------- Fidget
d = A['Fidget'].frame_range[1] / FPS; n = int(round(d * FPS)); frames = []
for i in range(n + 1):
    t = i / FPS
    p = blend(stand0, sample(A['Fidget'], t), smooth(t / 0.3))
    frames.append(blend(p, stand0, smooth((t - (d - 0.3)) / 0.3)))
write('Fidget', frames)
report['Fidget'] = {'duration': round(n / FPS, 3)}

# ---------------------------------------------------------------- Death (travel halved, world space)
src = A['Death']; d = src.frame_range[1] / FPS; n = int(round(d * FPS))
set_act(src); scene.frame_set(0)
pel0 = (rig.matrix_world @ rig.pose.bones['B_Pelvis'].matrix).translation.copy()
frames = []
for i in range(n + 1):
    t = i / FPS
    p = sample(src, t)
    M = rig.matrix_world @ rig.pose.bones['B_Pelvis'].matrix
    tr = M.translation - pel0
    M2 = M.copy(); M2.translation = pel0 + Vector((tr.x * DEATH_TRAVEL, tr.y * DEATH_TRAVEL, tr.z))
    rig.pose.bones['B_Pelvis'].matrix = rig.matrix_world.inverted() @ M2
    bpy.context.view_layer.update()
    p['B_Pelvis'] = (p['B_Pelvis'][0], rig.pose.bones['B_Pelvis'].location.copy())
    frames.append(blend(stand0, p, smooth(t / 0.35)))
write('Death', frames)
write('Dead', [frames[-1]] * (FPS + 1))
report['Death'] = {'duration': round(n / FPS, 3), 'travel_scale': DEATH_TRAVEL}

# ---------------------------------------------------------------- arm abduction (G6)
# The Behemoth's thighs are much thicker than Warrok's: hanging forearms went 7 cm (walk) and 15+ cm (hit, kneeling
# death) into them (scripts/g6_claws.py). Constant extra upper-arm abduction about the posed chest's forward axis.
ABDUCT = {'Walking': 9, 'Running': 6, 'Hit': 12, 'Death': (12, 10, 1.6, 2.5), 'Dead': 12, 'Attack': 4}
# (base, extra, t0, t1): the extra eases in and out over t0..t1 (Death: the arms swing through the thighs as it collapses)
CHEST_FWD = rig.data.bones['B_Spine2'].matrix_local.to_3x3().inverted() @ Vector((0, -1, 0))


def abduct(name, spec):
    act = A[name]; set_act(act)
    f0, f1 = map(int, act.frame_range)
    for f in range(f0, f1 + 1):
        scene.frame_set(f)
        if isinstance(spec, tuple):
            b0, ex, t0, t1 = spec; x = (f / FPS - t0) / (t1 - t0)
            deg = b0 + ex * (math.sin(math.pi * x) ** 2 if 0 < x < 1 else 0.0)
        else:
            deg = spec
        ch = (rig.matrix_world @ rig.pose.bones['B_Spine2'].matrix).to_3x3()
        fwd = (ch @ CHEST_FWD).normalized()
        for side, sgn in (('L', 1), ('R', -1)):
            pb = rig.pose.bones[f'B_{side}_UpperArm']
            M = rig.matrix_world @ pb.matrix
            R = Matrix.Rotation(math.radians(deg) * sgn, 4, fwd) @ M.to_3x3().to_4x4()
            R.translation = M.translation
            pb.matrix = rig.matrix_world.inverted() @ R
            bpy.context.view_layer.update()
            pb.keyframe_insert('rotation_quaternion', frame=f)
    set_act(None)


# forward swing (shoulder flexion about the posed chest's side axis) over a window: (degrees, t0, t1)
FLEX = {}   # tried Death +-35 deg over 1.5-2.6 s: the collapse curls the arms into the belly or the legs either way
CHEST_SIDE = rig.data.bones['B_Spine2'].matrix_local.to_3x3().inverted() @ Vector((1, 0, 0))


def flex(name, spec):
    act = A[name]; set_act(act)
    f0, f1 = map(int, act.frame_range); deg0, t0, t1 = spec
    for f in range(f0, f1 + 1):
        x = (f / FPS - t0) / (t1 - t0)
        if not 0 < x < 1:
            continue
        scene.frame_set(f)
        side = ((rig.matrix_world @ rig.pose.bones['B_Spine2'].matrix).to_3x3() @ CHEST_SIDE).normalized()
        for s_ in ('L', 'R'):
            pb = rig.pose.bones[f'B_{s_}_UpperArm']
            M = rig.matrix_world @ pb.matrix
            R = Matrix.Rotation(-math.radians(deg0) * math.sin(math.pi * x) ** 2, 4, side) @ M.to_3x3().to_4x4()
            R.translation = M.translation
            pb.matrix = rig.matrix_world.inverted() @ R
            bpy.context.view_layer.update()
            pb.keyframe_insert('rotation_quaternion', frame=f)
    set_act(None)


for name, spec in FLEX.items():
    flex(name, spec)
    report.setdefault(name, {})['arm_flex'] = spec
for name, deg in ABDUCT.items():
    abduct(name, deg)
    report.setdefault(name, {})['arm_abduction_deg'] = deg

# ---------------------------------------------------------------- floor pass
me = body.data
W_sole = np.zeros(len(me.vertices))
sole_groups = {g.index for g in body.vertex_groups if any(k in g.name for k in ('_Foot', '_Toe0'))}
for v in me.vertices:
    W_sole[v.index] = sum(e.weight for e in v.groups if e.group in sole_groups)
SOLE = W_sole > 0.5


def floor(name, mode):
    act = A[name]; set_act(act)
    f0, f1 = map(int, act.frame_range); stats = []
    for f in range(f0, f1 + 1):
        scene.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(dg); m = ev.to_mesh()
        z = np.array([v.co.z for v in m.vertices]); ev.to_mesh_clear()
        zmin = float(z[SOLE].min()) if mode == 'sole' else float(z.min())
        stats.append(zmin)
    corr = -np.array(stats)
    if mode == 'lift':                  # flight phases stay; only penetration is lifted (max over +-2 frames, eased)
        c = np.clip(corr, 0, None); c = np.array([c[max(0, i - 2):i + 3].max() for i in range(len(c))])
        k = np.array([1, 2, 3, 2, 1], float); k /= k.sum()
        corr = np.maximum(np.convolve(np.pad(c, 2, mode='wrap'), k, 'valid'), np.clip(corr, 0, None))
    if mode in ('sole', 'all', 'lift'):
        for f in range(f0, f1 + 1):
            scene.frame_set(f)
            pb = rig.pose.bones['B_Pelvis']
            M = rig.matrix_world @ pb.matrix
            M.translation.z += corr[f - f0]
            pb.matrix = rig.matrix_world.inverted() @ M
            bpy.context.view_layer.update()
            pb.keyframe_insert('location', frame=f)
    set_act(None)
    return [round(min(stats) * 100, 1), round(max(stats) * 100, 1)]


for name, mode in (('Standing', 'sole'), ('Attack', 'sole'), ('Hit', 'sole'), ('Fidget', 'sole'),
                   ('Death', 'all'), ('Dead', 'all'), ('Walking', 'sole'), ('Running', 'lift')):
    r = floor(name, mode)
    print(f'CLIP {name}: floor mode {mode}, lowest point before correction cm min {r[0]} max {r[1]}')
    report.setdefault(name, {})['floor_before_cm'] = r

for x in [a for a in A if a.name not in ('Standing', 'Walking', 'Running', 'Attack', 'Hit', 'Death', 'Dead', 'Fidget')]:
    A.remove(x)
for a in A:
    report.setdefault(a.name, {})['duration'] = round(a.frame_range[1] / FPS, 3)
json.dump(report, open(os.path.join(HERE, 'work', 'clip_timing.json'), 'w'), indent=1)
print('CLIP timing', json.dumps({k: v.get('impact', v['duration']) for k, v in report.items()}))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(OUT_BLEND))
