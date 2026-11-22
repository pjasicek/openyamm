"""Carnage Hand rig on work/clean_v2.blend -> work/rig_v1.blend (+ work/rig_info.json).
Forward -Y (palm), up +Z (fingers), thumb +X.

Bones: Root (hover root at the hand's centre) > Palm (rigid: palm, back of the hand, the whole mouth: rim, gullet,
tongue, fangs) > per finger <F>_1, <F>_2, <F>_3 (F = Thumb, Index, Middle, Ring, Pinky; thumb _1 is the metacarpal
from the carpometacarpal joint deep in the ball of the thumb), and LipUpper / LipLower (the lip lids, rigid, both
with their head on the hinge axis 0.06 m behind the palm; they turn about U to open).
Joints come from the finger centrelines of finger_axes.py (iso-geodesic contour centres from each tip): the web
between neighbouring fingers is the midpoint of the shortest skin path between their tips; the knuckle sits 2.5 cm
proximal of the web (arc length from the tip), the middle and end joints at 55 % and 27 % of that length.
Skin weights (skin only; every other part rigid): a skin vertex belongs to the finger whose centreline is nearest,
if its geodesic distance from that tip is below the knuckle's + 3 cm; along the finger it goes to the phalanx of its
geodesic distance with 1.2 cm linear blends at the joints, and into the palm with a 4 cm ramp at the knuckle; then
three smoothing passes on the skin graph."""
import bpy, os, json, heapq, math
import numpy as np
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'clean_v2.blend'))
ob = bpy.data.objects['Hand']; me = ob.data
FJ = json.load(open(os.path.join(HERE, 'work', 'fingers.json')))['fingers']
M = json.load(open(os.path.join(HERE, 'work', 'mouth.json')))
O, n_out, U = np.array(M['O']), np.array(M['n']), np.array(M['U'])
pa = np.zeros(len(me.polygons), np.int32); me.attributes['part'].data.foreach_get('value', pa)
co = np.array([tuple(v.co) for v in me.vertices]); nv = len(co)
vpart = -np.ones(nv, np.int32)
for p in me.polygons:
    for v in p.vertices:
        vpart[v] = max(vpart[v], pa[p.index]) if vpart[v] != 0 else 0
for p in me.polygons:                        # skin wins on shared rim vertices
    if pa[p.index] == 0:
        for v in p.vertices: vpart[v] = 0
skin = np.nonzero(vpart == 0)[0]
adj = {int(v): set() for v in skin}
for e in me.edges:
    a, b = e.vertices
    if a in adj and b in adj: adj[a].add(b); adj[b].add(a)


def dijkstra(src):
    d = {src: 0.0}; h = [(0.0, src)]
    while h:
        x, v = heapq.heappop(h)
        if x > d[v]: continue
        for o in adj[v]:
            y = x + float(np.linalg.norm(co[o] - co[v]))
            if y < d.get(o, 1e9): d[o] = y; heapq.heappush(h, (y, o))
    return d


