"""Sprint (bounding gallop) for the rat (2026-10-31): a third locomotion clip for the fast chase of the MAW ruleset
(fast melee monsters at Spd / 2 + 300, doubled while chasing). The engine plays one loop per stride of travel and picks
walk, run or sprint by how well each clip's authored speed fits (ActorModelPresentation.h, actorModelGait);
gait_gate.py targets a sprint of about 3.06 model units/s (fits 2.42-3.87). Run2 (gait2_rat.py, 0.51 m in 0.2833 s)
would play at x1.6-2.0 there and pedal.

A longer stride at about the same cadence: the legs' reach is the limit (front chain 0.14 m; a longer stride needs a
shorter stance, not a bigger reach), so the extra stride comes from the time the body spends in the air and from the
body itself moving relative to its average travel:
  - duty 0.22 (Run2 0.32): hind support, an extended flight, front support and a longer gathered flight; footfall
    order and phases as Run2 (hinds near 0, fronts near 0.45), so the engine's shared gait phase does not jump when it
    switches between them;
  - surge: the body lags its average travel while feet are planted and catches up in the flights (the body travelling
    during flight), so a planted paw covers less ground relative to its shoulder or hip than the stride x duty it
    covers on the floor;
  - the back flexes hard in the gathered flight (hinds swinging under the body) and extends in the extended flight
    (fronts reaching), with rocking and a bob that is high in the flights and low at mid stance; the head stays level;
  - swing paths follow through backward after the push-off and reach forward before the strike.
Footholds are planned per limb against the posed shoulder or hip over the stance (surge, bob, flex and rock included).
Floor rules, toe-tip planting, paw pitch and IK as gait2_rat.py (which is unchanged).

Keys at 60 fps. Reads work/anim_v1.blend (unchanged), saves work/sprint.blend and writes the Sprint clip (only) to the
GLB given as argument, to be grafted onto the installed export with ../../claude_shared/graft_clips.py.
Args: -- <out clips.glb>"""
import bpy, os, sys, math, json
import numpy as np
from mathutils import Vector, Matrix, Quaternion

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import posing as P

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.abspath(sys.argv[sys.argv.index('--') + 1])
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'anim_v1.blend'))
rig = bpy.data.objects['Rat_Rig']; mesh = bpy.data.objects['Rat']
FPS = 60
REACH = 0.97                    # wrist/ankle distance from the shoulder/hip, at most this share of the chain
TOE_CLEAR = 0.0015              # planted toe tip above its rest height
BOUND = {'hind_L': 0.0, 'hind_R': 0.05, 'front_L': 0.43, 'front_R': 0.50}
# Periodic curves over the gait phase, as (phase, value) keys through which a closed Catmull-Rom spline passes.
# Hind support 0-0.27, extended flight 0.27-0.43, front support 0.43-0.72, gathered flight 0.72-1.
CLIPS = {
    'Sprint': dict(
        speed=3.2, frames=16, feet=BOUND, duty=0.22, lift_f=0.065, lift_h=0.06, heel=50, tuck_f=40, tuck_h=28,
        follow_f=0.03, follow_h=0.012, reach_f=0.035, reach_h=0.02,
        # back flex (deg, + = arched): gathered over the hinds' landing, extended in the extended flight
        flex=[(0.0, 10.0), (0.14, 2.0), (0.30, -9.0), (0.42, -8.0), (0.58, -3.0), (0.72, 6.0), (0.86, 14.0)],
        # net pitch of the front body (deg, + = front down; the hips pitch by this minus the flex, so the rump tucks
        # under in the gathered flight and rises behind a low chest in the extended one): the front rises through
        # the hind push-off and lowers to meet the floor for the front strike
        pitch=[(0.0, -2.0), (0.14, -5.0), (0.30, -3.0), (0.42, 2.0), (0.58, 4.0), (0.72, 0.0), (0.86, -3.0)],
        # body height (m): low at mid support, high in the flights
        bob=[(0.0, -0.004), (0.13, -0.014), (0.33, 0.006), (0.43, -0.002), (0.58, -0.014), (0.75, -0.002),
             (0.88, 0.008)],
        # surge (m, + = backward): the body lags over each support and catches up in the flight after it
        surge=[(0.0, -0.013), (0.27, 0.012), (0.43, -0.012), (0.72, 0.013)],
        yaw=1.0, tail=6, head_level=1.0, head_up=4.0),
}
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
P.reset(rig)
for b in rig.pose.bones:
    b.rotation_mode = 'QUATERNION'
