"""Walk2 and Run2 for the MM8 Centaur (m532, mm8_centaur.glb: a horse body with a human torso carrying a bow), gait
rollout package q4 (2026-10-31), authored for the game's speeds (gait_gate.py targets; MAW leaves them unchanged): it
wanders at 2.68-2.88 and chases at 5.37-5.76 model units/s (metres: the model is 2.6 m tall at 102.5 units per
metre). The installed Walking (1.129 m in 0.75 s, 1.51) and Running (2.212 m in 0.6667 s, 3.32) are trots: wandering
played Walking x1.78-1.85 (C took Running x0.87) and chasing played Running x1.62-1.74.

  Walk2  working trot as Walking and Running (front L + hind R at 0), duty 0.52 (a diagonal pair always down).
  Run2   left-lead canter: hind R at 0 (as the walk's hind R), hind L .2 with front R .26, the leading front L .5, one
         suspension after the leading fore lifts; the horse body rocks (hindquarters down and forehand up as the
         hinds land, the forehand down as the leading fore lands), the neck of the horse being the rider's torso, which
         takes back most of the rocking; the tail lifts.

Horse body (Root, HorsePelvis, HorseSpine, HorseChest, the four legs and the tail) is new; the hooves are planted with
../../mm8_m532_claude/scripts/animate.py's leg(): front two-bone IK to the fetlock, hind two-bone IK to the hock with
the cannon aimed at the fetlock, the hoof in its rest orientation (here also tucked in the swing, raised by the toe's
drop). The rider (Spine and everything under it: torso, head, both arms with the carry-fixed bow hold, the bow and
its string bones) and the Quiver and Arrow keep their local channels from the installed clip sampled at the same
phase (Walking for Walk2, Running for Run2), so the accepted bow carry (../../mm8_centaur_reduce_claude README,
"Bow-carry fix") is unchanged; Spine is then turned back against the new body's rocking.

Reads ../../mm8_m532_claude/work/centaur_master_carry.blend (the current master of every clip; read only), saves
<package>/work/centaur_gaits.blend and writes only the new clips to the GLB given, to be grafted onto the installed
source with ../../claude_shared/graft_clips.py.

    blender -b --factory-startup -P gait_centaur.py -- <out clips.glb>
"""
import bpy, os, sys, math, json
import numpy as np
from mathutils import Vector, Matrix, Quaternion

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))          # the q4 package
CREATURES = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(CREATURES, 'mm6_rat_claude', 'scripts'))
import posing as Q  # noqa: E402

OUT = os.path.abspath(sys.argv[sys.argv.index('--') + 1])
bpy.ops.wm.open_mainfile(filepath=os.path.join(CREATURES, 'mm8_m532_claude', 'work', 'centaur_master_carry.blend'))
rig, body = bpy.data.objects['Rig'], bpy.data.objects['Body']
sc = bpy.context.scene
FPS = 48
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
rig.animation_data_create(); rig.animation_data.action = None
Q.reset(rig)
rest = {b.name: b.matrix_local.copy() for b in rig.data.bones}


def under(name):
    out = [name]
    for c in rig.data.bones[name].children:
        out += under(c.name)
    return out


RIDER = under('Spine') + ['Quiver', 'Arrow']
TROT = {('Front', 'L'): 0.0, ('Hind', 'R'): 0.0, ('Front', 'R'): 0.5, ('Hind', 'L'): 0.5}
CANTER = {('Hind', 'R'): 0.0, ('Hind', 'L'): 0.20, ('Front', 'R'): 0.26, ('Front', 'L'): 0.50}
# speed (m/s), frames at 48 fps, footfalls, duty, the clip the rider comes from, hoof lift front/hind, swing tuck (deg,
# + = toe down), root drop and bob (bob_harm a loop, lowest at bob_phase), body pitch (deg, + = nose down; pitch_harm a
# loop, most nose-down at pitch_phase), horse back wave (deg, twice a loop as Walking), rider's share of the pitch
# taken back, tail sway and lift (deg), swing timing (u ** early: under 1 lifts and tucks the hoof early in the swing)
CLIPS = {
    # Walking: 0.75 s, 1.129 m, duty 0.62, lift 0.15, drop 0.10; Running: 0.6667 s, 2.212 m, duty 0.52, lift 0.24,
    # drop 0.24.
    'Walk2': dict(speed=2.75, frames=31, feet=TROT, duty=0.52, rider='Walking', lift_f=0.17, lift_h=0.15, tuck=35.0,
                  drop=-0.17, bob=0.02, bob_harm=2, bob_phase=0.26, pitch=0.6, pitch_harm=2, pitch_phase=0.0,
                  wave=1.5, take_back=0.7, sway=3.0, tail_lift=4.0, early=0.8, early_h=0.9, hind_back=0.0),
    'Run2': dict(speed=5.45, frames=27, feet=CANTER, duty=0.34, rider='Running', lift_f=0.26, lift_h=0.16, tuck=55.0,
                 drop=-0.20, bob=0.035, bob_harm=1, bob_phase=0.36, pitch=2.5, pitch_harm=1, pitch_phase=0.55,
                 wave=0.0, take_back=0.7, sway=2.0, tail_lift=12.0, early=0.55, early_h=0.85, hind_back=0.07),
}
for _item in filter(None, os.environ.get('QG_SET', '').split(';')):          # tuning: "Clip:key=value,..."
    _clip, _pairs = _item.split(':', 1)
    for _pair in _pairs.split(','):
        _k, _v = _pair.split('=')
        CLIPS[_clip][_k] = float(_v)
