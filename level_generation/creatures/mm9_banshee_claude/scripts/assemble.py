"""Assembly on the ORIGINAL MM9 skeleton (bones translated, rest rotations unchanged). Everything in raw ABC space (01 chains at +x); mirror_glb.py at the end gives the true handedness.
- Upper (Meshy torso, sleeves): weights in bands on the MM9 chain.
- Dress: lattice tube on the Y chains, bridged to the waist cut (lattice.py). Cloak: lattice sheet on the Xc chains and the arm (separate object).
- Hands: ours, on MM9's four finger chains: voxel-joined tubes and palm, reduced, weights by connectivity along each chain; claws are separate rigid pieces on the last bone.
- Head: weights by hinge angle about the jaw joint (TMJ); teeth and tongue rigid. Neck: lofted to the torso's neck ring.
- Hair: 19 spikes lofted on MM9's own (spikes.py).
Output work/assembled.blend: MM9_Rig, Body (attr part: 0 torso/sleeves, 1 dress, 2 hand, 3 claw), Cloak, Head (attr hpart), Hair. Args: <head blend> <mm9 glb> <out blend> <report json>"""
import bpy, bmesh, sys, json, math, os
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lattice as L
import spikes as SP
IN, MM9, OUT, REP = sys.argv[sys.argv.index('--') + 1:]
rep = {}
TRIS_UPPER, TRIS_HAND = 2500, 520
Nt, Ns = 44, 19                    # dress grid
TMJ = np.array([0, -0.237, 0.545])


def ss(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


bpy.ops.wm.open_mainfile(filepath=IN)
up = bpy.data.objects['Upper']; head = bpy.data.objects['Head']
sc = bpy.context.scene
existing = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=MM9)
new = [o for o in bpy.data.objects if o not in existing]
arm = next(o for o in new if o.type == 'ARMATURE'); arm.name = 'MM9_Rig'
if arm.animation_data:
    arm.animation_data.action = None
for x in list(bpy.data.actions):
    bpy.data.actions.remove(x)
for o in new:
    if o is not arm:
        bpy.data.objects.remove(o)
for pb in arm.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
J = {b.name: np.array(arm.matrix_world @ b.head_local) for b in arm.data.bones}
report_j0 = {k: v.tolist() for k, v in J.items()}
# ------------------------------------------------------------- joints
info = json.load(open(os.path.join(os.path.dirname(IN), 'upper.json')))
sho = np.array(info['shoulder']); u = np.array(info['dir']); LA = info['length']
delta = sho - J['Zarmpiv01']
# -x side mirror of delta
children = {}
for b in arm.data.bones:
    children.setdefault(b.parent.name if b.parent else None, []).append(b.name)


def subtree(n):
    out = [n]
    for c in children.get(n, []):
        out += subtree(c)
    return out


for root, sx in (('Zarmpiv01', 1), ('Zarmpiv', -1)):
    d = delta * np.array([sx, 1, 1])
    for n in subtree(root):
        J[n] = J[n] + d
for tag, sx in (('01', 1), ('', -1)):
    # elbow on the straight sleeve axis
    M = np.array([sx, 1, 1])
    f = float((J['Zarm01'] - sho) @ u)
    el = (sho + u * f) * M
    dd = el - J['Zarm' + tag]
    # Zarm's subtree moves with it, the hand stays at MM9's distance
    for n in subtree('Zarm' + tag):
        J[n] = J[n] + dd
    J['Zarmbase' + tag] = (J['Xspine2'] * 0.35 + 0.65 * sho) * 1.0 if False else np.array([sx * 0.11, -0.085, 0.43])
# jaw: one hinge at the TMJ (clips_mm9.py folds Xjawpiv + Xjaw into Xjaw)
J['Xjawpiv'] = TMJ.copy(); J['Xjaw'] = TMJ.copy()
J['Xchin'] = TMJ + np.array([0, -0.11, -0.09])
bpy.context.view_layer.objects.active = arm
for o in bpy.data.objects:
    o.select_set(o == arm)
bpy.ops.object.mode_set(mode='EDIT')
inv = np.array(arm.matrix_world.inverted())
for b in arm.data.edit_bones:
    off = b.tail - b.head
    b.use_connect = False
    p = Vector((inv[:3, :3] @ J[b.name] + inv[:3, 3]).tolist())
    b.head = p; b.tail = p + off
bpy.ops.object.mode_set(mode='OBJECT')
for o in bpy.data.objects:
    o.select_set(False)


def verts_of(o):
    n = len(o.data.vertices)
    a = np.zeros(n * 3); o.data.vertices.foreach_get('co', a)
    return a.reshape(-1, 3)


def tris_of(o):
    o.data.calc_loop_triangles()
    a = np.zeros(len(o.data.loop_triangles) * 3, np.int32); o.data.loop_triangles.foreach_get('vertices', a)
    return a.reshape(-1, 3)


def new_object(name, co, faces):
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(map(float, c)) for c in co], [], [tuple(map(int, f)) for f in faces]); me.update()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
    return o


