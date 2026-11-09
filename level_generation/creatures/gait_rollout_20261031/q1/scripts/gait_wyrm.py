"""Walk2 and Run2 for the MM6 Wyrm (gait rollout q1, 2026-10-31): shorter strides for the game's slow speeds.

The Wyrm wanders at 0.11-0.19 and chases at 0.22-0.37 model units/s (gait_gate.py: walk 0.12-0.15, run 0.25-0.30).
The installed Walking (0.12 m in 0.75 s, 0.16) played Great Wyrm C's wandering at x0.69, and its chase fell back on
Walking x1.38 because Running (0.19 m in 0.625 s, 0.30) played x0.73. Slower speeds take shorter strides at a slightly
lower cadence (dynamic similarity), so:

  Walk2  0.111 m in 0.7917 s (19 keys at 24 fps), authored 0.140, duty 0.70, four-beat walk as Walking
  Run2   0.180 m in 0.6667 s (16 keys at 24 fps), authored 0.270, duty 0.58, diagonal gait as Running

Same machinery as ../../mm6_drr1_claude/scripts/anim_wyrm.py (copied, not imported: that script runs at import): the
paw two-bone IK with its poles, the body bob, the tail wave and its floor clamp, the same leg phases (front L down at
0, as Walking and Running), the Remains bone at scale 0 in living clips, linear keys at 24 fps.
Reads ../../mm6_drr1_claude/export/mm6_wyrm.blend (the current master, read only), saves work/wyrm_gaits.blend and writes
the two clips (only) to the GLB given as argument, for ../../claude_shared/graft_clips.py.
Args: -- <out clips.glb>"""
import bpy, math, json, sys, os
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix, Quaternion

Q1 = Path(__file__).resolve().parents[1]
PROJ = Q1.parents[1] / 'mm6_drr1_claude'
sys.path.insert(0, str(Q1.parents[1] / 'mm6_rat_claude/scripts'))
import posing
OUT = os.path.abspath(sys.argv[sys.argv.index('--') + 1])
bpy.ops.wm.open_mainfile(filepath=str(PROJ / 'export/mm6_wyrm.blend'))
rig = bpy.data.objects['Wyrm_Rig']; mesh = bpy.data.objects['Wyrm']; sc = bpy.context.scene
FPS = 24; sc.render.fps = FPS; sc.render.fps_base = 1
CLIPS = {'Walk2': dict(frames=19, stride=0.111, duty=0.70, running=False),
         'Run2': dict(frames=16, stride=0.180, duty=0.58, running=True)}
if rig.animation_data:
    rig.animation_data.action = None
for b in rig.pose.bones:
    b.rotation_mode = 'QUATERNION'
posing.reset(rig)
bpy.context.view_layer.update()
REST = {b.name: b.matrix.copy() for b in rig.pose.bones}
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))


def rot(name, axis, deg):
    if abs(deg) > 1e-7:
        posing.rotate_world(rig, name, axis, deg)


def smooth(t):
    t = max(0, min(1, t)); return t * t * (3 - 2 * t)


def leg(kind, side, offset=Vector(), pitch=0):
    upper, lower, paw = ((f'UpperArm_{side}', f'ForeArm_{side}', f'FrontPaw_{side}') if kind == 'front'
                         else (f'Thigh_{side}', f'Shin_{side}', f'HindPaw_{side}'))
    target = REST[paw].translation + offset; sign = 1 if side == 'L' else -1
    pole = target + Vector((.010 * sign, .18 if kind == 'front' else -.18, .08))
    posing.two_bone_ik(rig, upper, lower, target, pole)
    bone = rig.pose.bones[paw]
    bone.matrix = Matrix.LocRotScale(bone.head.copy(), Quaternion(X, math.radians(pitch)) @ REST[paw].to_quaternion(),
                                     Vector((1, 1, 1)))
    bpy.context.view_layer.update()


def tail(phase, amp=2, lift=0):
    for i in range(1, 11):
        rot(f'Tail{i}', Z, amp * (.4 + i / 10) * math.sin(2 * math.pi * (phase - .045 * i)))
        rot(f'Tail{i}', X, lift if i == 1 else 0)


def core(p):
    root = rig.pose.bones['Spine1']
    root.matrix = Matrix.Translation(Vector((0, p.get('travel', 0), p.get('height', 0)))) @ root.matrix
    bpy.context.view_layer.update()
    rot('Spine1', X, p.get('pitch', 0)); rot('Spine1', Y, p.get('roll', 0)); rot('Spine2', X, p.get('chest', 0))
    for n in ['Neck1', 'Neck2', 'Neck3']:
        rot(n, X, p.get('neck', 0) / 3); rot(n, Z, p.get('yaw', 0) / 3)
    rot('Head', X, p.get('head', 0)); rot('Jaw', X, p.get('jaw', 0))


