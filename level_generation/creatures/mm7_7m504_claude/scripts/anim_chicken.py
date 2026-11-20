"""Procedural MM7 Chicken clips (30 fps), the cat's framework (../../mm7_7m500_claude/scripts/anim_cat.py) on a two-legged bird rig (rig_chicken.py)
and the native 7m504 frames (one frame per 125 ms: stand, a 7-frame walk, a 3-frame death; no attack, hit or fidget
frames: attack = walk, hit = fidget = stand).
  Standing  2.0 s loop   breathing, quick head turns (a chicken looks round in jerks), tail sway
  Walking   13 frames    brisk two-legged walk, two cycles per native walk loop (0.875 s): MM7's speed 140 is
                         ~0.98 m/s at the binding scale, too far for one 45 cm hen step pair; the head holds still in
                         the stance and thrusts forward (head bob)
  Attack    1.0 s        crouch, peck forward-down (impact IMPACT), wings half lifted, recover
  Hit       0.5 s        flinch back, wings flap out, head recoil
  Death     0.9 s        wings flap open, it tips onto its side with the legs kicked out (native 7m504da-dc, corpse
                         xa); Dead holds it
  Fidget    1.6 s        pecks at the ground twice
Legs: knee shifted with the foot, Shin/Tarsus on two-bone IK (hock back), Foot flat (toes curled in the swing).
Floor rules as the rat/cat. Args: -- <in blend> <out blend>"""
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
STRIDE_WALK, STRIDE_RUN, IMPACT = 0.40, 0.40, 0.5
WALK_T = 13 / 30
P.reset(rig)
REST = {b.name: (rig.matrix_world @ b.matrix).copy() for b in rig.pose.bones}
SIDE = {'L': 1.0, 'R': -1.0}
# symmetric footholds (mean of both sides, mirrored: the rest stance is staggered by 4 cm)
AN = {s: REST[f'Foot_{s}'].translation.copy() for s in 'LR'}
hy, hx = (AN['L'].y + AN['R'].y) / 2, (abs(AN['L'].x) + abs(AN['R'].x)) / 2
ANKLE = {s: Vector((SIDE[s] * hx, hy, (AN['L'].z + AN['R'].z) / 2)) for s in 'LR'}
KNEE = {s: REST[f'Shin_{s}'].translation.copy() for s in 'LR'}
KNEE = {s: Vector((SIDE[s] * (abs(KNEE['L'].x) + abs(KNEE['R'].x)) / 2, (KNEE['L'].y + KNEE['R'].y) / 2,
                   (KNEE['L'].z + KNEE['R'].z) / 2)) for s in 'LR'}


