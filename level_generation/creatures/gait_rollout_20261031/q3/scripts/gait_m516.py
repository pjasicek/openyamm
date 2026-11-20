"""Walk2, Run2 and Sprint for the MM8 Thunder Lizard (m516, a two-legged digitigrade dinosaur), gait rollout package
q3 (2026-10-31), authored for the game's speeds (gait_gate.py targets): Standard wanders at 2.77-3.28 and chases at
5.55-6.56 model units/s, MAW (Spd / 2 + 300) chases at 10.34-10.85. The installed Walking (1.0) never played (the
wandering took Running, 2.4, x1.15-1.37) and Running played the chase x2.3-2.7 and MAW's x4.3-4.5.

The body, head, tail, arm and leg machinery are copied from ../../../mm8_m516_claude/scripts/animate_lizard.py (left
unchanged): analytic hip-knee-hock IK with the tarsus aimed at the ankle, the sole planted 8 mm above the floor on its
measured vertices, the torso shifting over the support foot and lowered for travel, the head steadied against the
hips, the tail countering the yaw with a delayed tip wave, the short arms swinging. The phase is Walking's (left foot
down at 0, right at 0.5). Strides follow dynamic similarity for the 1.05 m hip (Alexander: relative stride 2.3 Fr^0.3),
so the stance sweep stays about 1 m and the extra speed comes from cadence and flight:
  Walk2   grounded run (duty 0.52, no flight, as birds at this Froude number ~0.8): Standard's wandering.
  Run2    run with short flights (duty 0.33): Standard's chase.
  Sprint  long bounding strides (duty 0.24), the body lower and pitched forward, the tail out straight: MAW's chase.

Reads the project's rig blend (read only), saves <package>/work/m516_gaits.blend and writes only the new clips to the
GLB given, to be grafted onto the installed source with ../../claude_shared/graft_clips.py.

    blender -b --factory-startup -P gait_m516.py -- <out clips.glb>
"""
import bpy, os, sys, math, json
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix, Quaternion

HERE = Path(__file__).resolve().parents[1]                                   # the q3 package
PROJECT = HERE.parents[1] / 'mm8_m516_claude'
sys.path.insert(0, str(HERE.parents[1] / 'mm6_ckt_claude' / 'scripts'))
import posing as U  # noqa: E402

OUT = os.path.abspath(sys.argv[sys.argv.index('--') + 1])
bpy.ops.wm.open_mainfile(filepath=str(PROJECT / 'work' / 'rig_v1.blend'))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']
FPS = 60
DATA = json.loads((PROJECT / 'work' / 'rig.json').read_text()); NAMES = list(DATA['bones'])
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
REST = {s: {k: Vector(v) for k, v in zip(['hip', 'knee', 'hock', 'ankle', 'toe'], DATA['legs'][s])} for s in 'LR'}
Q = {s: rig.pose.bones['Foot_' + s].matrix.to_quaternion().copy() for s in 'LR'}
C = np.array([v.co[:] for v in body.data.vertices])
HIP_Y = (REST['L']['hip'].y + REST['R']['hip'].y) / 2      # the rest hips stand 14 cm apart along the body
FEET = {s: np.where((C[:, 0] * (1 if s == 'L' else -1) > 0) & (C[:, 2] < .115))[0] for s in 'LR'}

# Clip parameters: speed (model units/s), frames at 60 fps, duty, foothold centre (ankle y, + = back) and the share of
# the rest hips' 14 cm skew it follows per side (skew; Walking and Running take 0: both feet at .27 / .16), swing
# lift (m), toe and tarsus swing angles (deg), torso drop and bob (lowest at bob_phase of each step), side shift,
# pitch (deg, + = nose down), roll, yaw, head pitch, tail sway and lift, arm swing (deg).
# Walking: 1.0 s, 1.0 m, duty .62, centre .27, lift .13, toe 22, tarsus 12, drop -.095 +- .014, side .105, pitch 7,
# roll 4, yaw 3, head 5, tail 2.4 / .3, arms 5. Running: 0.75 s, 1.8 m, duty .45, centre .16, lift .20, drop -.13
# +- .05, pitch 12, head 8, tail 3.5 / 1.2, arms 9.
CLIPS = {
    'Walk2': dict(speed=2.84, frames=42, duty=0.52, centre=0.17, skew=1.0, lift=0.17, toe=24.0, tarsus=14.0, drop=-0.12,
                  bob=0.032, bob_phase=0.25, side=0.08, pitch=10.0, roll=3.0, yaw=3.0, head=7.0, tail=3.0,
                  tail_lift=0.8, arms=7.0),
    'Run2': dict(speed=5.69, frames=36, duty=0.33, centre=0.15, skew=1.0, lift=0.26, toe=30.0, tarsus=20.0, drop=-0.13,
                 bob=0.04, bob_phase=0.17, side=0.05, pitch=14.0, roll=2.5, yaw=3.0, head=10.0, tail=3.5,
                 tail_lift=1.5, arms=10.0),
    'Sprint': dict(speed=9.99, frames=29, duty=0.24, centre=0.11, skew=1.0, lift=0.34, toe=38.0, tarsus=28.0,
                   drop=-0.15, bob=0.035, bob_phase=0.12, side=0.03, pitch=18.0, roll=2.0, yaw=2.0, head=14.0,
                   tail=2.5, tail_lift=2.5, arms=12.0),
}
for _item in filter(None, os.environ.get('QG_SET', '').split(';')):          # tuning: "Clip:key=value,..."
    _clip, _pairs = _item.split(':', 1)
    for _pair in _pairs.split(','):
        _k, _v = _pair.split('=')
        CLIPS[_clip][_k] = float(_v)


