"""Sprint (full-speed half-bound) for the MM7 rat (2026-10-31), for the MAW ruleset's chase: Rat A-C chase at
16.16 model units/s there (Spd / 2 + 300, doubled), about 1.7 times Standard's chase that Run2 (8.96) is authored for.
The engine plays one loop per stride of travel, so a faster monster needs a longer stride, not quicker legs.

The extra stride comes from the flight, not the legs (their reach is limited, as in Run2): the same half-bound footfall
order and phases as Run2 (hind L at 0, so a walk/run/sprint switch on the shared gait phase does not jump), a lower
duty factor, a long extended flight (hinds trailing, fronts reaching) and a long gathered flight (hinds swung forward
under the flexed back), strong spine flexion and extension, the body rising through both flights.

Same rig, IK, toe planting and floor rules as gait2_rat7.py (kept unchanged), with:
  - footholds planned against the posed body: the shoulder/hip positions over each stance come from the spine flex,
    rocking and bob of that phase, so the stance can use the reach the lowered, flexed body gives;
  - the front paws reach ahead of their foothold late in swing and the hind paws trail behind theirs early in swing,
    which shows the extended flight.
Keys at 60 fps. Reads work/anim_v2u.blend (unchanged), saves work/sprint.blend and writes the Sprint clip (only) to
the GLB given as argument, to be grafted onto the installed export with ../../claude_shared/graft_clips.py.
Args: -- <out clips.glb>"""
import bpy, os, sys, math, json
import numpy as np
from mathutils import Vector, Matrix, Quaternion

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import posing as P

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.abspath(sys.argv[sys.argv.index('--') + 1])
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'anim_v2u.blend'))
rig = bpy.data.objects['Rig']; mesh = bpy.data.objects['Body']
FPS = 60
REACH = 0.97                    # wrist/ankle distance from the shoulder/hip, at most this share of the chain
TOE_CLEAR = 0.0015              # planted toe tip above its rest height
HALF_BOUND = {'hind_L': 0.0, 'hind_R': 0.06, 'front_L': 0.44, 'front_R': 0.52}   # Run2: fronts 0.42 / 0.52
CLIPS = {
    # speed (model units/s), frames at 60 fps, footfall phases, duty, swing lift front/hind, heel lift at push-off
    # (deg), body bob, rocking (hips pitch, deg), back flex (deg), spine yaw, tail sway; reach/trail: the paws' swing
    # overshoot ahead of the foothold (fronts) and behind the lift-off (hinds), m; counter: share of the back flex the
    # hips take back, so the flex arches and dips the back between level shoulders and hips
    'Sprint': dict(speed=13.2, frames=15, feet=HALF_BOUND, duty=0.18, lift_f=0.13, lift_h=0.13, heel=45, bob=0.06,
                   rock=8.0, rock_phase=0.42, flex=26.0, flex_phase=0.85, yaw=1.0, tail=8, base=0.045, bob_phase=0.12,
                   head_level=1.0, head_up=2.0, reach=0.05, trail=0.10, counter=0.45),
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
    pole = wrist + (Vector((SIDE[side] * 0.03, 0.3, 0.08)) if kind == 'front' else Vector((SIDE[side] * 0.03, -0.3, 0.18)))
    P.two_bone_ik(rig, upper, lower, wrist, pole)
    set_world_rot(paw, q @ REST[paw].to_quaternion())
    return ((W @ rig.pose.bones[paw].matrix @ PAW_LOCAL[foot]) - toe).length


def tail_wave(sway, pitch, phase, lift=0.0):
    """anim_rat7.py tail without the strike: sway about each segment's up axis, lift and wave about the hips' side axis"""
    side = (W @ rig.pose.bones['Spine1'].matrix).to_3x3() @ (REST['Spine1'].to_3x3().inverted() @ X)
    for i in range(1, 7):
        k = i / 6
        b = rig.pose.bones[f'Tail{i}']
        up = (W @ b.matrix).to_3x3() @ Vector((0, 0, 1))
        rot(f'Tail{i}', up.normalized(), sway * (0.3 + 0.7 * k) * math.sin(2 * math.pi * (phase - 0.1 * i)))
        rot(f'Tail{i}', side.normalized(), -lift * (1 - k) * 0.8 - pitch * k * math.sin(2 * math.pi * (phase - 0.1 * i)))


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
CORE = np.array([n.startswith(('Spine', 'Neck', 'Head', 'Thigh', 'UpperArm')) for n in _dom])
PAWS = np.array([n.startswith(('FrontPaw', 'HindPaw')) for n in _dom])


def mesh_co():
    dg = bpy.context.evaluated_depsgraph_get(); ev = mesh.evaluated_get(dg); me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); ev.to_mesh_clear()
    co = co.reshape(-1, 3)
    return co @ np.array(W.to_3x3()).T + np.array(W.translation)


