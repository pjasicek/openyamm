"""Walk2, Run2 and Sprint for the MM8 Gorgon (m564, armoured bull), gait rollout package q3 (2026-10-31), authored
for the game's speeds (gait_gate.py targets): Standard wanders at 0.62-0.75 and chases at 1.25-1.49 model units/s,
MAW (Spd / 2 + 300) chases at 2.49-2.62. The installed Walking (0.48) and Running (0.80) played the run x1.56-1.87
chasing and x3.1-3.3 under MAW.

The leg machinery is copied from ../../../mm8_m564_claude/scripts/animate_gorgon.py (left unchanged): two-bone IK of
upper/lower leg to the carpus or hock, the pastern inclined along the leg toward the shoulder or hip ("articulate"),
the hoof keeping its rest orientation (only pitched in the swing), footholds centred under the shoulder or hip, the
body dropped 4.5 cm and the hoof soles on the floor. Strides follow dynamic similarity (Alexander: relative stride
2.3 Fr^0.3 of the leg) so every clip sweeps about the installed walk's 0.30 m: the extra speed comes from cadence and,
in the gallop, from flights.
  Walk2   lateral-sequence walk as Walking (LH 0, FL .25, RH .5, FR .75), shorter loop.
  Run2    trot as Running (LH + FR at 0), lower duty: short suspensions.
  Sprint  transverse gallop (LH 0, RH .1, LF .45, RF .55; hind L at 0 as the walk), one gathered flight, back flexing,
          the body pitching with the footfalls and the head nodding down as the fore legs land.

Reads the project's animated blend (read only), saves <package>/work/m564_gaits.blend and writes only the new clips
to the GLB given, to be grafted onto the installed source with ../../claude_shared/graft_clips.py.

    blender -b --factory-startup -P gait_m564.py -- <out clips.glb>
"""
import bpy, os, sys, math, json
import numpy as np
from mathutils import Vector, Matrix, Quaternion

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))          # the q3 package
CREATURES = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(CREATURES, 'mm6_rat_claude', 'scripts'))
import posing as pose  # noqa: E402

OUT = os.path.abspath(sys.argv[sys.argv.index('--') + 1])
bpy.ops.wm.open_mainfile(filepath=os.path.join(CREATURES, 'mm8_m564_claude', 'work', 'anim_v1.blend'))
rig, mesh = bpy.data.objects['Gorgon_Rig'], bpy.data.objects['Gorgon']
FPS = 60
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))

LATERAL = {('Hind', 'L'): 0.0, ('Front', 'L'): 0.25, ('Hind', 'R'): 0.5, ('Front', 'R'): 0.75}
TROT = {('Hind', 'L'): 0.0, ('Front', 'R'): 0.0, ('Hind', 'R'): 0.5, ('Front', 'L'): 0.5}
GALLOP = {('Hind', 'L'): 0.0, ('Hind', 'R'): 0.1, ('Front', 'L'): 0.45, ('Front', 'R'): 0.55}
# Clip parameters: speed (model units/s), frames at 60 fps, footfall (touchdown) phases, duty, hoof lift front/hind
# and its profile (sin^lift_pow), swing pitch (deg, + = toes down; the hoof is raised by its tip's drop), front reach
# and hind trail in the swing (m), body drop and bob (bob_harm times a loop, lowest at bob_phase), hips pitch rocking
# (deg, + = nose down) and its phase, back flex (deg, + = arched) and its phase, head nod (deg, + = down) and its
# phase, body roll (deg), tail sway (deg).
COMMON = dict(lift_f=0.018, lift_h=0.018, lift_pow=1.5, tuck=12.0, reach=0.0, trail=0.0, drop=-0.045, bob=0.003,
              bob_harm=2, bob_phase=0.0, rock=0.6, rock_harm=2, rock_phase=0.0, flex=0.0, flex_phase=0.0, nod=1.2,
              nod_harm=2, nod_phase=0.0, roll=0.8, tail=2.5)
