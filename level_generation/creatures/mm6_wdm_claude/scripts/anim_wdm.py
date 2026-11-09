"""Flying demon clips on work/rig_head.blend (HD body + grafted head) (24 fps keys); saves work/anim_v1.blend.

Body motion: Mixamo (or other mixamorig) FBX clips listed in SOURCES, retargeted by bone direction + twist (same method
as mm6_pmn2_claude/scripts/retarget_fbx.py: T(f) = S(f) @ O with O aligning each rest direction) and time-warped onto
the native durations. Clips without an available FBX use the rest body. Layers on top, per frame:
  - hover: body lean like the native side frames and a bob against the wingbeat, hips translation damped,
  - legs dangle (thighs a little forward, knees bent, feet and talons pointed down) with a lagging sway; a source
    clip's legs are blended toward this so standing clips read as airborne,
  - wings flap on the native 0.75 s cycle (wdmfly a-f): high V -> broad spread -> downstroke with drooping tips ->
    rising; the outer wing lags, the fingers fold on the upstroke.
Clips: Flight 3.0 s loop (4 beats; Mixamo Floating), Attack 0.75, Cast 0.75, Hit 0.75, Death 1.0 (body shrinks inside the engine's
disintegration burst from 0.45 s), Dead (held)."""
import bpy, os, math
from mathutils import Matrix, Vector, Quaternion

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPS = 24
MIX = os.path.join(HERE, 'mixamo')
# clip -> (fbx file, source start s, source end s, leg_blend toward dangling, body weight)
SOURCES = {
    'Flight': ('floating.fbx', None, None, 0.6, 1.0),               # whole loop, played over the 3.0 s Flight
    'Attack': ('zombie_swipe_attack.fbx', 0.35, 1.45, 0.85, 1.0),   # windup, overhead swipe, rake down
    'Cast': ('wide_arm_spell_casting.fbx', 0.25, 1.40, 0.85, 1.0),  # gather in front, fling wide
    'Hit': ('large_hit_reaction_front.fbx', None, None, 0.7, 1.0),  # head back, arms thrown wide
    'Death': ('large_hit_reaction_front.fbx', 0.0, 0.8, 0.6, 1.0),  # recoil, then burns away
}
rig = bpy.data.objects['Demon_Rig']
scene = bpy.context.scene
TW = rig.matrix_world.copy(); TWI = TW.inverted()
SKIP = ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky', 'Eye', 'Jaw', 'End', 'HeadTop')
LEGS = [f'mixamorig:{s}{b}' for s in ('Left', 'Right') for b in ('UpLeg', 'Leg', 'Foot', 'ToeBase')]
SIDES = {'L': 1.0, 'R': -1.0}
ARMS = [f'mixamorig:{s}{b}' for s in ('Left', 'Right') for b in ('Arm', 'ForeArm', 'Hand')]


def update():
    bpy.context.view_layer.update()


def reset():
    if rig.animation_data:
        rig.animation_data.action = None
    for pb in rig.pose.bones:
        pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0)
        pb.scale = (1, 1, 1)
    update()


def rotate_world(name, axis, deg):
    if abs(deg) < 1e-6:
        return
    pb = rig.pose.bones[name]
    head = TW @ pb.head
    m = TW @ pb.matrix
    r = Matrix.Translation(head) @ Matrix.Rotation(math.radians(deg), 4, Vector(axis).normalized()) \
        @ Matrix.Translation(-head)
    pb.matrix = TWI @ (r @ m); update()


