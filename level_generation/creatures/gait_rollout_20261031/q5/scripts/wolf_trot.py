"""A procedural Trot for the MM9 wolf (mm9_wolf.glb: Grey, Red and Black Wolf, MM9 monsters 9114-9116), authored for
the speed MM9's AI wanders the wolves at (their profile WalkVel, 358 and 384 world units/s; see ../README.md).

The machinery of ../../q3/scripts/quad_gait.py (itself q2's, from ../../../mm7_m382_claude/scripts/sprint_rat7.py),
left unchanged there, mapped to the MM9 skeleton: each paw planted by its contact point (the front-most of its lowest
vertices in Standing), the wrist or hock following it through two-joint IK, the heel lifting at push-off, footholds
planned per limb against the posed body so the wrist or hock stays within REACH of the chain, floor rules (the tail
kept above the floor, lowest vertex reported).

MM9's joints are points: every bone points up, so nothing here reads a bone's tail. A limb is four joints (front:
shoulder Bone11, elbow Bone12, wrist Bone13, paw Bone19; hind: hip Bone01, hock Bone02, Bone03, paw Bone09; the right
side Bone16-17-18-05 and Bone06-07-08-42), solved by aiming each joint at its child's head. The two lower joints
are one rigid foot with Standing's rotations, pitched about the travel's side axis (heel up at push-off, the paw
tucked in the swing), so a planted paw keeps Standing's heading.

The body starts from Standing's first key every frame and keeps the wolf's carriage: hips Bone33 (bob, a little lower
than Standing), spine Bone35 and chest Bone32 (yaw sway), neck Bone26 and skull Bone27 (steadied: head hold), tail
Bone34-21-22-23-24 lifted back a little and swaying, as Walking carries it. The blend's Standing stands 5.35 cm
under the floor (the export's floor pass grounds its lowest vertex at 0), so the body is lifted by that much and the
footholds are on the floor at 0.

Reads ../../../mm9_wolf_claude/work/anim_v3.blend (read only), saves <package>/work/wolf_gaits.blend and writes only
the new clip to the GLB given, to be grafted onto the installed source with ../../../claude_shared/graft_clips.py.

    blender -b --factory-startup -P wolf_trot.py -- <out clips.glb>
"""
import bpy, os, sys, math, json
import numpy as np
from mathutils import Vector, Matrix, Quaternion

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))          # the q5 package
CREATURES = os.path.abspath(os.path.join(HERE, '..', '..'))

OUT = os.path.abspath(sys.argv[sys.argv.index('--') + 1])
FPS = 60
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))

# Footfall phases (touchdown, 0-1). The installed Walking is a diagonal-sequence walk: front R furthest forward at
# 0.97 with hind L at 0.00, front L at 0.45 with hind R at 0.55 (scripts/wolf_probe.py). The trot pairs the same
# diagonals and strikes front R + hind L at 0.
TROT = {'front_R': 0.0, 'hind_L': 0.0, 'front_L': 0.5, 'hind_R': 0.5}

# Clip parameters, as quad_gait.py: speed (model units/s), frames at 60 fps, footfall phases, duty, swing lift
# front/hind (m), heel lift at push-off (deg), swing tuck front/hind (deg, + = toes down), bob (m) with its phase and
# harmonic (2 = twice a loop), base (body height offset, m), rocking (hips pitch, deg), back flex (deg), counter (share
# of the flex the hips take back), spine yaw (deg), head level, head0 (neck/skull pitch, + = down), head hold (share of
# the skull's bob the neck takes back), tail sway and tail lift (deg), reach/trail (swing overshoot, m), hind_clear
# (height of the hind paws' lowest vertex over the floor while planted; Standing's is 5 cm), hind_wide (the hind
# footholds this much further out than Standing's: the hind paw passes outside the front paw lifting off on its side,
# which it otherwise brushes as it lands), hind_back (the hind footholds this much further back than planned), duty_f
# (the fronts' duty when above 0: shorter, so a front paw is up before the hind paw on its side arrives).
CLIPS = {
    'Trot': dict(speed=8.29, frames=22, feet=TROT, duty=0.42, lift_f=0.26, lift_h=0.10, heel=30, tuck_f=55,
                 tuck_h=-10, bob=0.06, bob_phase=0.19, bob_harm=2, base=-0.035, rock=1.5, rock_phase=0.0, rock_harm=2,
                 flex=2.0, flex_phase=0.19, flex_harm=2, counter=0.5, yaw=2.5, head_level=0.8, head0=2.0,
                 head_hold=0.5, tail=7.0, tail_lift=12.0, reach=0.04, trail=0.04, hind_clear=0.015, toe_clear=0.002,
                 hind_wide=0.0, hind_back=0.0, duty_f=0.33),
}
# Tuning: QG_SET="Clip:key=value,key=value;Clip:..." overrides clip parameters for a trial run.
for _item in filter(None, os.environ.get('QG_SET', '').split(';')):
    _clip, _pairs = _item.split(':', 1)
    for _pair in _pairs.split(','):
        _k, _v = _pair.split('=')
        CLIPS[_clip][_k] = type(CLIPS[_clip].get(_k, 0.0))(float(_v))