CLIPS = {
    # Walking is 1.0 s, 0.48 m, duty 0.62, lift 0.018, drop -0.045 +- 0.003 (twice a loop), rock 0.6, head 1.2.
    'Walk2': dict(COMMON, speed=0.64, frames=48, feet=LATERAL, duty=0.60, lift_f=0.022, lift_h=0.022, tuck=14.0),
    # Running is 0.75 s, 0.60 m, duty 0.50, lift 0.035.
    'Run2': dict(COMMON, speed=1.29, frames=36, feet=TROT, duty=0.40, lift_f=0.04, lift_h=0.035, lift_pow=1.0,
                 tuck=25.0, reach=0.01, trail=0.01, bob=0.005, bob_phase=0.2, rock=0.6, nod=1.2, roll=0.8, tail=4.0),
    'Sprint': dict(COMMON, speed=2.41, frames=28, feet=GALLOP, duty=0.26, lift_f=0.05, lift_h=0.045, lift_pow=0.8,
                   tuck=40.0, reach=0.02, trail=0.025, drop=-0.04, bob=0.01, bob_harm=1, bob_phase=0.4, rock=3.5,
                   rock_harm=1, rock_phase=0.5, flex=8.0, flex_phase=0.95, nod=3.0, nod_harm=1, nod_phase=0.58,
                   roll=0.5, tail=5.0),
}
for _item in filter(None, os.environ.get('QG_SET', '').split(';')):          # tuning: "Clip:key=value,..."
    _clip, _pairs = _item.split(':', 1)
    for _pair in _pairs.split(','):
        _k, _v = _pair.split('=')
        CLIPS[_clip][_k] = float(_v)

pose.reset(rig)
for b in rig.pose.bones:
    b.rotation_mode = 'QUATERNION'
bpy.context.view_layer.update()
rest = {b.name: b.matrix.copy() for b in rig.pose.bones}
points = np.array([tuple(v.co) for v in mesh.data.vertices])
foot = {}
for kind in ('Front', 'Hind'):
    for side, sign in [('L', 1), ('R', -1)]:
        name = f'{kind}Hoof_{side}'
        mask = (points[:, 0] * sign > 0) & ((points[:, 1] < 0) == (kind == 'Front')) & (points[:, 2] < .035)
        foot[kind, side] = rest[name].translation.copy() - Vector((0, 0, float(points[mask, 2].min())))


HOOF = {key: rig.pose.bones[f'{key[0]}Hoof_{key[1]}'].length for key in foot}


def rot(name, axis, degrees):
    if abs(degrees) > 1e-7:
        pose.rotate_world(rig, name, axis, degrees)


def smooth(t):
    t = max(0, min(1, t))
    return t * t * (3 - 2 * t)


def leg(kind, side, offset=Vector(), pitch=0.0):
    """animate_gorgon.py's leg(articulate=True); returns the hoof's miss (m) from its target."""
    hoof = f'{kind}Hoof_{side}'; pastern = f'{kind}Pastern_{side}'
    upper, lower = (f'UpperArm_{side}', f'ForeArm_{side}') if kind == 'Front' else (f'Thigh_{side}', f'Shin_{side}')
    target = foot[kind, side] + offset
    rotation = Quaternion(X, math.radians(pitch))
    direction = (target - rig.pose.bones[upper].head).normalized()
    rest_vector = rest[hoof].translation - rest[pastern].translation
    lower_vector = direction * rest_vector.length
    pastern_rotation = rest_vector.normalized().rotation_difference(direction)
    carpus = target - lower_vector
    pole = carpus + Vector((.02 if side == 'L' else -.02, .35 if kind == 'Front' else -.35, .04))
    pose.two_bone_ik(rig, upper, lower, carpus, pole)
    for name in (pastern, hoof):
        b = rig.pose.bones[name]
        b.matrix = Matrix.LocRotScale(b.head.copy(), (pastern_rotation if name == pastern else rotation)
                                      @ rest[name].to_quaternion(), Vector((1, 1, 1)))
        bpy.context.view_layer.update()
    return (rig.pose.bones[hoof].head - target).length


def body(drop=-.015, pitch=0.0, roll=0.0, head=0.0, yaw=0.0, flex=0.0):
    """animate_gorgon.py's body() plus back flex: Spine2/Spine3 arch by `flex` (+ = flexed, shoulders down toward
    the hips) and the neck takes it back."""
    pose.reset(rig)
    b = rig.pose.bones['Spine1']
    b.matrix = Matrix.Translation((0, 0, drop)) @ b.matrix
    bpy.context.view_layer.update()
    rot('Spine1', X, pitch); rot('Spine1', Y, roll)
    rot('Spine2', X, flex * 0.5); rot('Spine3', X, flex * 0.5)
    rot('Neck1', X, -flex + head * .35); rot('Head', X, head * .65)
    rot('Neck1', Z, yaw * .4); rot('Head', Z, yaw * .6)


