"""Walk2 for the MM8 Unicorn (m544), gait rollout package q4 (2026-10-31): a four-beat lateral-sequence walk for
Standard's (and MAW's) wandering, 0.46-0.51 model units/s (gait_gate.py: walk 0.34-0.62). The installed Walking is a
slow transverse gallop (0.64 m in 1.0 s, 0.64): Unicorn C wandered on it at x0.72. The chase (0.93-1.02) stays on
Running (0.853).

  Walk2  lateral-sequence walk (LH 0, LF .25, RH .5, RF .75; hind L at 0 as Walking's gallop), duty 0.62, the head
         nodding twice a loop (lowest as each fore hoof lands), the back rolling with the hind steps.

The leg machinery is ../../../mm8_m544_claude/scripts/animate_unicorn.py's (left unchanged; copied here because it keys
every clip when run): two-bone IK of upper/lower leg to the carpus or hock, the pastern inclined along the leg toward
the shoulder or hip ("articulate"), the hoof keeping its rest orientation (only pitched in the swing), footholds
centred at y -0.19 (front) and +0.19 (hind) as Walking. The swing hoof is raised by its tip's drop (q3's Gorgon) so a
tucked hoof does not graze the floor. The tail is lifted until its vertices clear 4 mm, as the project's clips.

Reads the project's animated blend (read only), saves <package>/work/m544_gaits.blend and writes only the new clips to
the GLB given, to be grafted onto the installed source with ../../claude_shared/graft_clips.py.

    blender -b --factory-startup -P gait_m544.py -- <out clips.glb>
"""
import bpy, os, sys, math, json
import numpy as np
from mathutils import Vector, Matrix, Quaternion

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))          # the q4 package
CREATURES = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(CREATURES, 'mm6_rat_claude', 'scripts'))
import posing as pose  # noqa: E402

OUT = os.path.abspath(sys.argv[sys.argv.index('--') + 1])
bpy.ops.wm.open_mainfile(filepath=os.path.join(CREATURES, 'mm8_m544_claude', 'work', 'anim_v1.blend'))
rig, mesh = bpy.data.objects['Unicorn_Rig'], bpy.data.objects['Unicorn']
FPS = 48
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))

LATERAL = {('Hind', 'L'): 0.0, ('Front', 'L'): 0.25, ('Hind', 'R'): 0.5, ('Front', 'R'): 0.75}
# speed (model units/s), frames at 48 fps, footfalls, duty, hoof lift front/hind (sin^lift_pow), swing tuck (deg),
# body drop and bob (twice a loop, lowest at bob_phase), pitch rocking (deg), roll (deg), head nod (deg, + = down,
# twice a loop, lowest at nod_phase), head yaw sway (deg), tail sway and lift (deg)
CLIPS = {
    'Walk2': dict(speed=0.49, frames=39, feet=LATERAL, duty=0.60, lift_f=0.034, lift_h=0.026, lift_pow=1.5,
                  tuck=28.0, drop=-0.030, bob=0.0035, bob_phase=0.10, rock=0.8, roll=1.2, nod=3.0, nod_phase=0.30,
                  yaw=1.5, tail=3.0, tail_lift=4.0),
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
    """animate_unicorn.py's leg(articulate=True); returns the hoof's miss (m) from its target."""
    hoof, pastern = f'{kind}Hoof_{side}', f'{kind}Pastern_{side}'
    upper, lower = (f'UpperArm_{side}', f'ForeArm_{side}') if kind == 'Front' else (f'Thigh_{side}', f'Shin_{side}')
    target = foot[kind, side] + offset
    rotation = Quaternion(X, math.radians(pitch))
    rest_vector = rest[hoof].translation - rest[pastern].translation
    direction = (target - rig.pose.bones[upper].head).normalized()
    lower_vector = direction * rest_vector.length
    pastern_rotation = rest_vector.normalized().rotation_difference(direction)
    carpus = target - lower_vector
    pole = carpus + Vector((.012 if side == 'L' else -.012, .35 if kind == 'Front' else -.35, .04))
    pose.two_bone_ik(rig, upper, lower, carpus, pole)
    for name in (pastern, hoof):
        bone = rig.pose.bones[name]
        q = (pastern_rotation if name == pastern else rotation) @ rest[name].to_quaternion()
        bone.matrix = Matrix.LocRotScale(bone.head.copy(), q, Vector((1, 1, 1)))
        bpy.context.view_layer.update()
    return (rig.pose.bones[hoof].head - target).length


def body(drop=-.016, pitch=0.0, roll=0.0, head=0.0, yaw=0.0):
    """animate_unicorn.py's body()"""
    pose.reset(rig)
    root = rig.pose.bones['Spine1']
    root.matrix = Matrix.Translation((0, 0, drop)) @ root.matrix
    bpy.context.view_layer.update()
    rot('Spine1', X, pitch)
    rot('Spine1', Y, roll)
    for name, weight in [('Neck1', .25), ('Neck2', .35), ('Head', .4)]:
        rot(name, X, head * weight)
        rot(name, Z, yaw * weight)


def tail(phase, amplitude=3, lift=0):
    """animate_unicorn.py's tail()"""
    for i in range(1, 6):
        rot(f'Tail{i}', Z, amplitude * (i / 5) * math.sin(2 * math.pi * phase - .55 * i))
        rot(f'Tail{i}', X, lift if i == 1 else 0)


MISS = []


def gait(phase, c, stride):
    two = lambda ph: math.cos(4 * math.pi * (phase - ph))                  # noqa: E731  twice a loop, 1 at ph
    body(drop=c['drop'] - c['bob'] * two(c['bob_phase']), pitch=c['rock'] * math.sin(4 * math.pi * phase),
         roll=c['roll'] * math.sin(2 * math.pi * phase), head=c['nod'] * two(c['nod_phase']),
         yaw=c['yaw'] * math.sin(2 * math.pi * (phase - 0.1)))
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
            pitch = -c['tuck'] * math.sin(math.pi * u)          # Walking's sign: - = toe up
            dz += HOOF[kind, side] * max(0.0, math.sin(math.radians(pitch)))    # a toe-down hoof's tip clears
        dy += (-.19 if kind == 'Front' else .19) - foot[key].y               # footholds centred as Walking
        m = leg(kind, side, Vector((0, dy, dz)), pitch)
        if q < duty:
            MISS.append(m)
    tail(phase, c['tail'], c['tail_lift'])


def evaluated():
    obj = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get()); data = obj.to_mesh()
    co = np.empty(len(data.vertices) * 3); data.vertices.foreach_get('co', co); obj.to_mesh_clear()
    return co.reshape(-1, 3)


tail_ids = [v.index for v in mesh.data.vertices if
            any(mesh.vertex_groups[g.group].name.startswith('Tail') and g.weight > .5 for g in v.groups)]
info = {}
for name, c in CLIPS.items():
    n = int(c['frames']); T = n / FPS; stride = c['speed'] * T
    rig.animation_data_create(); rig.animation_data.action = None
    frames, lows = [], []
    MISS.clear()
    for f in range(n + 1):
        gait((f % n) / n, c, stride)
        for attempt in range(40):                                             # the project's tail floor rule
            if float(evaluated()[tail_ids, 2].min()) >= .004:
                break
            rot('Tail1', X, 2)
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
json.dump(info, open(os.path.join(HERE, 'work', 'm544_gaits_info.json'), 'w'), indent=1)
pose.reset(rig)
bpy.context.scene.render.fps = FPS; bpy.context.scene.render.fps_base = 1
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'm544_gaits.blend'))
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