bpy.context.view_layer.update()
W = rig.matrix_world
REST = {b.name: (W @ b.matrix).copy() for b in rig.pose.bones}
SIDE = {'L': 1.0, 'R': -1.0}
LIMB = {'front': ('UpperArm', 'ForeArm', 'FrontPaw'), 'hind': ('Thigh', 'Shin', 'HindPaw')}
FEET = [f'{k}_{s}' for k in ('front', 'hind') for s in 'LR']


def bones(foot):
    kind, side = foot.split('_')
    return [f'{n}_{side}' for n in LIMB[kind]]


def head_of(name):
    return (W @ rig.pose.bones[name].head).copy()


def tail_of(name):
    return (W @ rig.pose.bones[name].tail).copy()


SHOULDER = {f: head_of(bones(f)[0]) for f in FEET}
WRIST = {f: head_of(bones(f)[2]) for f in FEET}
TOE = {f: tail_of(bones(f)[2]) for f in FEET}
PAW_VEC = {f: TOE[f] - WRIST[f] for f in FEET}
CHAIN = {f: rig.pose.bones[bones(f)[0]].length + rig.pose.bones[bones(f)[1]].length for f in FEET}


def ss(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def curve(keys, p):
    """Closed Catmull-Rom spline through (phase, value) keys, evaluated at phase p."""
    n = len(keys)
    ph = [k[0] for k in keys]; va = [k[1] for k in keys]
    p %= 1.0
    i = max(j for j in range(n) if ph[j] <= p) if p >= ph[0] else n - 1
    p0, p1 = ph[i], ph[(i + 1) % n] + (1.0 if i + 1 >= n else 0.0)
    pp = p if p >= p0 else p + 1.0
    t = (pp - p0) / (p1 - p0)
    a, b, c_, d = va[(i - 1) % n], va[i], va[(i + 1) % n], va[(i + 2) % n]
    return 0.5 * ((2 * b) + (-a + c_) * t + (2 * a - 5 * b + 4 * c_ - d) * t * t + (-a + 3 * b - 3 * c_ + d) * t ** 3)


def rot(name, axis, deg, pivot=None):
    if abs(deg) > 1e-6:
        P.rotate_world(rig, name, axis, deg, pivot)


def set_world_rot(name, q):
    b = rig.pose.bones[name]
    b.matrix = Matrix.LocRotScale(b.head.copy(), q, Vector((1, 1, 1))); bpy.context.view_layer.update()


PAW_LOCAL = {}


def place_toe(foot, toe, pitch):
    """IK the limb so the paw, pitched by `pitch` degrees (+ = heel up / toes down), ends with its toe at `toe`."""
    kind, side = foot.split('_')
    upper, lower, paw = bones(foot)
    q = Quaternion(X, math.radians(pitch))
    wrist = toe - q @ PAW_VEC[foot]
    pole = wrist + (Vector((SIDE[side] * 0.05, 0.25, 0.05)) if kind == 'front' else Vector((SIDE[side] * 0.04, -0.25, 0.10)))
    P.two_bone_ik(rig, upper, lower, wrist, pole)
    set_world_rot(paw, q @ REST[paw].to_quaternion())
    return ((W @ rig.pose.bones[paw].matrix @ PAW_LOCAL[foot]) - toe).length


def tail_wave(amp_yaw, amp_pitch, phase, lift=0.0):
    for i in range(1, 7):
        k = i / 6.0
        rot(f'Tail{i}', Z, amp_yaw * k * math.sin(2 * math.pi * (phase - 0.09 * i)))
        rot(f'Tail{i}', X, (lift if i == 1 else lift * 0.15) + amp_pitch * math.sin(2 * math.pi * (phase - 0.09 * i)))


def body(hips_d=Vector(), hips_pitch=0.0, spine_pitch=0.0, spine_yaw=0.0, head_pitch=0.0, head_yaw=0.0):
    root = rig.pose.bones['Spine1']
    root.matrix = Matrix.Translation(hips_d) @ root.matrix; bpy.context.view_layer.update()
    rot('Spine1', X, hips_pitch)
    for n, s in (('Spine2', 0.5), ('Spine3', 0.5)):
        rot(n, X, spine_pitch * s); rot(n, Z, spine_yaw * s)
    rot('Neck1', X, head_pitch * 0.4); rot('Head', X, head_pitch * 0.6)
    rot('Neck1', Z, head_yaw * 0.5); rot('Head', Z, head_yaw * 0.5)


# ---------------------------------------------------------------- floor (anim_rat.py rules)
_names = [g.name for g in mesh.vertex_groups]
_dom = np.array([_names[max(v.groups, key=lambda g: g.weight).group] if v.groups else '' for v in mesh.data.vertices])
CORE = np.array([n.startswith(('Spine', 'Neck', 'Head', 'Thigh', 'UpperArm', 'ForeArm', 'Shin')) for n in _dom])


def mesh_co():
    dg = bpy.context.evaluated_depsgraph_get(); ev = mesh.evaluated_get(dg); me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); ev.to_mesh_clear()
    co = co.reshape(-1, 3)
    return co @ np.array(W.to_3x3()).T + np.array(W.translation)


