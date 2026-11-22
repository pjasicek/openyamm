"""Procedural clips of the Flying Feet (30 fps). Each clip is a function of time that sets, per foot, a parameter set:
the pivot offset, yaw/pitch/roll about the foot's own axes (pitch + = toes up, roll + = the outer side up), the toe
curl (+ = toes down) and each wing's raise (+ = tip up, a turn about the foot's long axis through the wing root) and
fold (+ = swept back about the vertical through the root). The native idle bobs the two feet in turn with flapping
wings; the attack swings the near (left) foot back and stamps its sole at the party; frame 3 of the attack drops the
feet in a burst of feathers.

  Standing 2.0 s loop  alternating bob (1 s), wings 2.5 Hz, slight sway
  Walking  2.0 s loop  leaned toes-down 10 deg, wings 3.5 Hz, faster bob
  Running  2.0 s loop  leaned 18 deg, wings 4.5 Hz
  Attack   1.0 s       left foot draws back and up, sole turned to the party, stamps forward: IMPACT at the stamp
  Hit      0.5 s       both feet jolt back, roll, wings flare
  Death    1.6 s       wings flare and stop, the feet tumble to the floor: the right one onto its outer side, the left
                       one onto its inner side; wings fitted to the floor
  Dead     1.0 s       Death's last pose
  Fidget   2.0 s       toe wiggle on the left foot, two heel taps on the right one
Flyer rule (CLAUDE_QUADRUPED_PLAYBOOK.md, Flyers): the lowest point over every living clip meets the floor (one LIFT
for all of them); Death eases it out, the corpse rests on the floor.
Reads work/rig.blend, writes work/anim.blend and work/anim_info.json (clip lengths, lowest points, impact, gates)."""
import bpy, os, sys, json, math
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'rig.blend'))
rig = bpy.data.objects['Feet_Rig']; mesh = bpy.data.objects['Feet']
L = json.load(open(os.path.join(HERE, 'work', 'rig_layout.json')))
FPS = 30
pb = rig.pose.bones
for b in pb:
    b.rotation_mode = 'QUATERNION'
REST = {b.name: b.bone.matrix_local.copy() for b in pb}
SIDES = ('R', 'L')
PIV = {s: Vector(L['sides'][s]['pivot']) for s in SIDES}
BALL = {s: Vector(L['sides'][s]['ball']) for s in SIDES}
YAW = {s: L['layout'][s][1] for s in SIDES}
AX = {s: Matrix.Rotation(math.radians(YAW[s]), 3, 'Z') @ Vector((1, 0, 0)) for s in SIDES}     # lateral (+X) axis
FW = {s: Matrix.Rotation(math.radians(YAW[s]), 3, 'Z') @ Vector((0, -1, 0)) for s in SIDES}    # toe direction
WINGS = ('WingIn', 'WingOut')
HINGE = {(w, s): REST[f'{w}_{s}'].translation.copy() for w in WINGS for s in SIDES}
WSIGN = {(w, s): (1 if (HINGE[(w, s)] - PIV[s]).dot(AX[s]) > 0 else -1) for w in WINGS for s in SIDES}
PHASE = {'R': 0.0, 'L': 0.5}                 # the feet bob in turn
LIFT = 0.0
# vertex sides and body/wing labels (for the floor rules and the contact gate)
gname = {g.index: g.name for g in mesh.vertex_groups}
vside = np.array([gname[max(v.groups, key=lambda g: g.weight).group][-1] for v in mesh.data.vertices])
vwing = np.array([gname[max(v.groups, key=lambda g: g.weight).group].startswith('Wing') for v in mesh.data.vertices])
tris = np.array([p.vertices[:] for p in mesh.data.polygons])
tside = vside[tris[:, 0]]