def ss(x):
    x = min(1., max(0., x)); return x * x * (3 - 2 * x)


def rot(n, axis, d):
    U.rotate_world(rig, n, axis, d)


def co():
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
    a = np.empty(len(m.vertices) * 3); m.vertices.foreach_get('co', a); ev.to_mesh_clear(); return a.reshape(-1, 3)


def offset(v):
    b = rig.pose.bones['Hips']; b.matrix = Matrix.Translation(Vector(v)) @ b.matrix; bpy.context.view_layer.update()


def torso(lift=0., fwd=0., side=0., pitch=0., roll=0., yaw=0.):
    offset((side, -fwd, lift)); rot('Hips', Z, yaw); rot('Hips', Y, roll); rot('Hips', X, pitch)


def head(pitch=0., yaw=0., jaw=0., fan=0.):
    for n, w in [('Neck1', .28), ('Neck2', .37), ('Head', .35)]:
        rot(n, X, -pitch * w); rot(n, Z, yaw * w)
    rot('Jaw', X, jaw)
    for s, k in [('L', 1), ('R', -1)]:
        rot('Frill_' + s, Z, -k * fan)


def tail(t, period=2., sway=2., lift=0., counter=0.):
    for i in range(8):
        rot('Tail' + str(i + 1), Z,
            sway * (.45 + i * .10) * math.sin(2 * math.pi * t / period - i * .38) + counter / (i + 1))
        rot('Tail' + str(i + 1), X, lift * (1 - i * .09))


def arms(t, period=2., amount=2., up=0., axis=X):
    for s in 'LR':
        w = 2 * math.pi * t / period + (0 if s == 'L' else math.pi)
        rot('UpperArm_' + s, axis, up + amount * math.sin(w))
        rot('ForeArm_' + s, axis, -amount * .7 * math.sin(w - .4))
        rot('Hand_' + s, axis, amount * .4 * math.sin(w - .8))


def leg(s, ankle, pitch=0., toe=0.):
    r = REST[s]; tv = Matrix.Rotation(math.radians(-pitch), 3, X) @ (r['ankle'] - r['hock']); hock = Vector(ankle) - tv
    hip = rig.pose.bones['Thigh_' + s].head.copy(); pole = hip + Vector((0, -1, 0))
    U.two_bone_ik(rig, 'Thigh_' + s, 'Shin_' + s, hock, pole); U.aim_bone(rig, 'Tarsus_' + s, Vector(ankle))
    f = rig.pose.bones['Foot_' + s]
    f.matrix = Matrix.LocRotScale(f.head.copy(), Quaternion(X, math.radians(-toe)) @ Q[s], Vector((1, 1, 1)))
    bpy.context.view_layer.update()
    return (rig.pose.bones['Foot_' + s].head - Vector(ankle)).length


def planted(s, ankle, lift=0., pitch=0., toe=0.):
    target = Vector(ankle); target.z += lift; leg(s, target, pitch, toe)
    dz = .008 + lift - float(co()[FEET[s], 2].min()); target.z += dz; error = leg(s, target, pitch, toe)
    return error, abs(float(co()[FEET[s], 2].min()) - (.008 + lift))


