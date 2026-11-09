"""Walk2 and Run2 for the MM8 wererat rat form (2026-10-21 gait pass), keyed at 48 fps on work/rat_final.blend.

The game plays a gait one loop per stride of travel, and m452 wanders at 1.00-1.38 and chases at 1.99-2.76 model
units/s, so the clips are authored at those speeds (gait_gate.py targets 1.17 and 2.34):
  Walk2  quick long trot, 15 frames (0.3125 s), stride 0.365 m (1.168 m/s): diagonal pairs with the hind foot of each
         pair 0.05 of a cycle behind its front foot, duty 0.52 (a foot always on the floor), shoulders carried 2.5 cm
         lower and the front footholds shifted forward for reach, the body bobbing twice per cycle;
  Run2   half-bound, 16 frames (0.3333 s), stride 0.78 m (2.34 m/s): hind feet land almost together (HL 0, HR 0.06,
         duty 0.30), extended flight, front feet staggered (FL 0.44, FR 0.52, duty 0.25), gathered flight. The spine
         flexes (arched, hind feet reaching under the belly) at hind touchdown and extends at the extended flight;
         the hips slide back along the body through hind stance and forward through the gathered flight.
Feet are IK footholds moving backward at exactly the body speed through stance (planted), the paws flat in stance and
curled in swing. Floor rules each frame: the tail clamp of anim_rat.py; the clips report the lowest point and the IK
reach of every planted foot. Saves work/rat_gait2.blend and the donor export work/gait2_donor.glb (all clips, 48 fps
scene), whose Walk2/Run2 add_clips.py appends to the installed export.
"""
import bpy, sys, os, math, json
import numpy as np
from mathutils import Vector, Matrix, Quaternion
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import posing as P

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work/rat_final.blend'))
rig = bpy.data.objects['Rat_Rig']; mesh = bpy.data.objects['Rat']; sc = bpy.context.scene
FPS = 48
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
for b in rig.pose.bones:
    b.rotation_mode = 'QUATERNION'
P.reset(rig)
REST = {b.name: (rig.matrix_world @ b.matrix).copy() for b in rig.pose.bones}
WRIST = {s: REST[f'FrontPaw_{s}'].translation.copy() for s in 'LR'}
ANKLE = {s: REST[f'HindPaw_{s}'].translation.copy() for s in 'LR'}
SIDE = {'L': 1.0, 'R': -1.0}
CHAIN = {('front', s): (rig.pose.bones[f'UpperArm_{s}'].length + rig.pose.bones[f'ForeArm_{s}'].length) for s in 'LR'}
CHAIN.update({('hind', s): (rig.pose.bones[f'Thigh_{s}'].length + rig.pose.bones[f'Shin_{s}'].length) for s in 'LR'})
UPPER = {'front': 'UpperArm_{}', 'hind': 'Thigh_{}'}


def ss(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def rot(name, axis, deg, pivot=None):
    if abs(deg) > 1e-6:
        P.rotate_world(rig, name, axis, deg, pivot)


def set_world_rot(name, q):
    b = rig.pose.bones[name]
    b.matrix = Matrix.LocRotScale(b.head.copy(), q, Vector((1, 1, 1))); bpy.context.view_layer.update()


REACH = []


def place_leg(kind, side, target, pitch=0.0, planted=False):
    """As anim_rat.place_leg: target = wrist/ankle world point; pitch tilts the paw (+ = toes down)."""
    shoulder = rig.matrix_world @ rig.pose.bones[UPPER[kind].format(side)].head
    if planted:
        REACH.append(((target - shoulder).length / CHAIN[(kind, side)], kind + side, round(target.y - shoulder.y, 3)))
    if kind == 'front':
        pole = target + Vector((SIDE[side] * 0.05, 0.25, 0.05))
        P.two_bone_ik(rig, f'UpperArm_{side}', f'ForeArm_{side}', target, pole)
        paw, rest = f'FrontPaw_{side}', REST[f'FrontPaw_{side}']
    else:
        pole = target + Vector((SIDE[side] * 0.04, -0.25, 0.10))
        P.two_bone_ik(rig, f'Thigh_{side}', f'Shin_{side}', target, pole)
        paw, rest = f'HindPaw_{side}', REST[f'HindPaw_{side}']
    set_world_rot(paw, Quaternion(X, math.radians(pitch)) @ rest.to_quaternion())


def tail_wave(amp_yaw, amp_pitch, phase, lift=0.0):
    for i in range(1, 7):
        k = i / 6.0
        rot(f'Tail{i}', Z, amp_yaw * k * math.sin(2 * math.pi * (phase - 0.09 * i)))
        rot(f'Tail{i}', X, (lift if i == 1 else lift * 0.15) + amp_pitch * math.sin(2 * math.pi * (phase - 0.09 * i)))


def body(hips_d=Vector(), hips_pitch=0.0, hips_roll=0.0, spine_pitch=0.0, spine_yaw=0.0, head_pitch=0.0,
         head_yaw=0.0):
    root = rig.pose.bones['Spine1']
    root.matrix = Matrix.Translation(hips_d) @ root.matrix; bpy.context.view_layer.update()
    rot('Spine1', Y, hips_roll); rot('Spine1', X, hips_pitch)
    for n, s in (('Spine2', 0.5), ('Spine3', 0.5)):
        rot(n, X, spine_pitch * s); rot(n, Z, spine_yaw * s)
    rot('Neck1', X, head_pitch * 0.4); rot('Head', X, head_pitch * 0.6)
    rot('Neck1', Z, head_yaw * 0.5); rot('Head', Z, head_yaw * 0.5)


_names = [g.name for g in mesh.vertex_groups]
_dom = np.array([_names[max(v.groups, key=lambda g: g.weight).group] if v.groups else '' for v in mesh.data.vertices])
CORE = np.array([n.startswith(('Spine', 'Neck', 'Head', 'Jaw')) for n in _dom])
_dg = bpy.context.evaluated_depsgraph_get()


def mesh_co():
    ev = mesh.evaluated_get(_dg); me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); ev.to_mesh_clear()
    return co.reshape(-1, 3)


