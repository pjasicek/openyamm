"""Cloak bones and weights for the thief (work/rig_v1.blend in place, after build_rig_thf.py).

Chains: 17 chains of 4 bones (Cloak_<c>_<k>) around the back and sides at the angles in CHAIN_DEG (0 = back,
+90 = his left), each hanging from a ring at z 1.14 (just below the shoulders) to the hem; the root bone is parented
to the chest bone 'Spine'. Chain points lie mid-thickness in the cloak shell (rays from the body axis outward: mean
of the first and last cloak hit), so the bones follow the bell flare.
Weights of every cloak vertex (Meshy's are discarded):
 - hood: Head from z 1.33 (full at 1.43), neck at the hood base, chest ('Spine') below;
 - z < Z_TOP within the chain sector: two chains by angle (linear) and the chain bones by height (linear blend across
   each joint over +-30 % of the segment); outside the sector above z 0.95 (mantle front over the chest): Spine / Spine01; the lower front corners of
   the cloak (curling past the edge chains) follow the edge chain;
 - attach to the arm: cloak within ATTACH_D of the upper-arm segment (mantle over the shoulder, the side panel down
   to the elbow; fading out below z 0.92-1.02) blends toward Arm (clavicle near the shoulder), up to ATTACH_MAX,
   smoothed over the cloak's edges (only the mantle over the shoulder: fading in from z 1.05 to 1.15), so a raised
   arm lifts the mantle while the cloak below hangs.
All cloak weights are then diffused over the cloak's own edges (SMOOTH_ITERS), the hood's face opening excepted.
scene['thf_cloak'] stores the chains (bone names, rest points) for cloak_sim.py."""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'rig_v1.blend'))
scene = bpy.context.scene
arm = bpy.data.objects['Thief_Rig']; mesh = bpy.data.objects['Thief']; me = mesh.data
PARTS = json.loads(scene['thf_parts'])
CHAIN_DEG = [0, 13, -13, 27, -27, 40, -40, 54, -54, 67, -67, 81, -81, 95, -95, 108, -108]
Z_LEVELS = [1.14, 0.88, 0.62, 0.36]
Z_TOP = Z_LEVELS[0]
AXIS = Vector((0.015, 0.02, 0))
ATTACH_D, ATTACH_MAX = (0.05, 0.12), 1.0   # (0.08, 0.20) from z 0.92 stretched the cloak 9x into a sheet under a raised arm

part = np.zeros(len(me.polygons), dtype=np.int32); me.attributes['part'].data.foreach_get('value', part)
cl = PARTS.index('Cloak')
cface = [p for p in me.polygons if part[p.index] == cl]
cverts = sorted({v for p in cface for v in p.vertices})
co = {i: mesh.matrix_world @ me.vertices[i].co for i in range(len(me.vertices))}
tree = BVHTree.FromPolygons([co[i] for i in range(len(me.vertices))], [tuple(p.vertices) for p in cface])


def surface_point(deg, z):
    a = math.radians(deg); d = Vector((math.sin(a), math.cos(a), 0))
    o = Vector((AXIS.x, AXIS.y, z)); hits = []
    t = 0.0
    while t < 0.6:
        loc, n, i, dist = tree.ray_cast(o + d * (t + 1e-4), d, 0.6 - t)
        if loc is None:
            break
        hits.append(loc); t += dist + 1e-4
    if not hits:
        return None
    return (hits[0] + hits[-1]) / 2


chains = []
for deg in CHAIN_DEG:
    pts = []
    for z in Z_LEVELS:                                 # front edges recede at the elbow: step back toward the cloak
        q = None
        for back in range(0, 30, 3):
            q = surface_point(deg - math.copysign(back, deg), z)
            if q is not None:
                break
        pts.append(q)
    # hem: lowest cloak vertex near this angle
    near = [i for i in cverts if abs(((math.degrees(math.atan2(co[i].x - AXIS.x, co[i].y - AXIS.y)) - deg) + 180)
                                      % 360 - 180) < 8]
    low = min(co[i].z for i in near)
    hem = None
    for dz in (0.03, 0.05, 0.07, 0.10, 0.13):           # ragged hem: step up until the ray meets cloth
        hem = surface_point(deg, low + dz)
        if hem is not None:
            break
    pts.append(hem)
    if any(p is None for p in pts):
        print('MISSING', deg, pts, 'low', low); raise RuntimeError('missing chain point')
    chains.append({'deg': deg, 'pts': [tuple(p) for p in pts]})
    print('CHAIN', deg, [tuple(round(x, 3) for x in p) for p in pts])