def set_weights(o, W):
    """W: list of {bone: w} per vertex"""
    names = set(k for d in W for k in d)
    for n in names:
        if n not in o.vertex_groups:
            o.vertex_groups.new(name=n)
    groups = {g.name: g for g in o.vertex_groups}
    for i, d in enumerate(W):
        top = sorted(d.items(), key=lambda t: -t[1])[:4]
        tot = sum(x for _, x in top)
        for n, x in top:
            if x > 1e-4:
                groups[n].add([i], x / tot, 'REPLACE')


# ------------------------------------------------------------- upper: reduce, waist loop, neck ring
for o in bpy.data.objects:
    o.select_set(o == up)
bpy.context.view_layer.objects.active = up
mod = up.modifiers.new('d', 'DECIMATE'); mod.ratio = min(TRIS_UPPER / len(up.data.polygons), 1.0); mod.use_symmetry = True; mod.symmetry_axis = 'X'
bpy.ops.object.modifier_apply(modifier='d')
print('UPPER reduced', len(up.data.polygons))


def boundary_loops(o):
    bm = bmesh.new(); bm.from_mesh(o.data); bm.edges.ensure_lookup_table(); bm.verts.ensure_lookup_table()
    left = {e for e in bm.edges if e.is_boundary}
    loops = []
    while left:
        e = left.pop(); cur = [e.verts[0], e.verts[1]]; 
        grow = True
        while grow:
            grow = False
            for end in (0, -1):
                v = cur[end]
                for x in v.link_edges:
                    if x in left:
                        left.discard(x); w = x.other_vert(v)
                        if end == 0:
                            cur.insert(0, w)
                        else:
                            cur.append(w)
                        grow = True
                        break
        loops.append([v.index for v in cur])
    bm.free()
    return loops


co = verts_of(up)
loops = boundary_loops(up)
info_l = sorted([(len(l), co[l].mean(0).round(3).tolist()) for l in loops], key=lambda t: -t[0])
print('UPPER LOOPS', info_l[:8])
waist = max([l for l in loops if co[l, 2].mean() < 0.2 and abs(co[l, 0].mean()) < 0.05], key=len)
neck = max([l for l in loops if co[l, 2].mean() > 0.4 and abs(co[l, 0].mean()) < 0.05], key=len)
if waist[0] == waist[-1]:
    waist = waist[:-1]
if neck[0] == neck[-1]:
    neck = neck[:-1]
print('WAIST', len(waist), 'NECK', len(neck))
wc = co[waist].mean(0)


def ring_at(idx, angle, centre, axis=2):
    """point of the closed loop at an azimuth about the centre; angle 0 = front (-y), pi/2 = +x"""
    P = co[idx]
    a = np.arctan2(P[:, 0] - centre[0], -(P[:, 1] - centre[1]))
    o_ = np.argsort(a)
    aa = np.r_[a[o_] - 2 * np.pi, a[o_], a[o_] + 2 * np.pi]
    pp = np.vstack([P[o_]] * 3)
    return np.stack([np.interp(angle, aa, pp[:, c]) for c in range(3)], -1)


# ------------------------------------------------------------- dress
angs_c = []
for ch in L.SKIRT_CHAINS:
    q = J[ch[0]]
    angs_c.append(math.atan2(q[0], -(q[1] - wc[1])))
ang8 = np.array([0, 0.6, 1.25, 2.0, np.pi, -2.0, -1.25, -0.6])
top8 = ring_at(waist, ang8, wc)
GRID, WD, ST = L.skirt_grid(J, top8, nt=Nt, ns=Ns)
# the top ring exactly on the waist, at even azimuths; columns blended into it
az = np.linspace(0, 2 * np.pi, Nt, endpoint=False)
az = np.where(az > np.pi, az - 2 * np.pi, az)
# the grid's own azimuth per column (lattice columns are not even): take from ring 0
g0 = GRID[0]
az0 = np.arctan2(g0[:, 0] - wc[0], -(g0[:, 1] - wc[1]))
snap = ring_at(waist, az0, wc)
for r in range(Ns):
    k = 1 - ss(0, 4, r)
    GRID[r] = GRID[r] + (snap - g0) * k[None] if np.ndim(k) else GRID[r] + (snap - g0) * k
# folds: long vertical ripples that grow to the hem
fr = 2 * np.pi * np.arange(Nt) / Nt
for r in range(1, Ns):
    s = r / (Ns - 1)
    c = GRID[r].mean(0)
    rad = GRID[r] - c; rad[:, 2] *= 0.3
    rad /= np.maximum(np.linalg.norm(rad, axis=1, keepdims=True), 1e-6)
    amp = 0.016 * ss(0.12, 0.8, s)
    GRID[r] += rad * (amp * (np.sin(11 * fr + 0.6) + 0.5 * np.sin(17 * fr + 1.7)))[:, None]
faces = []
for r in range(Ns - 1):
    for k in range(Nt):
        k1 = (k + 1) % Nt
        faces.append((r * Nt + k, r * Nt + k1, (r + 1) * Nt + k1, (r + 1) * Nt + k))