def gait(t, period, stride, duty, running=False):
    """anim_wyrm.gait unchanged."""
    posing.reset(rig); phase = t / period
    core({'height': -.005 - .002 * math.cos(phase * 4 * math.pi), 'neck': -3 if running else 0})
    tail(phase, 2.5)
    phases = [('front', 'L', 0), ('front', 'R', .5), ('hind', 'L', .5 if running else .75),
              ('hind', 'R', 0 if running else .25)]
    for kind, side, shift in phases:
        q = (phase + shift) % 1
        if q < duty:
            dy = stride * (q - duty / 2); dz = 0; pitch = 0
        else:
            u = (q - duty) / (1 - duty); dy = stride * duty * (.5 - smooth(u))
            dz = (.022 if kind == 'front' else .017) * math.sin(math.pi * u); pitch = 10 * math.sin(math.pi * u)
        leg(kind, side, Vector((0, dy, dz)), pitch)


deps = bpy.context.evaluated_depsgraph_get()


def coords():
    bpy.context.view_layer.update(); ev = mesh.evaluated_get(deps); me = ev.to_mesh()
    a = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', a); ev.to_mesh_clear()
    a = a.reshape(-1, 3)
    return a @ np.array(mesh.matrix_world.to_3x3()).T + np.array(mesh.matrix_world.translation)


names = {g.index: g.name for g in mesh.vertex_groups}
tail_sections = {n: [v.index for v in mesh.data.vertices if any(names[g.group] == n and g.weight > .45 for g in v.groups)]
                 for n in [f'Tail{i}' for i in range(1, 11)]}
tail_clearance = {n: max(.008, -min((REST[n].inverted() @ mesh.data.vertices[i].co).z for i in ids)) + .003
                  for n, ids in tail_sections.items() if ids}


def floor():
    """anim_wyrm.floor for living clips: a tail bone whose tip drops under its clearance is aimed up to it."""
    for i in range(1, 11):
        b = rig.pose.bones[f'Tail{i}']; h = b.head.copy(); d = b.tail - h
        clearance = tail_clearance.get(b.name, .008)
        if b.tail.z < clearance:
            flat = Vector((d.x, d.y, 0)).normalized(); dz = min(clearance - h.z, d.length * .99)
            posing.aim_bone(rig, b.name, h + flat * math.sqrt(max(d.length * d.length - dz * dz, 1e-8)) + Vector((0, 0, dz)))


report = {}
if rig.animation_data is None:
    rig.animation_data_create()
for name, c in CLIPS.items():
    rig.animation_data.action = None
    old = bpy.data.actions.get(name)
    if old:
        bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name); act.use_fake_user = True
    n = c['frames']; period = n / FPS; poses = []; lows = []
    for f in range(n + 1):
        gait((f % n) / FPS, period, c['stride'], c['duty'], c['running']); floor()
        rig.pose.bones['Remains'].scale = (0, 0, 0)
        lows.append(float(coords()[:, 2].min()))
        poses.append({b.name: (b.location.copy(), b.rotation_quaternion.copy(), b.scale.copy()) for b in rig.pose.bones})
    rig.animation_data.action = act
    if len(getattr(act, 'slots', [])):
        rig.animation_data.action_slot = act.slots[0]
    previous = {}
    for f, pose in enumerate(poses):
        for b in rig.pose.bones:
            loc, q, scale = pose[b.name]
            if b.name in previous and previous[b.name].dot(q) < 0:
                q = -q
            previous[b.name] = q; b.location = loc; b.rotation_quaternion = q; b.scale = scale
            for prop in ['location', 'rotation_quaternion', 'scale']:
                b.keyframe_insert(prop, frame=f)
    act.use_frame_range = True; act.frame_start, act.frame_end = 0, n
    rig.animation_data.action = None
    report[name] = {'seconds': period, 'stride': c['stride'], 'authored_speed': c['stride'] / period,
                    'duty': c['duty'], 'lowest': [min(lows), max(lows)]}
    print('CLIP', name, report[name], flush=True)
    assert min(lows) > -.003, (name, min(lows))
for a in bpy.data.actions:
    for layer in getattr(a, 'layers', []):
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    for k in fc.keyframe_points:
                        k.interpolation = 'LINEAR'
(Q1 / 'work/wyrm_gaits_info.json').write_text(json.dumps(report, indent=1) + '\n')
posing.reset(rig)
bpy.ops.wm.save_as_mainfile(filepath=str(Q1 / 'work/wyrm_gaits.blend'))
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
