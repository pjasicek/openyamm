"""Root the Lobber's upper arms and middle limbs in the head and keep one mouth tooth on its jaw (2026-10-30 fix; runs
on the re-weighted UV blend, so UVs, the retexture and the textures stay valid).

Args: <uv blend> <out blend> <report json> [<blend with the final UVs>]
With the fourth argument the result carries that blend's UVMap (same mesh topology): the texture pass laid new UVs and
repainted on roots v1, and these weight fixes keep every vertex where the paint saw it (weights only, see below).

Why (claude_shared/detached_parts_audit.py): MM9's Lobber is one connected mesh; ours has separate limb pieces.
- Upper arms (XCbase -> XCpiv -> XCarm, both sides): fit_limbs.py starts each arm at its XCbase joint, which lies
  1.2-1.5 cm above our HD head shell, and the arm hangs on Xmouth while the head surface under it is about half Xjaw
  (reweight_head.py); when MM9 opens the lid the two part, up to 6.2 cm (Dead).
- Middle limbs (XBpiv -> XBarm): rooted only 2-6 mm, rigid on XBpiv, while the head there blends Xjawpiv/Xheadpiv/
  Xjawbase: 4.5-9.3 mm gaps in AttackRanged, Cast, Hit and Death.
- One 14-tri tooth (TOOTH_AT, lower mouth corner, -x side) does not touch the head shell (1.5 cm off); it is wedged
  between an upper and a lower tooth, but is rigid with a hinge-band head vertex and carries 24 % Xchin (a top-lid
  bone): when the lid opens it is dragged 9 mm off both teeth (AttackRanged 0.23 s).

Limbs: each limb's own piece (the connected part holding its tip) is rooted as in ../mm9_eye_claude root_limbs.py:
the head surface is found along the root bone's axis (J0 -> J1) by a ray cast back from the middle of the first
segment; the first segment (cap to J1) is stretched along that axis until the cap is DEPTH inside the head (at most
half the head's thickness there); J1 and the rest of the limb do not move, vertices move only along the axis, so the
rod keeps its section and UVs. The weights of the root blend from the limb's own (at the surface) to the head's
weights at the entry point (barycentric), fully the head's from DEPTH/2 inside, so the buried root follows the head
surface it enters.
Upper arms, second pass (hardened audit, 2026-10-30: XCarm01 parted 4.1 cm, Death frame 24, 78/268 poses): the cap stayed
in the head, but the rod above the surface hung fully on XCbase/XCpiv, which ride Xmouth, while the surface there is
about half Xjaw, so the rod's base lifted 4-6 cm off the surface when the lid opened. The head's weights now run up the
exposed rod and fade out at J1 (BAND_TO_J1; both sides, so the pair stays alike). No vertex moves.
Tendril (TENDRIL_AT, audit part 14, 20 cm, -x side, 1.6 cm off in Cast frame 11): rigid on Xheadpiv/Xhead, while its
mirror twin rides Xjawpiv and stays attached; it takes the twin's weights.
Tooth: rigid with the lower-head tooth it sits on (the nearest mouth piece whose dominant bone is a lower-head bone;
audit part 17, Xhead). Dropping only the lid shares was tried: it moved the gap to Standing (5.8 mm).
"""
import bpy, sys, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP = argv[:3]
UV_FROM = argv[3] if len(argv) > 3 else None
LIMBS = [['XCbase', 'XCpiv', 4], ['XCbase01', 'XCpiv01', 5], ['XBpiv', 'XBarm', 2], ['XBpiv01', 'XBarm01', 3]]
BAND_TO_J1 = {'XCbase', 'XCbase01'}
DEPTH_MAX = 0.03
LOWER = {'Xheadpiv', 'Xhead', 'Xheadmid'}
TOOTH_AT = Vector((-0.061, -0.186, 0.889))  # Blender coordinates (glTF -0.061, 0.889, 0.186): audit part 7
TENDRIL_AT = Vector((-0.034, -0.077, 0.995))   # Blender coordinates of the -x tendril's centre (glTF z = +0.077)