def ss(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def rot(name, axis, deg, pivot=None):
    if abs(deg) > 1e-6:
        P.rotate_world(rig, name, axis, deg, pivot)


def set_world_rot(name, q):
    b = rig.pose.bones[name]
    b.matrix = Matrix.LocRotScale(b.head.copy(), q, Vector((1, 1, 1))); bpy.context.view_layer.update()


def place_leg(side, target, pitch=0.0, free=None):
    if free is not None:                                      # FK: (thigh deg, shin deg, tarsus deg, splay deg)
        th, sh, ta, splay = free
        rot(f'Thigh_{side}', Y, splay * SIDE[side]); rot(f'Thigh_{side}', X, th)
        rot(f'Shin_{side}', X, sh); rot(f'Tarsus_{side}', X, ta)
        return
    body_d = rig.matrix_world @ rig.pose.bones[f'Thigh_{side}'].head - REST[f'Thigh_{side}'].translation
    knee = KNEE[side] + body_d + Vector((0, 0.5 * (target.y - ANKLE[side].y), 0))   # the knee follows the foot halfway
    P.aim_bone(rig, f'Thigh_{side}', knee)
    pole = target + Vector((0, 0.3, 0.05))                    # the hock bends backward
    P.two_bone_ik(rig, f'Shin_{side}', f'Tarsus_{side}', target, pole)
    set_world_rot(f'Foot_{side}', Quaternion(X, math.radians(pitch)) @ REST[f'Foot_{side}'].to_quaternion())


def body(hips_d=Vector(), hips_pitch=0.0, hips_roll=0.0, hips_yaw=0.0, neck_pitch=0.0, head_pitch=0.0, head_yaw=0.0,
         head_roll=0.0, head_thrust=0.0):
    root = rig.pose.bones['Body']
    root.matrix = Matrix.Translation(hips_d) @ root.matrix; bpy.context.view_layer.update()
    # pitch angles: positive raises the front (a +X world rotation tips forward-pointing bones down)
    rot('Body', Z, hips_yaw); rot('Body', Y, hips_roll); rot('Body', X, -hips_pitch)
    # head thrust: the lower neck leans forward and the upper neck back up (the head moves forward, stays level)
    rot('Neck1', X, head_thrust - neck_pitch * 0.5); rot('Neck2', X, -1.6 * head_thrust - neck_pitch * 0.5)
    rot('Head', X, 0.6 * head_thrust - head_pitch)
    rot('Neck2', Z, head_yaw * 0.4); rot('Head', Z, head_yaw * 0.6); rot('Head', Y, head_roll)


def wings(lift, fold=0.0):
    """lift: the folded wing's trailing edge swings out and up about the wing's root (degrees); fold: Wing2 extra"""
    for sd in 'LR':
        b = rig.pose.bones[f'Wing1_{sd}']
        ax = ((rig.matrix_world @ b.tail) - (rig.matrix_world @ b.head)).normalized()
        rot(f'Wing1_{sd}', ax, -SIDE[sd] * lift)
        b2 = rig.pose.bones[f'Wing2_{sd}']
        ax2 = ((rig.matrix_world @ b2.tail) - (rig.matrix_world @ b2.head)).normalized()
        rot(f'Wing2_{sd}', ax2, -SIDE[sd] * (0.5 * lift + fold))


def tail(sway, phase, lift=0.0):
    rot('Tail1', Z, sway * math.sin(2 * math.pi * phase)); rot('Tail1', X, -lift)


# ---------------------------------------------------------------- floor rules
_vn = [g.name for g in MESH.vertex_groups]
_dom = np.array([_vn[max(v.groups, key=lambda g: g.weight).group] if v.groups else '' for v in MESH.data.vertices])
CORE = np.array([n.startswith(('Body', 'Chest', 'Neck', 'Head', 'Thigh', 'Wing', 'Tail')) for n in _dom])
LIMBS = {sd: np.array([n in (f'Shin_{sd}', f'Tarsus_{sd}', f'Foot_{sd}') for n in _dom]) for sd in 'LR'}
FLOOR = 0.004


def mesh_co():
    dg = bpy.context.evaluated_depsgraph_get(); ev = MESH.evaluated_get(dg); me = ev.to_mesh()
    c = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', c); ev.to_mesh_clear()
    return c.reshape(-1, 3)


def clamp_limbs():
    for sd, mask in LIMBS.items():
        for _ in range(15):
            co = mesh_co(); low = co[mask, 2].min()
            if low > co[CORE, 2].min() - 0.01:
                break
            b = rig.pose.bones[f'Shin_{sd}']
            d = (b.tail - b.head).normalized(); axis = d.cross(Z)
            if axis.length < 1e-3:
                axis = X.copy()
            axis.normalize()
            P.rotate_world(rig, f'Shin_{sd}', axis, -6.0)
            if mesh_co()[mask, 2].min() < low:
                P.rotate_world(rig, f'Shin_{sd}', axis, 12.0)


def floor_fit(lift_core=True, ground=False):
    co = mesh_co()
    low = co[CORE, 2].min() if not ground else co[:, 2].min()
    if (lift_core and low < -FLOOR) or ground:
        root = rig.pose.bones['Body']
        root.matrix = Matrix.Translation(Vector((0, 0, -low))) @ root.matrix; bpy.context.view_layer.update()


# ---------------------------------------------------------------- clips
def gait(t, T, stride, duty, lift):
    p = (t / T) % 1.0
    P.reset(rig)
    bob = 0.006; s = stride * duty
    # the head holds still while a foot is planted and thrusts forward at each step (twice per cycle)
    q2 = (2 * p) % 1.0; thrust = 12 * (ss(q2 / 0.35) if q2 < 0.35 else 1 - ss((q2 - 0.35) / 0.65))
    body(hips_d=Vector((0, 0, -bob * math.cos(4 * math.pi * p) - bob)), hips_roll=4 * math.sin(2 * math.pi * p),
         hips_yaw=3 * math.sin(2 * math.pi * p), hips_pitch=-3, head_thrust=thrust - 6)
    wings(2 * math.sin(4 * math.pi * p))
    tail(4, p)
    for side, ph in (('L', 0.0), ('R', 0.5)):
        q = (p + ph) % 1.0
        if q < duty:
            dy = s / 2 - s * (q / duty); dz = 0.0; pitch = 0.0             # planted: slides back (body moves -Y)
        else:
            u = (q - duty) / (1 - duty)
            dy = -s / 2 + s * ss(u); dz = lift * math.sin(math.pi * u); pitch = -25 * math.sin(math.pi * u)
        place_leg(side, ANKLE[side] + Vector((0, -dy, dz)), pitch)


def standing(t):
    P.reset(rig)
    b = math.sin(2 * math.pi * t / 2.0)
    # quick head turns: held, then a snap to the next angle
    u = (t / 2.0) % 1.0
    yaw = -18 + 36 * ss((u - 0.20) / 0.06) - 36 * ss((u - 0.70) / 0.06) * 1.0
    body(hips_d=Vector((0, 0, 0.003 * b)), neck_pitch=-1.5 * b, head_pitch=2 * b, head_yaw=yaw, head_roll=4 * b)
    wings(1.5 * b)
    tail(3, t / 2.0)
    for side in 'LR':
        place_leg(side, ANKLE[side])


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
         neck_pitch=pm.get('neck', 0.0), head_pitch=pm.get('head', 0.0), head_yaw=pm.get('head_yaw', 0.0),
         head_roll=pm.get('head_roll', 0.0), head_thrust=pm.get('thrust', 0.0))
    wings(pm.get('wing', 0.0), pm.get('wing2', 0.0))
    tail(pm.get('tail_sway', 0.0), pm.get('tail_phase', 0.0), lift=pm.get('tail_lift', 0.0))
    for side in 'LR':
        if legs_free:
            k = '' if side == 'L' else 'r'
            place_leg(side, None, free=(pm.get(k + 'th', 0.0), pm.get(k + 'sh', 0.0), pm.get(k + 'ta', 0.0),
                                        pm.get(k + 'sp', 0.0)))
        else:
            place_leg(side, ANKLE[side] + pm.get('foot_' + side, Vector()), pm.get('toe_' + side, 0.0))


