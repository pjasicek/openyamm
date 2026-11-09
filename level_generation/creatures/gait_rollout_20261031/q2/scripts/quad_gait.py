"""New locomotion clips for the q2 quadrupeds of the 2026-10-31 gait rollout (MM7 rat m382 for zrat, MM7 dog m509,
MM7 cat 7m500, MM8 Dire Wolf), authored for the game's speeds (gait_gate.py targets). The engine plays one loop per
stride of travel, so a clip is defined by its stride (authored speed x length) and footfall phases.

The machinery is ../../../mm7_m382_claude/scripts/sprint_rat7.py's (copied, the pilot is left unchanged): every paw
planted by its contact point (the toe), the wrist/ankle following it through two-bone IK, the heel lifting at push-off;
footholds planned per limb against the posed body (shoulder/hip of each stance phase) so the wrist/ankle stays inside
REACH of the chain; the swing paw reaching ahead (fronts) or trailing (hinds) for flights; floor rules (tail ends kept
above the floor, lowest vertex reported). Per model a style keeps the look of the model's installed walk (body pitch,
tail carriage), so a switch between walk, run and sprint on the engine's shared gait phase does not jump: every clip
strikes the same foot at phase 0 as the model's walk.

Reads the model project's editable blend (read only), saves <package>/work/<model>_gaits.blend and writes only the new
clips to the GLB given, to be grafted onto the installed source with ../../claude_shared/graft_clips.py.

    blender -b --factory-startup -P quad_gait.py -- <model> <out clips.glb>      model: m382 | m509 | 7m500 | wolf
"""
import bpy, os, sys, math, json
import numpy as np
from mathutils import Vector, Matrix, Quaternion

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))          # the q2 package
CREATURES = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(CREATURES, 'mm6_rat_claude', 'scripts'))
import posing as P  # noqa: E402

KEY, OUT = sys.argv[sys.argv.index('--') + 1:]
OUT = os.path.abspath(OUT)
FPS = 60
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))

# Footfall phases (touchdown, 0-1). Each model's new clips strike the foot its installed walk strikes at 0.
LOPE = {'hind_L': 0.0, 'hind_R': 0.12, 'front_R': 0.40, 'front_L': 0.52}          # m382 Walk2's
TROT_FL = {'front_L': 0.0, 'hind_R': 0.0, 'front_R': 0.5, 'hind_L': 0.5}         # dog and wolf Walking: FL+HR at 0
TROT_HL = {'hind_L': 0.0, 'front_R': 0.0, 'hind_R': 0.5, 'front_L': 0.5}         # cat Walking: HL at 0, FR at 0.25
ROTARY_HR = {'hind_R': 0.0, 'hind_L': 0.07, 'front_L': 0.42, 'front_R': 0.51}    # gallop, HR at 0 as the wolf's walk

# Clip parameters: speed (model units/s), frames at 60 fps, footfall phases, duty, swing lift front/hind (m), heel
# lift at push-off (deg), swing tuck front/hind (deg, + = toes down), bob (m) and its phase and harmonic (2 = twice a
# loop), base (body height offset, m), rocking (hips pitch, deg) and its phase/harmonic, back flex (deg) and its
# phase/harmonic, counter (share of the flex the hips take back), spine yaw (deg), head level/up (deg), tail sway (deg),
# reach/trail (swing overshoot of fronts ahead of the foothold and hinds behind the lift-off, m).
COMMON = dict(heel=30, tuck_f=25, tuck_h=-15, bob=0.0, bob_phase=0.0, bob_harm=2, base=0.0, rock=0.0,
              rock_phase=0.0, rock_harm=1, flex=0.0, flex_phase=0.0, flex_harm=1, counter=0.0, yaw=2.0,
              head_level=0.9, head_up=0.0, tail=10, reach=0.0, trail=0.0)
