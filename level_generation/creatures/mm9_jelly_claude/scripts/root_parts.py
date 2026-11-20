"""Keep the Jellyspore's bell on its stalk and every leg in the stalk (2026-10-30 fix; runs on the UV blend, so UVs,
the retexture and the textures stay valid).

Args: <uv blend> <out blend> <report json>

Why: rig_body.py gives the bell's dark underside shell the weights of the top shell at the same azimuth and relative
radius, so its centre (where the stalk enters, 0.4 m below XbB) rides the cap bones XbB*. When MM9 inverts the bell
(fidgetwater, swim, hattackwater1/2) those bones turn about 180 degrees and the underside centre swings up with them:
the bell left the stalk by up to 24.7 cm (Fidget 0.30 s). MM9's own bell never does: its underside runs from a neck on
Xbellpiv* (at the collar) through an XbA* ring to the XbC* rim and never uses XbB*. Separately, the Xarmpiv02 leg's
root cap stopped 1.5 cm short of the stalk in every pose.

Underside: by relative radius rho from the stalk axis, the weights blend from MM9's neck bones (Xbellpiv*, by azimuth,
rho <= RHO_NECK) to its XbA* ring (RHO_XBA) and back into the shell's own weights (RHO_KEEP and out); the rim and the
outer shell keep theirs. The bind pose is unchanged; in the inverted poses the underside now gathers into a short neck
on the stalk top, as MM9's funnel does.
Legs: the leg the detached-parts audit flags at bind (ROOT_LEGS: Xarmpiv02; the other three sit in the stalk or a
collar ring, and a surface-normal inside test is unreliable on the thin collar rings) is rooted as in
../mm9_eye_claude root_limbs.py:
the first segment (cap to J1) is stretched along the root bone's axis until the cap is DEPTH inside the surface it
meets (at most half that part's thickness along the axis); J1 and the rest of the leg do not move, vertices move only
along the axis, so the rod keeps its section and UVs. The extension's weights blend from the leg's own to the weights
at the entry point (barycentric), fully those from half DEPTH inside.
"""
import bpy, sys, json, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP = argv
BELL_Z = 0.25
RHO_NECK, RHO_XBA, RHO_KEEP = 0.15, 0.30, 0.70
LEGS = [['Xarmpiv', 'XarmA'], ['Xarmpiv01', 'XarmA01'], ['Xarmpiv02', 'XarmA02'], ['Xarmpiv03', 'XarmA03']]
ROOT_LEGS = {'Xarmpiv02'}
DEPTH_MAX = 0.03
CHAIN_IDS = ['01', '03', '05', '07']