def smooth(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


uv_final = None
if UV_FROM:
    bpy.ops.wm.open_mainfile(filepath=UV_FROM)
    src = bpy.data.objects['Body'].data
    uv_final = [0.0] * (2 * len(src.loops))
    src.uv_layers['UVMap'].data.foreach_get('uv', uv_final)
    uv_corners = [l.vertex_index for l in src.loops]
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
W = np.zeros((n, len(groups)))
for v in me.vertices:
    for g in v.groups:
        W[v.index, g.group] = g.weight
J = {b.name: arm.matrix_world @ b.head_local for b in arm.data.bones}
nbr = [[] for _ in range(n)]
for e in me.edges:
    a, b = e.vertices
    nbr[a].append(b); nbr[b].append(a)


def connected(start):
    comp, st = {start}, [start]
    while st:
        x = st.pop()
        for y in nbr[x]:
            if y not in comp:
                comp.add(y); st.append(y)
    return comp


def bary_weights(Wsrc, tri, loc):
    A, B, C = (co[i] for i in tri)
    v0, v1, v2 = B - A, C - A, loc - A
    d00, d01, d11, d20, d21 = v0.dot(v0), v0.dot(v1), v1.dot(v1), v2.dot(v0), v2.dot(v1)
    den = d00 * d11 - d01 * d01
    bv = (d11 * d20 - d01 * d21) / den
    bw = (d00 * d21 - d01 * d20) / den
    bary = (1 - bv - bw, bv, bw)
    return sum(bary[m] * Wsrc[tri[m]] for m in range(3))


# the head (and bulb): the core body shell, without limbs, stalk or mouth pieces
core = (chain == -1) & (piece == 0)
head_polys = [p.vertices[:] for p in me.polygons if all(core[i] for i in p.vertices)]
bvh = BVHTree.FromPolygons(co, head_polys)
report = {'limbs': {}, 'tooth': {}}
newco = list(co)
newW = W.copy()

for r0, r1, k in LIMBS:
    j0, j1 = J[r0], J[r1]
    L1 = (j1 - j0).length
    a = (j1 - j0) / L1
    lab = np.nonzero((chain == k) & (piece == 0))[0]
    tip = int(lab[np.argmax([(co[i] - j0).dot(a) for i in lab])])
    ids = np.array(sorted(connected(tip)))
    s = np.array([(co[i] - j0).dot(a) for i in ids])
    rr = np.array([((co[i] - j0) - a * si).length for si, i in zip(s, ids)])
    first = (s < L1) & (rr < 0.06)
    s_min = float(s[first].min())
    radius = float(np.median(rr[first & (s > 0) & (s < L1)]))
    start = j0 + a * (0.5 * L1)
    loc, nrm, fi, hs = bvh.ray_cast(start, -a, 0.5)
    assert loc is not None, r0
    s_entry = 0.5 * L1 - hs
    loc2, _, _, h2 = bvh.ray_cast(loc - a * 1e-4, -a, 0.5)
    thick = h2 if loc2 is not None else 0.5
    depth = min(DEPTH_MAX, max(radius, 0.01), 0.5 * thick)
    s0 = min(s_min, s_entry - depth)
    stretch = (L1 - s0) / (L1 - s_min)
    Wb = bary_weights(W, head_polys[fi], loc)
    moved = 0
    for si, i, f in zip(s, ids, first):
        if not f:
            continue
        sn = s0 + (si - s_min) * stretch
        if abs(sn - si) > 1e-7:
            newco[i] = co[i] + a * (sn - si)
            moved += 1
        if r0 in BAND_TO_J1:
            t = smooth((L1 - sn) / (L1 - s_entry))        # all head at the surface and below, own weights at J1
            newW[i] = (1 - t) * W[i] + t * Wb
        elif sn < s_entry:
            t = smooth((s_entry - sn) / (0.5 * depth))
            newW[i] = (1 - t) * W[i] + t * Wb
    report['limbs'][r0] = {'piece_vertices': int(len(ids)), 'rod_radius': round(radius, 4),
                           'cap_outside_by': round(s_min - s_entry, 4), 'head_thickness': round(thick, 4),
                           'depth': round(depth, 4), 'first_segment': round(L1, 4), 'stretch': round(stretch, 3),
                           'moved': moved,
                           'entry_weights': {groups[g]: round(float(Wb[g]), 3) for g in np.nonzero(Wb > 0.01)[0]}}

# the tooth: the mouth piece nearest TOOTH_AT
pieces2 = np.nonzero(piece == 2)[0]
seed = int(pieces2[np.argmin([(co[i] - TOOTH_AT).length for i in pieces2])])
tooth = sorted(connected(seed))
cen = sum((co[i] for i in tooth), Vector()) / len(tooth)
assert (cen - TOOTH_AT).length < 0.02, cen
before = {groups[g]: round(float(W[tooth[0], g]), 3) for g in np.nonzero(W[tooth[0]] > 0)[0]}
tset = set(tooth)
best = None
for i in pieces2:
    if i in tset or groups[int(np.argmax(W[i]))] not in LOWER:
        continue
    d = min((co[i] - co[j]).length for j in tooth)
    if best is None or d < best[0]:
        best = (d, int(i))
host = sorted(connected(best[1]))
hcen = sum((co[i] for i in host), Vector()) / len(host)
hw = W[host[0]]
assert all(np.allclose(W[i], hw, atol=1e-4) for i in host), 'the host tooth is rigid'
for i in tooth:
    newW[i] = hw
report['tooth'] = {'vertices': len(tooth), 'centre': [round(x, 4) for x in cen], 'weights_before': before,
                   'host_tooth_centre': [round(x, 4) for x in hcen], 'host_distance': round(best[0], 4),
                   'weights_after': {groups[g]: round(float(hw[g]), 3) for g in np.nonzero(hw > 0)[0]}}

# the tendril: rigid with its mirror twin
seed = int(pieces2[np.argmin([(co[i] - TENDRIL_AT).length for i in pieces2])])
tendril = sorted(connected(seed))
cen = sum((co[i] for i in tendril), Vector()) / len(tendril)
assert (cen - TENDRIL_AT).length < 0.02, cen
twin_at = Vector((-cen.x, cen.y, cen.z))
seed = int(pieces2[np.argmin([(co[i] - twin_at).length for i in pieces2])])
twin = sorted(connected(seed))
tw = W[twin[0]]
assert all(np.allclose(W[i], tw, atol=1e-4) for i in twin), 'the twin is rigid'
twin_cen = sum((co[i] for i in twin), Vector()) / len(twin)
assert (twin_cen - twin_at).length < 0.02, twin_cen
for i in tendril:
    newW[i] = tw
report['tendril'] = {'vertices': len(tendril), 'centre': [round(x, 4) for x in cen], 'twin_vertices': len(twin),
                     'weights_after': {groups[g]: round(float(tw[g]), 3) for g in np.nonzero(tw > 0)[0]}}

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
if uv_final:
    assert [l.vertex_index for l in me.loops] == uv_corners, 'the UV blend has another topology'
    me.uv_layers['UVMap'].data.foreach_set('uv', uv_final)
me.update()
report['changed_weights'] = int((np.abs(newW - W) > 1e-4).any(1).sum())
report['moved_vertices'] = int(sum((newco[i] - co[i]).length > 1e-7 for i in range(n)))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(report, open(REP, 'w'), indent=1)
print('ROOTS ' + json.dumps(report))