def clamp_tail():
    for i in range(1, 7):
        b = rig.pose.bones[f'Tail{i}']
        t = rig.matrix_world @ b.tail
        if t.z < 0.012:
            h = rig.matrix_world @ b.head
            d = t - h; L = d.length
            flat = Vector((d.x, d.y, 0)).normalized()
            dz = 0.012 - h.z
            target = h + flat * math.sqrt(max(L * L - dz * dz, 1e-6)) + Vector((0, 0, dz)) if abs(dz) < L else h + flat * L
            P.aim_bone(rig, b.name, target)


def foot(kind, side, q, duty, travel, centre, lift, curl, swing_ease=True):
    """Foothold offset (dy, dz) and paw pitch for cycle position q (0 = touchdown). Stance moves the foot back by
    `travel` at constant speed; swing brings it forward with a lift and a curled paw."""
    if q < duty:
        return Vector((0, centre - travel / 2 + travel * (q / duty), 0)), 0.0, True
    u = (q - duty) / (1 - duty)
    w = ss(u) if swing_ease else u
    return Vector((0, centre + travel / 2 - travel * w, lift * math.sin(math.pi * u) ** 0.8)), curl * math.sin(math.pi * u), False


# ---------------------------------------------------------------- Walk2: quick long trot
W_T, W_STRIDE, W_DUTY = 15 / FPS, 0.365, 0.52
W_LEGS = (('front', 'L', 0.00), ('hind', 'R', 0.05), ('front', 'R', 0.50), ('hind', 'L', 0.55))
W_CENTRE = {'front': -0.016, 'hind': -0.022}     # stance centre relative to the rest foothold (front reaches forward)


def walk2(t):
    p = (t / W_T) % 1.0
    P.reset(rig)
    bob = math.cos(4 * math.pi * (p - 0.10))
    body(hips_d=Vector((0, 0.004 * math.sin(4 * math.pi * p), -0.010 - 0.006 * bob)),
         hips_pitch=1.0 * math.sin(4 * math.pi * p), hips_roll=2.0 * math.sin(2 * math.pi * p),
         spine_pitch=7.0 + 1.5 * math.sin(4 * math.pi * (p - 0.1)), spine_yaw=4 * math.sin(2 * math.pi * p),
         head_pitch=-6.0 - 2.0 * math.sin(4 * math.pi * (p - 0.1)), head_yaw=-3 * math.sin(2 * math.pi * p))
    tail_wave(12, 5, p, lift=8)
    s = W_STRIDE * W_DUTY
    for kind, side, ph in W_LEGS:
        off, pitch, planted = foot(kind, side, (p - ph) % 1.0, W_DUTY, s, W_CENTRE[kind],
                                   0.050 if kind == 'front' else 0.040, 35)
        place_leg(kind, side, (WRIST if kind == 'front' else ANKLE)[side] + off, pitch, planted)
    clamp_tail()


# ---------------------------------------------------------------- Run2: half-bound
R_T, R_STRIDE = 16 / FPS, 0.78
R_LEGS = (('hind', 'L', 0.00, 0.30), ('hind', 'R', 0.06, 0.30), ('front', 'L', 0.44, 0.25), ('front', 'R', 0.52, 0.25))
R_CENTRE = {'front': -0.022, 'hind': -0.030}
R_LIFT = {'front': 0.075, 'hind': 0.060}


