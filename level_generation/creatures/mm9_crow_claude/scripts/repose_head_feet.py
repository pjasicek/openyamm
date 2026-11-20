"""Head and feet repair of the UV'd, weighted crow (2026-10-30; after uv_export.py, before dump_uv3d/bake_ao/export).
Topology and UVs are unchanged, so the retexture stays valid.

Args: <uv blend> <out blend> <report json> <mm9 rig blend (work/mm9_crow_rig.blend)> [key=value ...]
  mode=weights  re-weight the head and neck only (no head turn, no feet; for a blend that already had the full pass)
  s_fade= s_necka= s_headpiv= s_head=  neck stations (defaults below)
  throat=1 [throat_from= throat_to=]  the throat bends with the neck (second head pass)

Head. The Meshy skull is larger and sits further back than MM9's, so the nearest-MM9-vertex labels gave the crown and
nape to XneckA, the skull to Xheadpiv and the beak to Xbeak, and nothing to Xhead. MM9's flight clips raise the head
~57 deg over XneckA (15), Xheadpiv (27) and Xhead (15): the beak turned 42 deg more than the crown, the skull folded
into a block under the chin with the beak coming out of its bottom (the "upside-down head") and the throat pinched.
Now the whole skull (and the eye pieces) is rigid on Xhead, the beak keeps Xbeak (MM9's peck), and the neck blends
XneckA -> Xheadpiv -> Xhead along the neck axis (Xneckpiv joint -> eye centre) behind the skull. The Meshy bind head
also pointed its beak 15 deg higher than MM9's (skull -> beak tip), so in flight it ended above MM9's and the low skull
hung under the chin: the head is turned down to MM9's bind direction about the skull base, blended over the neck.

Feet. The bones follow MM9 (toe direction within ~12 deg of MM9's closed diamond foot), but the Meshy foot is a
perching grip: toes forward-down with the claws hooked back (plantar side facing back). MM9's flight swings the
tarsus back ~75-85 deg, which turns that plantar side up: soles up, claws pointing up like an upturned hand. Each
foot is rolled 180 deg about its knee -> toe-tip axis (the twist spread over the tarsus), so the plantar side faces
forward in the bind pose and down in flight, the claws hooking down. Weights are unchanged.
"""
import bpy, bmesh, sys, json, math, heapq
import numpy as np
from mathutils import Vector, Quaternion

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP, MM9 = argv[:4]
OPT = dict(a.split('=', 1) for a in argv[4:])
WEIGHTS_ONLY = OPT.get('mode') == 'weights'
# neck stations along the axis (0 = Xneckpiv joint, 1 = eye centre): blend from the old weights to XneckA,
# then XneckA -> Xheadpiv -> Xhead; the skull from S_HEAD on is rigid on Xhead
# The first pass (uv_v2 -> uv_v3) ran with these defaults; its geometry is what the 4K retexture was painted on.
# The second head pass (mode=weights on uv_v4, README) moves the skull border back to s 0.68: the Meshy skull reaches
# ~3 cm behind the eyes, and with the border at 0.84 its crown stayed half on XneckA, kept its bind attitude in flight
# and stood as a flat wall above the beak (the head read upside down).
S_FADE, S_NECKA, S_HEADPIV, S_HEAD = (float(OPT.get(k, d)) for k, d in
                                      (('s_fade', 0.40), ('s_necka', 0.55), ('s_headpiv', 0.70), ('s_head', 0.84)))
R_FULL, R_NONE = 0.045, 0.065     # radial reach of the new head/neck weights (m from the neck axis)
SMOOTH = 3                        # neighbour-averaging passes over the re-weighted neck
BEAK_RINGS, BEAK_SMOOTH = 2, 4    # rings around the Xbeak/Xhead border and averaging passes over them
FEET = {'L': ('Xfoot', 'Xtoe', 2), 'R': ('Xfoot01', 'Xtoe01', 3)}   # bones and fit chain index per leg
TWIST_START = 0.25                # fraction of the knee -> toe-branch surface path where the roll starts
KNEE_RING = 0.06                  # leg vertices above this tarsus fraction below the knee seed the geodesic roll