REACH = 0.97                    # wrist/hock distance from the shoulder/hip, at most this share of the chain
CONTACT_BAND = 0.06               # wide: the pivot is the claw tips, so a heel lift sinks nothing
PLAN_RANGE = 0.4
TAIL_FLOOR = 0.06               # tail joints kept this far above the floor

HIPS, SPINE, CHEST, NECK, SKULL = 'Bone33', 'Bone35', 'Bone32', 'Bone26', 'Bone27'
TAIL = ['Bone34', 'Bone21', 'Bone22', 'Bone23', 'Bone24']
LIMB = {'front_L': ('Bone11', 'Bone12', 'Bone13', 'Bone19'), 'front_R': ('Bone16', 'Bone17', 'Bone18', 'Bone05'),
        'hind_L': ('Bone01', 'Bone02', 'Bone03', 'Bone09'), 'hind_R': ('Bone06', 'Bone07', 'Bone08', 'Bone42')}
FEET = list(LIMB)

bpy.ops.wm.open_mainfile(filepath=os.path.join(CREATURES, 'mm9_wolf_claude', 'work', 'anim_v3.blend'))
rig = bpy.data.objects['Wolf_Rig']; mesh = bpy.data.objects['Wolf']
assert rig.matrix_world == Matrix.Identity(4), 'the rig is expected at the origin'
scene = bpy.context.scene
for b in rig.pose.bones:
    b.rotation_mode = 'QUATERNION'
rig.animation_data.action = bpy.data.actions['Standing']
if len(getattr(bpy.data.actions['Standing'], 'slots', [])):
    rig.animation_data.action_slot = bpy.data.actions['Standing'].slots[0]
scene.frame_set(0)
STAND_BASIS = {b.name: b.matrix_basis.copy() for b in rig.pose.bones}
rig.animation_data.action = None


def reset():
    for b in rig.pose.bones:
        b.matrix_basis = STAND_BASIS[b.name]
    bpy.context.view_layer.update()


reset()
STAND = {b.name: b.matrix.copy() for b in rig.pose.bones}
STAND_ROT = {n: m.to_quaternion() for n, m in STAND.items()}


def head(name):
    return rig.pose.bones[name].head.copy()


def rotate(name, q, pivot=None):
    """Turn bone `name` (and its children) by world rotation q about its head (or pivot)."""
    b = rig.pose.bones[name]
    h = b.head.copy() if pivot is None else Vector(pivot)
    b.matrix = Matrix.Translation(h) @ q.to_matrix().to_4x4() @ Matrix.Translation(-h) @ b.matrix
    bpy.context.view_layer.update()


def rot(name, axis, deg, pivot=None):
    if abs(deg) > 1e-6:
        rotate(name, Quaternion(Vector(axis).normalized(), math.radians(deg)), pivot)


def aim(name, child, target):
    """Turn joint `name` about its head so the head of `child` moves to target (shortest rotation)."""
    h = head(name)
    rotate(name, (head(child) - h).rotation_difference(Vector(target) - h))


def set_world_rot(name, q):
    b = rig.pose.bones[name]
    loc, _, sc = b.matrix.decompose()
    b.matrix = Matrix.LocRotScale(loc, q, sc)
    bpy.context.view_layer.update()


SIDE = {'L': 1.0, 'R': -1.0}                                 # +X is the wolf's left (it faces -Y)
UPPER = {f: (head(LIMB[f][1]) - head(LIMB[f][0])).length for f in FEET}
LOWER = {f: (head(LIMB[f][2]) - head(LIMB[f][1])).length for f in FEET}
CHAIN = {f: UPPER[f] + LOWER[f] for f in FEET}
WRIST = {f: head(LIMB[f][2]) for f in FEET}
POLES = {'front': (0.0, 0.6, 0.0), 'hind': (0.0, 0.6, 0.0)}   # elbow and hock behind the chain