def run2(t):
    p = (t / R_T) % 1.0
    P.reset(rig)
    flex = math.cos(2 * math.pi * (p - 0.92))          # +1 gathered (arched) at hind touchdown, -1 extended at 0.42
    rise = 0.5 + 0.5 * math.cos(4 * math.pi * (p - 0.40))  # high in the two flights
    body(hips_d=Vector((0, -0.020 * math.cos(2 * math.pi * p), -0.012 + 0.014 * rise)),
         hips_pitch=-6.0 * flex - 3.0 * math.sin(2 * math.pi * (p - 0.15)),
         hips_roll=1.5 * math.sin(2 * math.pi * p),
         spine_pitch=8.0 + 11.0 * flex, spine_yaw=2 * math.sin(2 * math.pi * p),
         head_pitch=-10.0 - 6.0 * flex + 3.0 * math.sin(2 * math.pi * (p - 0.15)), head_yaw=0.0)
    tail_wave(6, 9, p + 0.2, lift=4 - 8 * flex)
    for kind, side, ph, duty in R_LEGS:
        off, pitch, planted = foot(kind, side, (p - ph) % 1.0, duty, R_STRIDE * duty, R_CENTRE[kind], R_LIFT[kind], 55)
        place_leg(kind, side, (WRIST if kind == 'front' else ANKLE)[side] + off, pitch, planted)
    clamp_tail()


CLIPS = {'Walk2': (15, walk2), 'Run2': (16, run2)}
STRIDES = {'Walk2': W_STRIDE, 'Run2': R_STRIDE}


def key_action(name, n, fn):
    old = bpy.data.actions.get(name)
    if old:
        bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name); act.use_fake_user = True; act['loop'] = True
    if rig.animation_data is None:
        rig.animation_data_create()
    rig.animation_data.action = None
    poses, lows = [], []
    REACH.clear()
    for f in range(n + 1):
        fn((f % n) / FPS)
        co = mesh_co()
        lows.append((float(co[:, 2].min()), float(co[CORE, 2].min())))
        poses.append({b.name: (b.rotation_quaternion.copy(), b.location.copy()) for b in rig.pose.bones})
    rig.animation_data.action = act
    prev = {}
    for f, pose in enumerate(poses):
        for b in rig.pose.bones:
            q, loc = pose[b.name]
            if b.name in prev and prev[b.name].dot(q) < 0:
                q = -q
            prev[b.name] = q
            b.rotation_quaternion = q; b.location = loc
            b.keyframe_insert('rotation_quaternion', frame=f + 1)
            b.keyframe_insert('location', frame=f + 1)
    for layer in act.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for key in curve.keyframe_points:
                        key.interpolation = 'LINEAR'
    assert all(abs(abs(poses[0][k][0].dot(poses[-1][k][0])) - 1) < 1e-5 and
               (poses[0][k][1] - poses[-1][k][1]).length < 1e-5 for k in poses[0])
    rig.animation_data.action = None
    return {'frames': n, 'seconds': n / FPS, 'stride_m': STRIDES[name], 'speed': STRIDES[name] / (n / FPS),
            'lowest_m': min(l for l, _ in lows), 'core_lowest_m': min(c for _, c in lows),
            'planted_reach_max': max(r for r, _, _ in REACH),
            'reach_by_leg': {leg: [round(min(r for r, l, _ in REACH if l == leg), 3),
                                   round(max(r for r, l, _ in REACH if l == leg), 3),
                                   min(d for _, l, d in REACH if l == leg), max(d for _, l, d in REACH if l == leg)]
                             for leg in sorted({l for _, l, _ in REACH})}}


report = {}
for name, (n, fn) in CLIPS.items():
    report[name] = key_action(name, n, fn)
    print('CLIP', name, json.dumps(report[name]), flush=True)
json.dump(report, open(os.path.join(HERE, 'work/gait2_report.json'), 'w'), indent=2)
sc.render.fps = FPS
rig.animation_data.action = bpy.data.actions['Standing']; sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work/rat_gait2.blend'))
for obj in bpy.data.objects:
    obj.select_set(obj in (mesh, rig))
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'work/gait2_donor.glb'), use_selection=True, export_format='GLB',
    export_yup=True, export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
    export_frame_step=1, export_skins=True, export_all_influences=False, export_attributes=False, export_morph=False,
    export_image_format='AUTO', export_reset_pose_bones=True, export_anim_slide_to_zero=True)
print('SAVED rat_gait2.blend gait2_donor.glb')