bpy.context.view_layer.objects.active = arm
for o in bpy.data.objects:
    o.select_set(o == arm)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.data.edit_bones
AWI = arm.matrix_world.inverted()
for c in chains:
    tag = ('p' if c['deg'] >= 0 else 'm') + str(abs(c['deg']))
    c['bones'] = []
    parent = eb['Spine']
    for k in range(4):
        b = eb.new(f'Cloak_{tag}_{k}')
        b.head = AWI @ Vector(c['pts'][k]); b.tail = AWI @ Vector(c['pts'][k + 1])
        b.roll = 0.0
        b.parent = parent; b.use_connect = k > 0; b.use_deform = True
        parent = b; c['bones'].append(b.name)
bpy.ops.object.mode_set(mode='OBJECT')
for c in chains:
    for n in c['bones']:
        if n not in mesh.vertex_groups:
            mesh.vertex_groups.new(name=n)


def smooth(x, a, b):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def chain_weights(c, z):
    """Bone weights along one chain at height z (piecewise by the chain points' heights)."""
    zs = [p[2] for p in c['pts']]
    w = {}
    for k in range(4):
        z0, z1 = zs[k], zs[k + 1]
        if z1 <= z <= z0 or (k == 3 and z < z1) or (k == 0 and z > z0):
            t = 0.0 if z0 == z1 else (z0 - z) / (z0 - z1)
            w[c['bones'][k]] = 1.0
            if t < 0.3 and k > 0:
                b = 0.5 * (1 - t / 0.3); w[c['bones'][k - 1]] = b; w[c['bones'][k]] = 1 - b
            elif t > 0.7 and k < 3:
                b = 0.5 * (t - 0.7) / 0.3; w[c['bones'][k + 1]] = b; w[c['bones'][k]] = 1 - b
            return w
    return {c['bones'][3]: 1.0}


# arm attach: the upper-arm segment only (shoulder -> elbow); the forearm and hand hang in front of the cloak.
# The weights come from the segment itself (clavicle near the shoulder, Arm along it), not from a copied sleeve
# vertex (single vertices that copied forearm/hand weights spiked to the raised hand, review/stress_v1_sheet.png).
segs = {}
for s_ in ('Left', 'Right'):
    segs[s_] = (arm.matrix_world @ arm.data.bones[s_ + 'Arm'].head_local,
                arm.matrix_world @ arm.data.bones[s_ + 'ForeArm'].head_local)


def arm_attach(p):
    best = (1e9, None, 0.0)
    for s_, (a, b) in segs.items():
        ab = b - a; t = max(0.0, min(1.0, (p - a).dot(ab) / ab.length_squared))
        d = (p - (a + ab * t)).length
        if d < best[0]:
            best = (d, s_, t)
    d, s_, t = best
    w = {s_ + 'Arm': 1.0}
    if t < 0.3:
        c = 0.4 * (1 - t / 0.3); w = {s_ + 'Arm': 1 - c, s_ + 'Shoulder': c}
    return d, w


edge = max(abs(d) for d in CHAIN_DEG)
att = {}
for i in cverts:
    d, _ = arm_attach(co[i])
    att[i] = ATTACH_MAX * (1 - smooth(d, *ATTACH_D)) * smooth(co[i].z, 1.05, 1.15)
nbr = {i: set() for i in cverts}
for e in me.edges:
    a_, b_ = e.vertices
    if a_ in nbr and b_ in nbr:
        nbr[a_].add(b_); nbr[b_].add(a_)
for _ in range(12):                                      # neighbours may not disagree (no single-vertex spikes)
    att = {i: 0.5 * att[i] + 0.5 * (sum(att[j] for j in nbr[i]) / len(nbr[i]) if nbr[i] else att[i]) for i in cverts}