# name the fingers by x of the tip: thumb is the +X one, then index .. pinky by angle round the palm
tips = {int(k): np.array(f['tip']) for k, f in FJ.items()}
thumb = max(tips, key=lambda k: tips[k][0])
rest = sorted([k for k in tips if k != thumb], key=lambda k: -math.atan2(tips[k][2] - 0.15, tips[k][0]))
rest = sorted(rest, key=lambda k: -tips[k][0])
NAMES = dict(zip([thumb] + rest, ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky']))
print('FINGERS', {NAMES[k]: np.round(tips[k], 3).tolist() for k in tips})
G = {NAMES[k]: dijkstra(k) for k in tips}
order = ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky']
web = {}
for a, b in zip(order[:-1], order[1:]):
    best = min(adj, key=lambda v: max(G[a].get(v, 9), G[b].get(v, 9)))
    web[(a, b)] = (best, G[a][best], G[b][best])
    print('WEB', a, b, np.round(co[best], 3).tolist(), round(G[a][best], 3), round(G[b][best], 3))
wd = {'Thumb': web[('Thumb', 'Index')][1],
      'Index': web[('Index', 'Middle')][1],
      'Middle': (web[('Index', 'Middle')][2] + web[('Middle', 'Ring')][1]) / 2,
      'Ring': (web[('Middle', 'Ring')][2] + web[('Ring', 'Pinky')][1]) / 2,
      'Pinky': web[('Ring', 'Pinky')][2]}
line = {}
for k, f in FJ.items():
    nm = NAMES[int(k)]
    pts = np.array([f['tip']] + f['centres']); ds = np.r_[0.0, 0.006 + 0.005 * np.arange(len(f['centres']))]
    line[nm] = (pts, ds)


def at(nm, s):
    pts, ds = line[nm]
    s = min(s, ds[-1]); i = max(1, int(np.searchsorted(ds, s)))
    t = (s - ds[i - 1]) / (ds[i] - ds[i - 1])
    return pts[i - 1] + (pts[i] - pts[i - 1]) * t


CMC = (0.13, 0.01, 0.10)
J = {}
for nm in order:
    if nm == 'Thumb':
        # the thumb's contour line merges into the ball of the thumb past 0.26 m (ring radius 6-7 cm) and the web to
        # the index is reached round the back; joints from the line's own narrowing instead: end joint at 0.10 (behind
        # the fat pad), knuckle at 0.20, carpometacarpal deep in the ball of the thumb toward the heel
        s = [0.30, 0.20, 0.10]
        pts = [np.array(CMC), at(nm, 0.20), at(nm, 0.10)]
    else:
        sk = wd[nm] + 0.025; s = [sk, sk * 0.55, sk * 0.27]
        pts = [at(nm, x) for x in s]
    J[nm] = {'s': s, 'pts': pts + [line[nm][0][0]]}
    print('JOINTS', nm, [round(x, 3) for x in s], [np.round(p, 3).tolist() for p in J[nm]['pts']])
# curl plane per finger (SVD of the centreline up to the knuckle) -> flexion axis, sign: curls toward the palm side
axes = {}
for nm in order:
    P = np.array(J[nm]['pts'])
    pts, ds = line[nm]; Q = pts[ds <= min(J[nm]['s'][0], 0.25)]
    c = Q.mean(0); _, _, vt = np.linalg.svd(Q - c); a = vt[2]
    d = P[1] - P[0]; d /= np.linalg.norm(d)
    target = O + n_out * 0.10
    if nm == 'Thumb':
        want = target - P[1]
    else:
        want = n_out
    if np.dot(np.cross(a, d), want) < 0: a = -a          # +angle about a moves d toward 'want'
    axes[nm] = a.tolist()

arm = bpy.data.armatures.new('Hand_Rig'); rig = bpy.data.objects.new('Hand_Rig', arm)
bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects: o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT'); eb = arm.edit_bones


def bone(name, head, tail, parent=None, deform=True):
    b = eb.new(name); b.head = Vector(head); b.tail = Vector(tail); b.parent = parent; b.use_deform = deform
    d = (b.tail - b.head).normalized()
    b.align_roll(Vector((0, -1, 0)) if abs(d.y) < 0.9 else Vector((0, 0, 1)))
    return b


skc = co[skin]; centre = (skc.min(0) + skc.max(0)) / 2
root = bone('Root', centre, centre + np.array([0, 0, 0.15]))
palm_c = O - n_out * 0.05
palm = bone('Palm', palm_c, palm_c + np.array([0, 0, 0.15]), root)
for nm in order:
    P = J[nm]['pts']; par = palm
    for i in range(3):
        par = bone(f'{nm}_{i + 1}', P[i], P[i + 1], par)
        par.use_connect = i > 0
C = np.array(M['hinge']); V = np.array(M['V'])
bone('LipUpper', C, C + V * 0.06, palm)
bone('LipLower', C, C - V * 0.06, palm)
bpy.ops.object.mode_set(mode='OBJECT')

# weights
W = {b.name: np.zeros(nv) for b in arm.bones if b.use_deform and b.name != 'Root'}
RIGID = {1: 'Palm', 2: 'Palm', 3: 'Palm', 4: 'Palm', 5: 'LipUpper', 6: 'LipLower'}
for v in range(nv):
    if vpart[v] != 0: W[RIGID[int(vpart[v])]][v] = 1.0


def seg_dist(p, pts):
    best = 9
    for a, b in zip(pts[:-1], pts[1:]):
        ab = b - a; t = np.clip(np.dot(p - a, ab) / np.dot(ab, ab), 0, 1)
        best = min(best, np.linalg.norm(p - (a + ab * t)))
    return best


BL = 0.012
for v in skin:
    v = int(v); p = co[v]
    cands = []
    for nm in order:
        g = G[nm].get(v, 9); lim = J[nm]['s'][0] + 0.03
        if g < lim:
            P = np.array(J[nm]['pts'])
            P = np.vstack([P[0] - (P[1] - P[0]) * 0.25, P])     # a little past the base joint
            cands.append((seg_dist(p, P), nm, g))
    if not cands:
        W['Palm'][v] = 1.0; continue
    _, nm, g = min(cands)
    s0, s1, s2 = J[nm]['s']
    ramp = np.clip((s0 + 0.02 - g) / 0.04, 0, 1); ramp = ramp * ramp * (3 - 2 * ramp)
    # phalanx: _1 between s0 and s1, _2 between s1 and s2, _3 beyond s2 (toward the tip), linear blends at joints
    w3 = np.clip((s2 + BL - g) / (2 * BL), 0, 1)
    w2 = np.clip((s1 + BL - g) / (2 * BL), 0, 1) - w3
    w1 = 1 - w2 - w3
    W[f'{nm}_1'][v] += w1 * ramp; W[f'{nm}_2'][v] += w2 * ramp; W[f'{nm}_3'][v] += w3 * ramp
    W['Palm'][v] += 1 - ramp
names = list(W); Wm = np.stack([W[k] for k in names], 1)
for _ in range(3):
    new = Wm.copy()
    for v in skin:
        v = int(v); nb = list(adj[v])
        new[v] = 0.5 * Wm[v] + 0.5 * Wm[nb].mean(0)
    Wm = new
Wm /= Wm.sum(1, keepdims=True)
for k, nm in enumerate(names):
    g = ob.vertex_groups.new(name=nm)
    for v in np.nonzero(Wm[:, k] > 0.002)[0]:
        g.add([int(v)], float(Wm[v, k]), 'REPLACE')
mod = ob.modifiers.new('Armature', 'ARMATURE'); mod.object = rig
ob.parent = rig
cnt = {nm: int((Wm[:, k] > 0.5).sum()) for k, nm in enumerate(names)}
print('WEIGHTS >0.5', cnt, 'unweighted', int((Wm.sum(1) < 0.99).sum()))
json.dump({'joints': {k: {'s': J[k]['s'], 'pts': [np.asarray(p).tolist() for p in J[k]['pts']]} for k in J},
           'axes': axes, 'centre': centre.tolist(), 'palm': palm_c.tolist(), 'hinge': C.tolist(), 'U': U.tolist(),
           'n': n_out.tolist(), 'height': float(co[:, 2].max())},
          open(os.path.join(HERE, 'work', 'rig_info.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v1.blend'))