dress = new_object('Dress', GRID.reshape(-1, 3), faces)
set_weights(dress, [d for row in WD for d in row])
rs = ST[..., 1].reshape(-1); rt = ST[..., 0].reshape(-1)
for nm_, v_ in (('robe_s', rs), ('robe_t', rt)):
    a_t = dress.data.attributes.new(nm_, 'FLOAT', 'POINT'); a_t.data.foreach_set('value', v_.astype(float).tolist())
np.savez(os.path.join(os.path.dirname(OUT), 'dress_grid.npz'), s=rs, t=rt, Nt=Nt, Ns=Ns)
# ------------------------------------------------------------- upper weights
CO = verts_of(up)
sp = [(k, J[k][2]) for k in ('XCENTER', 'Xspine', 'Xspine1', 'Xspine2')]
e_ = float((J['Zarm01'] - sho) @ u)
WU = []
for p in CO:
    side = 1 if p[0] > 0 else -1
    tag = '01' if side > 0 else ''
    Ms = np.array([side, 1, 1.0])
    uu = u * Ms; s0 = sho * Ms
    al = float((p - s0) @ uu)
    rad = float(np.linalg.norm(p - s0 - uu * al))
    tube = 1 - ss(0.085 + 0.25 * max(0.0, -al), 0.135 + 0.25 * max(0.0, -al), rad)
    arm_t = float(ss(-0.10, 0.05, al) * tube) if abs(p[0]) > 0.09 else 0.0
    z = p[2]
    if z <= sp[1][1]:
        f = ss(sp[0][1], sp[1][1], z); tw = [('XCENTER', 1 - f), ('Xspine', f)]
    elif z <= sp[2][1]:
        f = ss(sp[1][1], sp[2][1], z); tw = [('Xspine', 1 - f), ('Xspine1', f)]
    elif z <= sp[3][1]:
        f = ss(sp[2][1], sp[3][1], z); tw = [('Xspine1', 1 - f), ('Xspine2', f)]
    else:
        n = ss(0.47, 0.505, z); tw = [('Xspine2', 1 - n), ('Xneckbase', n)]
    w = {}
    for k, x in tw:
        w[k] = w.get(k, 0) + float(x) * (1 - arm_t)
    if arm_t > 0:
        base = float(1 - ss(-0.03, 0.12, al))
        w['Zarmbase' + tag] = arm_t * base
        rest = arm_t * (1 - base)
        f = float(ss(e_ - 0.05, e_ + 0.05, al))
        w['Zarmpiv' + tag] = rest * (1 - f)
        w['Zarm' + tag] = rest * f          # the sleeve stays on the forearm: the hand turns inside the cuff
    WU.append(w)
set_weights(up, WU)
# ------------------------------------------------------------- hands, built on the +x chains, mirrored
HAND = []


def tube(points, radii, sides=9, flat=None):
    pts = np.array(points); r = np.array(radii)
    C, tq = L.resample_arc(pts, max(10, 3 * len(pts)))
    rq = np.interp(tq, np.arange(len(r)), r)
    tang = np.gradient(C, axis=0); tang /= np.linalg.norm(tang, axis=1, keepdims=True)
    ref = np.array(flat if flat is not None else [0.1, 0.2, 1.0]); ref /= np.linalg.norm(ref)
    verts = []; faces = []
    for i, (c, t, rr) in enumerate(zip(C, tang, rq)):
        a = np.cross(t, ref); a /= np.linalg.norm(a); b = np.cross(t, a)
        for k in range(sides):
            th = 2 * np.pi * k / sides
            verts.append(c + rr * (np.cos(th) * a + np.sin(th) * b))
    n = len(C)
    for i in range(n - 1):
        for k in range(sides):
            k1 = (k + 1) % sides
            faces.append((i * sides + k, i * sides + k1, (i + 1) * sides + k1, (i + 1) * sides + k))
    faces.append(tuple(range(sides - 1, -1, -1))); faces.append(tuple((n - 1) * sides + k for k in range(sides)))
    return np.array(verts), faces


def loft_ellipse(rows, sides=14):
    """rows: list of (centre, a axis*half, b axis*half)"""
    verts = []; faces = []
    for c, a, b in rows:
        for k in range(sides):
            th = 2 * np.pi * k / sides
            verts.append(c + np.cos(th) * a + np.sin(th) * b)
    n = len(rows)
    for i in range(n - 1):
        for k in range(sides):
            k1 = (k + 1) % sides
            faces.append((i * sides + k, i * sides + k1, (i + 1) * sides + k1, (i + 1) * sides + k))
    faces.append(tuple(range(sides - 1, -1, -1))); faces.append(tuple((n - 1) * sides + k for k in range(sides)))
    return np.array(verts), faces


FINGERS = {'A': ('04', 1.0), 'B': ('05', 1.0), 'C': ('06', 0.95), 'T': ('07', 1.15)}