def clamp_tail():
    """Raise any tail segment whose end dips under the floor (bone by bone, base to tip)."""
    for i in range(1, 7):
        b = rig.pose.bones[f'Tail{i}']
        t = W @ b.tail
        if t.z < 0.012:
            h = W @ b.head
            d = t - h; L = d.length
            flat = Vector((d.x, d.y, 0)).normalized()
            dz = 0.012 - h.z
            target = h + flat * math.sqrt(max(L * L - dz * dz, 1e-6)) + Vector((0, 0, dz)) if abs(dz) < L else h + flat * L
            P.aim_bone(rig, b.name, target)


REST_CO = mesh_co()


def contact(foot):
    """The paw's front-most vertex within 4 mm of its lowest one at rest: the point it rolls over at push-off."""
    co = REST_CO[_dom == bones(foot)[2]]
    low = co[co[:, 2] < co[:, 2].min() + 0.004]
    return Vector(low[np.argmin(low[:, 1])])


# the paw is planted by this contact point, TOE_CLEAR above the floor; TOE is redefined as it
for _f in FEET:
    TOE[_f] = contact(_f) + Vector((0, 0, TOE_CLEAR - contact(_f).z))
    PAW_VEC[_f] = TOE[_f] - WRIST[_f]
TOE_Z = {f: TOE[f].z for f in FEET}
PAW_LOCAL = {f: (W @ rig.pose.bones[bones(f)[2]].matrix).inverted() @ TOE[f] for f in FEET}


# ---------------------------------------------------------------- body and footholds
def heel(c, foot, q, duty):
    """Paw pitch over the stance (heel lifts over its last 40 %) and swing (paw tucks, then reaches flat)."""
    if q < duty:
        u = q / duty
        return c['heel'] * ss((u - 0.6) / 0.4)
    u = (q - duty) / (1 - duty)
    tuck = c['tuck_f'] if foot.startswith('front') else c['tuck_h']
    return c['heel'] * (1 - ss(u / 0.35)) + tuck * math.sin(math.pi * min(1.0, u / 0.8))


def pose_body(p, c):
    P.reset(rig)
    flex = curve(c['flex'], p)
    rock = curve(c['pitch'], p) - flex
    body(hips_d=Vector((0, curve(c['surge'], p), curve(c['bob'], p))), hips_pitch=rock, spine_pitch=flex,
         spine_yaw=c['yaw'] * math.sin(2 * math.pi * p),
         head_pitch=-c['head_level'] * curve(c['pitch'], p) - c['head_up'] - 2 * math.cos(4 * math.pi * p),
         head_yaw=-1.5 * math.sin(2 * math.pi * p))
    tail_wave(c['tail'], 4, p, lift=6 + 0.5 * rock)
    return rock


def plan(c, foot, sweep):
    """Shift of the foothold along the body (dy, + = backward) keeping the wrist/ankle within REACH of the posed
    shoulder/hip over the stance (surge, bob, flex and rock included)."""
    phase, duty = c['feet'][foot], c['duty']
    ks = np.linspace(0, 1, 11)
    joints = []
    for k in ks:
        pose_body(phase + duty * k, c)
        joints.append(head_of(bones(foot)[0]))
    best = None
    for dy in np.linspace(-0.15, 0.15, 121):
        worst = 0.0
        for k, joint in zip(ks, joints):
            toe = Vector((TOE[foot].x, TOE[foot].y + dy - sweep / 2 + sweep * k, TOE_Z[foot]))
            a = c['heel'] * ss((k - 0.6) / 0.4)
            wrist = toe - Quaternion(X, math.radians(a)) @ PAW_VEC[foot]
            worst = max(worst, (wrist - joint).length / CHAIN[foot])
        cost = 100 * max(0.0, worst - REACH) + abs(dy)
        if best is None or cost < best[0]:
            best = (cost, dy, worst)
    return best