MODELS = {
    # MM7 rat: Walk3, a slower lope for the arena zrats (Standard wander 2.80; Walk2 4.48 played x0.63). Same
    # rotary lope phases as Walk2, longer stances (no suspension), lower cadence.
    'm382': dict(blend='mm7_m382_claude/work/anim_v2u.blend', rig='Rig', mesh='Body', style='rat',
                 tail_floor=0.03, contact_band=0.004, plan_range=0.2, toe_clear=0.0015,
                 clips={'Walk3': dict(COMMON, speed=2.90, frames=16, feet=LOPE, duty=0.52, lift_f=0.09, lift_h=0.08,
                                      heel=30, bob=0.012, bob_phase=0.2, rock=1.0, rock_phase=0.45, flex=2.5, counter=0.5,
                                      flex_phase=0.9, yaw=2.0, tail=10, head_level=0.9)}),
    # MM7 dog: Trot, a fast flying trot for Standard's chase (2.36; the walk played x2.12), same diagonal phases as
    # the installed trot walk (FL+HR at 0), short suspensions, the body lowered a little.
    'm509': dict(blend='mm7_m509_claude/work/anim_v2u.blend', rig='Rig', mesh='Body', style='dog',
                 tail_floor=0.03, contact_band=0.004, plan_range=0.2, toe_clear=0.0015,
                 clips={'Trot': dict(COMMON, speed=2.23, frames=26, feet=TROT_FL, duty=0.40, lift_f=0.09, lift_h=0.08,
                                     heel=30, tuck_h=20, bob=0.012, bob_phase=0.2, base=-0.03, rock=0.5, rock_harm=2,
                                     rock_phase=0.1, flex=1.0, flex_harm=2, flex_phase=0.2, yaw=3.0, tail=12,
                                     head_level=0.6, reach=0.02, trail=0.03)}),
    # MM7 cat: Trot for Standard's chase (1.40; the walk played x1.99), diagonal pairs with HL+FR at 0 (the walk's HL
    # strike), crouched a little as a hurrying cat.
    '7m500': dict(blend='mm7_7m500_claude/work/anim_v2u.blend', rig='Rig', mesh='Body', style='dog',
                  tail_floor=0.015, contact_band=0.003, plan_range=0.1, toe_clear=0.001,
                  clips={'Trot': dict(COMMON, speed=1.32, frames=22, feet=TROT_HL, duty=0.42, lift_f=0.045,
                                      lift_h=0.04, heel=30, tuck_h=20, bob=0.006, bob_phase=0.21, base=-0.025,
                                      rock=0.5, rock_harm=2, rock_phase=0.1, flex=1.0, flex_harm=2, flex_phase=0.21,
                                      yaw=3.0, tail=12, head_level=0.6, reach=0.01, trail=0.015)}),
    # MM8 Dire Wolf: Walk2 (trot, Standard wander 0.98-1.16), Run2 (flying trot, Standard chase 1.97-2.32) and Sprint
    # (rotary gallop, MAW chase 2.85-3.68). The installed Walking/Running (0.34 and 0.77) played x3 and x1.5-3.
    'wolf': dict(blend='mm8_m512_claude/work/anim_v1.blend', rig='Wolf_Rig', mesh='Wolf', style='wolf',
                 tail_floor=0.03, contact_band=0.004, plan_range=0.15, toe_clear=0.0025,
                 clips={
                     'Walk2': dict(COMMON, speed=1.01, frames=27, feet=TROT_FL, duty=0.56, lift_f=0.05, lift_h=0.045,
                                   heel=25, tuck_h=20, bob=0.006, bob_phase=0.28, base=-0.012, rock=0.0, rock_harm=2,
                                   rock_phase=0.1, flex=0.4, flex_harm=2, flex_phase=0.28, yaw=2.0, tail=4,
                                   head_level=0.6, pitch0=7, head0=-4, tail_lift=-35, head_hold=0.4),
                     'Run2': dict(COMMON, speed=2.01, frames=21, feet=TROT_FL, duty=0.38, lift_f=0.07, lift_h=0.06,
                                  heel=30, tuck_h=20, bob=0.01, bob_phase=0.19, base=-0.01, rock=0.3, rock_harm=2,
                                  rock_phase=0.1, flex=0.6, flex_harm=2, flex_phase=0.19, yaw=2.0, tail=5,
                                  head_level=0.6, pitch0=7, head0=-4, tail_lift=-30, reach=0.015, trail=0.02,
                                  head_hold=0.4),
                     'Sprint': dict(COMMON, speed=3.06, frames=25, feet=ROTARY_HR, duty=0.22, lift_f=0.08, lift_h=0.08,
                                    heel=30, tuck_h=20, bob=0.025, bob_phase=0.12, base=0.012, rock=5.0,
                                    rock_phase=0.42, flex=16.0, flex_phase=0.85, counter=0.55, yaw=1.0, tail=6,
                                    head_level=1.0, head_up=2.0, pitch0=4, head0=-4, tail_lift=-25, reach=0.03, trail=0.05,
                                    head_hold=0.7)}),
}
M = MODELS[KEY]
CLIPS = M['clips']
# Tuning: QG_SET="Clip:key=value,key=value;Clip:..." overrides clip parameters for a trial run.
for _item in filter(None, os.environ.get('QG_SET', '').split(';')):
    _clip, _pairs = _item.split(':', 1)
    for _pair in _pairs.split(','):
        _k, _v = _pair.split('=')
        CLIPS[_clip][_k] = type(CLIPS[_clip].get(_k, 0.0))(float(_v))
REACH = 0.97                    # wrist/ankle distance from the shoulder/hip, at most this share of the chain