# ---------------------------------------------------------------- floor
_names = [g.name for g in mesh.vertex_groups]
_dom = np.array([_names[max(v.groups, key=lambda g: g.weight).group] if v.groups else '' for v in mesh.data.vertices])
CORE = np.array([n in (HIPS, SPINE, CHEST, NECK, SKULL, 'Bone28', 'Bone30', 'Bone11', 'Bone16', 'Bone01', 'Bone06')
                 for n in _dom])


def mesh_co():
    dg = bpy.context.evaluated_depsgraph_get(); ev = mesh.evaluated_get(dg); me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); ev.to_mesh_clear()
    co = co.reshape(-1, 3)
    mw = mesh.matrix_world
    return co @ np.array(mw.to_3x3()).T + np.array(mw.translation)


STAND_CO = mesh_co()
FLOOR = float(STAND_CO[:, 2].min())                          # Standing's lowest vertex: the export lifts it to 0
LIFT = -FLOOR
FOOT_GROUPS = {f: LIMB[f][2:] for f in FEET}                 # the paw and the joint above it: the skin of the foot


def foot_co(co, foot):
    return co[np.isin(_dom, FOOT_GROUPS[foot])]


def contact(foot):
    """The foot's front-most vertex within CONTACT_BAND of its lowest one in Standing: the point it rolls over."""
    co = foot_co(STAND_CO, foot)
    low = co[co[:, 2] < co[:, 2].min() + CONTACT_BAND]
    return Vector(low[np.argmin(low[:, 1])])


PAW_LOW = {f: float(foot_co(STAND_CO, f)[:, 2].min()) for f in FEET}
CONTACT = {f: contact(f) for f in FEET}
FOOT_VEC = {f: CONTACT[f] - WRIST[f] for f in FEET}          # wrist/hock -> contact, Standing
PAW_LOCAL = {f: STAND[LIMB[f][3]].inverted() @ CONTACT[f] for f in FEET}


def toe_base(c):
    """Footholds at Standing's place under the body, each paw's lowest vertex at its clearance over the floor; the
    two sides take the same place along the body."""
    toe = {}
    for f in FEET:
        clear = c['toe_clear'] if f.startswith('front') else c['hind_clear']
        toe[f] = CONTACT[f] + Vector((0, 0, clear - PAW_LOW[f]))
    for k in ('front', 'hind'):
        y = (toe[f'{k}_L'].y + toe[f'{k}_R'].y) / 2
        for s in 'LR':
            toe[f'{k}_{s}'].y = y
            if k == 'hind':
                toe[f'{k}_{s}'].x += SIDE[s] * c['hind_wide']
    return toe


def place_toe(foot, toe, pitch):
    """IK the limb so the foot, pitched by `pitch` degrees (+ = heel up / toes down) about the side axis, ends with
    its contact at `toe`. Returns the contact's miss (m)."""
    kind, side = foot.split('_')
    upper, mid, wrist_bone, paw = LIMB[foot]
    q = Quaternion(X, math.radians(pitch))
    wrist = toe - q @ FOOT_VEC[foot]
    shoulder = head(upper)
    d = wrist - shoulder
    dist = min(d.length, CHAIN[foot] * 0.999)
    d.normalize()
    la, lb = UPPER[foot], LOWER[foot]
    cos_a = (la * la + dist * dist - lb * lb) / (2 * la * dist)
    angle = math.acos(max(-1.0, min(1.0, cos_a)))
    px, py, pz = POLES[kind]
    pole = wrist + Vector((SIDE[side] * px, py, pz)) - shoulder
    pole = (pole - d * pole.dot(d)).normalized()
    elbow = shoulder + (d * math.cos(angle) + pole * math.sin(angle)) * la
    aim(upper, mid, elbow)
    aim(mid, wrist_bone, shoulder + d * dist)
    set_world_rot(wrist_bone, q @ STAND_ROT[wrist_bone])
    set_world_rot(paw, q @ STAND_ROT[paw])
    return ((rig.pose.bones[paw].matrix @ PAW_LOCAL[foot]) - toe).length