V = Vector
ATTACK = [   # crouch, peck forward-down, recover
    (0.00, {}),
    (0.30, {'hips': V((0, 0.015, -0.012)), 'hips_pitch': 6, 'neck': 10, 'head': 6, 'thrust': -8, 'wing': 10,
            'tail_lift': 6}),
    (IMPACT, {'hips': V((0, -0.02, -0.02)), 'hips_pitch': -22, 'neck': -30, 'head': -25, 'thrust': 14, 'wing': 18,
              'tail_lift': 12}),
    (0.62, {'hips': V((0, -0.015, -0.015)), 'hips_pitch': -16, 'neck': -20, 'head': -12, 'thrust': 8, 'wing': 12,
            'tail_lift': 8}),
    (1.00, {}),
]
HIT = [
    (0.000, {}),
    (0.10, {'hips': V((0, 0.025, 0.01)), 'hips_pitch': 10, 'neck': 14, 'head': 12, 'head_yaw': 15, 'thrust': -10,
            'wing': 35, 'wing2': 10, 'tail_lift': 15}),
    (0.28, {'hips': V((0, 0.015, 0.0)), 'hips_pitch': 5, 'neck': 6, 'head': 4, 'head_yaw': 8, 'wing': 10,
            'tail_lift': 6}),
    (0.50, {}),
]
DEATH = [
    (0.00, {}),
    (0.18, {'hips': V((0, 0.01, 0.02)), 'hips_pitch': 12, 'neck': 18, 'head': 14, 'wing': 45, 'wing2': 15,
            'tail_lift': 15, 'th': -10, 'rth': -10}),
    (0.40, {'hips': V((0, 0.02, -0.03)), 'hips_pitch': 6, 'roll': 45, 'neck': 20, 'head': 10, 'wing': 40,
            'wing2': 10, 'th': -35, 'sh': 20, 'ta': 10, 'sp': 15, 'rth': -15, 'rsh': 30, 'rta': 20, 'tail_lift': 8}),
    (0.75, {'hips': V((0, 0.02, -0.07)), 'hips_pitch': 2, 'roll': 88, 'neck': 30, 'head': 15, 'head_roll': -10,
            'wing': 12, 'th': -55, 'sh': 25, 'ta': 15, 'sp': 20, 'rth': -45, 'rsh': 20, 'rta': 15, 'rsp': 10}),
    (0.90, {'hips': V((0, 0.02, -0.07)), 'hips_pitch': 2, 'roll': 90, 'neck': 32, 'head': 16, 'head_roll': -12,
            'wing': 8, 'th': -55, 'sh': 25, 'ta': 15, 'sp': 20, 'rth': -45, 'rsh': 20, 'rta': 15, 'rsp': 10}),
]