bpy.ops.wm.open_mainfile(filepath=os.path.join(CREATURES, M['blend']))
rig = bpy.data.objects[M['rig']]; mesh = bpy.data.objects[M['mesh']]
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
    """The rat's and dog's tail: sway about each segment's up axis, lift and wave about the hips' side axis."""
    side = (W @ rig.pose.bones['Spine1'].matrix).to_3x3() @ (REST['Spine1'].to_3x3().inverted() @ X)
    for i in range(1, 7):
        k = i / 6
        b = rig.pose.bones[f'Tail{i}']
        up = (W @ b.matrix).to_3x3() @ Vector((0, 0, 1))
        rot(f'Tail{i}', up.normalized(), sway * (0.3 + 0.7 * k) * math.sin(2 * math.pi * (phase - 0.1 * i)))
        rot(f'Tail{i}', side.normalized(), -lift * (1 - k) * 0.8 - pitch * k * math.sin(2 * math.pi * (phase - 0.1 * i)))


def tail_wolf(sway, phase, lift):
    """animate_wolf.py's tail: Tail1 lowered by `lift` about world X, every segment swaying about world Z."""
    for i in range(1, 7):
        rot(f'Tail{i}', X, lift if i == 1 else 0)
        rot(f'Tail{i}', Z, sway * i / 6 * math.sin(2 * math.pi * phase - i * 0.4))


def body(hips_d=Vector(), hips_pitch=0.0, spine_pitch=0.0, spine_yaw=0.0, head_pitch=0.0, head_yaw=0.0):
    root = rig.pose.bones['Spine1']
    root.matrix = Matrix.Translation(hips_d) @ root.matrix; bpy.context.view_layer.update()
    rot('Spine1', X, hips_pitch)
    for n, s in (('Spine2', 0.5), ('Spine3', 0.5)):
        rot(n, X, spine_pitch * s); rot(n, Z, spine_yaw * s)
    rot('Neck1', X, head_pitch * 0.4); rot('Head', X, head_pitch * 0.6)
    rot('Neck1', Z, head_yaw * 0.5); rot('Head', Z, head_yaw * 0.5)


# ---------------------------------------------------------------- floor
_names = [g.name for g in mesh.vertex_groups]
_dom = np.array([_names[max(v.groups, key=lambda g: g.weight).group] if v.groups else '' for v in mesh.data.vertices])
CORE = np.array([n.startswith(('Spine', 'Neck', 'Head', 'Thigh', 'UpperArm')) for n in _dom])


def mesh_co():
    dg = bpy.context.evaluated_depsgraph_get(); ev = mesh.evaluated_get(dg); me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); ev.to_mesh_clear()
    co = co.reshape(-1, 3)
    mw = mesh.matrix_world
    return co @ np.array(mw.to_3x3()).T + np.array(mw.translation)


def clamp_tail():
    """Tail segments 2-6 keep their ends tail_floor above the floor."""
    floor = M['tail_floor']
    for i in range(2, 7):
        b = rig.pose.bones[f'Tail{i}']
        t = W @ b.tail
        if t.z < floor:
            h = W @ b.head; d = t - h; L = d.length
            flat = Vector((d.x, d.y, 0)).normalized(); dz = floor - h.z
            P.aim_bone(rig, b.name, h + flat * math.sqrt(max(L * L - dz * dz, 1e-6)) + Vector((0, 0, dz)) if abs(dz) < L
                       else h + flat * L)


REST_CO = mesh_co()


def contact(foot):
    """The paw's front-most vertex within contact_band of its lowest one at rest: the point it rolls over."""
    co = REST_CO[_dom == bones(foot)[2]]
    low = co[co[:, 2] < co[:, 2].min() + M['contact_band']]
    return Vector(low[np.argmin(low[:, 1])])


for _f in FEET:
    TOE[_f] = contact(_f) + Vector((0, 0, M['toe_clear'] - contact(_f).z))
for _k in ('front', 'hind'):                  # the same place along the body on both sides (rest poses are uneven)
    _y = (TOE[f'{_k}_L'].y + TOE[f'{_k}_R'].y) / 2
    for _s in 'LR':
        TOE[f'{_k}_{_s}'].y = _y
for _f in FEET:
    PAW_VEC[_f] = TOE[_f] - WRIST[_f]
TOE_Z = {f: TOE[f].z for f in FEET}
PAW_LOCAL = {f: (W @ rig.pose.bones[bones(f)[2]].matrix).inverted() @ TOE[f] for f in FEET}