def chain(tag):
    return ['Zfingbase' + tag, 'ZfingA' + tag, 'ZfingB' + tag, 'ZfingC' + tag]


wr = J['Zhand01']
base = [J['Zfingbase' + t] for t in ('04', '05', '06')]
kn = np.mean(base, 0)
fan = base[2] - base[0]; half = 0.5 * np.linalg.norm(fan) + 0.016; a_ = fan / np.linalg.norm(fan)
d_ = kn - wr; Lp = np.linalg.norm(d_); d_ /= Lp
n_ = np.cross(d_, a_); n_ /= np.linalg.norm(n_)
if n_[2] < 0:
    n_ = -n_            # back of the hand up
a_ = np.cross(n_, d_)
rows = [(wr - d_ * 0.05, a_ * 0.024, n_ * 0.02), (wr - d_ * 0.015, a_ * 0.026, n_ * 0.02), (wr + d_ * Lp * 0.3, a_ * 0.034, n_ * 0.019), (wr + d_ * Lp * 0.75, a_ * (half - 0.003), n_ * 0.017), (kn - d_ * 0.005, a_ * half, n_ * 0.0155), (kn + d_ * 0.012, a_ * (half - 0.006), n_ * 0.011)]
V, F = loft_ellipse(rows)
parts = [(V, F)]
prof = lambda k: [0.0125 * k, 0.0118 * k, 0.0108 * k, 0.0088 * k, 0.0098 * k, 0.0079 * k, 0.0070 * k]
claws = []
for key, (tag, k) in FINGERS.items():
    q = [J[n] for n in chain(tag)]
    tip = q[3] + (q[3] - q[2]) * 0.12
    cb = q[2] + (q[3] - q[2]) * 0.42
    # phalanges: the finger keeps some length past its knuckles, the claw starts on the last bone
    pts = [q[0], 0.5 * (q[0] + q[1]), q[1], 0.5 * (q[1] + q[2]), q[2], 0.5 * (q[2] + cb), cb]
    r = prof(k)
    if key == 'T':
        r = [0.0145, 0.0138, 0.0118, 0.0102, 0.0106, 0.0088, 0.0078]
        pts = [wr + d_ * 0.01 + (q[0] - wr) * 0.6] + pts[1:] if False else pts
    parts.append(tube(pts, r, flat=n_))
    # claw: tapered and hooked toward the palm
    axis = tip - cb; L_ = np.linalg.norm(axis); ax = axis / L_
    hook = -n_ - ax * (-n_ @ ax); hook /= np.linalg.norm(hook)
    ns = 6; ring = 6; cv = []; cf = []
    start = cb - ax * 0.014
    for i in range(ns):
        t = i / (ns - 1)
        c = start + (cb + axis * 1.0 - start) * t + hook * 0.012 * (t ** 2)
        rr = (0.0078 * k if i <= 1 else 0.0078 * k * (1 - (t - 1 / (ns - 1)) / (1 - 1 / (ns - 1))) ** 0.8) + 1e-4
        e1 = np.cross(ax, n_); e1 /= np.linalg.norm(e1); e2 = np.cross(ax, e1)
        for s_ in range(ring):
            th = 2 * np.pi * s_ / ring
            cv.append(c + rr * (np.cos(th) * e1 * 1.0 + np.sin(th) * e2 * 0.75))
    for i in range(ns - 1):
        for s_ in range(ring):
            s1 = (s_ + 1) % ring
            cf.append((i * ring + s_, i * ring + s1, (i + 1) * ring + s1, (i + 1) * ring + s_))
    cf.append(tuple(range(ring - 1, -1, -1))); cf.append(tuple((ns - 1) * ring + s_ for s_ in range(ring)))
    claws.append((key, np.array(cv), cf))
allv = []; allf = []; off = 0
for V, F in parts:
    allv.append(V); allf += [tuple(i + off for i in f) for f in F]; off += len(V)
hand = new_object('HandR', np.concatenate(allv), allf)
for o in bpy.data.objects:
    o.select_set(o == hand)
bpy.context.view_layer.objects.active = hand
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.normals_make_consistent(inside=False); bpy.ops.object.mode_set(mode='OBJECT')
m = hand.modifiers.new('r', 'REMESH'); m.mode = 'VOXEL'; m.voxel_size = 0.0024; m.use_smooth_shade = True
bpy.ops.object.modifier_apply(modifier='r')
m = hand.modifiers.new('s', 'SMOOTH'); m.factor = 0.6; m.iterations = 6
bpy.ops.object.modifier_apply(modifier='s')
print('HAND voxel', len(hand.data.polygons))
hand.data.calc_loop_triangles()
m = hand.modifiers.new('d', 'DECIMATE'); m.ratio = TRIS_HAND / len(hand.data.loop_triangles)
bpy.ops.object.modifier_apply(modifier='d')
print('HAND', len(hand.data.polygons))
HC = verts_of(hand)
HT = []
chs = {k: [J[n] for n in chain(t)] for k, (t, _) in FINGERS.items()}


