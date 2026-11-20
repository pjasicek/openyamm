"""Weight the grafted chicken 'Body' to the MM9 HEN.abc / ROOSTER.abc skeleton (from mm9_crow_claude/scripts/rig_body.py).

Args: <graft blend> <out blend> <config json> <report json>

- Legs: vertices below the leg exit height (config leg_exit_z) on each side only see their own leg chain's MM9
  vertices (Xuprleg .. toes); the core (everything else) sees every bone above the knee, so the thigh feathers follow
  Xuprleg as in MM9 and nothing on the body borrows a shank bone.
- Toes: foot vertices below the ankle take the MM9 toe (Xtoepiv*) whose direction from the ankle is nearest in angle
  (MM9's three toe angles shifted onto ours); the hind toe and the ankle pad take Xfoot; blended to Xfoot within
  TOE_BLEND of the ankle.
- Head: the grafted head shell, its eyes and the comb/wattles are rigid on Xhead where the raw head height is above
  SKULL_Z or forward of THROAT_Y (the skull, beak, comb and the wattles under the beak); the throat behind the beak and
  the stub blend into the neck chain (crow lesson: no hanging chin). The loft and the neck take the MM9 neck chain
  (Xneck, XneckB, XneckC, Xhead) by their position along it (smoothstep between segment centres).
- Body: nearest MM9 vertex label, diffused along the mesh (DIFFUSE iterations, legs/head held), then a short free pass
  outside the rigid head. Tail feathers follow the label of the nearest MM9 tail vertex as everything else.
- Small separate pieces (wing sheets, the eyes, wattles) are rigid with the main-body vertex nearest their centre.
"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree

argv = sys.argv[sys.argv.index('--') + 1:]
FIT, OUT, CFGF, REP = argv
cfg = json.load(open(CFGF))
DIFFUSE = cfg.get('diffuse', 10)
HINGE = cfg.get('hinge', 2)
LEG_EXIT = cfg['leg_exit_z']
SKULL_Z = cfg['skull_z']          # raw head frame
SKULL_BLEND = cfg.get('skull_blend', 0.06)
THROAT_Y = cfg['throat_y']        # raw head frame: forward of this the head is rigid (beak, wattles)
THROAT_BLEND = cfg.get('throat_blend', 0.05)
TOE_BLEND = cfg.get('toe_blend', 0.012)
SIDES = {-1: ['Xuprleg', 'Xleg', 'Xlowrleg', 'Xfoot', 'Xtoepiv', 'Xtoe', 'Xtoepiv01', 'Xtoe01', 'Xtoepiv02', 'Xtoe02'],
         1: ['Xuprleg01', 'Xleg01', 'Xlowrleg01', 'Xfoot01', 'Xtoepiv03', 'Xtoe03', 'Xtoepiv04', 'Xtoe04', 'Xtoepiv05',
             'Xtoe05']}
TOES = {-1: ['Xtoepiv', 'Xtoepiv01', 'Xtoepiv02'], 1: ['Xtoepiv03', 'Xtoepiv04', 'Xtoepiv05']}
NECK = ['Xneck', 'XneckB', 'XneckC', 'Xhead']

bpy.ops.wm.open_mainfile(filepath=FIT)
arm = bpy.data.objects['MM9_Rig']
body = bpy.data.objects['Body']
J = {b.name: np.array(arm.matrix_world @ b.head_local) for b in arm.data.bones}
mpos, mlab = [], []
for o in bpy.data.objects:
    if o.type != 'MESH' or o.name == 'Body':
        continue
    for v in o.data.vertices:
        if v.groups:
            g = max(v.groups, key=lambda g: g.weight)
            mpos.append(np.array(o.matrix_world @ v.co)); mlab.append(o.vertex_groups[g.group].name)
mpos = np.array(mpos)
mlab = np.array(['Xbeak' if x == 'beaknode' else x for x in mlab])
lower = set(b for s in SIDES.values() for b in s[1:])        # below the thigh: leg-only bones


def tree(mask):
    ids = np.nonzero(mask)[0]
    k = KDTree(len(ids))
    for j, i in enumerate(ids):
        k.insert(Vector(mpos[i]), j)
    k.balance()
    return k, ids


trees = {s: tree(np.isin(mlab, b)) for s, b in SIDES.items()}
core = tree(~np.isin(mlab, list(lower)))
bones = [b.name for b in arm.data.bones]
bi = {b: i for i, b in enumerate(bones)}
me = body.data
n = len(me.vertices)
P = np.array([tuple(v.co) for v in me.vertices])
piece = np.array([d.value for d in me.attributes['piece'].data])
hz = np.array([d.value for d in me.attributes['head_rz'].data])
hy = np.array([d.value for d in me.attributes['head_ry'].data])
part_f = np.array([d.value for d in me.attributes['part'].data])
vpart = np.zeros(n, int)
for p in me.polygons:
    for i in p.vertices:
        vpart[i] = max(vpart[i], part_f[p.index])
W = np.zeros((n, len(bones)))
side = np.where(P[:, 0] < 0, -1, 1)
is_leg = (P[:, 2] < LEG_EXIT) & (np.abs(P[:, 0]) > 0.012) & (vpart == 0)
for i in range(n):
    k, ids = trees[side[i]] if is_leg[i] else core
    W[i, bi[mlab[ids[k.find(Vector(P[i]))[1]]]]] = 1
# toes by angle
toe_rep = {}
for s in (-1, 1):
    foot, chain = SIDES[s][3], TOES[s]
    ank = J[foot]
    fm = is_leg & (side == s) & (P[:, 2] < cfg['ankle_z'])
    ids = np.nonzero(fm)[0]
    d = P[ids, :2] - ank[:2]
    r = np.linalg.norm(d, axis=1)
    th = np.arctan2(d[:, 0], -d[:, 1])     # 0 = straight forward (-Y), + toward +X
    d9 = np.array([J[t.replace('piv', '')][:2] - ank[:2] for t in chain])
    th9 = np.arctan2(d9[:, 0], -d9[:, 1])
    order = np.argsort(th9)
    fwd = (np.abs(th) < np.radians(100)) & (r > 0.006)
    shift = np.median(th[fwd & (r > 0.02)]) - np.median(th9)
    bnd = (np.sort(th9)[:-1] + np.sort(th9)[1:]) / 2 + shift
    for k_, i in enumerate(ids):
        W[i] = 0
        if not fwd[k_]:
            W[i, bi[foot]] = 1
            continue
        t = chain[order[np.searchsorted(bnd, th[k_])]]
        f = np.clip((r[k_] - 0.004) / TOE_BLEND, 0, 1); f = f * f * (3 - 2 * f)
        W[i, bi[t]] = f; W[i, bi[foot]] += 1 - f
    toe_rep[int(s)] = {'mm9_deg': np.degrees(th9).round(1).tolist(), 'shift_deg': float(np.degrees(shift)),
                       'verts': int(len(ids))}
# neck chain coordinate (segment centres along the MM9 polyline) for the loft, the stub and the neck
pts = [J[b] for b in NECK]


def chain_w(p):
    best = (1e9, 0, 0.0)
    for k in range(len(pts) - 1):
        a, b = pts[k], pts[k + 1]
        u = float(np.clip((p - a) @ (b - a) / ((b - a) @ (b - a)), 0, 1))
        dd = np.linalg.norm(p - (a + u * (b - a)))
        if dd < best[0]:
            best = (dd, k, u)
    _, k, u = best
    x = k + u                         # 0 .. 3 along Xneck .. Xhead
    w = {}
    c = [kk + 0.5 for kk in range(len(NECK) - 1)]   # centre of each bone's segment
    if x <= c[0]:
        return {NECK[0]: 1.0}
    if x >= c[-1]:
        f = np.clip((x - c[-1]) / 0.5, 0, 1); f = f * f * (3 - 2 * f)
        return {NECK[-2]: 1 - f, NECK[-1]: f}
    for kk in range(len(c) - 1):
        if c[kk] <= x <= c[kk + 1]:
            f = (x - c[kk]) / (c[kk + 1] - c[kk]); f = f * f * (3 - 2 * f)
            return {NECK[kk]: 1 - f, NECK[kk + 1]: f}
    return w


headpart = vpart >= 1
rig_w = np.zeros(n)
for i in np.nonzero(headpart)[0]:
    if vpart[i] == 3 and hz[i] < -4:          # loft
        rig_w[i] = 0.0
    else:
        a_ = np.clip((hz[i] - SKULL_Z) / SKULL_BLEND + 0.5, 0, 1)
        b_ = np.clip((THROAT_Y - hy[i]) / THROAT_BLEND + 0.5, 0, 1)
        f = max(a_, b_); rig_w[i] = f * f * (3 - 2 * f)
    cw = chain_w(P[i])
    W[i] = 0
    for b, x in cw.items():
        W[i, bi[b]] += x * (1 - rig_w[i])
    W[i, bi['Xhead']] += rig_w[i]
# the body's own neck above the shoulders: the chain as well, blended in from the shoulder
U = J['Xhead'] - J['Xneck']; U /= np.linalg.norm(U)
u_sh = cfg.get('neck_u0', 0.04); u_full = cfg.get('neck_u1', 0.09)
for i in np.nonzero(~headpart & (piece == 0))[0]:
    u = (P[i] - J['Xneck']) @ U
    if u <= u_sh:
        continue
    radial = np.linalg.norm((P[i] - J['Xneck']) - u * U)
    if radial > cfg.get('neck_r', 0.08):
        continue
    f = np.clip((u - u_sh) / (u_full - u_sh), 0, 1); f = f * f * (3 - 2 * f)
    cw = chain_w(P[i])
    row = np.zeros(len(bones))
    for b, x in cw.items():
        row[bi[b]] = x
    W[i] = (1 - f) * W[i] + f * row
nbr = [[] for _ in range(n)]
for e in me.edges:
    a, b = e.vertices
    nbr[a].append(b); nbr[b].append(a)
# separate pieces in the tail (the rooster's sickle feathers) keep their own per-vertex labels and are smoothed like
# the body, so they bend with MM9's tail bones; other pieces (wing sheets, eyes) are rigid (below)
comp_of = np.arange(n)
def _f(x):
    while comp_of[x] != x:
        comp_of[x] = comp_of[comp_of[x]]; x = comp_of[x]
    return x
for e in me.edges:
    a_, b_ = _f(e.vertices[0]), _f(e.vertices[1])
    comp_of[a_] = b_
comp_of = np.array([_f(i) for i in range(n)])
TAIL_Y = cfg.get('label_pieces_y_min', 9.0)
labelled = np.zeros(n, bool)
for c in np.unique(comp_of[piece == 2]):
    m = comp_of == c
    if P[m, 1].mean() > TAIL_Y:
        labelled[m] = True
body_v = (piece == 0) | labelled
hold = is_leg & (P[:, 2] < cfg['ankle_z']) | (rig_w > 0.98) | headpart


def diffuse(W, iters, hold):
    for _ in range(iters):
        avg = np.array([W[nb].mean(0) if nb else W[i] for i, nb in enumerate(nbr)])
        new = 0.5 * W + 0.5 * avg
        keep = hold | ~body_v
        new[keep] = W[keep]
        W = new
    return W


W = diffuse(W, DIFFUSE, hold)
W = diffuse(W, HINGE, (rig_w > 0.98) | (is_leg & (P[:, 2] < cfg['ankle_z'])))
# small pieces rigid with their nearest body vertex
bid = np.nonzero(piece == 0)[0]
kb = KDTree(len(bid))
for j, i in enumerate(bid):
    kb.insert(Vector(P[i]), j)
kb.balance()
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
seen = set(); pieces = 0
for v in bm.verts:
    if piece[v.index] != 2 or v.index in seen or labelled[v.index]:
        continue
    comp, st = [], [v]; seen.add(v.index)
    while st:
        x = st.pop(); comp.append(x.index)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen:
                seen.add(y.index); st.append(y)
    # anchor: the body vertex nearest the piece's centre (a wing sheet's nearest point can be on the neck)
    W[comp] = W[bid[kb.find(Vector(P[comp].mean(0)))[1]]]
    pieces += 1
order = np.argsort(-W, axis=1)
for i in range(n):
    keep = order[i, :4]
    row = np.zeros(len(bones)); row[keep] = W[i, keep]
    row[row < 0.02] = 0
    W[i] = row / row.sum()
for g in list(body.vertex_groups):
    body.vertex_groups.remove(g)
for b in bones:
    body.vertex_groups.new(name=b)
for i in range(n):
    for j in np.nonzero(W[i])[0]:
        body.vertex_groups[bones[j]].add([i], float(W[i, j]), 'REPLACE')
for g in list(body.vertex_groups):
    if not np.any(W[:, bi[g.name]] > 0):
        body.vertex_groups.remove(g)
body.parent = arm
body.matrix_parent_inverse = arm.matrix_world.inverted()
for m in list(body.modifiers):
    body.modifiers.remove(m)
mod = body.modifiers.new('Armature', 'ARMATURE'); mod.object = arm
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o.name != 'Body':
        bpy.data.objects.remove(o)
usage = {bones[j]: int((W[:, j] > 0.5).sum()) for j in range(len(bones)) if (W[:, j] > 0).any()}
rep = {'verts': n, 'pieces_rigid': pieces, 'labelled_piece_verts': int(labelled.sum()), 'legs': int(is_leg.sum()), 'head_rigid': int((rig_w > 0.98).sum()),
       'toes': toe_rep, 'dominant_counts': usage, 'max_influences': int((W > 0).sum(1).max()),
       'unweighted': int((W.sum(1) == 0).sum())}
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('RIG ' + json.dumps(rep))
