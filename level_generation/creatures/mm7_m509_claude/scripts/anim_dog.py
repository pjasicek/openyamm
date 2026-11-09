"""Procedural MM7 Dog clips (30 fps), from the MM7 rat's (mm7_m382_claude/scripts/anim_rat7.py) and the native m509
frames (one frame per 125 ms; the native has no attack, hit or fidget frames: attack = walk, hit = fidget = stand).
  Standing  2.0 s loop   breathing, head turns, tail sway
  Walking   26 frames    trot (diagonal pairs) at the native 0.875 s cycle; at the binding scale MM7's speed 140 moves
                         the dog ~1.0 m per cycle (STRIDE_WALK), a natural trot for its size
  Attack    1.0 s        crouch, lunging snap (impact IMPACT), recover (no native frames: the walk is shown)
  Hit       0.625 s      flinch back, head recoil, tail tucked
  Death     1.1 s        rears up with the forelegs off the ground (native m509da/db), twists and falls onto its side
                         (m509dc/dd, corpse m509xa); Dead holds it
  Fidget    1.6 s        sniffs: head turns and nods, tail sway (the binding may use Standing: the native has none)
Legs on IK footholds; floor rules as the rat. Args: -- <in blend> <out blend>"""
import bpy, sys, os, math, json
import numpy as np
from mathutils import Vector, Matrix, Quaternion
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import posing as P
src, out = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; MESH = bpy.data.objects['Body']; sc = bpy.context.scene
FPS = 30; X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
STRIDE_WALK, STRIDE_RUN, IMPACT, TAIL_ROLL = 1.0, 1.0, 0.5, 0.0
WALK_T = 26 / 30
P.reset(rig)
REST = {b.name: (rig.matrix_world @ b.matrix).copy() for b in rig.pose.bones}
SIDE = {'L': 1.0, 'R': -1.0}
# symmetric footholds (mean of both sides, mirrored)
WR = {s: REST[f'FrontPaw_{s}'].translation.copy() for s in 'LR'}
AN = {s: REST[f'HindPaw_{s}'].translation.copy() for s in 'LR'}
fy, fx = (WR['L'].y + WR['R'].y) / 2, (abs(WR['L'].x) + abs(WR['R'].x)) / 2
hy, hx = (AN['L'].y + AN['R'].y) / 2, (abs(AN['L'].x) + abs(AN['R'].x)) / 2
WRIST = {s: Vector((SIDE[s] * fx, fy, (WR['L'].z + WR['R'].z) / 2)) for s in 'LR'}
ANKLE = {s: Vector((SIDE[s] * hx, hy, (AN['L'].z + AN['R'].z) / 2)) for s in 'LR'}


