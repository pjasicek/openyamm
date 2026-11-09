"""Procedural hydra clips (30 fps), after mm7_m278_claude/scripts/anim_manticore.py (quadruped body, IK legs, tail) and
mm6_hyd_claude/scripts/anim_hyd.py (neck chains, lashes, head separation), choreographed from the native m266 frames
(125 ms each):
  Standing  2.0 s loop   breathing, the five necks sway on their own phases, heads look about, tail drifts
  Walking   1.0 s loop   lateral-sequence walk (native 8 x 125 ms), necks bob forward in turn, tail swings
  Running   0.6 s loop   faster trot, necks stretched forward
  Attack    1.0 s        the necks rear back and up (native aa-ad), then the middle three lash forward and down
                         (ae-af; a bend travelling base to head), the outer two follow less; recover; impact IMPACT
  Hit       0.75 s       necks recoil back, body flinches, heads shake (native n, 6 frames)
  Death     1.25 s       rears, sags onto its right side, necks splay and fall to the ground (native f, d, x)
  Dead      1.0 s        last Death pose held
  Fidget    1.0 s        heads look round on their own beats, outer heads outward (native f with the 375 ms hold)
Legs: two-bone IK on symmetric footholds (the rest stance is skewed by the three-quarter master). Necks: each bone is
turned in world space about the chest's lateral axis (pitch, + = forward/down) and world Z (yaw), root to tip, with
the bend weighted toward the head; Head<k> takes extra pitch/yaw. Heads are kept apart: the necks start spread by
BASE_YAW, and whenever a head's triangles overlap another head or upper neck on the posed mesh (BVH, every frame), the
two necks yaw apart by 3 degrees more (iterated; a rule on head-centre distances missed the fins and horns).
Floor rules: body lifted if the core sinks; tail and neck bones aimed back above the floor (their radius); lying
legs swung up in Death.
Args: -- <in blend> <out blend>"""
import bpy, sys, os, math, json
import numpy as np
from mathutils import Vector, Matrix, Quaternion
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import posing as P
src, out = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; MESH = bpy.data.objects['Body']; sc = bpy.context.scene
FPS = 30; X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
STRIDE_WALK, STRIDE_RUN, IMPACT = 1.3, 1.9, 0.62
HEAD_FLOOR = 0.14      # m: Head<k> bone end (snout) stays this high (the grafted skulls are wider than the bone)
RJ = json.load(open(os.path.join(HERE, 'work', 'rig.json')))['chains']
NECKS = [c['names'] for c in RJ[1:6]]
NECK_R = [c['radius'] for c in RJ[1:6]]
TAIL = [n for n in (b.name for b in rig.pose.bones) if n.startswith('Tail')]
TAIL.sort(key=lambda n: int(n[4:]))
TAIL_R = next(c['radius'] for c in RJ if c['names'][0] == 'Tail1')
# constant outward spread of the necks (deg, + = toward +x): head 1's wide fins overlapped head 2 at rest
BASE_YAW = [-16.0, -5.0, 0.0, 5.0, 8.0]
HEAD_COUNTER = 0.85     # share of the spread yaw the head turns back
P.reset(rig)
REST = {b.name: (rig.matrix_world @ b.matrix).copy() for b in rig.pose.bones}
SIDE = {'L': 1.0, 'R': -1.0}
WR = {s: REST[f'FrontPaw_{s}'].translation.copy() for s in 'LR'}
AN = {s: REST[f'HindPaw_{s}'].translation.copy() for s in 'LR'}


def sym(pts):
    cx = (pts['L'].x + pts['R'].x) / 2; hx = (pts['L'].x - pts['R'].x) / 2
    y = (pts['L'].y + pts['R'].y) / 2; z = (pts['L'].z + pts['R'].z) / 2
    return {s: Vector((cx + SIDE[s] * hx, y, z)) for s in 'LR'}


WRIST, ANKLE = sym(WR), sym(AN)
PHASE = [0.0, 1.9, 0.7, 3.3, 5.1]