# ---- FBX sources ------------------------------------------------------------------------------------------------
class Source:
    """A mixamorig FBX clip sampled as world matrices; retargets onto the demon rig by direction + twist."""

    def __init__(self, path):
        before = set(bpy.data.objects); acts = set(bpy.data.actions)
        fps = scene.render.fps
        bpy.ops.import_scene.fbx(filepath=path)
        self.fps = scene.render.fps; scene.render.fps = fps
        new = set(bpy.data.objects) - before
        self.arm = next(o for o in new if o.type == 'ARMATURE')
        for o in new:
            if o.type == 'MESH':
                o.hide_viewport = True
        self.act = next(iter(set(bpy.data.actions) - acts))
        self.arm.animation_data.action = self.act
        self.f0, self.f1 = self.act.frame_range
        self.duration = (self.f1 - self.f0) / self.fps
        scene.frame_set(int(self.f0))
        pl = self.arm.matrix_world @ self.arm.pose.bones['mixamorig:LeftUpLeg'].head
        pr = self.arm.matrix_world @ self.arm.pose.bones['mixamorig:RightUpLeg'].head
        lat = pl - pr
        self.yaw = Matrix.Rotation(-math.atan2(lat.y, lat.x), 4, 'Z')   # face forward (-Y) at the first frame
        SW = self.arm.matrix_world
        self.names = [b.name for b in rig.data.bones
                      if b.name in self.arm.data.bones and not any(k in b.name for k in SKIP)]
        Y = Vector((0, 1, 0))
        self.offset = {}
        for n in self.names:
            Rs = (SW @ self.arm.data.bones[n].matrix_local).to_3x3().normalized()
            Rt = (TW @ rig.data.bones[n].matrix_local).to_3x3().normalized()
            swing = (Rt @ Y).rotation_difference(Rs @ Y).to_matrix()
            self.offset[n] = Rs.inverted() @ (swing @ Rt)
        hs = (SW @ self.arm.data.bones['mixamorig:Hips'].head_local).z
        ht = (TW @ rig.data.bones['mixamorig:Hips'].head_local).z
        self.k = ht / hs
        scene.frame_set(int(self.f0))
        self.hips0 = (self.yaw @ SW @ self.arm.pose.bones['mixamorig:Hips'].matrix).translation.copy()
        self.cache = {}

    def sample(self, t):
        key = round(t, 4)
        if key not in self.cache:
            f = self.f0 + t * self.fps
            scene.frame_set(int(math.floor(f)), subframe=f - math.floor(f))
            SW = self.arm.matrix_world
            self.cache[key] = {n: (self.yaw @ SW @ self.arm.pose.bones[n].matrix).copy() for n in self.names}
        return self.cache[key]

    def apply(self, t, hips_move=0.35, weight=1.0):
        frame = self.sample(t)
        for n in self.names:                               # parents first (bone order)
            pb = rig.pose.bones[n]
            R = frame[n].to_3x3().normalized() @ self.offset[n]
            M = R.to_4x4()
            if n == 'mixamorig:Hips':
                p = frame[n].translation
                th = TW @ rig.data.bones[n].head_local
                d = (p - self.hips0) * self.k * hips_move
                M.translation = th + d
            else:
                M.translation = TW @ pb.head
            if weight < 1.0:
                cur = (TW @ pb.matrix)
                q = cur.to_quaternion().slerp(M.to_quaternion(), weight)
                M = Matrix.LocRotScale(M.translation, q, Vector((1, 1, 1)))
            pb.matrix = TWI @ M
            update()


SRC = {}
for fn in sorted(set(v[0] for v in SOURCES.values()) | {'treading_water.fbx'}):
    path = os.path.join(MIX, fn)
    if os.path.exists(path):
        SRC[fn] = Source(path)
print('SOURCES', {k: round(v.duration, 3) for k, v in SRC.items()})


# ---- layers -----------------------------------------------------------------------------------------------------
def capture():
    return {pb.name: (pb.rotation_quaternion.copy(), pb.location.copy(), pb.scale.copy()) for pb in rig.pose.bones}


def apply_pose(pose, names=None):
    for k, (q, l, s) in pose.items():
        if names is None or k in names:
            pb = rig.pose.bones[k]; pb.rotation_quaternion = q; pb.location = l; pb.scale = s
    update()


def mix(a, b, u, names=None):
    out = dict(a)
    for k in (names or a.keys()):
        qa, la, sa = a[k]; qb, lb, sb = b[k]
        if qa.dot(qb) < 0:
            qb = -qb
        out[k] = (qa.slerp(qb, u), la.lerp(lb, u), sa.lerp(sb, u))
    return out


def hover(lean, bob):
    hips = rig.pose.bones['mixamorig:Hips']
    m = TW @ hips.matrix
    hips.matrix = TWI @ (Matrix.Translation(Vector((0, 0, bob))) @ m); update()
    rotate_world('mixamorig:Hips', (1, 0, 0), lean)


def dangle(t, swing=1.0):
    """Airborne legs: thighs slightly forward, knees bent, feet and talons pointing down, lagging sway."""
    for side, sg in (('Left', 1), ('Right', -1)):
        lag = math.sin(2 * math.pi * t / 0.75 - 1.3 - (0.35 if sg > 0 else 0.0))
        rotate_world(f'mixamorig:{side}UpLeg', (1, 0, 0), -8 - 4 * swing * lag)
        rotate_world(f'mixamorig:{side}Leg', (1, 0, 0), 26 + 6 * swing * lag)
        rotate_world(f'mixamorig:{side}Foot', (1, 0, 0), 40 + 6 * swing * lag)
        rotate_world(f'mixamorig:{side}ToeBase', (1, 0, 0), 12)