def ss(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def rot(name, axis, deg, pivot=None):
    if abs(deg) > 1e-6:
        P.rotate_world(rig, name, axis, deg, pivot)


def set_world_rot(name, q):
    b = rig.pose.bones[name]
    b.matrix = Matrix.LocRotScale(b.head.copy(), q, Vector((1, 1, 1))); bpy.context.view_layer.update()


def place_leg(kind, side, target, pitch=0.0, free=None):
    if free is not None:                                      # FK: (upper deg, lower deg, splay deg)
        up, lo, splay = free
        u, l = (f'UpperArm_{side}', f'ForeArm_{side}') if kind == 'front' else (f'Thigh_{side}', f'Shin_{side}')
        rot(u, Y, splay * SIDE[side]); rot(u, X, up); rot(l, X, lo)
        return
    if kind == 'front':
        pole = target + Vector((SIDE[side] * 0.03, 0.3, 0.08))          # elbow back
        P.two_bone_ik(rig, f'UpperArm_{side}', f'ForeArm_{side}', target, pole)
        paw, rest = f'FrontPaw_{side}', REST[f'FrontPaw_{side}']
    else:
        pole = target + Vector((SIDE[side] * 0.03, -0.3, 0.18))         # knee forward
        P.two_bone_ik(rig, f'Thigh_{side}', f'Shin_{side}', target, pole)
        paw, rest = f'HindPaw_{side}', REST[f'HindPaw_{side}']
    set_world_rot(paw, Quaternion(X, math.radians(pitch)) @ rest.to_quaternion())


def body(hips_d=Vector(), hips_pitch=0.0, hips_roll=0.0, spine_pitch=0.0, spine_yaw=0.0, head_pitch=0.0, head_yaw=0.0,
         head_roll=0.0):
    root = rig.pose.bones['Spine1']
    root.matrix = Matrix.Translation(hips_d) @ root.matrix; bpy.context.view_layer.update()
    rot('Spine1', Y, hips_roll); rot('Spine1', X, hips_pitch)
    for n, s in (('Spine2', 0.5), ('Spine3', 0.5)):
        rot(n, X, spine_pitch * s); rot(n, Z, spine_yaw * s)
    rot('Neck1', X, head_pitch * 0.4); rot('Head', X, head_pitch * 0.6)
    rot('Neck1', Z, head_yaw * 0.5); rot('Head', Z, head_yaw * 0.5); rot('Head', Y, head_roll)


def tail(sway, phase, lift=0.0, strike=0.0):
    """straighten into the middle plane (TAIL_ROLL about the hips' forward axis), then sway, lift and strike:
    strike > 0 rolls the arch forward over the head (segment pitch toward the front)"""
    fwd = ((rig.matrix_world @ rig.pose.bones['Spine1'].matrix).to_3x3() @ (REST['Spine1'].to_3x3().inverted() @ Y))
    rot('Tail1', fwd.normalized(), TAIL_ROLL)
    side = (rig.matrix_world @ rig.pose.bones['Spine1'].matrix).to_3x3() @ (REST['Spine1'].to_3x3().inverted() @ X)
    for i in range(1, 7):
        k = i / 6
        b = rig.pose.bones[f'Tail{i}']
        up = (rig.matrix_world @ b.matrix).to_3x3() @ Vector((0, 0, 1))
        rot(f'Tail{i}', up.normalized(), sway * (0.3 + 0.7 * k) * math.sin(2 * math.pi * (phase - 0.1 * i)))
        # strike: the arch swings forward from its base while the distal segments open (a lash); per-segment curl
        # compounded into a ball, and a base swing alone drove the stinger into the back
        rot(f'Tail{i}', side.normalized(), -lift * (1 - k) * 0.8 + strike * {1: 0.75, 2: 0.3, 3: -0.2, 4: -0.3, 5: -0.2, 6: 0.0}.get(i, 0.0))


# ---------------------------------------------------------------- floor rules
_vn = [g.name for g in MESH.vertex_groups]
_dom = np.array([_vn[max(v.groups, key=lambda g: g.weight).group] if v.groups else '' for v in MESH.data.vertices])
CORE = np.array([n.startswith(('Spine', 'Neck', 'Head', 'Thigh', 'UpperArm')) for n in _dom])
LIMBS = {(k, sd): np.array([n in ((f'UpperArm_{sd}', f'ForeArm_{sd}', f'FrontPaw_{sd}') if k == 'front' else
                                  (f'Thigh_{sd}', f'Shin_{sd}', f'HindPaw_{sd}')) for n in _dom])
         for k in ('front', 'hind') for sd in 'LR'}
FLOOR = 0.004


def mesh_co():
    dg = bpy.context.evaluated_depsgraph_get(); ev = MESH.evaluated_get(dg); me = ev.to_mesh()
    c = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', c); ev.to_mesh_clear()
    return c.reshape(-1, 3)


def clamp_tail():
    for i in range(2, 7):
        b = rig.pose.bones[f'Tail{i}']
        t = rig.matrix_world @ b.tail
        if t.z < 0.03:
            h = rig.matrix_world @ b.head; d = t - h; L = d.length
            flat = Vector((d.x, d.y, 0)).normalized(); dz = 0.03 - h.z
            P.aim_bone(rig, b.name, h + flat * math.sqrt(max(L * L - dz * dz, 1e-6)) + Vector((0, 0, dz)) if abs(dz) < L else h + flat * L)


def clamp_limbs():
    for (kind, sd), mask in LIMBS.items():
        upper = f'UpperArm_{sd}' if kind == 'front' else f'Thigh_{sd}'
        for _ in range(15):
            co = mesh_co(); low = co[mask, 2].min()
            if low > co[CORE, 2].min() - 0.02:
                break
            b = rig.pose.bones[upper]
            d = (b.tail - b.head).normalized(); axis = d.cross(Z)
            if axis.length < 1e-3:
                axis = X.copy()
            axis.normalize()
            P.rotate_world(rig, upper, axis, -6.0)
            if mesh_co()[mask, 2].min() < low:
                P.rotate_world(rig, upper, axis, 12.0)


def floor_fit(lift_core=True, ground=False):
    co = mesh_co()
    low = co[CORE, 2].min() if not ground else co[:, 2].min()
    if (lift_core and low < -FLOOR) or ground:
        root = rig.pose.bones['Spine1']
        root.matrix = Matrix.Translation(Vector((0, 0, -low))) @ root.matrix; bpy.context.view_layer.update()
    clamp_tail()


# ---------------------------------------------------------------- clips
def gait(t, T, stride, duty, lift_f, lift_h, flex, bound=False):
    p = (t / T) % 1.0
    P.reset(rig)
    bob = 0.008
    body(hips_d=Vector((0, 0, -bob * math.cos(4 * math.pi * p) - bob)), spine_pitch=flex * math.sin(4 * math.pi * p),
         spine_yaw=3 * math.sin(2 * math.pi * p), head_pitch=-2 * math.cos(4 * math.pi * p),
         head_yaw=-2 * math.sin(2 * math.pi * p))
    tail(12, p, lift=2)
    s = stride * duty
    order = (('hind', 'L', 0.0), ('front', 'L', 0.25), ('hind', 'R', 0.5), ('front', 'R', 0.75)) if not bound else \
        (('front', 'L', 0.0), ('hind', 'R', 0.0), ('front', 'R', 0.5), ('hind', 'L', 0.5))
    for kind, side, ph in order:
        q = (p + ph) % 1.0
        if q < duty:
            dy = s / 2 - s * (q / duty); dz = 0.0; pitch = 0.0             # planted: slides back (body moves -Y)
        else:
            u = (q - duty) / (1 - duty)
            dy = -s / 2 + s * ss(u); dz = (lift_f if kind == 'front' else lift_h) * math.sin(math.pi * u)
            pitch = (10 if kind == 'front' else -8) * math.sin(math.pi * u)
            # (toes down sank 7 cm into the floor)
        base = WRIST[side] if kind == 'front' else ANKLE[side]
        place_leg(kind, side, base + Vector((0, -dy, dz)), pitch)


def standing(t):
    P.reset(rig)
    b = math.sin(2 * math.pi * t / 2.0)
    body(hips_d=Vector((0, 0, 0.006 * b)), spine_pitch=-1.2 * b, head_pitch=2 * b, head_yaw=6 * math.sin(math.pi * t / 2.0))
    tail(5, t / 2.0)
    for kind in ('front', 'hind'):
        for side in 'LR':
            place_leg(kind, side, (WRIST if kind == 'front' else ANKLE)[side])


def keyed(keys, t):
    for (t0, a), (t1, b) in zip(keys[:-1], keys[1:]):
        if t <= t1:
            u = ss((t - t0) / max(t1 - t0, 1e-6)); out = {}
            for k in set(a) | set(b):
                va, vb = a.get(k, 0.0), b.get(k, 0.0)
                if isinstance(va, Vector) or isinstance(vb, Vector):
                    va = va if isinstance(va, Vector) else Vector(); vb = vb if isinstance(vb, Vector) else Vector()
                    out[k] = va.lerp(vb, u)
                else:
                    out[k] = va + (vb - va) * u
            return out
    return keys[-1][1]


def generic(pm, legs_free=False):
    P.reset(rig)
    body(hips_d=pm.get('hips', Vector()), hips_pitch=pm.get('hips_pitch', 0.0), hips_roll=pm.get('roll', 0.0),
         spine_pitch=pm.get('spine', 0.0), spine_yaw=pm.get('yaw', 0.0), head_pitch=pm.get('head', 0.0),
         head_yaw=pm.get('head_yaw', 0.0), head_roll=pm.get('head_roll', 0.0))
    tail(pm.get('tail_sway', 0.0), pm.get('tail_phase', 0.0), lift=pm.get('tail_lift', 0.0),
         strike=pm.get('strike', 0.0))
    for side in 'LR':
        if legs_free:
            place_leg('front', side, None, free=(pm.get('fu', 0.0), pm.get('fl', 0.0), pm.get('fs', 0.0)))
            place_leg('hind', side, None, free=(pm.get('hu', 0.0), pm.get('hl', 0.0), pm.get('hs', 0.0)))
        else:
            place_leg('front', side, WRIST[side] + pm.get('front_' + side, Vector()), pm.get('paw', 0.0))
            place_leg('hind', side, ANKLE[side] + pm.get('hind_' + side, Vector()))


V = Vector
ATTACK = [   # crouch, lunging snap at the target, recover
    (0.00, {}),
    (0.30, {'hips': V((0, 0.05, -0.04)), 'hips_pitch': 5, 'spine': 5, 'head': 12, 'tail_lift': 10,
            'front_L': V((0.0, 0.03, 0.0)), 'front_R': V((0.0, 0.03, 0.0))}),
    (IMPACT, {'hips': V((0, -0.12, -0.01)), 'hips_pitch': 4, 'spine': -6, 'head': -10, 'tail_lift': -4,
              'front_L': V((0.02, -0.12, 0.0)), 'front_R': V((-0.02, -0.12, 0.0))}),
    (0.62, {'hips': V((0, -0.10, 0.0)), 'hips_pitch': 2, 'spine': -4, 'head': 4, 'head_yaw': -8,
            'front_L': V((0.02, -0.10, 0.0)), 'front_R': V((-0.02, -0.10, 0.0))}),
    (1.00, {}),
]
HIT = [
    (0.000, {}),
    (0.12, {'hips': V((0, 0.04, -0.01)), 'hips_pitch': -6, 'spine': 6, 'head': -16, 'head_yaw': 12, 'tail_lift': 30,
            'front_L': V((0.03, 0.03, 0.0)), 'front_R': V((-0.03, 0.03, 0.0))}),
    (0.35, {'hips': V((0, 0.03, -0.008)), 'hips_pitch': -4, 'spine': 4, 'head': -8, 'head_yaw': 6, 'tail_lift': 18}),
    (0.625, {}),
]
DEATH = [
    (0.00, {}),
    (0.25, {'hips': V((0, 0.03, 0.01)), 'hips_pitch': -40, 'spine': -15, 'head': 25, 'fu': -70, 'fl': 40, 'fs': 25,
            'hu': -10, 'hl': 10, 'tail_lift': 20}),
    (0.60, {'hips': V((0, 0.04, -0.05)), 'hips_pitch': -12, 'roll': 55, 'spine': -6, 'head': 6, 'fu': -30, 'fl': 50,
            'fs': 35, 'hu': -25, 'hl': 30, 'hs': 20, 'tail_sway': 15, 'tail_phase': 0.3}),
    (0.95, {'hips': V((0, 0.04, -0.15)), 'hips_pitch': -3, 'roll': 90, 'spine': 6, 'head': 12, 'head_roll': -10,
            'fu': 15, 'fl': 45, 'fs': 20, 'hu': 20, 'hl': 40, 'hs': 15, 'tail_sway': 10, 'tail_phase': 0.2}),
    (1.10, {'hips': V((0, 0.04, -0.15)), 'hips_pitch': -3, 'roll': 92, 'spine': 8, 'head': 14, 'head_roll': -12,
            'fu': 18, 'fl': 50, 'fs': 20, 'hu': 22, 'hl': 45, 'hs': 15, 'tail_sway': 10, 'tail_phase': 0.2}),
]


def fidget(t):
    P.reset(rig)
    u = t / 1.6; e = math.sin(math.pi * u)
    sniff = 4 * math.sin(2 * math.pi * 7 * u) * e
    body(hips_d=Vector((0, 0.01 * e, 0)), hips_pitch=-4 * e, head_pitch=14 * e + sniff,
         head_yaw=22 * math.sin(2 * math.pi * u), head_roll=4 * math.sin(2 * math.pi * 2 * u) * e)
    tail(16 * e, u * 2)
    for kind in ('front', 'hind'):
        for side in 'LR':
            place_leg(kind, side, (WRIST if kind == 'front' else ANKLE)[side])


CLIPS = {
    'Standing': (2.0, True, standing),
    'Walking': (WALK_T, True, lambda t: gait(t, WALK_T, STRIDE_WALK, 0.55, 0.06, 0.05, 2, bound=True)),
    'Attack': (1.0, False, lambda t: generic(keyed(ATTACK, t))),
    'Hit': (0.625, False, lambda t: generic(keyed(HIT, t))),
    'Death': (1.1, False, lambda t: generic(keyed(DEATH, t), legs_free=True)),
    'Fidget': (1.6, False, fidget),
}


def key_action(name, seconds, loop, fn):
    old = bpy.data.actions.get(name)
    if old:
        bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name); act.use_fake_user = True
    rig.animation_data_create(); rig.animation_data.action = None
    n = int(round(seconds * FPS)); poses = []
    for f in range(n + 1):
        t = (f % n) / FPS if loop else f / FPS
        fn(t)
        lying = name == 'Dead' or (name == 'Death' and t > 0.7)    # Dead's own clock starts at 0: always lying
        floor_fit(lift_core=name in ('Attack', 'Hit', 'Death', 'Dead'), ground=lying)
        if name == 'Dead' or (name == 'Death' and t > 0.5):
            clamp_limbs()
            floor_fit(lift_core=True, ground=lying)                  # the clamp moved limbs after grounding
        poses.append({b.name: (b.rotation_quaternion.copy(), b.location.copy()) for b in rig.pose.bones})
    rig.animation_data.action = act
    if len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    prev = {}
    for f, pose in enumerate(poses):
        for b in rig.pose.bones:
            q, loc = pose[b.name]
            if b.name in prev and prev[b.name].dot(q) < 0:
                q = -q
            prev[b.name] = q; b.rotation_quaternion = q; b.location = loc
            b.keyframe_insert('rotation_quaternion', frame=f); b.keyframe_insert('location', frame=f)
    act.use_frame_range = True; act.frame_start, act.frame_end = 0, n
    rig.animation_data.action = None
    return act


for b in rig.pose.bones:
    b.rotation_mode = 'QUATERNION'
for name, (sec, loop, fn) in CLIPS.items():
    key_action(name, sec, loop, fn)
    print('CLIP', name, sec, flush=True)
key_action('Dead', 1.0, False, lambda t: generic(keyed(DEATH, 1.1), legs_free=True))
json.dump({'fps': FPS, 'walk_stride_m': STRIDE_WALK, 'run_stride_m': STRIDE_RUN, 'attack_impact_s': IMPACT,
           'durations': {k: v[0] for k, v in CLIPS.items()}},
          open(os.path.join(HERE, 'work', 'clips.json'), 'w'), indent=1)
P.reset(rig)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
print('SAVED', out)