def ss(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def rot(name, axis, deg, pivot=None):
    if abs(deg) > 1e-6:
        P.rotate_world(rig, name, axis, deg, pivot)


def world_axis(bone, local):
    b = rig.pose.bones[bone]
    return ((rig.matrix_world @ b.matrix).to_3x3() @ (REST[bone].to_3x3().inverted() @ local)).normalized()


def set_world_rot(name, q):
    b = rig.pose.bones[name]
    b.matrix = Matrix.LocRotScale(b.head.copy(), q, Vector((1, 1, 1))); bpy.context.view_layer.update()


LAST = {}


def place_leg(kind, side, target, pitch=0.0, free=None):
    if free is not None:
        LAST.pop((kind, side), None)
        up, lo, splay = free
        u, l = (f'UpperArm_{side}', f'ForeArm_{side}') if kind == 'front' else (f'Thigh_{side}', f'Shin_{side}')
        rot(u, Y, splay * SIDE[side]); rot(u, X, up); rot(l, X, lo)
        return
    LAST[(kind, side)] = (target.copy(), pitch)
    if kind == 'front':
        pole = target + Vector((SIDE[side] * 0.05, 0.6, 0.25))
        P.two_bone_ik(rig, f'UpperArm_{side}', f'ForeArm_{side}', target, pole)
        paw, rest = f'FrontPaw_{side}', REST[f'FrontPaw_{side}']
    else:
        pole = target + Vector((SIDE[side] * 0.04, -0.6, 0.2))
        P.two_bone_ik(rig, f'Thigh_{side}', f'Shin_{side}', target, pole)
        paw, rest = f'HindPaw_{side}', REST[f'HindPaw_{side}']
    set_world_rot(paw, Quaternion(X, math.radians(pitch)) @ rest.to_quaternion())


def body(hips=Vector(), pitch=0.0, roll=0.0, yaw=0.0, spine=0.0, spine_yaw=0.0):
    root = rig.pose.bones['Spine1']
    root.matrix = Matrix.Translation(hips) @ root.matrix; bpy.context.view_layer.update()
    rot('Spine1', Z, yaw); rot('Spine1', Y, roll); rot('Spine1', X, pitch)
    for n in ('Spine2', 'Spine3'):
        rot(n, world_axis(n, X), spine * 0.5); rot(n, Z, spine_yaw * 0.5)


def tail(sway, phase, curl=0.0, lift=0.0):
    n = len(TAIL)
    for i, b in enumerate(TAIL):
        k = (i + 1) / n
        rot(b, Z, sway * (0.3 + 0.7 * k) * math.sin(2 * math.pi * (phase - 0.12 * i)) + curl * k)
        if lift:
            rot(b, world_axis(b, X), -lift * (1 - k))


def neck(k, pitch, yaw, hp=0.0, hy=0.0, power=1.3):
    """k 0..4. pitch/yaw: per bone lists (degrees) or totals spread toward the head."""
    names = NECKS[k]; n = len(names) - 1
    if not isinstance(pitch, (list, tuple, np.ndarray)):
        # power > 0: bend toward the head; power < 0: from the base (a whole neck falling)
        w = np.array([((i + 1) / n) ** power if power > 0 else ((n - i) / n) ** -power for i in range(n)]); w /= w.sum()
        pitch = list(pitch * w); yaw = list(yaw * w) if not isinstance(yaw, (list, tuple, np.ndarray)) else yaw
    elif not isinstance(yaw, (list, tuple, np.ndarray)):
        w = np.array([((i + 1) / n) ** power for i in range(n)]); w /= w.sum(); yaw = list(yaw * w)
    lat = world_axis('Spine3', X)
    for i in range(n):
        rot(names[i], lat, pitch[i]); rot(names[i], Z, yaw[i])
    rot(names[-1], lat, hp); rot(names[-1], Z, hy)


def whip(k, fn, t, lag):
    """per-bone pitch (deg) for a bend travelling from the neck base to the head: bone i follows fn(t - lag i/n)"""
    n = len(NECKS[k]) - 1
    w = np.array([((i + 1) / n) ** 1.2 for i in range(n)]); w /= w.sum()
    return [fn(t - lag * i / n) * w[i] for i in range(n)]




def necks(args):
    """args: per neck (pitch, yaw, hp, hy[, power]); then heads are pushed apart: while a head's triangles overlap
    another head or another neck on the posed mesh (BVH), the two necks yaw apart a little more (iterated)."""
    snap = {b.name: b.matrix_basis.copy() for b in rig.pose.bones}
    extra = np.zeros(5)
    for it in range(32):
        for b in rig.pose.bones:
            if b.name.startswith(('Neck', 'Head')):
                b.matrix_basis = snap[b.name]
        bpy.context.view_layer.update()
        for k, (p, y, hp, hy, *pw) in enumerate(args):
            ex = extra[k] + BASE_YAW[k]
            yy = (np.array(y) + ex / len(y)) if isinstance(y, (list, tuple, np.ndarray)) else y + ex
            neck(k, p, yy, hp, hy - HEAD_COUNTER * ex, *pw)      # spread necks, heads still facing ahead
        pairs = head_contacts()
        if not pairs:
            break
        for a_, b_ in pairs:          # a_ right of b_ (lower index = toward -x): the fan opens on both sides of the pair
            extra[:a_ + 1] -= 2.5; extra[b_:] += 2.5


def head_contacts():
    """(a, b) neck index pairs (a < b) whose head and the other's head or neck overlap on the posed mesh"""
    co = [tuple(c) for c in mesh_co()]
    trees = {k: BVHTree.FromPolygons(co, HEAD_F[k]) for k in range(5)}
    necks_ = {k: BVHTree.FromPolygons(co, NECK_F[k]) for k in range(5)}
    out = set()
    for k in range(5):
        for j in range(5):
            if j == k:
                continue
            if trees[k].overlap(trees[j]) or trees[k].overlap(necks_[j]):
                out.add((min(k, j), max(k, j)))
    return sorted(out)


# ---------------------------------------------------------------- floor rules
_vn = [g.name for g in MESH.vertex_groups]
_dom = np.array([_vn[max(v.groups, key=lambda g: g.weight).group] if v.groups else '' for v in MESH.data.vertices])
CORE = np.array([n.startswith(('Spine', 'Thigh', 'UpperArm')) for n in _dom])
LIMBS = {(k, sd): np.array([n in ((f'UpperArm_{sd}', f'ForeArm_{sd}', f'FrontPaw_{sd}') if k == 'front' else
                                  (f'Thigh_{sd}', f'Shin_{sd}', f'HindPaw_{sd}')) for n in _dom])
         for k in ('front', 'hind') for sd in 'LR'}


_part = np.zeros(len(MESH.data.polygons), np.int32); MESH.data.attributes['part'].data.foreach_get('value', _part)
_own = np.zeros(len(MESH.data.vertices), np.int32); MESH.data.attributes['chain_owner'].data.foreach_get('value', _own)
_polys = [list(p.vertices) for p in MESH.data.polygons]
_fown = np.array([np.bincount(_own[p], minlength=6).argmax() for p in _polys])
_zrest = np.array([MESH.data.vertices[p[0]].co.z for p in _polys])
HEAD_F = {k: [_polys[i] for i in range(len(_polys)) if _part[i] == k + 1] for k in range(5)}
NECK_F = {k: [_polys[i] for i in range(len(_polys)) if _part[i] == 0 and _fown[i] == k + 1 and _zrest[i] > 1.05]
          for k in range(5)}                                      # the upper necks (their shared bases always touch)


def mesh_co():
    dg = bpy.context.evaluated_depsgraph_get(); ev = MESH.evaluated_get(dg); me = ev.to_mesh()
    c = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', c); ev.to_mesh_clear()
    return c.reshape(-1, 3)


def clamp_chain(names, floor):
    for i, n in enumerate(names):
        b = rig.pose.bones[n]
        h = rig.matrix_world @ b.head; t = rig.matrix_world @ b.tail
        f = floor[i + 1] if isinstance(floor, (list, tuple)) else floor
        if t.z < f:
            d = t - h; L = d.length; flat = Vector((d.x, d.y, 0))
            flat = flat.normalized() if flat.length > 1e-6 else Vector((0, -1, 0))
            dz = f - h.z
            tgt = h + flat * math.sqrt(max(L * L - dz * dz, 1e-6)) + Vector((0, 0, dz)) if abs(dz) < L else h + flat * L
            P.aim_bone(rig, n, tgt)


def floor_fit(lift_core=True, ground=False):
    co = mesh_co()
    low = co[CORE, 2].min()                     # ground: the belly on the floor (necks and heads clamped below)
    if (lift_core and low < -0.004) or ground:
        root = rig.pose.bones['Spine1']
        root.matrix = Matrix.Translation(Vector((0, 0, -low))) @ root.matrix; bpy.context.view_layer.update()
    clamp_chain(TAIL, [max(0.05, 0.95 * r) for r in TAIL_R])
    co = mesh_co()
    for (kind, sd), mask in LIMBS.items():                    # a leg on IK that sinks is re-solved higher
        if (kind, sd) in LAST:
            low = co[mask, 2].min()
            if low < -0.003:
                tgt, pitch = LAST[(kind, sd)]
                place_leg(kind, sd, tgt + Vector((0, 0, -low)), pitch)
    for k in range(5):
        clamp_chain(NECKS[k], [max(0.06, 0.8 * r) for r in NECK_R[k][:-1]] + [HEAD_FLOOR])


def clamp_limbs():
    for (kind, sd), mask in LIMBS.items():
        upper = f'UpperArm_{sd}' if kind == 'front' else f'Thigh_{sd}'
        for _ in range(30):
            co = mesh_co(); low = co[mask, 2].min()
            if low > max(co[CORE, 2].min() - 0.02, -0.01):
                break
            b = rig.pose.bones[upper]
            d = (b.tail - b.head).normalized(); axis = d.cross(Z)
            axis = axis.normalized() if axis.length > 1e-3 else X.copy()
            P.rotate_world(rig, upper, axis, -6.0)
            if mesh_co()[mask, 2].min() < low:
                P.rotate_world(rig, upper, axis, 12.0)


def legs_planted(front=None, hind=None, paw=0.0):
    for side in 'LR':
        place_leg('front', side, WRIST[side] + (front or {}).get(side, Vector()), paw)
        place_leg('hind', side, ANKLE[side] + (hind or {}).get(side, Vector()))


# ---------------------------------------------------------------- clips
def standing(t):
    P.reset(rig)
    b = math.sin(2 * math.pi * t / 2.0)
    body(hips=Vector((0, 0, 0.008 * b)), spine=-1.0 * b)
    tail(5, t / 2.0)
    legs_planted()
    args = []
    for k in range(5):
        ph = 2 * math.pi * t / 2.0 + PHASE[k]
        args.append((4 * math.sin(ph), 5 * math.sin(ph + k), -5 * math.sin(ph + 1.0), 10 * math.sin(ph + 2.0 * k)))
    necks(args)


def gait(t, T, stride, duty, lift_f, lift_h, run=False):
    p = (t / T) % 1.0
    P.reset(rig)
    bob = 0.02 if run else 0.012
    body(hips=Vector((0, 0, -bob * math.cos(4 * math.pi * p) - bob)), spine=2 * math.sin(4 * math.pi * p),
         spine_yaw=3 * math.sin(2 * math.pi * p))
    tail(10 if not run else 7, p, lift=3)
    s = stride * duty
    order = (('hind', 'L', 0.0), ('front', 'L', 0.25), ('hind', 'R', 0.5), ('front', 'R', 0.75)) if not run else \
        (('front', 'L', 0.0), ('hind', 'R', 0.0), ('front', 'R', 0.5), ('hind', 'L', 0.5))
    for kind, side, ph in order:
        q = (p + ph) % 1.0
        if q < duty:
            dy = s / 2 - s * (q / duty); dz = 0.0; pitch = 0.0
        else:
            u = (q - duty) / (1 - duty)
            dy = -s / 2 + s * ss(u); dz = (lift_f if kind == 'front' else lift_h) * math.sin(math.pi * u)
            pitch = 12 * math.sin(math.pi * u)
        base = WRIST[side] if kind == 'front' else ANKLE[side]
        place_leg(kind, side, base + Vector((0, -dy, dz)), pitch)
    args = []
    for k in range(5):
        ph = 2 * math.pi * p * (2 if run else 1) + PHASE[k]
        fwd = 14 if run else 6
        args.append((fwd + 6 * math.sin(ph), 6 * math.sin(ph * 0.5 + k), -fwd * 0.6 - 4 * math.sin(ph + 1.2),
                     5 * math.sin(ph - 0.8)))
    necks(args)


def lash(t0, back=-55.0, fwd=85.0):
    """neck pitch total (deg) of one strike starting at t0: wind-up back over WIND s (native rearing ab-ad), a short
    hold, a ~0.1 s lash forward and down, recovery by 1.0 s"""
    def at(u):
        u -= t0
        return back * ss(u / 0.40) + (fwd - back) * ss((u - 0.48) / 0.12) - fwd * ss((u - 0.72) / 0.26)
    return at


def attack(t):
    P.reset(rig)
    rear = ss(t / 0.4) * (1 - ss((t - 0.5) / 0.15)); drive = ss((t - 0.5) / 0.12) * (1 - ss((t - 0.72) / 0.26))
    body(hips=Vector((0, 0.06 * rear - 0.08 * drive, 0.03 * rear)), pitch=-6 * rear + 5 * drive)
    tail(8, t, lift=6 * rear)
    legs_planted()
    args = []
    for k in range(5):
        if k in (1, 2, 3):
            t0 = 0.03 * abs(k - 2)
            f = lash(t0, back={1: -26.0, 2: -55.0, 3: -38.0}[k])            # the side strikers rear less (heads crowded)
            u = t - t0
            hp = -25 * ss(u / 0.4) + 50 * ss((u - 0.52) / 0.1) - 25 * ss((u - 0.72) / 0.26)
            spread = 15.0 * (k - 2) * ss(t / 0.4) * (1 - ss((t - 0.5) / 0.2))      # the rearing necks part
            args.append((whip(k, f, t, 0.08), spread, hp, -0.8 * spread))
        else:
            f = lash(0.05, back=-30, fwd=25)
            args.append((whip(k, f, t, 0.08), 32.0 * ss(t / 0.4) * (1 if k == 4 else -1) * (1 - ss((t - 0.55) / 0.3)),
                         -10 * ss(t / 0.4) + 20 * ss((t - 0.55) / 0.12) - 10 * ss((t - 0.75) / 0.25), 0.0))
    necks(args)


def hit(t):
    P.reset(rig)
    r = ss(t / 0.1) * (1 - ss((t - 0.25) / 0.45))
    body(hips=Vector((0, 0.06 * r, -0.03 * r)), pitch=-4 * r, spine=5 * r)
    tail(14 * r, t * 2, lift=10 * r)
    legs_planted()
    args = []
    for k in range(5):
        args.append((-28 * r, 6 * r * (k - 2), -15 * r, 18 * math.sin(2 * math.pi * t / 0.25 + k) * r))
    necks(args)


def death(t):
    """native f/d frames: the necks rear and splay, then the hydra collapses onto its belly, legs sprawled, a slight
    roll to its right, and the necks fall forward in a fan onto the ground (corpse xa: necks stretched out in front)"""
    P.reset(rig)
    a = ss(t / 0.3) * (1 - ss((t - 0.3) / 0.3)); b = ss((t - 0.25) / 0.55); c = ss((t - 0.55) / 0.55)
    body(hips=Vector((0, 0.04 * a, 0.03 * a - 0.24 * b)), pitch=-8 * a + 3 * b, roll=-12 * b, spine=-5 * a)
    tail(6 * (1 - b), t, curl=-12 * b, lift=6 * a)
    for side in 'LR':
        if b < 0.02:
            place_leg('front', side, WRIST[side]); place_leg('hind', side, ANKLE[side])
        else:
            place_leg('front', side, None, free=(-25 * b, 30 * b, 35 * b))
            place_leg('hind', side, None, free=(15 * b, 20 * b, 30 * b))
    args = []
    for k in range(5):
        f = ss((t - 0.3 - 0.04 * k) / 0.6)
        fan = (k - 2) * 16
        args.append((-10 * a + 135 * f, fan * f + 6 * (k - 2) * a, -15 * a - 25 * f, 0.0, 1.3 - 2.3 * f))
    necks(args)


def fidget(t):
    P.reset(rig)
    env = ss(t / 0.15) * (1 - ss((t - 0.75) / 0.25))
    body(spine=-2 * env)
    tail(10 * env, t)
    legs_planted()
    args = []
    for k in range(5):
        ph = 2 * math.pi * t + PHASE[k]
        out_ = (-1 if k == 0 else 1 if k == 4 else 0)
        args.append((env * (6 * math.sin(ph + 0.5) - 3), env * (8 * math.sin(ph) + 18 * out_),
                     -8 * env * math.sin(ph + 2.0), env * (22 * math.sin(ph * 1.5 + k) + 25 * out_)))
    necks(args)


CLIPS = {
    'Standing': (2.0, True, standing),
    'Walking': (1.0, True, lambda t: gait(t, 1.0, STRIDE_WALK, 0.62, 0.10, 0.08)),
    'Running': (0.6, True, lambda t: gait(t, 0.6, STRIDE_RUN, 0.45, 0.15, 0.12, run=True)),
    'Attack': (1.0, False, attack),
    'Hit': (0.75, False, hit),
    'Death': (1.25, False, death),
    'Fidget': (1.0, False, fidget),
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
        floor_fit(lift_core=name in ('Attack', 'Hit', 'Death', 'Dead'), ground=name == 'Dead' or (name == 'Death' and t > 0.8))
        if name in ('Death', 'Dead'):
            clamp_limbs()
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
only = os.environ.get('CLIPS')
for name, (sec, loop, fn) in CLIPS.items():
    if only and name not in only.split(','):
        continue
    key_action(name, sec, loop, fn)
    print('CLIP', name, sec, flush=True)
if not only or 'Dead' in only:
    key_action('Dead', 1.0, False, lambda t: death(1.25))
json.dump({'fps': FPS, 'walk_stride_m': STRIDE_WALK, 'run_stride_m': STRIDE_RUN, 'attack_impact_s': IMPACT,
           'durations': {k: v[0] for k, v in CLIPS.items()}},
          open(os.path.join(HERE, 'work', 'clips.json'), 'w'), indent=1)
P.reset(rig)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
print('SAVED', out)