def fidget(t):
    """pecks at the ground twice"""
    u = t / 1.6
    e = ss(u / 0.2) * (1 - ss((u - 0.8) / 0.2))
    peck = max(0.0, math.sin(2 * math.pi * 2 * (u - 0.2) / 0.6)) if 0.2 < u < 0.8 else 0.0
    return generic({'hips': V((0, -0.01 * e, -0.01 * e)), 'hips_pitch': -14 * e - 6 * peck, 'neck': -30 * e - 25 * peck,
                    'head': -20 * e - 10 * peck, 'thrust': 6 * e + 6 * peck, 'tail_lift': 10 * e, 'wing': 4 * e})


CLIPS = {
    'Standing': (2.0, True, standing),
    'Walking': (WALK_T, True, lambda t: gait(t, WALK_T, STRIDE_WALK, 0.55, 0.045)),
    'Attack': (1.0, False, lambda t: generic(keyed(ATTACK, t))),
    'Hit': (0.5, False, lambda t: generic(keyed(HIT, t))),
    'Death': (0.9, False, lambda t: generic(keyed(DEATH, t), legs_free=True)),
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
        lying = name == 'Dead' or (name == 'Death' and t > 0.6)    # Dead's own clock starts at 0: always lying
        floor_fit(lift_core=name in ('Attack', 'Hit', 'Death', 'Dead'), ground=lying)
        if name == 'Dead' or (name == 'Death' and t > 0.4):
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
key_action('Dead', 1.0, False, lambda t: generic(keyed(DEATH, 0.9), legs_free=True))
json.dump({'fps': FPS, 'walk_stride_m': STRIDE_WALK, 'run_stride_m': STRIDE_RUN, 'attack_impact_s': IMPACT,
           'durations': {k: v[0] for k, v in CLIPS.items()}},
          open(os.path.join(HERE, 'work', 'clips.json'), 'w'), indent=1)
P.reset(rig)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
print('SAVED', out)