def pose(c, p, stride, seconds):
    """animate_lizard.py's pose() for Walking/Running, with the clip's parameters."""
    U.reset(rig); errors = []; contacts = []
    w = 2 * math.pi * p; duty = c['duty']; yaw = c['yaw'] * math.sin(w); t = p * seconds
    torso(lift=c['drop'] - c['bob'] * math.cos(2 * w - 4 * math.pi * c['bob_phase']), side=c['side'] * math.sin(w),
          pitch=c['pitch'], roll=-c['roll'] * math.sin(w), yaw=yaw)
    head(pitch=c['head'], yaw=-yaw, jaw=2 + 2 * math.sin(2 * w))
    tail(t, seconds, c['tail'], lift=c['tail_lift'], counter=-yaw * .7)
    arms(t, seconds, c['arms'])
    for s in 'LR':
        phase = (p + (0 if s == 'L' else .5)) % 1.
        a = REST[s]['ankle'].copy(); a.y = c['centre'] + c['skew'] * (REST[s]['hip'].y - HIP_Y)
        if phase < duty:
            a.y += stride * (phase - duty / 2); lift = toe = tp = 0.
        else:
            u = (phase - duty) / (1 - duty); a.y += stride * duty * (.5 - ss(u))
            lift = c['lift'] * math.sin(math.pi * u); toe = c['toe'] * math.sin(math.pi * u)
            tp = c['tarsus'] * math.sin(math.pi * u)
        err, contact = planted(s, a, lift, tp, toe); errors.append(err)
        if err > 0.005:
            MISSES.setdefault(s, []).append((round(p, 2), round(phase, 2), round(err * 1000, 1)))
        if lift < 1e-7:
            contacts.append(contact)
    for _ in range(12):                                   # animate_lizard.py: the tail tip kept off the floor
        if float(co()[C[:, 1] > .78, 2].min()) >= .006:
            break
        rot('Tail1', X, 1.)
    return max(errors), max(contacts, default=0.)


MISSES = {}
info = {}
for old in list(bpy.data.actions):
    bpy.data.actions.remove(old)
for name, c in CLIPS.items():
    n = int(c['frames']); seconds = n / FPS; stride = c['speed'] * seconds
    samples = {b: [] for b in NAMES}; lows, ik, contact = [], [], []
    for f in range(n + 1):
        rig.animation_data_clear()
        e, k = pose(c, (f % n) / n, stride, seconds); ik.append(e); contact.append(k)
        lows.append(float(co()[:, 2].min()))
        for b in NAMES:
            bone = rig.pose.bones[b]; q = bone.rotation_quaternion.copy()
            if samples[b] and q.dot(samples[b][-1][1]) < 0:
                q.negate()
            samples[b].append((bone.location.copy(), q))
    action = bpy.data.actions.new(name); action.use_fake_user = True
    rig.animation_data_create(); rig.animation_data.action = action
    if len(getattr(action, 'slots', [])):
        rig.animation_data.action_slot = action.slots[0]
    for f in range(n + 1):
        for b in NAMES:
            bone = rig.pose.bones[b]; bone.location, bone.rotation_quaternion = samples[b][f]
            bone.keyframe_insert('location', frame=f); bone.keyframe_insert('rotation_quaternion', frame=f)
    action.use_frame_range = True; action.frame_start, action.frame_end = 0, n
    rig.animation_data.action = None
    info[name] = dict(c, seconds=seconds, stride=stride, sweep=stride * c['duty'], lowest=[min(lows), max(lows)],
                      ik_error=max(ik), contact_error=max(contact))
    print(f'CLIP {name}: {seconds:.4f} s, stride {stride:.4f}, sweep {stride * c["duty"]:.3f}, lowest vertex '
          f'{min(lows) * 100:+.2f}..{max(lows) * 100:+.2f} cm, worst IK error {max(ik) * 1000:.1f} mm, contact '
          f'{max(contact) * 1000:.1f} mm', flush=True)
    for side, rows in MISSES.items():
        print(f'MISS {name} {side}: {len(rows)} keys (phase, foot phase, mm) {rows[:8]}', flush=True)
    MISSES.clear()
json.dump(info, open(HERE / 'work' / 'm516_gaits_info.json', 'w'), indent=1)
U.reset(rig)
bpy.context.scene.render.fps = FPS; bpy.context.scene.render.fps_base = 1
bpy.ops.wm.save_as_mainfile(filepath=str(HERE / 'work' / 'm516_gaits.blend'))
for o in bpy.data.objects:
    o.select_set(o in (body, rig))
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=OUT, use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_all_influences=False, export_materials='NONE',
                          export_attributes=False, export_morph=False, export_reset_pose_bones=True,
                          export_anim_slide_to_zero=True)
print('EXPORTED', OUT)