HOOF = {(k, s): rig.data.bones[f'{k}Hoof_{s}'].length for k in ('Front', 'Hind') for s in 'LR'}


def smooth(x):
    x = max(0, min(1, x)); return x * x * (3 - 2 * x)


def orient(name, R):
    b = rig.pose.bones[name]; b.matrix = Matrix.Translation(b.head) @ R.to_4x4(); bpy.context.view_layer.update()


def leg(side, front, dy=0.0, lift=0.0, tuck=0.0):
    """animate.py's leg(), plus the hoof tuck; returns the fetlock's miss (m)."""
    pre = 'Front' if front else 'Hind'; sg = 1 if side == 'L' else -1
    hoof = pre + 'Hoof_' + side; ankle = rest[hoof].translation + Vector((0, dy, lift))
    if front:
        Q.two_bone_ik(rig, pre + 'Upper_' + side, pre + 'Lower_' + side, ankle, (sg * .32, -.15, .62))
    else:
        hock = ankle - Vector((0, -.025, -.337))
        Q.two_bone_ik(rig, 'HindUpper_' + side, 'HindLower_' + side, hock, (sg * .36, -.1, .8))
        Q.aim_bone(rig, 'HindCannon_' + side, ankle)
    orient(hoof, Quaternion(X, math.radians(tuck)).to_matrix() @ rest[hoof].to_3x3())
    return (rig.pose.bones[hoof].head - ankle).length


def sample_rider(clip, phase):
    act = bpy.data.actions[clip]
    rig.animation_data.action = act
    if len(getattr(act, 'slots', [])):
        rig.animation_data.action_slot = act.slots[0]
    f = phase * act.frame_range[1]
    sc.frame_set(int(f), subframe=f - int(f))
    out = {n: (rig.pose.bones[n].location.copy(), rig.pose.bones[n].rotation_quaternion.copy(),
               rig.pose.bones[n].scale.copy()) for n in RIDER}
    rig.animation_data.action = None
    return out


MISS = []


def gait(phase, c, stride):
    rider = sample_rider(c['rider'], phase)
    Q.reset(rig)
    w = lambda harm, ph: math.cos(2 * math.pi * harm * (phase - ph))          # noqa: E731
    root = rig.pose.bones['Root']
    M = root.matrix.copy(); M.translation.z += c['drop'] - c['bob'] * w(c['bob_harm'], c['bob_phase'])
    root.matrix = M; bpy.context.view_layer.update()
    pitch = c['pitch'] * w(c['pitch_harm'], c['pitch_phase'])
    Q.rotate_world(rig, 'Root', 'X', pitch, pivot=(0, 0.0, 1.1 + c['drop']))    # + pitch = nose down
    Q.rotate_world(rig, 'HorseSpine', 'X', -c['wave'] * math.sin(4 * math.pi * phase))
    duty = c['duty']; distance = stride * duty
    for (kind, side), touch in c['feet'].items():
        q = (phase - touch) % 1
        if q < duty:
            dy = -distance / 2 + stride * q; lift = tuck = 0.0
        else:
            u = (q - duty) / (1 - duty)
            e = u ** c['early' if kind == 'Front' else 'early_h']   # flexed early in the swing, reaching nearly straight to land
            dy = distance / 2 - distance * smooth(e)
            lift = (c['lift_f'] if kind == 'Front' else c['lift_h']) * math.sin(math.pi * e)
            tuck = c['tuck'] * math.sin(math.pi * e)
            lift += HOOF[kind, side] * math.sin(math.radians(tuck)) * 0.7    # the tucked toe clears the floor
        if kind == 'Hind':
            dy += c['hind_back']                                             # hind footholds centred further back
        m = leg(side, kind == 'Front', dy, lift, tuck)
        if q < duty:
            MISS.append((m, f'{kind}{side}', round(q, 2)))
    for k in range(1, 6):
        Q.rotate_world(rig, f'Tail{k}', 'Z', (c['sway'] + k * .7) * math.sin(2 * math.pi * phase - k * .38))
    Q.rotate_world(rig, 'Tail1', 'X', c['tail_lift'])                        # + = raised
    for attempt in range(30):                                                # the tail hair clears the floor
        if float(mesh_co()[TAIL, 2].min()) >= .01:
            break
        Q.rotate_world(rig, 'Tail1', 'X', 2)
    for n in RIDER:                                                          # parents before children (pre-order)
        b = rig.pose.bones[n]
        b.location, b.rotation_quaternion, b.scale = rider[n]
    bpy.context.view_layer.update()
    Q.rotate_world(rig, 'Spine', 'X', -c['take_back'] * pitch)               # the torso takes back the rocking
    return pitch