def body_axes():
    q = (TW @ rig.pose.bones['mixamorig:Spine2'].matrix).to_quaternion() @ \
        (TW @ rig.data.bones['mixamorig:Spine2'].matrix_local).to_quaternion().inverted()
    return q @ Vector((0, -1, 0)), q @ Vector((0, 0, 1))


def rest_elevation(s):
    """Front-view elevation (deg) of the line from the wing root to the leading tip in the rest pose."""
    d = rig.data.bones[f'Wing_{s}_Lead'].tail_local - rig.data.bones[f'Wing_{s}_Root'].head_local
    return math.degrees(math.atan2(d.z, abs(d.x)))


REST_ELEV = {s: rest_elevation(s) for s in SIDES}
MAX_ELEV = 46.0      # native high V (wdmflya): root-to-tip about 42 deg; higher and the wings cross behind the head


def wings(up, sweep, fold, lag):
    """up: front-view elevation of the root-to-tip line (deg, absolute; native cycle about -6..42); sweep: swung back
    about the vertical; lag: outer wing (Arm) trailing; fold: fingers swept toward the body."""
    fwd, upv = body_axes()
    for s, sg in SIDES.items():
        rotate_world(f'Wing_{s}_Root', upv * sg, -sweep)
        rotate_world(f'Wing_{s}_Root', fwd * sg, min(up, MAX_ELEV) - REST_ELEV[s])   # about -Y for the left wing: + raises it
        rotate_world(f'Wing_{s}_Arm', fwd * sg, lag)
        for k, a in (('Lead', 0.4), ('Finger1', 0.7), ('Finger2', 1.0), ('Finger3', 0.6)):
            rotate_world(f'Wing_{s}_{k}', upv * sg, fold * a)


def flap(p, amp=1.0, mid=8.0):
    """Native wdmfly cycle phase p in [0,1): a high V (p 0), b/c spread (0.17-0.33), d lowest (0.5), e/f rising."""
    c, s = math.cos(2 * math.pi * p), math.sin(2 * math.pi * p)
    return {'up': 10 + mid + 24 * amp * c, 'sweep': 4 + 6 * amp * c, 'fold': 22 * amp * max(0.0, -s) ** 1.3,
            'lag': 10 * amp * s, 'bob': -0.03 * amp * c}


def ss(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def body(clip, t, duration):
    fn, a, b, leg_blend, weight = SOURCES.get(clip, (None, None, None, 0, 0))
    src = SRC.get(fn)
    if src is None:
        return 0.0
    a = 0.0 if a is None else a; b = src.duration if b is None else b
    tt = a + (b - a) * (t / duration)
    if clip == 'Flight':
        tt = (t / duration) * src.duration % src.duration          # whole source loop over the clip
    src.apply(tt, weight=weight)
    return leg_blend


def pose_clip(clip, t, duration, flap_amp=1.0, flap_mid=8.0, lean=8.0, period=0.75, src_t=None):
    """src_t: source clip time when it differs from the wingbeat time t (an action's ready pause)."""
    reset()
    rest = capture()
    leg_blend = body(clip, t if src_t is None else src_t, duration)
    src_pose = capture()
    if clip == 'Flight':                     # native forearms hang with the claws low; Floating raises them
        src_pose = mix(src_pose, rest, 0.6, ARMS)
    reset()
    f = flap((t % period) / period, flap_amp, flap_mid)
    dangle(t)
    dangling = capture()
    reset()
    apply_pose(src_pose)
    if leg_blend:
        apply_pose(mix(src_pose, dangling, leg_blend, LEGS), LEGS)
    else:
        apply_pose(dangling, LEGS)
    hover(lean, f['bob'])
    wings(f['up'], f['sweep'], f['fold'], f['lag'])
    return f


def key_action(name, seconds, loop, fn):
    old = bpy.data.actions.get(name)
    if old:
        bpy.data.actions.remove(old)
    n = int(round(seconds * FPS))
    poses = []
    for f in range(n + 1):
        fn(((f % n) if loop else f) / FPS)
        poses.append(capture())
    act = bpy.data.actions.new(name); act.use_fake_user = True
    rig.animation_data_create(); rig.animation_data.action = act
    prev = {}
    for f, pose in enumerate(poses):
        for k, (q, l, s) in pose.items():
            if k in prev and prev[k].dot(q) < 0:
                q = -q
            prev[k] = q
            pb = rig.pose.bones[k]; pb.rotation_quaternion = q; pb.location = l; pb.scale = s
            pb.keyframe_insert('rotation_quaternion', frame=f); pb.keyframe_insert('location', frame=f)
            pb.keyframe_insert('scale', frame=f)
    rig.animation_data.action = None
    print('CLIP', name, seconds, flush=True)


def death(t):
    pose_clip('Death', t, 1.0, flap_amp=1.2, flap_mid=14, lean=8 + 20 * ss(t / 0.8), period=0.4)
    k = 1.0 - 0.995 * ss((t - 0.45) / 0.45)
    rig.pose.bones['mixamorig:Hips'].scale = (k, k, k); update()


import sys
if '--preview' in sys.argv:
    # Full-length retargets of every source (body only), for picking the time windows: actions Src_<file>.
    for fn, src in SRC.items():
        key_action('Src_' + fn[:-4], src.duration, False, lambda t, src=src: (reset(), src.apply(min(t, src.duration))))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'preview_sources.blend'))
    raise SystemExit(0)