def seg_param(p, q):
    """p (n,3), q polyline (m,3): nearest distance and (segment index + fraction)"""
    best = np.full(len(p), 1e9); par = np.zeros(len(p))
    for i in range(len(q) - 1):
        a, b = q[i], q[i + 1]
        t = np.clip(((p - a) @ (b - a)) / ((b - a) @ (b - a)), 0, 1)
        d = np.linalg.norm(p - (a + (b - a) * t[:, None]), axis=1)
        m_ = d < best
        best[m_] = d[m_]; par[m_] = i + t[m_]
    return best, par


def hand_weights(P):
    dist = {}; par = {}
    for k, q in chs.items():
        dist[k], par[k] = seg_param(P, np.array(q))
    keys = list(chs)
    D = np.stack([dist[k] for k in keys], 1)
    near = D.argmin(1)
    W = []
    al = (P - wr) @ d_
    for i in range(len(P)):
        k = keys[near[i]]; tag = FINGERS[k][0]
        pp = par[k][i]; names = chain(tag)
        # distance beyond the knuckle along the chain (metres)
        L0 = np.linalg.norm(chs[k][1] - chs[k][0])
        blend = 0.014
        w = {}
        if pp < 1e-3 and D[i, near[i]] > 0.0:
            # at or behind the chain's root: palm; the knuckle bends over 1.5 cm
            beh = float((chs[k][0] - P[i]) @ d_) if k != 'T' else float(np.linalg.norm(P[i] - chs[k][0]))
            f = float(ss(-0.002, 0.016, beh))
            w['Zhand01'] = f; w[names[0]] = 1 - f
        else:
            seg = int(pp); fr_ = pp - seg
            L_ = np.linalg.norm(chs[k][min(seg + 1, 3)] - chs[k][seg])
            distal = (1 - fr_) * L_; prox = fr_ * L_
            bone = names[min(seg, 2)]
            w[bone] = 1.0
            if seg < 2 and distal < blend:
                f = 0.5 * (1 - distal / blend); w = {bone: 1 - f, names[seg + 1]: f}
            elif seg > 0 and seg <= 2 and prox < blend:
                f = 0.5 * (1 - prox / blend); w = {bone: 1 - f, names[seg - 1]: f}
            elif seg == 0 and prox < blend:
                f = 0.5 * (1 - prox / blend); w = {bone: 1 - f, 'Zhand01': f}
        W.append(w)
    return W


WH = hand_weights(HC)
set_weights(hand, WH)
# claws as one object, rigid on the last moving bone
cv = []; cf = []; cw = []; off = 0
for key, V, F in claws:
    cv.append(V); cf += [tuple(i + off for i in f) for f in F]; off += len(V)
    cw += [{'ZfingB' + FINGERS[key][0]: 1.0}] * len(V)
claw = new_object('ClawR', np.concatenate(cv), cf)
set_weights(claw, cw)
# mirror both onto -x
def mirrored(o, name):
    d = o.copy(); d.data = o.data.copy(); d.name = name; sc.collection.objects.link(d)
    bm = bmesh.new(); bm.from_mesh(d.data)
    for v in bm.verts:
        v.co.x = -v.co.x
    bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    bm.to_mesh(d.data); bm.free()
    ren = {}
    for g in d.vertex_groups:
        n = g.name
        if n.startswith('Zhand'):
            g.name = 'Zhand'
        elif n[-2:] in ('04', '05', '06', '07'):
            g.name = n[:-2] + {'04': '', '05': '01', '06': '02', '07': '03'}[n[-2:]]
    return d


handL = mirrored(hand, 'HandL'); clawL = mirrored(claw, 'ClawL')
def zip_loops(bm, va, vb, centre, axis):
    """Stitch two closed vertex loops around one axis with a triangle strip, walking both by azimuth (bmesh's bridge twists loops of unequal length into a membrane across the ring)."""
    axis = axis / np.linalg.norm(axis); e1 = np.array([1.0, 0, 0]) - axis * axis[0]; e1 /= np.linalg.norm(e1); e2 = np.cross(axis, e1)
    az = lambda v: math.atan2(float((np.array(v.co[:]) - centre) @ e1), float((np.array(v.co[:]) - centre) @ e2)) % (2 * math.pi)
    A = sorted(va, key=az); B = sorted(vb, key=az)
    i = j = 0; na, nb = len(A), len(B); made = []
    while i < na or j < nb:
        ai0 = az(A[i % na]) + (2 * math.pi if i >= na else 0); aj0 = az(B[j % nb]) + (2 * math.pi if j >= nb else 0)
        nxa = az(A[(i + 1) % na]) + (2 * math.pi if i + 1 >= na else 0); nxb = az(B[(j + 1) % nb]) + (2 * math.pi if j + 1 >= nb else 0)
        if j >= nb or (i < na and nxa <= nxb):
            f = (A[i % na], A[(i + 1) % na], B[j % nb]); i += 1
        else:
            f = (A[i % na], B[(j + 1) % nb], B[j % nb]); j += 1
        if len(set(f)) == 3:
            made.append(bm.faces.new(f))
    return made