def ss(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def bump(t, a, b):
    return 0.0 if t <= a or t >= b else math.sin(math.pi * (t - a) / (b - a)) ** 2


def P(**kw):
    p = dict(off=Vector((0, 0, 0)), yaw=0.0, pitch=0.0, roll=0.0, toes=0.0,
             raise_in=0.0, raise_out=0.0, fold_in=0.0, fold_out=0.0)
    p.update(kw); return p


def pose(params):
    """params: {side: P(...)}; sets every pose bone (armature space = world, rig at identity)."""
    for s in SIDES:
        p = params[s]
        R = (Matrix.Rotation(math.radians(p['yaw']), 4, 'Z') @ Matrix.Rotation(math.radians(-p['pitch']), 4, AX[s])
             @ Matrix.Rotation(math.radians(p['roll'] * (1 if s == 'L' else -1)), 4, FW[s]))
        c = PIV[s]
        D = Matrix.Translation(c + p['off'] + Vector((0, 0, LIFT))) @ R @ Matrix.Translation(-c)   # world delta
        pb[f'Foot_{s}'].matrix = D @ REST[f'Foot_{s}']
        bpy.context.view_layer.update()        # children are set against the updated parent
        b = BALL[s]
        T = Matrix.Translation(b) @ Matrix.Rotation(math.radians(p['toes']), 4, AX[s]) @ Matrix.Translation(-b)
        pb[f'Toes_{s}'].matrix = D @ T @ REST[f'Toes_{s}']
        for w, key in (('WingIn', 'in'), ('WingOut', 'out')):
            h = HINGE[(w, s)]; sg = WSIGN[(w, s)]
            W = (Matrix.Translation(h) @ Matrix.Rotation(math.radians(sg * p['fold_' + key]), 4, 'Z')
                 @ Matrix.Rotation(math.radians(sg * p['raise_' + key]), 4, FW[s]) @ Matrix.Translation(-h))
            pb[f'{w}_{s}'].matrix = D @ W @ REST[f'{w}_{s}']
    bpy.context.view_layer.update()


def flap(t, f, amp, bias=-4.0, ph=0.0):
    return bias + amp * math.sin(2 * math.pi * (f * t + ph))


def flap_s(t, f, amp, s):
    """A side's wing beat with Standing's phase, so one-shot clips start and end on Standing frame 0."""
    return flap(t, f, amp, ph=0.15 * (s == 'L'))


def hover(t, Lc=2.0, lean=0.0, f=2.5, amp=30.0, bob=0.022, sway=1.0, nbob=2):
    out = {}
    for s in SIDES:
        ph = PHASE[s]
        z = bob * math.sin(2 * math.pi * (nbob * t / Lc + ph))
        y = 0.012 * sway * math.sin(2 * math.pi * (t / Lc + ph + 0.25))
        a = flap_s(t, f, amp, s)
        out[s] = P(off=Vector((0, y, z)), pitch=-lean + 3 * sway * math.sin(2 * math.pi * (nbob * t / Lc + ph + 0.2)),
                   yaw=3 * sway * math.sin(2 * math.pi * (t / Lc + ph)), roll=2 * sway * math.sin(2 * math.pi * (t / Lc + ph + 0.4)),
                   raise_in=a, raise_out=a)
    return out


def standing(t): return hover(t)
def walking(t): return hover(t, lean=10, f=3.5, amp=32, bob=0.028, sway=1.4)
def running(t): return hover(t, lean=18, f=4.5, amp=34, bob=0.03, sway=1.2)


IMPACT = 0.45


def attack(t):
    base = hover(0.0)
    env = ss(t / 0.14) * (1 - ss((t - 0.6) / 0.4))                 # in from / back to Standing frame 0
    # the kicking (left) foot: wind-up back and up with the sole turned forward, then the stamp
    wind = ss((t - 0.08) / 0.27)
    stamp = ss((t - 0.35) / (IMPACT - 0.35))
    back = 1 - ss((t - 0.55) / 0.4)
    y = (0.10 * wind - 0.32 * stamp) * back
    z = (0.17 * wind + 0.03 * stamp) * back
    pitch = (68 * wind + 20 * stamp) * back
    l = base['L']
    l['off'] = l['off'] * (1 - env) + Vector((0.0, y, z))
    l['pitch'] = l['pitch'] * (1 - env) + pitch
    l['toes'] = -18 * wind * back + 8 * bump(t, 0.4, 0.6)            # toes spread up on the wind-up
    a = flap_s(t, 4.0, 30 + 6 * env, 'L')
    l['raise_in'] = l['raise_out'] = a + 10 * env
    r = base['R']
    r['off'] = r['off'] + Vector((0.0, 0.04 * env, 0.03 * env))
    r['pitch'] += 6 * env
    r['raise_in'] = r['raise_out'] = flap_s(t, 4.0, 30, 'R')
    return base


def hit(t):
    base = hover(0.0)
    k = ss(t / 0.1) * (1 - ss((t - 0.12) / 0.38))
    for s, sg in (('R', 1), ('L', -1)):
        p = base[s]
        p['off'] = p['off'] + Vector((0.0, 0.08 * k, 0.04 * k))
        p['roll'] += 16 * k * sg; p['pitch'] += 14 * k
        a = flap_s(t, 4.0, 30 * (1 - k), s)
        p['raise_in'] = p['raise_out'] = a + 30 * k
    return base


CORPSE = {}                                   # solved final pose (set below)


def death(t):
    start = hover(0.0)
    fl = bump(t, 0.0, 0.5)                    # the flare: wings thrown up as the feathers burst
    k = ss((t - 0.2) / 1.05)                  # the fall and tumble
    out = {}
    for s in SIDES:
        a, b = start[s], CORPSE[s]
        p = P()
        for key in ('yaw', 'pitch', 'roll', 'toes', 'raise_in', 'raise_out', 'fold_in', 'fold_out'):
            p[key] = a[key] * (1 - k) + b[key] * k
        beat = flap_s(t, 4.0, 30 * (1 - ss(t / 0.7)), s)
        p['raise_in'] += (beat - a['raise_in']) * (1 - k) + 35 * fl * (1 - k)
        p['raise_out'] += (beat - a['raise_out']) * (1 - k) + 35 * fl * (1 - k)
        drop = k * k                           # accelerating fall
        o = a['off'] + Vector((0, 0, LIFT)) + Vector((0, 0.03 * fl, 0.04 * fl))
        p['off'] = o * (1 - drop) + b['off'] * drop - Vector((0, 0, LIFT))
        out[s] = p
    return out


def dead(t):
    return {s: dict(CORPSE[s], off=CORPSE[s]['off'] - Vector((0, 0, LIFT))) for s in SIDES}


def fidget(t):
    base = hover(t)
    l = base['L']
    l['toes'] = 22 * bump(t, 0.2, 0.75) - 12 * bump(t, 0.75, 1.1) + 22 * bump(t, 1.1, 1.6)
    r = base['R']
    tap = bump(t, 0.35, 0.75) + bump(t, 1.05, 1.45)
    r['pitch'] += 16 * tap; r['off'] = r['off'] + Vector((0, 0, -0.012 * tap))
    return base


def world_co():
    dg = bpy.context.evaluated_depsgraph_get(); ev = mesh.evaluated_get(dg); me = ev.to_mesh()
    a = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', a); ev.to_mesh_clear()
    return a.reshape(-1, 3)


def reset():
    for b in pb:
        b.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()


def contact(co):
    """Smallest gap between the two feet (BVH overlap = contact)."""
    tr = BVHTree.FromPolygons([tuple(v) for v in co], [tuple(t) for t in tris[tside == 'R']])
    tl = BVHTree.FromPolygons([tuple(v) for v in co], [tuple(t) for t in tris[tside == 'L']])
    return len(tr.overlap(tl))


HINGE_V = {s: np.array([np.linalg.norm(np.array(mesh.data.vertices[i].co) - np.array(HINGE[('WingIn', s)])) for i in
          range(len(mesh.data.vertices))]) for s in SIDES}
HINGE_V2 = {s: np.array([np.linalg.norm(np.array(mesh.data.vertices[i].co) - np.array(HINGE[('WingOut', s)])) for i in
           range(len(mesh.data.vertices))]) for s in SIDES}
vbody = ~vwing


def wing_inside(co):
    """Wing vertices (more than 3 cm from their root) inside their own foot's body: ray parity along +Z and +X."""
    n = 0
    for s in SIDES:
        body_t = tris[(tside == s) & vbody[tris[:, 0]] & vbody[tris[:, 1]] & vbody[tris[:, 2]]]
        bvh = BVHTree.FromPolygons([tuple(v) for v in co], [tuple(t) for t in body_t])
        far = (vside == s) & vwing & (np.minimum(HINGE_V[s], HINGE_V2[s]) > 0.03)
        for i in np.nonzero(far)[0][::3]:
            inside = True
            for d in (Vector((0, 0, 1)), Vector((1, 0, 0))):
                o = Vector(co[i]); k = 0
                while True:
                    loc, nrm, idx, dist = bvh.ray_cast(o, d, 2.0)
                    if loc is None: break
                    k += 1; o = loc + d * 1e-5
                inside &= k % 2 == 1
            n += inside
    return n


# --- corpse: solve each foot onto the floor, then fit its wings to the floor
CORPSE_SPEC = {'R': dict(yaw=28.0, pitch=-6.0, roll=-82.0, toes=6.0, off=Vector((-0.05, 0.06, 0.0))),
               'L': dict(yaw=-18.0, pitch=4.0, roll=78.0, toes=10.0, off=Vector((0.05, -0.09, 0.0)))}


def solve_corpse():
    global LIFT
    keep = LIFT; LIFT = 0.0
    cp = {s: P(**CORPSE_SPEC[s], raise_in=-30.0, raise_out=-30.0, fold_in=35.0, fold_out=35.0) for s in SIDES}
    for s in SIDES:                            # ground the body (Foot/Toes vertices) of each foot
        reset(); pose(cp); co = world_co()
        sel = (vside == s) & ~vwing
        cp[s]['off'] = cp[s]['off'] + Vector((0, 0, -float(co[sel, 2].min()) + 0.002))
    reset(); pose(cp)
    for s in SIDES:                            # each wing: the raise nearest its target with the wing on/above the floor
        hz = {w: pb[f'{w}_{s}'].head.z for w in WINGS}
        for w, key in (('WingIn', 'in'), ('WingOut', 'out')):
            gi = {g.name: g.index for g in mesh.vertex_groups}[f'{w}_{s}']
            sel = np.array([any(g.group == gi and g.weight > 0.5 for g in v.groups) for v in mesh.data.vertices])
            best = None
            upper = hz[w] >= max(hz.values())
            target = 80 if upper else -20          # the upper wing lies back along the ankle, the lower one droops
            for ang in sorted(range(-60, 121, 3), key=lambda x: abs(x - target)):
                cp[s]['raise_' + key] = float(ang); reset(); pose(cp)
                z = world_co()[sel, 2]
                if z.min() >= 0.001:
                    best = (ang, float(z.min())); break
            cp[s]['raise_' + key] = float(best[0]) if best else 90.0
            print('CORPSE wing', w, s, best, flush=True)
    reset(); pose(cp); co = world_co()
    print('CORPSE lowest', round(float(co[:, 2].min()) * 100, 2), 'cm', flush=True)
    LIFT = keep
    return cp


INFO = {}
LIVING = {'Standing': (60, standing, True), 'Walking': (60, walking, True), 'Running': (60, running, True),
          'Attack': (30, attack, False), 'Hit': (15, hit, False), 'Fidget': (60, fidget, False)}
low = 1e9; where = None
for name, (n, fn, loop) in LIVING.items():
    for f in range(n + 1):
        reset(); pose(fn(f / FPS)); z = float(world_co()[:, 2].min())
        if z < low: low, where = z, (name, f)
LIFT = -low
print('LOWEST before lift', round(low * 100, 2), 'cm at', where, flush=True)
print('LIFT', round(LIFT, 4), flush=True)
CORPSE.update(solve_corpse())


def key_action(name, n, fn, loop):
    old = bpy.data.actions.get(name)
    if old: bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name); act.use_fake_user = True
    if rig.animation_data is None: rig.animation_data_create()
    rig.animation_data.action = None
    poses, lows, contacts, track, inside = [], [], [], [], []
    for f in range(n + 1):
        reset(); pose(fn(f / FPS)); co = world_co()
        lows.append(float(co[:, 2].min())); contacts.append(contact(co)); inside.append(wing_inside(co))
        track.append(co[::7].copy())
        poses.append({b.name: (b.rotation_quaternion.copy(), b.location.copy(), b.scale.copy()) for b in pb})
    if loop: poses[-1] = poses[0]
    rig.animation_data.action = act
    if len(getattr(act, 'slots', [])): rig.animation_data.action_slot = act.slots[0]
    prev = {}
    for f, ps in enumerate(poses):
        for b in pb:
            q, loc, sc = ps[b.name]
            if b.name in prev and prev[b.name].dot(q) < 0: q = -q
            prev[b.name] = q
            b.rotation_quaternion = q; b.location = loc; b.scale = sc
            for path in ('rotation_quaternion', 'location', 'scale'):
                b.keyframe_insert(path, frame=f)
    act.use_frame_range = True; act.frame_start, act.frame_end = 0, n
    act['fps'] = FPS
    rig.animation_data.action = None
    tr = np.array(track)                                          # frames x samples x 3
    acc = np.linalg.norm(tr[2:] - 2 * tr[1:-1] + tr[:-2], axis=2).max(1) * FPS * FPS if n > 2 else np.zeros(1)
    seam = float(np.abs(tr[-1] - tr[0]).max()) if loop else None
    INFO[name] = {'seconds': round(n / FPS, 4), 'lowest_cm': [round(min(lows) * 100, 2), round(max(lows) * 100, 2)],
                  'last_lowest_cm': round(lows[-1] * 100, 2), 'contact_frames': int(sum(c > 0 for c in contacts)), 'wing_inside_max': int(max(inside)),
                  'max_accel_m_s2': round(float(acc.max()), 1), 'loop_seam_mm': None if seam is None else round(seam * 1000, 2)}
    print('CLIP', name, INFO[name], flush=True)


for name, (n, fn, loop) in LIVING.items():
    key_action(name, n, fn, loop)
key_action('Death', 48, death, False)
key_action('Dead', 30, dead, False)
# the attack's impact: the kicking foot's furthest-forward frame
reset()
ys = []
for f in range(31):
    reset(); pose(attack(f / FPS)); ys.append(pb['Foot_L'].matrix.translation.y)
INFO['Attack']['stamp_frame'] = int(np.argmin(ys)); INFO['Attack']['stamp_y'] = round(float(min(ys)), 3)
json.dump({'clips': INFO, 'impact': IMPACT, 'lift': LIFT}, open(os.path.join(HERE, 'work', 'anim_info.json'), 'w'), indent=1)
reset(); rig.animation_data.action = bpy.data.actions['Standing']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'anim.blend'))
print('SAVED anim.blend', 'stamp frame', INFO['Attack']['stamp_frame'])