# ---------------------------------------------------------------- gait
def heel(c, foot, q, duty):
    """Paw pitch over the stance (heel lifts over its last 40 %) and swing (paw tucks, then reaches flat)."""
    if q < duty:
        return c['heel'] * ss((q / duty - 0.6) / 0.4)
    u = (q - duty) / (1 - duty)
    tuck = c['tuck_f'] if foot.startswith('front') else c['tuck_h']
    return c['heel'] * (1 - ss(u / 0.35)) + tuck * math.sin(math.pi * min(1.0, u / 0.8))


def pose_body(p, c):
    """The body of the gait at phase p (no legs): rocking, back flex, bob, head and tail."""
    P.reset(rig)
    rock = c['rock'] * math.sin(2 * math.pi * c['rock_harm'] * (p - c['rock_phase']))
    flex = c['flex'] * math.cos(2 * math.pi * c['flex_harm'] * (p - c['flex_phase']))
    harm = c['bob_harm']
    bob = c['base'] - c['bob'] * (0.5 + 0.5 * math.cos(2 * math.pi * harm * (p - c['bob_phase'])))  # low in stance
    hips = c.get('pitch0', 0.0) + rock - c['counter'] * flex
    body(hips_d=Vector((0, 0, bob)), hips_pitch=hips, spine_pitch=flex, spine_yaw=c['yaw'] * math.sin(2 * math.pi * p),
         head_pitch=c.get('head0', 0.0) - c['head_level'] * (rock - c['counter'] * flex + flex) - c['head_up']
         - 2 * math.cos(4 * math.pi * p), head_yaw=-2 * math.sin(2 * math.pi * p))
    hold(p, c)
    if M['style'] == 'wolf':
        tail_wolf(c['tail'], p, c['tail_lift'])
    elif M['style'] == 'dog':
        tail_wave(c['tail'], 0.0, p, lift=2)
    else:
        tail_wave(c['tail'], 4 + 0.5 * c['rock'], p, lift=6 + rock)


def head_height():
    return (W @ rig.pose.bones['Head'].head).z


def hold(p, c):
    """Head hold: the neck flexes against the body's rise and fall, as running animals steady the head. Neck1 pitches
    so the Head joint's height moves back toward its mean over the loop by the share head_hold; Head turns back by the
    same angle so the head keeps its pitch."""
    share = c.get('head_hold', 0.0)
    if share <= 0 or 'head_mean' not in c:
        return
    neck = rig.pose.bones['Neck1']
    span = Vector(((W @ neck.tail) - (W @ neck.head)).to_tuple())
    reach = math.hypot(span.y, span.x) or neck.length
    dz = head_height() - c['head_mean']
    angle = math.degrees(math.asin(max(-0.9, min(0.9, share * dz / reach))))
    rot('Neck1', X, angle); rot('Head', X, -angle)


def plan(c, foot, sweep):
    """Shift of the foothold along the body (dy, + = backward) keeping wrist/ankle within REACH over the stance, from
    the shoulder/hip of the posed body at each stance phase."""
    samples = []
    for k in np.linspace(0, 1, 11):
        pose_body((c['feet'][foot] + k * c['duty']) % 1.0, c)
        samples.append((k, head_of(bones(foot)[0])))
    best = None
    span = M['plan_range']
    for dy in np.linspace(-span, span, 81):
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


MISSES = {}


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
            y = y0 + s / 2 - s * ss(u)
            z = (c['lift_f'] if foot.startswith('front') else c['lift_h']) * math.sin(math.pi * u)
            if foot.startswith('front'):
                y -= c['reach'] * math.sin(math.pi * min(1.0, max(0.0, (u - 0.4) / 0.6)))
            else:
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
            b.rotation_quaternion = q; b.location = loc; b.scale = (1, 1, 1)
            b.keyframe_insert('rotation_quaternion', frame=f)
            b.keyframe_insert('location', frame=f)
    act.use_frame_range = True; act.frame_start, act.frame_end = 0, n
    rig.animation_data.action = None
    return act, min(lows), max(lows), miss, min(core_lows)


info = {}
for name, c in CLIPS.items():
    T = c['frames'] / FPS
    stride = c['speed'] * T
    c.pop('head_mean', None)
    if c.get('head_hold', 0.0) > 0:
        heights = []
        for k in range(24):
            pose_body(k / 24, c)
            heights.append(head_height())
        c['head_mean'] = sum(heights) / len(heights)
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
        print(f'MISS {name} {foot}: {len(rows)} keys, worst {max(r[2] for r in rows)} mm, {rows[:6]}', flush=True)
    MISSES.clear()
os.makedirs(os.path.join(HERE, 'work'), exist_ok=True)
json.dump(info, open(os.path.join(HERE, 'work', f'{KEY}_gaits_info.json'), 'w'), indent=1)
P.reset(rig)
bpy.context.scene.render.fps = FPS; bpy.context.scene.render.fps_base = 1
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', f'{KEY}_gaits.blend'))
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