stats = {'hood': 0, 'chain': 0, 'front': 0, 'attached': 0}
WV = {}
SMOOTH_ITERS = 4
for i in cverts:
    p = co[i]
    a = math.degrees(math.atan2(p.x - AXIS.x, p.y - AXIS.y))
    w = {}
    if p.z >= Z_TOP or (abs(a) > edge + 12 and p.z > 0.95):   # mantle front; lower front corners follow the edge chain
        h = smooth(p.z, 1.33, 1.43) if p.z > 1.28 else 0.0
        n = smooth(p.z, 1.24, 1.33) * (1 - h)
        rest = 1 - h - n
        w = {'Head': h, 'neck': n}
        if p.z >= Z_TOP - 0.06:
            w['Spine'] = rest
        else:                                            # mantle front below the ring: lower chest, blended into the
            w['Spine'] = rest * 0.5; w['Spine01'] = rest * 0.5     # edge chain near the cloak's front edge (it tore
            e_ = math.copysign(edge, a)                  # 13 cm from the chain when the cloak spread in the death)
            tch = smooth(abs(a), edge + 12, edge + 40) * smooth(p.z, 0.95, 1.08)
            if tch < 1:
                ec = next(c for c in chains if c['deg'] == e_)
                w = {k_: x * tch for k_, x in w.items()}
                for k_, x in chain_weights(ec, p.z).items():
                    w[k_] = w.get(k_, 0) + x * (1 - tch)
        stats['hood' if h > 0 else 'front'] += 1
    else:
        ac = max(-edge, min(edge, a))
        order = sorted(CHAIN_DEG)
        for lo, hi in zip(order, order[1:]):
            if lo <= ac <= hi:
                t = (ac - lo) / (hi - lo); break
        cl_lo = next(c for c in chains if c['deg'] == lo); cl_hi = next(c for c in chains if c['deg'] == hi)
        for c, f in ((cl_lo, 1 - t), (cl_hi, t)):
            for n, x in chain_weights(c, p.z).items():
                w[n] = w.get(n, 0) + x * f
        # blend into the chest just below the ring (the bones turn about the ring, so this only softens)
        b = smooth(p.z, Z_TOP - 0.08, Z_TOP)
        if b > 0:
            w = {n: x * (1 - b) for n, x in w.items()}; w['Spine'] = w.get('Spine', 0) + b
        stats['chain'] += 1
    if att[i] > 0.01:
        _, aw = arm_attach(p)
        w = {n: x * (1 - att[i]) for n, x in w.items()}
        for n, x in aw.items():
            w[n] = w.get(n, 0) + x * att[i]
        stats['attached'] += 1
    WV[i] = w
# weights diffused over the cloak's own edges (neighbouring vertices may not disagree: per-vertex rules tore the hem by
# 11-16 cm in the walk and run where neighbours fell into different chain sectors); the face opening of the hood
# (Head >= 0.99) stays rigid on the head
names = sorted({n for w in WV.values() for n in w})
col = {n: j for j, n in enumerate(names)}
Wm = np.zeros((len(me.vertices), len(names)))
for i, w in WV.items():
    for n, x in w.items():
        Wm[i, col[n]] = x
fixed = {i for i, w in WV.items() if w.get('Head', 0) >= 0.99}
for _ in range(SMOOTH_ITERS):
    nxt = Wm.copy()
    for i in cverts:
        if i in fixed or not nbr[i]:
            continue
        nxt[i] = 0.5 * Wm[i] + 0.5 * Wm[list(nbr[i])].mean(0)
    Wm = nxt
for i in cverts:
    for g in mesh.vertex_groups:
        g.remove([i])
    w = Wm[i]
    top = np.argsort(-w)[:4]
    s_ = w[top].sum()
    for j in top:
        if w[j] > 1e-4:
            mesh.vertex_groups[names[j]].add([i], float(w[j] / s_), 'REPLACE')
print('CLOAK_WEIGHTS', stats, 'verts', len(cverts), 'smoothed x%d' % SMOOTH_ITERS)
scene['thf_cloak'] = json.dumps(chains)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'rig_v1.blend'))