bpy.ops.wm.open_mainfile(filepath=IN)
rig = bpy.data.objects['MM9_Rig']
body = bpy.data.objects['Body']
if rig.animation_data:
    rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
J = {b.name: np.array(b.head_local) for b in rig.data.bones}
me = body.data
n = len(me.vertices)
P = np.array([tuple(v.co) for v in me.vertices])
piece = np.array([d.value for d in me.attributes['piece'].data])
chain = np.array([d.value for d in me.attributes['chain'].data])
for name in ('Xhead',):
    if name not in body.vertex_groups:
        body.vertex_groups.new(name=name)
groups = [g.name for g in body.vertex_groups]
gi = {g: i for i, g in enumerate(groups)}
W = np.zeros((n, len(groups)))
for v in me.vertices:
    for g in v.groups:
        W[v.index, g.group] = g.weight
dom = np.array(groups)[W.argmax(1)]
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
nbr = [[e.other_vert(v).index for e in v.link_edges] for v in bm.verts]
comp = np.full(n, -1)
for v in bm.verts:
    if comp[v.index] >= 0:
        continue
    st = [v.index]; comp[v.index] = v.index
    while st:
        x = st.pop()
        for y in nbr[x]:
            if comp[y] < 0:
                comp[y] = v.index; st.append(y)
report = {}

# ---------------- head
eyes_c = [c for c in np.unique(comp[piece == 2])
          if np.linalg.norm(P[comp == c].mean(0) - J['Xheadpiv']) < 0.05]
eyes = np.isin(comp, eyes_c)
E = P[eyes].mean(0)
N0 = J['Xneckpiv']
axis = E - N0
L = np.linalg.norm(axis); a = axis / L
s = (P - N0) @ a / L
radial = np.linalg.norm((P - N0) - np.outer((P - N0) @ a, a), axis=1)
core = (chain < 0) & (piece == 0)
beak = W[:, gi['Xbeak']] > 0.5
ramp = lambda x, x0, x1: np.clip((x - x0) / (x1 - x0), 0, 1)
smooth = lambda x: x * x * (3 - 2 * x)
Wn = np.zeros_like(W)
k_a, k_p, k_h = gi['XneckA'], gi['Xheadpiv'], gi['Xhead']
u1 = smooth(ramp(s, S_NECKA, S_HEADPIV)); u2 = smooth(ramp(s, S_HEADPIV, S_HEAD))
Wn[:, k_a] = (1 - u1)
Wn[:, k_p] = u1 * (1 - u2)
Wn[:, k_h] = u1 * u2
alpha = smooth(ramp(s, S_FADE, S_NECKA)) * (1 - smooth(ramp(radial, R_FULL, R_NONE)))
alpha[~core | beak] = 0
W2 = W * (1 - alpha[:, None]) + Wn * alpha[:, None]
# the beak keeps Xbeak but its remainder (skull side of the beak base) goes to Xhead instead of neck bones
for i in np.nonzero(core & beak)[0]:
    rest = W2[i].sum() - W2[i, gi['Xbeak']]
    if rest > 0:
        W2[i, :] *= 0
        W2[i, gi['Xbeak']] = W[i, gi['Xbeak']]
        W2[i, k_h] = rest
region = alpha > 0
for _ in range(SMOOTH):
    avg = np.array([W2[nb].mean(0) if nb else W2[i] for i, nb in enumerate(nbr)])
    hold = ~region | beak | (s >= S_HEAD + 0.05)
    W2 = np.where(hold[:, None], W2, 0.5 * W2 + 0.5 * avg)