def mesh_co():
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh()
    a = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', a); ev.to_mesh_clear()
    return a.reshape(-1, 3)


_groups = {g.index: g.name for g in body.vertex_groups}
TAIL = np.array([bool(v.groups) and _groups[max(v.groups, key=lambda g: g.weight).group].startswith('Tail')
                 for v in body.data.vertices])
ARROW = np.array([bool(v.groups) and _groups[max(v.groups, key=lambda g: g.weight).group] == 'Arrow'
                  for v in body.data.vertices])
for b in rig.pose.bones:
    b.rotation_mode = 'QUATERNION'
info = {}
for name, c in CLIPS.items():
    n = int(c['frames']); T = n / FPS; stride = c['speed'] * T
    frames, lows = [], []
    MISS.clear()
    for f in range(n + 1):
        gait((f % n) / n, c, stride)
        co = mesh_co()
        co = co[~ARROW]                                                       # the hidden arrow sits at Root
        lows.append(float(co[:, 2].min()))
        frames.append({b.name: (b.location.copy(), b.rotation_quaternion.copy(), b.scale.copy())
                       for b in rig.pose.bones})
    old = bpy.data.actions.get(name)
    if old:
        bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name); act.use_fake_user = True; rig.animation_data.action = act
    if len(getattr(act, 'slots', [])):
        rig.animation_data.action_slot = act.slots[0]
    previous = {}
    for f, frame in enumerate(frames):
        for b in rig.pose.bones:
            loc, q, s = frame[b.name]
            if b.name in previous and q.dot(previous[b.name]) < 0:
                q = -q
            previous[b.name] = q
            b.location, b.rotation_quaternion, b.scale = loc, q, s
            for path in ('location', 'rotation_quaternion', 'scale'):
                b.keyframe_insert(path, frame=f, group=b.name)
    act.use_frame_range = True; act.frame_start, act.frame_end = 0, n
    rig.animation_data.action = None
    worst = max(MISS)
    info[name] = dict({k: v for k, v in c.items() if k != 'feet'}, seconds=T, stride=stride,
                      sweep=stride * c['duty'], lowest=[min(lows), max(lows)], planted_miss=worst[0])
    print(f'CLIP {name}: {T:.4f} s, stride {stride:.4f}, sweep {stride * c["duty"]:.3f}, lowest vertex '
          f'{min(lows) * 100:+.2f}..{max(lows) * 100:+.2f} cm, worst planted fetlock miss {worst[0] * 1000:.1f} mm '
          f'({worst[1]} at stance {worst[2]}); over 5 mm: {sorted(m for m in MISS if m[0] > .005)[-5:]}', flush=True)
json.dump(info, open(os.path.join(HERE, 'work', 'centaur_gaits_info.json'), 'w'), indent=1)
Q.reset(rig)
sc.render.fps = FPS; sc.render.fps_base = 1
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'centaur_gaits.blend'))
for a in list(bpy.data.actions):
    if a.name not in CLIPS:
        bpy.data.actions.remove(a)
for o in bpy.data.objects:
    o.select_set(o in (body, rig))
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=OUT, use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_all_influences=False, export_materials='NONE',
                          export_attributes=False, export_morph=False, export_reset_pose_bones=True,
                          export_anim_slide_to_zero=True)
print('EXPORTED', OUT)