# ------------------------------------------------------------- body = upper + dress (bridged) + hands + claws
def tag_part(o, v):
    a = o.data.attributes.new('part', 'INT', 'FACE'); a.data.foreach_set('value', [v] * len(o.data.polygons))


tag_part(up, 0); tag_part(dress, 1); tag_part(hand, 2); tag_part(handL, 2); tag_part(claw, 3); tag_part(clawL, 3)
for o in bpy.data.objects:
    o.select_set(o in (up, dress, hand, handL, claw, clawL))
bpy.context.view_layer.objects.active = up
bpy.ops.object.join()
body = up; body.name = 'Body'; body.data.name = 'Body'
# weld the dress's top ring on the waist: bridge
bm = bmesh.new(); bm.from_mesh(body.data); bm.edges.ensure_lookup_table(); bm.verts.ensure_lookup_table()
part = bm.faces.layers.int.get('part')
wl = [e for e in bm.edges if e.is_boundary and abs(e.verts[0].co.z - e.verts[1].co.z) < 0.01 and e.verts[0].co.z < 0.2 and abs(e.verts[0].co.x) < 0.2 and e.link_faces[0][part] == 0]
tl = [e for e in bm.edges if e.is_boundary and e.link_faces[0][part] == 1 and e.verts[0].co.z > -0.0 and e.verts[1].co.z > -0.0]
print('BRIDGE', len(wl), len(tl))
va = list({v for e in wl for v in e.verts}); vb = list({v for e in tl for v in e.verts})
for f in zip_loops(bm, va, vb, wc, np.array([0, 0, 1.0])):
    f[part] = 0
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
bm.to_mesh(body.data); bm.free(); body.data.update()
# ------------------------------------------------------------- cloak
def back_of(x, z):
    """the torso's back at (x, z)"""
    bvh = BVHTree.FromPolygons([Vector(c) for c in verts_of(body).tolist()], tris_of(body).tolist())
    hit = bvh.ray_cast(Vector((x, 1.5, z)), Vector((0, -1, 0)), 3.0)
    return np.array(hit[0][:]) if hit[0] else None


bvh_b = BVHTree.FromPolygons([Vector(c) for c in verts_of(body).tolist()], tris_of(body).tolist())
def root_pt(x, z):
    hit = bvh_b.ray_cast(Vector((x, 1.5, z)), Vector((0, -1, 0)), 3.0)
    return np.array(hit[0][:]) + np.array([0, -0.006, 0])


Ml = np.array([-1, 1, 1])
elbow = J['Zarm01'] * Ml; wrist = J['Zhand01'] * Ml
R = {'c': root_pt(0, 0.47), 'a': root_pt(-0.09, 0.47), 'b': root_pt(-0.19, 0.42),
     'e': elbow + np.array([0, 0.02, 0.012]), 'w': wrist + np.array([0, 0.018, 0.01]) - (u * Ml) * 0.03}
print('ROOTS', {k: v.round(3).tolist() for k, v in R.items()})
lat, bones = L.cloak_lattice(J, np.array([0, .245, .295]) + np.array([0, 0.02, 0.01]), J['XcBmid'] + np.array([0, -.005, -.07]), J['XcCmid'] + np.array([0, 0, -.04]), R)
NU, NV = 20, 13
cg, WC, uv, sides = L.cloak_grid(lat, bones, nu_half=NU, nv=NV)
WC = L.mirrored_weights(WC, sides)
nr, nc = cg.shape[:2]
# folds from root to rim
n0 = np.cross(np.gradient(cg, axis=1), np.gradient(cg, axis=0)); n0 /= np.maximum(np.linalg.norm(n0, axis=2, keepdims=True), 1e-9)
us = np.linspace(-1, 1, nc)
fold = (np.sin(us * 19 + 0.4) + 0.5 * np.sin(us * 31 + 2.1))
for r in range(1, nr):
    v = r / (nr - 1)
    sign = 1
    cg[r] += n0[r] * (0.016 * ss(0.15, 0.85, v) * fold)[:, None]
faces = []
for r in range(nr - 1):
    for k in range(nc - 1):
        faces.append((r * nc + k, r * nc + k + 1, (r + 1) * nc + k + 1, (r + 1) * nc + k))
cloak = new_object('Cloak', cg.reshape(-1, 3), faces)
set_weights(cloak, [d for row in WC for d in row])
luv = cloak.data.uv_layers.new(name='UVMap')
c_uv = uv.reshape(-1, 2)
for p in cloak.data.polygons:
    for li in p.loop_indices:
        vi = cloak.data.loops[li].vertex_index
        luv.data[li].uv = (float(c_uv[vi, 0]), float(1 - c_uv[vi, 1]))