def gait(p, c, centres, stride):
    pose_body(p, c)
    miss = 0.0
    for foot, phase in c['feet'].items():
        duty = c['duty']
        s = stride * duty
        q = (p - phase) % 1.0
        front = foot.startswith('front')
        y0 = TOE[foot].y + centres[foot]
        if q < duty:
            y = y0 - s / 2 + s * (q / duty); z = 0.0
        else:
            u = (q - duty) / (1 - duty)
            # follow-through backward after the push-off, reach forward before the strike (both ease to 0 at the ends)
            follow = (c['follow_f'] if front else c['follow_h']) * math.sin(math.pi * min(1.0, u / 0.45))
            reach = (c['reach_f'] if front else c['reach_h']) * math.sin(math.pi * max(0.0, (u - 0.45) / 0.55))
            y = y0 + s / 2 - s * ss(u) + follow - reach
            z = (c['lift_f'] if front else c['lift_h']) * math.sin(math.pi * u) ** 0.8
        pitch = heel(c, foot, q, duty)
        if q >= duty and pitch < 0:                  # toes up in swing: the paw turns about its toe, lift the heel clear
            z += -math.sin(math.radians(pitch)) * PAW_VEC[foot].length
        m = place_toe(foot, Vector((TOE[foot].x, y, TOE_Z[foot] + z)), pitch)
        if m > 0.004:
            MISSES.setdefault(foot, []).append((round(p, 2), round(q, 2), round(m * 1000, 1)))
        miss = max(miss, m)
    clamp_tail()
    return miss


MISSES = {}


def key_action(name, n, fn):
    old = bpy.data.actions.get(name)
    if old:
        bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name); act.use_fake_user = True
    if rig.animation_data is None:
        rig.animation_data_create()
    rig.animation_data.action = None
    poses, lows, core_lows, miss = [], [], [], 0.0
    for f in range(n + 1):
        miss = max(miss, fn((f % n) / n))
        co = mesh_co()
        lows.append(float(co[:, 2].min())); core_lows.append(float(co[CORE, 2].min()))
        if os.environ.get('GAIT_DEBUG') and lows[-1] < -0.003:
            i = int(np.argmin(co[:, 2]))
            print(f'LOW {name} f{f}: {_dom[i]} {co[i].round(3)}', flush=True)
        poses.append({b.name: (b.rotation_quaternion.copy(), b.location.copy()) for b in rig.pose.bones})
    rig.animation_data.action = act
    if len(getattr(act, 'slots', [])):
        rig.animation_data.action_slot = act.slots[0]
    prev = {}
    for f, pose in enumerate(poses):
        for b in rig.pose.bones:
            q, loc = pose[b.name]
            if b.name in prev and prev[b.name].dot(q) < 0:
                q = -q
            prev[b.name] = q
            b.rotation_quaternion = q; b.location = loc
            b.keyframe_insert('rotation_quaternion', frame=f)
            b.keyframe_insert('location', frame=f)
    act.use_frame_range = True; act.frame_start, act.frame_end = 0, n
    rig.animation_data.action = None
    return act, min(lows), max(lows), miss, min(core_lows)


info = {}
for name, c in CLIPS.items():
    T = c['frames'] / FPS
    stride = c['speed'] * T
    centres = {}
    for foot in FEET:
        cost, dy, worst = plan(c, foot, stride * c['duty'])
        centres[foot] = dy
        print(f'PLAN {name} {foot}: dy {dy:+.3f} reach {worst:.2f} of chain', flush=True)
    act, low, high, miss, core = key_action(name, c['frames'], lambda p: gait(p, c, centres, stride))
    info[name] = {'seconds': T, 'stride': round(stride, 4), 'authored_speed': c['speed'], 'sweep': stride * c['duty'],
                  'lowest': [low, high], 'core_lowest': core, 'toe_miss': miss}
    print(f'CLIP {name}: {T:.4f} s, stride {stride:.4f} m, sweep {stride * c["duty"]:.3f} m, lowest vertex '
          f'{low * 100:+.2f}..{high * 100:+.2f} cm, core {core * 100:+.2f} cm, worst toe miss {miss * 1000:.1f} mm',
          flush=True)
    for foot, rows in MISSES.items():
        print(f'MISS {name} {foot}: {rows[:8]}', flush=True)
    MISSES.clear()
json.dump(info, open(os.path.join(HERE, 'work', 'sprint_info.json'), 'w'), indent=1)
P.reset(rig)
bpy.context.scene.render.fps = FPS; bpy.context.scene.render.fps_base = 1
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'sprint.blend'))
for a in list(bpy.data.actions):
    if a.name not in CLIPS:
        bpy.data.actions.remove(a)
for o in bpy.data.objects:
    o.select_set(o in (mesh, rig))
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=OUT, use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_all_influences=False, export_materials='NONE',
                          export_attributes=False, export_morph=False, export_reset_pose_bones=True,
                          export_anim_slide_to_zero=True)
print('EXPORTED', OUT)