def tail(t, amplitude=3):
    for i in range(1, 6):
        rot(f'Tail{i}', Z, amplitude * (i / 5) * math.sin(2 * math.pi * t - .55 * i))


MISS = []


def gait(phase, c, stride):
    w = lambda harm, ph: math.cos(2 * math.pi * harm * (phase - ph))          # noqa: E731
    body(drop=c['drop'] - c['bob'] * w(c['bob_harm'], c['bob_phase']),
         pitch=c['rock'] * w(c['rock_harm'], c['rock_phase']) if c['rock_harm'] == 1 else
         c['rock'] * math.sin(4 * math.pi * phase),
         roll=c['roll'] * math.sin(2 * math.pi * phase), flex=c['flex'] * w(1, c['flex_phase']),
         head=c['nod'] * w(c['nod_harm'], c['nod_phase']) if c['nod_harm'] == 1 else
         -c['nod'] * math.sin(4 * math.pi * phase))
    duty = c['duty']; distance = stride * duty
    for key, touch in c['feet'].items():
        q = (phase - touch) % 1
        kind, side = key
        if q < duty:
            dy = -distance / 2 + stride * q
            dz = pitch = 0
        else:
            u = (q - duty) / (1 - duty)
            dy = distance / 2 - distance * smooth(u)
            dz = (c['lift_f'] if kind == 'Front' else c['lift_h']) * math.sin(math.pi * u) ** c['lift_pow']
            pitch = c['tuck'] * math.sin(math.pi * u)
            dz += HOOF[kind, side] * math.sin(math.radians(pitch))   # the tucked hoof's tip clears the floor
            if kind == 'Front':
                dy -= c['reach'] * math.sin(math.pi * min(1.0, max(0.0, (u - 0.4) / 0.6)))
            else:
                dy += c['trail'] * math.sin(math.pi * min(1.0, u / 0.45))
        upper = f'UpperArm_{side}' if kind == 'Front' else f'Thigh_{side}'
        dy += rest[upper].translation.y - rest[f'{kind}Hoof_{side}'].translation.y
        m = leg(kind, side, Vector((0, dy, dz)), pitch)
        if q < duty:
            MISS.append(m)
    tail(phase, c['tail'])


def evaluated():
    obj = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get()); data = obj.to_mesh()
    co = np.empty(len(data.vertices) * 3); data.vertices.foreach_get('co', co); obj.to_mesh_clear()
    return co.reshape(-1, 3)


info = {}
for name, c in CLIPS.items():
    n = int(c['frames']); T = n / FPS; stride = c['speed'] * T
    rig.animation_data_create(); rig.animation_data.action = None
    frames, lows = [], []
    MISS.clear()
    for f in range(n + 1):
        gait((f % n) / n, c, stride)
        lows.append(float(evaluated()[:, 2].min()))
        frames.append({b.name: (b.location.copy(), b.rotation_quaternion.copy()) for b in rig.pose.bones})
    old = bpy.data.actions.get(name)
    if old:
        bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name); act.use_fake_user = True; rig.animation_data.action = act
    if len(getattr(act, 'slots', [])):
        rig.animation_data.action_slot = act.slots[0]
    previous = {}
    for f, frame in enumerate(frames):
        for b in rig.pose.bones:
            loc, q = frame[b.name]
            if b.name in previous and q.dot(previous[b.name]) < 0:
                q = -q
            previous[b.name] = q
            b.location, b.rotation_quaternion = loc, q
            b.keyframe_insert('location', frame=f); b.keyframe_insert('rotation_quaternion', frame=f)
    act.use_frame_range = True; act.frame_start, act.frame_end = 0, n
    rig.animation_data.action = None
    info[name] = dict({k: v for k, v in c.items() if k != 'feet'}, seconds=T, stride=stride,
                      sweep=stride * c['duty'], lowest=[min(lows), max(lows)], planted_miss=max(MISS))
    print(f'CLIP {name}: {T:.4f} s, stride {stride:.4f}, sweep {stride * c["duty"]:.3f}, lowest vertex '
          f'{min(lows) * 100:+.2f}..{max(lows) * 100:+.2f} cm, worst planted hoof miss {max(MISS) * 1000:.1f} mm',
          flush=True)
json.dump(info, open(os.path.join(HERE, 'work', 'm564_gaits_info.json'), 'w'), indent=1)
pose.reset(rig)
bpy.context.scene.render.fps = FPS; bpy.context.scene.render.fps_base = 1
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'm564_gaits.blend'))
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