# ------------------------------------------------------------- head weights + neck
Hco = verts_of(head)
hp = np.zeros(len(Hco), np.int32); head.data.attributes['hpart'].data.foreach_get('value', hp)
yz = Hco[:, 1:3] - TMJ[1:3]
MOUTH = np.array([-0.345, 0.513]) - TMJ[1:3]
a0 = math.atan2(MOUTH[1], MOUTH[0])
phi = np.degrees((np.arctan2(yz[:, 1], yz[:, 0]) - a0 + np.pi) % (2 * np.pi) - np.pi)    # + = above? sign fixed below
# y is forward negative: rotating from the mouth line toward the chin is decreasing z: find sign with the chin
chin_phi = np.degrees((math.atan2(0.45 - TMJ[2], -0.33 - TMJ[1]) - a0 + np.pi) % (2 * np.pi) - np.pi)
phi = phi * np.sign(chin_phi)
rr = np.linalg.norm(yz, axis=1)
wj = ss(-3, 9, phi) * ss(0.02, 0.07, rr) * (1 - ss(70, 105, phi))
hweights = []
for i in range(len(Hco)):
    if hp[i] in (3,):
        hweights.append({'Xhead': 1.0})
    elif hp[i] == 4:
        hweights.append({'Xjaw': 1.0})
    elif hp[i] == 2:
        hweights.append({'Xjaw': 0.8, 'Xhead': 0.2})
    elif hp[i] == 1:
        hweights.append({'Xhead': 1.0})
    else:
        w = float(wj[i])
        d = {'Xhead': 1 - w}
        if w > 0:
            d['Xjaw'] = w
        hweights.append(d)
set_weights(head, hweights)
# neck ring of the head
hl = boundary_loops(head)
hl = [l for l in hl if hp[l].max() == 0]
ring = max(hl, key=len)
if ring[0] == ring[-1]:
    ring = ring[:-1]
print('HEAD RING', len(ring), Hco[ring].mean(0).round(3), 'NECK top', len(neck), CO[neck].mean(0).round(3))
NN = 28
hc = Hco[ring].mean(0); tc = CO[neck].mean(0)
def ring_points(P, c, n):
    a = np.arctan2(P[:, 0] - c[0], -(P[:, 1] - c[1]))
    o_ = np.argsort(a); aa = np.r_[a[o_] - 2 * np.pi, a[o_], a[o_] + 2 * np.pi]; pp = np.vstack([P[o_]] * 3)
    q = np.linspace(-np.pi, np.pi, n, endpoint=False)
    return np.stack([np.interp(q, aa, pp[:, c_]) for c_ in range(3)], -1)
ra = ring_points(Hco[ring], hc, NN); rb = ring_points(CO[neck], tc, NN)
# loft: head ring -> torso ring, leaving each along its own axis, the waist of the neck slightly in
n_rows = 6
t_a = np.array([0, 0.68, -0.73]); t_b = np.array([0, 0.6, -0.8])
rowsN = []
D_ = np.linalg.norm(tc - hc)
for k in range(n_rows):
    t = k / (n_rows - 1)
    h00, h10, h01, h11 = 2 * t ** 3 - 3 * t ** 2 + 1, t ** 3 - 2 * t ** 2 + t, -2 * t ** 3 + 3 * t ** 2, t ** 3 - t ** 2
    c_ = h00 * hc + h10 * t_a * D_ + h01 * tc + h11 * t_b * D_
    rel_a = ra - hc; rel_b = rb - tc
    rowsN.append(c_ + rel_a * (1 - ss(0, 1, t)) + rel_b * ss(0, 1, t))
neckv = np.concatenate(rowsN)
fN = []
for k in range(n_rows - 1):
    for i in range(NN):
        i1 = (i + 1) % NN
        fN.append((k * NN + i, k * NN + i1, (k + 1) * NN + i1, (k + 1) * NN + i))
neckO = new_object('Neck', neckv, fN)
wn = []
for k in range(n_rows):
    t = k / (n_rows - 1)
    if t < 0.5:
        f = ss(0, 0.5, t); w = {'Xheadpiv': 1 - f, 'Xneck': f}
    else:
        f = ss(0.5, 1, t); w = {'Xneck': 1 - f, 'Xneckbase': f}
    wn += [w] * NN
set_weights(neckO, wn)
a = neckO.data.attributes.new('hpart', 'INT', 'POINT'); a.data.foreach_set('value', [5] * len(neckO.data.vertices))
# stump's weights fade into Xheadpiv
pl = Hco[ring].mean(0); nl = np.array([0, 0.68, -0.73])
d_ring = (Hco - pl) @ (-nl)
gi = head.vertex_groups
if 'Xheadpiv' not in gi:
    gi.new(name='Xheadpiv')
for i in np.where((d_ring < 0.05) & (hp == 0) & (Hco[:, 1] > -0.27))[0]:
    k = float(1 - ss(0.0, 0.05, d_ring[i]))
    g_ = {g.group: g.weight for g in head.data.vertices[int(i)].groups}
    for gidx, w in g_.items():
        gi[gidx].add([int(i)], w * (1 - k), 'REPLACE')
    gi['Xheadpiv'].add([int(i)], k, 'REPLACE')
for o in bpy.data.objects:
    o.select_set(o in (head, neckO))
