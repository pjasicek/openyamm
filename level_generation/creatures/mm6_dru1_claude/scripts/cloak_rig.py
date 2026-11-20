"""Cloak bones and weights for the druidess (adapted from mm6_thf_claude/scripts/cloak_rig.py to the B_* rig).
Args: -- <in blend> <out blend>

The cloak (piece 100, step1_clean.py) is one open sheet hanging from the shoulder tops behind the arms to the ankles,
wrapping +-80 deg round the back at the shoulders and +-100 deg at the hem (cloak_probe.py).
Chains: 15 chains of 4 bones (Cloak_<c>_<k>) at CHAIN_DEG (0 = straight back, +90 = her left), from a ring at
Z_LEVELS[0] (just below the shoulders) to the hem; roots parented to the chest bone B_Spine2. Chain points lie
mid-thickness in the sheet (rays from the body axis: mean of the first and last hit); front-edge chains step back to
the cloth where the edge recedes.
Weights of every cloak vertex (Meshy's are discarded):
 - above Z_TOP: the chest (B_Spine2);
 - below: two chains by angle (linear) and the chain bones by height (blend over +-30 % of each segment), blended into
   the chest just below the ring; lower front corners beyond the edge chain follow the edge chain;
 - mantle over the shoulder: cloak within ATTACH_D of the upper-arm segment fades toward the upper arm (clavicle near
   the shoulder), only above z ATTACH_Z (the thief: attaching cloth down to the elbow pulled a 9x sheet under a raised
   arm), so a raised arm lifts the cloak's shoulder while the rest hangs.
Then all cloak weights are diffused over the cloak's own edges (SMOOTH_ITERS passes; per-vertex rules tore the hem
where neighbours fell into different sectors). scene['cloak_chains'] stores the chains for cloak_sim.py."""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
scene = bpy.context.scene
arm = bpy.data.objects['Rig']; mesh = bpy.data.objects['Body']; me = mesh.data
CLOAK = 100
# denser across the back, where the walking legs swing (the trailing boot bulged between 13-deg chains); 15 chains keep
# the rig at 116 joints, under the 128-joint palette row (ModelRenderer.h)
CHAIN_DEG = [0, 10, -10, 20, -20, 30, -30, 42, -42, 55, -55, 68, -68, 82, -82]
Z_LEVELS = [1.32, 1.00, 0.68, 0.38]
Z_TOP = Z_LEVELS[0]
CHEST, CHEST_LO = 'B_Spine2', 'B_Spine1'
AXIS = Vector(tuple(arm.data.bones['B_Spine1'].head_local)[:2] + (0.0,))
ATTACH_D, ATTACH_MAX = (0.05, 0.12), 1.0
ATTACH_Z = (1.26, 1.36)
SMOOTH_ITERS = 4

pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
cface = [p for p in me.polygons if all(pv[v] == CLOAK for v in p.vertices)]
cverts = sorted({v for p in cface for v in p.vertices})
co = {i: mesh.matrix_world @ me.vertices[i].co for i in range(len(me.vertices))}
tree = BVHTree.FromPolygons([co[i] for i in range(len(me.vertices))], [tuple(p.vertices) for p in cface])


def surface_point(deg, z):
    a = math.radians(deg); d = Vector((math.sin(a), math.cos(a), 0))
    o = Vector((AXIS.x, AXIS.y, z)); hits = []
    t = 0.0
    while t < 0.7:
        loc, n, i, dist = tree.ray_cast(o + d * (t + 1e-4), d, 0.7 - t)
        if loc is None:
            break
        hits.append(loc); t += dist + 1e-4
    if not hits:
        return None
    return (hits[0] + hits[-1]) / 2


chains = []
for deg in CHAIN_DEG:
    pts = []
    for z in Z_LEVELS:
        q = None
        for back in range(0, 40, 3):                     # front edges recede near the shoulders: step back to the cloth
            q = surface_point(deg - math.copysign(back, deg) if deg else 0, z)
            if q is not None:
                break
        pts.append(q)
    near = [i for i in cverts if abs(((math.degrees(math.atan2(co[i].x - AXIS.x, co[i].y - AXIS.y)) - deg) + 180)
                                      % 360 - 180) < 8]
    low = min(co[i].z for i in near)
    hem = None
    for dz in (0.03, 0.05, 0.07, 0.10, 0.13):
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
    parent = eb[CHEST]
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
    zs = [p[2] for p in c['pts']]
    for k in range(4):
        z0, z1 = zs[k], zs[k + 1]
        if z1 <= z <= z0 or (k == 3 and z < z1) or (k == 0 and z > z0):
            t = 0.0 if z0 == z1 else (z0 - z) / (z0 - z1)
            w = {c['bones'][k]: 1.0}
            if t < 0.3 and k > 0:
                b = 0.5 * (1 - t / 0.3); w[c['bones'][k - 1]] = b; w[c['bones'][k]] = 1 - b
            elif t > 0.7 and k < 3:
                b = 0.5 * (t - 0.7) / 0.3; w[c['bones'][k + 1]] = b; w[c['bones'][k]] = 1 - b
            return w
    return {c['bones'][3]: 1.0}


segs = {}
for s_ in ('L', 'R'):
    segs[s_] = (arm.matrix_world @ arm.data.bones[f'B_{s_}_UpperArm'].head_local,
                arm.matrix_world @ arm.data.bones[f'B_{s_}_Forearm'].head_local)