def ss(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def body(hips_d, hips_pitch, spine_pitch, spine_yaw, head_pitch, head_yaw):
    rig.pose.bones[HIPS].matrix = Matrix.Translation(hips_d) @ rig.pose.bones[HIPS].matrix
    bpy.context.view_layer.update()
    rot(HIPS, X, hips_pitch)
    for n in (SPINE, CHEST):
        rot(n, X, spine_pitch * 0.5); rot(n, Z, spine_yaw * 0.5)
    rot(NECK, X, head_pitch * 0.4); rot(SKULL, X, head_pitch * 0.6)
    rot(NECK, Z, head_yaw * 0.5); rot(SKULL, Z, head_yaw * 0.5)


def tail(c, p):
    """Walking's tail: the base lifted back by tail_lift (a positive X turn lifts a hanging tail backward), every
    segment swaying about the vertical with a lag along the chain, growing to the tip."""
    rot(TAIL[0], X, c['tail_lift'])
    n = len(TAIL)
    for i, b in enumerate(TAIL):
        k = (i + 1) / n
        rot(b, Z, c['tail'] * (0.3 + 0.7 * k) * math.sin(2 * math.pi * (p - 0.08 * i)))


def clamp_tail():
    """Tail joints keep TAIL_FLOOR above the floor: a segment whose child joint dips is turned up about its head."""
    for parent, child in zip(TAIL[:-1], TAIL[1:]):
        h = head(parent); t = head(child)
        floor = TAIL_FLOOR
        if t.z < floor:
            dvec = t - h; L = dvec.length; flat = Vector((dvec.x, dvec.y, 0)).normalized(); dz = floor - h.z
            target = h + flat * math.sqrt(max(L * L - dz * dz, 1e-6)) + Vector((0, 0, dz)) if abs(dz) < L \
                else h + flat * L
            aim(parent, child, target)


def skull_height():
    return head(SKULL).z


def hold(c):
    """Head hold: Bone26 pitches so the skull joint moves back toward its mean height by the share head_hold, and the
    skull turns back by the same angle so the head keeps its pitch."""
    share = c.get('head_hold', 0.0)
    if share <= 0 or 'head_mean' not in c:
        return
    span = head(SKULL) - head(NECK)
    reach = math.hypot(span.y, span.x) or span.length
    dz = skull_height() - c['head_mean']
    angle = math.degrees(math.asin(max(-0.9, min(0.9, share * dz / reach))))
    rot(NECK, X, angle); rot(SKULL, X, -angle)


def pose_body(p, c):
    """The body of the gait at phase p (no legs): rocking, back flex, bob, head and tail."""
    reset()
    rock = c['rock'] * math.sin(2 * math.pi * c['rock_harm'] * (p - c['rock_phase']))
    flex = c['flex'] * math.cos(2 * math.pi * c['flex_harm'] * (p - c['flex_phase']))
    bob = LIFT + c['base'] - c['bob'] * (0.5 + 0.5 * math.cos(2 * math.pi * c['bob_harm'] * (p - c['bob_phase'])))
    hips = rock - c['counter'] * flex
    body(Vector((0, 0, bob)), hips, flex, c['yaw'] * math.sin(2 * math.pi * p),
         c['head0'] - c['head_level'] * (hips + flex), -2 * math.sin(2 * math.pi * p))
    hold(c)
    tail(c, p)


def duty_of(c, foot):
    return c['duty_f'] if foot.startswith('front') and c.get('duty_f', 0) > 0 else c['duty']


def plan(c, foot, sweep, toe):
    """Shift of the foothold along the body (dy, + = backward) keeping the wrist/hock within REACH over the stance."""
    samples = []
    for k in np.linspace(0, 1, 11):
        pose_body((c['feet'][foot] + k * duty_of(c, foot)) % 1.0, c)
        samples.append((k, head(LIMB[foot][0])))
    best = None
    for dy in np.linspace(-PLAN_RANGE, PLAN_RANGE, 81):
        worst = 0.0
        for k, shoulder in samples:
            t = Vector((toe[foot].x, toe[foot].y + dy - sweep / 2 + sweep * k, toe[foot].z))
            a = c['heel'] * ss((k - 0.6) / 0.4)
            wrist = t - Quaternion(X, math.radians(a)) @ FOOT_VEC[foot]
            worst = max(worst, (wrist - shoulder).length / CHAIN[foot])
        cost = 100 * max(0.0, worst - REACH) + abs(dy)
        if best is None or cost < best[0]:
            best = (cost, dy, worst)
    return best


def heel(c, foot, q, duty):
    """Foot pitch over the stance (the heel lifts over its last 40 %) and the swing (the paw tucks, then reaches)."""
    if q < duty:
        return c['heel'] * ss((q / duty - 0.6) / 0.4)
    u = (q - duty) / (1 - duty)
    tuck = c['tuck_f'] if foot.startswith('front') else c['tuck_h']
    return c['heel'] * (1 - ss(u / 0.35)) + tuck * math.sin(math.pi * min(1.0, u / 0.8))


MISSES = {}


def gait(p, c, centres, stride, toe):
    pose_body(p, c)
    miss = 0.0
    for foot, phase in c['feet'].items():
        duty = duty_of(c, foot)
        s = stride * duty
        q = (p - phase) % 1.0
        y0 = toe[foot].y + centres[foot]
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
        if q >= duty and pitch < 0:            # toes up in swing: the paw turns about its toe, lift the heel clear
            z += -math.sin(math.radians(pitch)) * FOOT_VEC[foot].length
        m = place_toe(foot, Vector((toe[foot].x, y, toe[foot].z + z)), pitch)
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
    rig.animation_data.action = None
    poses, lows, core_lows, miss = [], [], [], 0.0
    for f in range(n + 1):
        miss = max(miss, fn((f % n) / n))
        co = mesh_co()
        lows.append(float(co[:, 2].min())); core_lows.append(float(co[CORE, 2].min()))
        poses.append({b.name: (b.rotation_quaternion.copy(), b.location.copy(), b.scale.copy())
                      for b in rig.pose.bones})
    rig.animation_data.action = act
    if len(getattr(act, 'slots', [])):
        rig.animation_data.action_slot = act.slots[0]
    prev = {}
    for f, pose in enumerate(poses):
        for b in rig.pose.bones:
            q, loc, sc = pose[b.name]
            if b.name in prev and prev[b.name].dot(q) < 0:
                q = -q
            prev[b.name] = q
            b.rotation_quaternion = q; b.location = loc; b.scale = sc
            b.keyframe_insert('rotation_quaternion', frame=f)
            b.keyframe_insert('location', frame=f)
            b.keyframe_insert('scale', frame=f)
    act.use_frame_range = True; act.frame_start, act.frame_end = 0, n
    rig.animation_data.action = None
    return act, min(lows), max(lows), miss, min(core_lows)


print(f'FLOOR {FLOOR:+.4f}  chains ' + ', '.join(f'{f} {UPPER[f]:.3f}+{LOWER[f]:.3f}' for f in FEET), flush=True)
info = {'standing_floor_in_blend': FLOOR}
for name, c in CLIPS.items():
    T = c['frames'] / FPS
    stride = c['speed'] * T
    toe = toe_base(c)
    c.pop('head_mean', None)
    if c.get('head_hold', 0.0) > 0:
        heights = []
        for k in range(24):
            pose_body(k / 24, c)
            heights.append(skull_height())
        c['head_mean'] = sum(heights) / len(heights)
    centres = {}
    for foot in FEET:
        cost, dy, worst = plan(c, foot, stride * duty_of(c, foot), toe)
        centres[foot] = dy + (c['hind_back'] if foot.startswith('hind') else 0.0)
        print(f'PLAN {name} {foot}: dy {dy:+.3f} reach {worst:.3f} of chain', flush=True)
    act, low, high, miss, core = key_action(name, c['frames'], lambda p: gait(p, c, centres, stride, toe))
    info[name] = {'seconds': T, 'stride': round(stride, 4), 'authored_speed': c['speed'], 'duty': c['duty'],
                  'sweep': stride * c['duty'], 'lowest_over_floor': [low, high], 'core_lowest': core, 'toe_miss': miss,
                  'centres': centres, 'params': {k: v for k, v in c.items() if k != 'feet'}}
    print(f'CLIP {name}: {T:.4f} s, stride {stride:.4f} m, sweep {stride * c["duty"]:.3f} m, lowest vertex over the '
          f'floor {low * 100:+.2f}..{high * 100:+.2f} cm, core {core * 100:+.2f} cm, worst toe miss {miss * 1000:.1f} mm',
          flush=True)
    for foot, rows in MISSES.items():
        print(f'MISS {name} {foot}: {len(rows)} keys, worst {max(r[2] for r in rows)} mm, {rows[:6]}', flush=True)
    MISSES.clear()
os.makedirs(os.path.join(HERE, 'work'), exist_ok=True)
json.dump(info, open(os.path.join(HERE, 'work', 'wolf_gaits_info.json'), 'w'), indent=1, default=str)
reset()
scene.render.fps = FPS; scene.render.fps_base = 1
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'wolf_gaits.blend'))
for a in list(bpy.data.actions):
    if a.name not in CLIPS:
        bpy.data.actions.remove(a)
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
for o in bpy.data.objects:
    o.select_set(o in (mesh, rig))
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=OUT, use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_all_influences=False, export_materials='NONE',
                          export_attributes=False, export_morph=False, export_reset_pose_bones=True,
                          export_anim_slide_to_zero=True)
print('EXPORTED', OUT)