mods = [m for o in bpy.data.objects if o.type == 'MESH' for m in o.modifiers if m.type == 'ARMATURE']
for m in mods:
    m.show_viewport = False
def blended(clip, t, duration, t_in=0.1, t_out=0.18, lead=0.0, **kw):
    """Action clip that starts from and returns to the Flight pose (the engine switches clips at these ends). lead:
    a ready pause (the source's first pose eased in while the wings keep beating) before the source window."""
    pose_clip('Flight', t, 3.0); base = capture()
    pose_clip(clip, t, duration, src_t=max(0.0, t - lead), **kw); act = capture()
    w = ss(t / (t_in + lead)) * (1.0 - ss((t - (lead + duration - t_out)) / t_out))
    apply_pose(mix(base, act, w))


# Clip timing (2026-10-10, engine action events): Attack and Cast play their source windows at source speed after a
# ready pause; the blow/release (peak claw speed, printed as IMPACT) is the actors.yml `events` marker. Previously
# both were squeezed into the native 0.75 s (1.47x / 1.53x).
ATTACK_SRC, ATTACK_LEAD = SOURCES['Attack'][2] - SOURCES['Attack'][1], 0.0
CAST_SRC, CAST_LEAD = SOURCES['Cast'][2] - SOURCES['Cast'][1], 0.15
CLIPS = {'Flight': (3.0, True, lambda t: pose_clip('Flight', t, 3.0)),
         'Attack': (ATTACK_LEAD + ATTACK_SRC, False, lambda t: blended('Attack', t, ATTACK_SRC, lead=ATTACK_LEAD,
                                                                       flap_amp=0.6, flap_mid=4, lean=12)),
         'Cast': (CAST_LEAD + CAST_SRC, False, lambda t: blended('Cast', t, CAST_SRC, lead=CAST_LEAD,
                                                                 flap_amp=0.6, flap_mid=10, lean=8)),
         'Hit': (0.75, False, lambda t: blended('Hit', t, 0.75, t_in=0.04, flap_amp=0.8, flap_mid=20, lean=0)),
         'Death': (1.0, False, death),
         'Dead': (1.0, False, lambda t: death(1.0))}
for name, (sec, loop, fn) in CLIPS.items():
    key_action(name, sec, loop, fn)
for m in mods:
    m.show_viewport = True
for src in SRC.values():
    for o in [src.arm] + list(src.arm.children):
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.actions.remove(src.act)
# Attack blow = peak claw-tip speed (either hand) after the blend-in; Cast release = hands flung widest.
for name, lead in (('Attack', ATTACK_LEAD), ('Cast', CAST_LEAD)):
    act = bpy.data.actions[name]; rig.animation_data.action = act; tips = []
    for f in range(int(act.frame_range[1]) + 1):
        scene.frame_set(f)
        tips.append([TW @ rig.pose.bones[f'mixamorig:{s}Hand'].tail for s in ('Left', 'Right')])
    first = int(round((lead + 0.15) * FPS))
    if name == 'Attack':
        speed = [max((tips[f + 1][i] - tips[f][i]).length for i in (0, 1)) for f in range(len(tips) - 1)]
        k = max(range(first, len(speed)), key=speed.__getitem__); impact = (k + 0.5) / FPS
    else:
        k = max(range(first, len(tips)), key=lambda f: (tips[f][0] - tips[f][1]).length); impact = k / FPS
    print(f'{name.upper()} {len(tips) - 1} frames {(len(tips) - 1) / FPS:.3f} s, blow at {impact:.3f} s -> '
          f'wind-up stretch {0.75 / impact:.2f}x; IMPACT {impact:.3f}', flush=True)
rig.animation_data.action = bpy.data.actions['Flight']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'anim_v1.blend'))
print('SAVED')