def clamp_tail():
    """anim_rat7.py: tail segments 2-6 keep their ends 3 cm above the floor."""
    for i in range(2, 7):
        b = rig.pose.bones[f'Tail{i}']
        t = W @ b.tail
        if t.z < 0.03:
            h = W @ b.head; d = t - h; L = d.length
            flat = Vector((d.x, d.y, 0)).normalized(); dz = 0.03 - h.z
            P.aim_bone(rig, b.name, h + flat * math.sqrt(max(L * L - dz * dz, 1e-6)) + Vector((0, 0, dz)) if abs(dz) < L
                       else h + flat * L)


REST_CO = mesh_co()


def contact(foot):
    """The paw's front-most vertex within 4 mm of its lowest one at rest: the point it rolls over at push-off."""
    co = REST_CO[_dom == bones(foot)[2]]
    low = co[co[:, 2] < co[:, 2].min() + 0.004]
    return Vector(low[np.argmin(low[:, 1])])


# the paw is planted by this contact point, TOE_CLEAR above the floor; TOE is redefined as it
for _f in FEET:
    TOE[_f] = contact(_f) + Vector((0, 0, TOE_CLEAR - contact(_f).z))
for _k in ('front', 'hind'):                  # the same place along the body on both sides (the rest pose is uneven)
    _y = (TOE[f'{_k}_L'].y + TOE[f'{_k}_R'].y) / 2
    for _s in 'LR':
        TOE[f'{_k}_{_s}'].y = _y
for _f in FEET:
    PAW_VEC[_f] = TOE[_f] - WRIST[_f]
TOE_Z = {f: TOE[f].z for f in FEET}
PAW_LOCAL = {f: (W @ rig.pose.bones[bones(f)[2]].matrix).inverted() @ TOE[f] for f in FEET}


# ---------------------------------------------------------------- footholds
def heel(c, foot, q, duty):
    """Paw pitch over the stance (heel lifts over its last 40 %) and swing (paw tucks, then reaches flat)."""
    if q < duty:
        u = q / duty
        return c['heel'] * ss((u - 0.6) / 0.4)
    u = (q - duty) / (1 - duty)
    tuck = 25 if foot.startswith('front') else -15     # the long hind foot tips its toes up (anim_rat7.py)
    return c['heel'] * (1 - ss(u / 0.35)) + tuck * math.sin(math.pi * min(1.0, u / 0.8))


def pose_body(p, c):
    """The body of the gait at phase p (no legs): rocking, back flex, bob, head and tail."""
    P.reset(rig)
    rock = c['rock'] * math.sin(2 * math.pi * (p - c['rock_phase']))
    flex = c['flex'] * math.cos(2 * math.pi * (p - c['flex_phase']))
    bob = c['base'] - c['bob'] * (0.5 + 0.5 * math.cos(4 * math.pi * (p - c['bob_phase'])))  # low at the stances
    hips = rock - c['counter'] * flex             # the hips counter-pitch: the back bends, shoulders keep their height
    body(hips_d=Vector((0, 0, bob)), hips_pitch=hips, spine_pitch=flex, spine_yaw=c['yaw'] * math.sin(2 * math.pi * p),
         head_pitch=-c['head_level'] * (hips + flex) - c['head_up'] - 2 * math.cos(4 * math.pi * p),
         head_yaw=-2 * math.sin(2 * math.pi * p))
    tail_wave(c['tail'], 4 + 0.5 * c['rock'], p, lift=6 + rock)


def plan(c, foot, sweep):
    """Shift of the foothold along the body (dy, + = backward) keeping wrist/ankle within REACH over the stance, from
    the shoulder/hip of the posed body at each stance phase."""
    samples = []
    for k in np.linspace(0, 1, 11):
        pose_body((c['feet'][foot] + k * c['duty']) % 1.0, c)
        samples.append((k, head_of(bones(foot)[0])))
    best = None
    for dy in np.linspace(-0.2, 0.2, 81):
        worst = 0.0
        for k, shoulder in samples:
            toe = Vector((TOE[foot].x, TOE[foot].y + dy - sweep / 2 + sweep * k, TOE_Z[foot]))
            a = c['heel'] * ss((k - 0.6) / 0.4)
            wrist = toe - Quaternion(X, math.radians(a)) @ PAW_VEC[foot]
            worst = max(worst, (wrist - shoulder).length / CHAIN[foot])
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
        y0 = TOE[foot].y + centres[foot]
        if q < duty:
            y = y0 - s / 2 + s * (q / duty); z = 0.0
        else:
            u = (q - duty) / (1 - duty)
            y = y0 + s / 2 - s * ss(u); z = (c['lift_f'] if foot.startswith('front') else c['lift_h']) * math.sin(math.pi * u)
            if foot.startswith('front'):         # reach ahead of the foothold late in swing, back onto it at the strike
                y -= c['reach'] * math.sin(math.pi * min(1.0, max(0.0, (u - 0.4) / 0.6)))
            else:                                # trail behind the lift-off early in swing
                y += c['trail'] * math.sin(math.pi * min(1.0, u / 0.45))
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