# the beak base: MM9 nods Xbeak against Xhead (up to ~20 deg in the death); a hard Xbeak/Xhead border pinched the
# hinge edges, so the border is softened over a few rings on both sides
kb = gi['Xbeak']
ring = (W2[:, kb] > 0.01) & (W2[:, kb] < 0.99)
for _ in range(BEAK_RINGS):
    ring = ring | np.array([any(ring[j] for j in nb) for nb in nbr])
ring &= core
for _ in range(BEAK_SMOOTH):
    avg = np.array([W2[nb].mean(0) if nb else W2[i] for i, nb in enumerate(nbr)])
    W2 = np.where(ring[:, None], 0.5 * W2 + 0.5 * avg, W2)
# the throat (below the eyes, behind the beak base): the Meshy crow looks down in the bind pose, so its throat lies
# between the beak base and the chest; rigid on Xhead it swung under the beak as a hanging chin once MM9 raised the
# head. With throat=1 it bends with the neck instead: Xhead at the beak base, Xheadpiv/XneckA further back.
if OPT.get('throat') == '1':
    bk_ = np.nonzero(W2[:, kb] > 0.9)[0]
    Bb = P[bk_[np.argsort(np.linalg.norm(P[bk_] - E, axis=1))[:max(3, len(bk_) // 10)]]].mean(0)
    T0, T1 = float(OPT.get('throat_from', 0.006)), float(OPT.get('throat_to', 0.03))
    throat = core & ~beak & (alpha > 0) & (P[:, 2] < E[2] - 0.002) & (P[:, 1] > Bb[1])
    tt = smooth(ramp(np.linalg.norm(P - Bb, axis=1), T0, T1))
    Wt_ = np.zeros_like(W2)
    Wt_[:, k_h] = 1 - tt
    Wt_[:, k_p] = 0.5 * tt
    Wt_[:, k_a] = 0.5 * tt
    W2[throat] = Wt_[throat]
    zone = throat.copy()
    for _ in range(2):
        zone = zone | np.array([any(zone[j] for j in nb) for nb in nbr])
    zone &= core & ~beak
    for _ in range(3):
        avg = np.array([W2[nb].mean(0) if nb else W2[i] for i, nb in enumerate(nbr)])
        W2 = np.where(zone[:, None], 0.5 * W2 + 0.5 * avg, W2)
    report['throat_verts'] = int(throat.sum())
W2[eyes] = 0
W2[eyes, k_h] = 1
report['head'] = {'eye_centre': E.tolist(), 'axis_len': float(L), 'reweighted': int(region.sum()),
                  'rigid_xhead': int(((W2[:, k_h] > 0.99)).sum()), 'eye_verts': int(eyes.sum())}

# ---------------- head direction: skull -> beak tip as in MM9's bind pose (sagittal turn about the skull base)
if not WEIGHTS_ONLY:
    with bpy.data.libraries.load(MM9) as (src, dst):
        dst.objects = [o for o in src.objects]
    mp, ml = [], []
    for o in dst.objects:
        if o is None or o.type != 'MESH':
            continue
        for v in o.data.vertices:
            g = max(v.groups, key=lambda g: g.weight)
            mp.append(tuple(o.matrix_world @ v.co)); ml.append(o.vertex_groups[g.group].name)
    mp, ml = np.array(mp), np.array(ml)
    sk9 = mp[np.isin(ml, ['Xhead', 'Xheadpiv'])].mean(0)
    bk9 = mp[np.isin(ml, ['Xbeak', 'Xjawpiv'])]
    d9 = bk9[np.argsort(np.linalg.norm(bk9 - sk9, axis=1))[-max(3, len(bk9) // 10):]].mean(0) - sk9
    bko = np.nonzero(beak)[0]
    do = P[bko[np.argsort(np.linalg.norm(P[bko] - E, axis=1))[-max(3, len(bko) // 50):]]].mean(0) - E
    sag = lambda d: math.atan2(d[2], -d[1])
    turn = sag(do) - sag(d9)                   # about +X; sag grows the other way (the creature faces -Y)
    pivot = N0 + a * L * S_HEAD
    wt = np.where(core, smooth(ramp(s, S_HEADPIV, S_HEAD)) * (1 - smooth(ramp(radial, R_FULL, R_NONE))), 0.0)
    wt[beak & core] = 1.0
    wt[eyes] = 1.0
    Ph = P.copy()
    for i in np.nonzero(wt > 0)[0]:
        Ph[i] = pivot + np.array(Quaternion(Vector((1, 0, 0)), turn * wt[i]) @ Vector(P[i] - pivot))
    P = Ph
    report['head']['turn_deg'] = math.degrees(turn)
    report['head']['mm9_dir_deg'] = math.degrees(sag(d9))
    report['head']['ours_dir_deg'] = math.degrees(sag(do))

# ---------------- feet: roll 180 deg about the knee -> toe-tip line; the roll ramps in over the tarsus and is full
# from the toe branch on (the toe tips lie on the line, so the toes keep their direction and only turn over)
P2 = P.copy()
for side, (fb, tb, ci) in ({} if WEIGHTS_ONLY else FEET).items():
    leg = chain == ci
    toe = np.nonzero(leg & (dom == tb))[0]
    knee = J[fb]
    tipc = P[toe[np.argsort(np.linalg.norm(P[toe] - knee, axis=1))[-max(3, len(toe) // 5):]]].mean(0)
    u = (tipc - knee) / np.linalg.norm(tipc - knee)
    dk = np.linalg.norm(P[toe] - knee, axis=1)
    branch = P[toe[np.argsort(dk)[:max(3, len(toe) // 8)]]].mean(0)
    # roll fraction by geodesic distance along the leg surface from the knee ring (every tarsus cross-section turns
    # as one; the hind toe, which sticks back from the ankle, is past the branch along the surface and turns fully)
    v = (branch - knee) / np.linalg.norm(branch - knee)
    ft = (P - knee) @ v / np.linalg.norm(branch - knee)
    ids = set(np.nonzero(leg)[0].tolist())
    seeds = [i for i in ids if ft[i] < KNEE_RING]     # the knee ring and the thigh above it
    gd = {i: 0.0 for i in seeds}
    pq = [(0.0, i) for i in seeds]
    heapq.heapify(pq)
    while pq:
        d0, i = heapq.heappop(pq)
        if d0 > gd[i]:
            continue
        for j in nbr[i]:
            if j in ids:
                nd = d0 + float(np.linalg.norm(P[j] - P[i]))
                if nd < gd.get(j, 1e9):
                    gd[j] = nd; heapq.heappush(pq, (nd, j))
    toe_base = toe[np.argsort(dk)[:max(3, len(toe) // 8)]]
    gb = float(np.mean([gd[i] for i in toe_base if i in gd]))
    moved = 0
    for i, g in gd.items():
        k = smooth(ramp(g / gb, TWIST_START, 1.0))
        if k <= 0:
            continue
        q = Quaternion(Vector(u), math.pi * k)
        P2[i] = knee + np.array(q @ Vector(P[i] - knee))
        moved += 1
    off = np.linalg.norm((branch - knee) - ((branch - knee) @ u) * u)
    report['foot_' + side] = {'axis': u.tolist(), 'branch': branch.tolist(), 'branch_off_axis': float(off),
                              'moved': moved, 'branch_geodesic': gb}

for v in me.vertices:
    v.co = Vector(P2[v.index])
W2[W2 < 0.01] = 0
order = np.argsort(-W2, axis=1)
for i in range(n):
    row = np.zeros(len(groups)); keep = order[i, :4]; row[keep] = W2[i, keep]
    W2[i] = row / row.sum()
for g in body.vertex_groups:
    g.remove(list(range(n)))
for i in range(n):
    for j in np.nonzero(W2[i])[0]:
        body.vertex_groups[groups[j]].add([i], float(W2[i, j]), 'REPLACE')
me.update()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(report, open(REP, 'w'), indent=1)
print('REPOSE ' + json.dumps(report))