def arm_attach(p):
    best = (1e9, None, 0.0)
    for s_, (a, b) in segs.items():
        ab = b - a; t = max(0.0, min(1.0, (p - a).dot(ab) / ab.length_squared))
        d = (p - (a + ab * t)).length
        if d < best[0]:
            best = (d, s_, t)
    d, s_, t = best
    w = {f'B_{s_}_UpperArm': 1.0}
    if t < 0.3:
        c = 0.4 * (1 - t / 0.3); w = {f'B_{s_}_UpperArm': 1 - c, f'B_{s_}_Clavicle': c}
    return d, w


edge = max(abs(d) for d in CHAIN_DEG)
nbr = {i: set() for i in cverts}
for e in me.edges:
    a_, b_ = e.vertices
    if a_ in nbr and b_ in nbr:
        nbr[a_].add(b_); nbr[b_].add(a_)
att = {}
for i in cverts:
    d, _ = arm_attach(co[i])
    att[i] = ATTACH_MAX * (1 - smooth(d, *ATTACH_D)) * smooth(co[i].z, *ATTACH_Z)
for _ in range(12):
    att = {i: 0.5 * att[i] + 0.5 * (sum(att[j] for j in nbr[i]) / len(nbr[i]) if nbr[i] else att[i]) for i in cverts}
stats = {'top': 0, 'chain': 0, 'front': 0, 'attached': 0}
WV = {}
order = sorted(CHAIN_DEG)
for i in cverts:
    p = co[i]
    a = math.degrees(math.atan2(p.x - AXIS.x, p.y - AXIS.y))
    w = {}
    if p.z >= Z_TOP:
        w = {CHEST: 1.0}; stats['top'] += 1
    elif abs(a) > edge + 12 and p.z > 0.95:              # front corners near the shoulders: chest blended into the edge chain
        ec = next(c for c in chains if c['deg'] == math.copysign(edge, a))
        tch = smooth(abs(a), edge + 12, edge + 40) * smooth(p.z, 0.95, 1.08)
        w = {CHEST: 0.5 * tch, CHEST_LO: 0.5 * tch}
        for k_, x in chain_weights(ec, p.z).items():
            w[k_] = w.get(k_, 0) + x * (1 - tch)
        stats['front'] += 1
    else:
        ac = max(-edge, min(edge, a))
        for lo, hi in zip(order, order[1:]):
            if lo <= ac <= hi:
                t = (ac - lo) / (hi - lo); break
        cl_lo = next(c for c in chains if c['deg'] == lo); cl_hi = next(c for c in chains if c['deg'] == hi)
        for c, f in ((cl_lo, 1 - t), (cl_hi, t)):
            for n, x in chain_weights(c, p.z).items():
                w[n] = w.get(n, 0) + x * f
        b = smooth(p.z, Z_TOP - 0.08, Z_TOP)
        if b > 0:
            w = {n: x * (1 - b) for n, x in w.items()}; w[CHEST] = w.get(CHEST, 0) + b
        stats['chain'] += 1
    if att[i] > 0.01:
        _, aw = arm_attach(p)
        w = {n: x * (1 - att[i]) for n, x in w.items()}
        for n, x in aw.items():
            w[n] = w.get(n, 0) + x * att[i]
        stats['attached'] += 1
    WV[i] = w
# junction (G4: the cloak top joins the shoulder skin; chest-only cloak weights against arm-following skin stretched
# the seam 3.6x under the raised attack arm): cloak vertices within JOIN_D of the attached torso skin blend into the
# weights of their nearest skin vertex (1 at the seam, 0 at JOIN_D)
JOIN_D = 0.06
JOIN_Z = 1.36          # below this the nearest skin is the upper arm the cloak hangs behind (3.9x when raised)
skin_ids = [i for i in range(len(me.vertices)) if pv[i] == 0]
from mathutils.kdtree import KDTree
kd = KDTree(len(skin_ids))
for k_, i in enumerate(skin_ids):
    kd.insert(co[i], k_)
kd.balance()
gname = {g.index: g.name for g in mesh.vertex_groups}
joined = 0
for i in cverts:
    if co[i].z < JOIN_Z:                                # only at the seam (shoulder tops, z 1.40-1.42)
        continue
    loc, k_, d = kd.find(co[i])
    if d >= JOIN_D:
        continue
    b = 1 - smooth(d, 0.0, JOIN_D)
    sw = {gname[e.group]: e.weight for e in me.vertices[skin_ids[k_]].groups if e.weight > 1e-4}
    tot = sum(sw.values()) or 1.0
    w = {n: x * (1 - b) for n, x in WV[i].items()}
    for n, x in sw.items():
        w[n] = w.get(n, 0) + b * x / tot
    WV[i] = w; joined += 1
stats['joined'] = joined
names = sorted({n for w in WV.values() for n in w})
col = {n: j for j, n in enumerate(names)}
Wm = np.zeros((len(me.vertices), len(names)))
for i, w in WV.items():
    for n, x in w.items():
        Wm[i, col[n]] = x
for _ in range(SMOOTH_ITERS):
    nxt = Wm.copy()
    for i in cverts:
        if nbr[i]:
            nxt[i] = 0.5 * Wm[i] + 0.5 * Wm[list(nbr[i])].mean(0)
    Wm = nxt
gidx = {g.name: g for g in mesh.vertex_groups}
for i in cverts:
    for g in mesh.vertex_groups:
        g.remove([i])
    w = Wm[i]
    top = np.argsort(-w)[:4]
    s_ = w[top].sum()
    for j in top:
        if w[j] > 1e-4:
            gidx[names[j]].add([i], float(w[j] / s_), 'REPLACE')
print('CLOAK_WEIGHTS', stats, 'verts', len(cverts), 'smoothed x%d' % SMOOTH_ITERS)
scene['cloak_chains'] = json.dumps(chains)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