bpy.context.view_layer.objects.active = head
bpy.ops.object.join()
bm = bmesh.new(); bm.from_mesh(head.data); bm.edges.ensure_lookup_table()
layer = bm.verts.layers.int.get('hpart')
la = [e for e in bm.edges if e.is_boundary and e.verts[0][layer] == 0 and e.verts[1][layer] == 0 and np.linalg.norm(np.array(e.verts[0].co[:]) - hc) < 0.11]
lb = [e for e in bm.edges if e.is_boundary and e.verts[0][layer] == 5 and e.verts[1][layer] == 5 and np.linalg.norm(np.array(e.verts[0].co[:]) - hc) < np.linalg.norm(np.array(e.verts[0].co[:]) - tc)]
print('NECK BRIDGE', len(la), len(lb))
va = list({v for e in la for v in e.verts}); vb = list({v for e in lb for v in e.verts})
zip_loops(bm, va, vb, hc, np.array([0, -0.68, 0.73]))
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
bm.to_mesh(head.data); bm.free(); head.data.update()
# torso's neck ring onto the loft's last row, so no crack
bvert = verts_of(body)
last = rowsN[-1]
idx = np.array(neck)
tb = {}
for i in idx:
    pass
# ------------------------------------------------------------- hair spikes
d9 = np.load(os.path.join(os.path.dirname(IN), 'mm9_parts.npz'))
lines = SP.spike_lines(d9)
HV = []; HF = []; HW = []; HUV = []; off = 0
bvh_h = BVHTree.FromPolygons([Vector(c) for c in verts_of(head).tolist()], tris_of(head).tolist())
def nearest_head(p):
    return np.array(bvh_h.find_nearest(Vector(p.tolist()))[0][:])
RINGN, STN = 5, 7
for li, s in enumerate(lines):
    pts = s['points'][::-1]                   # root first
    bn = s['bones'][::-1]; wid = s['width'][::-1]
    # root inside the cap
    root = pts[0]
    hit = nearest_head(root)
    pts = np.vstack([hit + (np.array([0, -0.2, 0.62]) - hit) * 0.12, pts[1:]]) if len(pts) > 2 else np.vstack([hit, pts])
    bn2 = ['Xhead'] + bn[1:] if len(pts) == len(bn) else ['Xhead'] + bn
    C, tq = L.resample_arc(pts, STN)
    tang = np.gradient(C, axis=0); tang /= np.linalg.norm(tang, axis=1, keepdims=True)
    out = C - np.array([0, -0.2, 0.62]); 
    for i in range(STN):
        t = i / (STN - 1)
        w_ = 0.031 * (1 - t ** 1.6) + 0.0004            # half width
        th_ = 0.42 * w_ + 0.0004                       # half thickness
        a = np.cross(tang[i], out[i]); a /= np.maximum(np.linalg.norm(a), 1e-6)
        b = np.cross(a, tang[i])
        for k in range(RINGN):
            ang = 2 * np.pi * k / RINGN
            HV.append(C[i] + a * w_ * math.cos(ang) + b * th_ * math.sin(ang))
            HUV.append((((li % 5) + k / (RINGN)) / 5, 1 - t))
        tt = tq[i]
        n_b = len(bn2)
        bb = max(tt - 0.5, 0); j0 = min(int(bb), max(n_b - 3, 0)); g = min(bb - j0, 1.0)
        names = bn2
        w = {}
        if n_b >= 3:
            w[names[j0]] = 1 - g; w[names[j0 + 1]] = w.get(names[j0 + 1], 0) + g
        else:
            w[names[0]] = 1.0
        HW += [w] * RINGN
    for i in range(STN - 1):
        for k in range(RINGN):
            k1 = (k + 1) % RINGN
            HF.append((off + i * RINGN + k, off + i * RINGN + k1, off + (i + 1) * RINGN + k1, off + (i + 1) * RINGN + k))
    # tip cap
    HF.append(tuple(off + (STN - 1) * RINGN + k for k in range(RINGN)))
    off += STN * RINGN
hair = new_object('Hair', HV, HF)
set_weights(hair, HW)
hl_ = hair.data.uv_layers.new(name='UVMap')
for p in hair.data.polygons:
    for li_ in p.loop_indices:
        vi = hair.data.loops[li_].vertex_index
        hl_.data[li_].uv = HUV[vi]
# parent everything
for o in (body, cloak, head, hair):
    o.parent = arm; o.matrix_parent_inverse = Matrix.Identity(4)
    for m in list(o.modifiers):
        o.modifiers.remove(m)
    md = o.modifiers.new('Armature', 'ARMATURE'); md.object = arm
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:]) if o not in (cloak,) else None
    bm.to_mesh(o.data); bm.free()
    o.data.update()
    print(o.name, len(o.data.vertices), len(o.data.polygons))
rep['joints'] = {k: v.tolist() for k, v in J.items()}
json.dump(rep, open(REP, 'w'))
for o in list(bpy.data.objects):
    if o.name in ('Neck',):
        bpy.data.objects.remove(o)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('SAVED')