def smooth(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


bpy.ops.wm.open_mainfile(filepath=IN)
arm = bpy.data.objects['MM9_Rig']
body = bpy.data.objects['Body']
if arm.animation_data:
    arm.animation_data.action = None
for pb in arm.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
me = body.data
n = len(me.vertices)
piece = np.array([d.value for d in me.attributes['piece'].data])
chain = np.array([d.value for d in me.attributes['chain'].data])
M = body.matrix_world
Mi = M.inverted()
co = [M @ v.co for v in me.vertices]
groups = [g.name for g in body.vertex_groups]
gidx = {g: i for i, g in enumerate(groups)}


def ensure_group(name):
    if name not in gidx:
        body.vertex_groups.new(name=name)
        groups.append(name)
        gidx[name] = len(groups) - 1
    return gidx[name]


for c in CHAIN_IDS:
    ensure_group('Xbellpiv' + c)
    ensure_group('XbA' + c)
W = np.zeros((n, len(groups)))
for v in me.vertices:
    for g in v.groups:
        W[v.index, g.group] = g.weight
J = {b.name: arm.matrix_world @ b.head_local for b in arm.data.bones}
report = {'underside': {}, 'legs': {}}

# ---------------------------------------------------------------- underside shell (same selection as rig_body.py)
nbr = [[] for _ in range(n)]
for e in me.edges:
    a, b = e.vertices
    nbr[a].append(b); nbr[b].append(a)
seen, shells = set(), []
for s in range(n):
    if s in seen or piece[s] != 0:
        continue
    comp, st = [], [s]; seen.add(s)
    while st:
        x = st.pop(); comp.append(x)
        for y in nbr[x]:
            if y not in seen:
                seen.add(y); st.append(y)
    zs = np.array([co[i].z for i in comp])
    if zs.min() > BELL_Z - 0.05 and len(comp) > 300:
        shells.append((zs.mean(), comp))
shells.sort(key=lambda t: -t[0])
assert len(shells) >= 2, 'expected the two bell shells'
under = np.array(shells[1][1])
axis = J['Xtailpiv']  # the stalk axis (x, y of the stalk pivot)
r = np.array([math.hypot(co[i].x - axis.x, co[i].y - axis.y) for i in under])
rho = r / r.max()
az = np.array([math.atan2(co[i].y - axis.y, co[i].x - axis.x) for i in under])
caz = {c: math.atan2(J['XbA' + c].y - axis.y, J['XbA' + c].x - axis.x) for c in CHAIN_IDS}
newW = W.copy()
for k, i in enumerate(under):
    wn = np.zeros(len(groups)); wa = np.zeros(len(groups))
    for c in CHAIN_IDS:
        d = abs((az[k] - caz[c] + math.pi) % (2 * math.pi) - math.pi)
        f = max(0.0, 1 - d / (math.pi / 2))
        wn[gidx['Xbellpiv' + c]] += f
        wa[gidx['XbA' + c]] += f
    wn /= wn.sum(); wa /= wa.sum()
    x = rho[k]
    if x <= RHO_NECK:
        w = wn
    elif x <= RHO_XBA:
        t = smooth((x - RHO_NECK) / (RHO_XBA - RHO_NECK)); w = (1 - t) * wn + t * wa
    elif x < RHO_KEEP:
        t = smooth((x - RHO_XBA) / (RHO_KEEP - RHO_XBA)); w = (1 - t) * wa + t * W[i]
    else:
        continue
    newW[i] = w
report['underside'] = {'vertices': int(len(under)), 'radius': round(float(r.max()), 4),
                       'reweighted': int((rho < RHO_KEEP).sum()),
                       'rho': [RHO_NECK, RHO_XBA, RHO_KEEP]}


# ---------------------------------------------------------------- legs
def bary_weights(Wsrc, tri, loc, pts):
    A, B, C = (pts[i] for i in tri)
    v0, v1, v2 = B - A, C - A, loc - A
    d00, d01, d11, d20, d21 = v0.dot(v0), v0.dot(v1), v1.dot(v1), v2.dot(v0), v2.dot(v1)
    den = d00 * d11 - d01 * d01
    bv = (d11 * d20 - d01 * d21) / den
    bw = (d00 * d21 - d01 * d20) / den
    bary = (1 - bv - bw, bv, bw)
    return sum(bary[m] * Wsrc[tri[m]] for m in range(3))


newco = list(co)
for k, (r0, r1) in enumerate(LEGS):
    if r0 not in ROOT_LEGS:
        continue
    j0, j1 = J[r0], J[r1]
    L1 = (j1 - j0).length
    a = (j1 - j0) / L1
    # the leg's own piece: the connected part holding its tip (the 'chain' label also covers stalk-top vertices)
    lab = np.nonzero((chain == k) & (piece == 0))[0]
    tip = int(lab[np.argmax([(co[i] - j0).dot(a) for i in lab])])
    comp, st = {tip}, [tip]
    while st:
        x = st.pop()
        for y in nbr[x]:
            if y not in comp:
                comp.add(y); st.append(y)
    ids = np.array(sorted(comp))
    polys = [p.vertices[:] for p in me.polygons if not any(i in comp for i in p.vertices)]
    bvh = BVHTree.FromPolygons(co, polys)
    s = np.array([(co[i] - j0).dot(a) for i in ids])
    rr = np.array([((co[i] - j0) - a * si).length for si, i in zip(s, ids)])
    first = (s < L1) & (rr < 0.06)
    s_min = float(s[first].min())
    radius = float(np.median(rr[first & (s > 0) & (s < 0.12)]))
    cap = j0 + a * s_min
    rep = {'rod_radius': round(radius, 4)}
    loc, nrm, fi, h = bvh.ray_cast(cap, -a, 0.3)
    assert loc is not None, r0
    # thickness of the part met along the axis (exit point), so the root never pokes out of the far side
    loc2, _, _, h2 = bvh.ray_cast(loc - a * 1e-4, -a, 0.3)
    thick = h2 if loc2 is not None else 0.3
    depth = min(DEPTH_MAX, max(radius, 0.01), 0.5 * thick)
    s_entry = s_min - h
    s0 = s_entry - depth
    stretch = (L1 - s0) / (L1 - s_min)
    Wb = bary_weights(newW, polys[fi], loc, co)
    moved = 0
    for si, i, f in zip(s, ids, first):
        if not f:
            continue
        sn = s0 + (si - s_min) * stretch
        newco[i] = co[i] + a * (sn - si)
        moved += 1
        if sn < s_entry + 0.5 * h:
            # from the leg's own weights half-way along the new root to the entry point's, fully from half DEPTH in
            t = smooth((s_entry + 0.5 * h - sn) / (0.5 * h + 0.5 * depth))
            newW[i] = (1 - t) * W[i] + t * Wb
    rep.update({'gap_along_axis': round(h, 4), 'thickness': round(thick, 4), 'depth': round(depth, 4),
                'first_segment': round(L1, 4), 'stretch': round(stretch, 3), 'moved': moved,
                'entry_weights': {groups[g]: round(float(Wb[g]), 3) for g in np.nonzero(Wb > 0.01)[0]}})
    report['legs'][r0] = rep

# at most four influences, normalised
for i in range(n):
    row = newW[i]
    keep = np.argsort(-row)[:4]
    out = np.zeros_like(row)
    out[keep] = row[keep]
    out[out < 0.02] = 0
    newW[i] = out / out.sum()
for i, p in enumerate(newco):
    me.vertices[i].co = Mi @ p
for g in body.vertex_groups:
    g.remove(list(range(n)))
for i in range(n):
    for j in np.nonzero(newW[i])[0]:
        body.vertex_groups[groups[j]].add([i], float(newW[i, j]), 'REPLACE')
for g in list(body.vertex_groups):
    if not np.any(newW[:, gidx[g.name]] > 0):
        body.vertex_groups.remove(g)
me.update()
report['changed_weights'] = int((np.abs(newW - W) > 1e-4).any(1).sum())
report['moved_vertices'] = int(sum((newco[i] - co[i]).length > 1e-7 for i in range(n)))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(report, open(REP, 'w'), indent=1)
print('ROOTS ' + json.dumps(report))
