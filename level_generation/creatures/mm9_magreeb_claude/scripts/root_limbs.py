"""Root the Magreeb's legs in the body and tie the +X upper arm to its shoulder piece (2026-10-30, after the
detached-parts audit, claude_shared/detached_parts_mm9.md; adapted from mm9_eye_claude/scripts/root_limbs.py).

Args: <in blend (uv_v7)> <out blend> <report json>

Why: fit_magreeb.py maps every separate Meshy leg piece onto its MM9 chain from the chain's root joint, and two MM9
leg roots (Bone114, Bone61) lie outside our HD body shell, so those legs stopped 4.7 and 1.6 cm short of it at bind.
The +X arm is three separate pieces; the upper arm (Bone21) touches the shoulder piece (Bone38) at bind but is
weighted differently where they meet, so it pulls 2.1 cm away in Death.

Legs (every leg; one whose cap is already ROOTED_OK deep is left alone): the root bone's axis (J0 -> J1) cast back
from J0 hits the body after h; the first segment (root cap to J1) is stretched along that axis so the cap ends DEPTH
(3 cm) inside the shell. J1 and the rest of the leg stay; vertices move only along the axis.
Weights of the extension (in front of J0) blend from the leg's own to the body's at the hit point, fully the body's
just inside the shell, so the buried root follows the body surface it enters.
Arm pieces (JOINS: piece by dominant bone): the same stretch along the piece's own root bone into the pieces around it
(shoulder piece and body), taking their weights where it enters; when the piece already reaches past the entry (a
sideways gap, as Bone21), its vertices within REACH of the other pieces take their weights
at the nearest point instead (fully from REACH / 3 in), so the junction moves as one.
Topology and UVs are unchanged; this runs before the texture pass UVs (uv_atlas_v8.py), so nothing is re-textured.
"""
import bpy, sys, os, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mag_cfg as C

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP = argv
DEPTH = 0.03          # cap depth inside the shell
ROOTED_OK = 0.01      # a leg whose cap is already this deep is left alone
REACH = 0.06          # sideways joins: weight blend distance
JOINS = {'Bone21': ('Bone38', 'Bone22')}   # +X upper-arm piece: (shoulder bone, its next joint); -X passes


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
W = np.zeros((n, len(groups)))
for v in me.vertices:
    for g in v.groups:
        W[v.index, g.group] = g.weight

# connected components
parent = list(range(n))


def find(i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]
        i = parent[i]
    return i


for e in me.edges:
    a, b = find(e.vertices[0]), find(e.vertices[1])
    if a != b:
        parent[a] = b
comp = np.array([find(i) for i in range(n)])

core = (chain == -1) & (piece == 0)
polys = [p.vertices[:] for p in me.polygons if all(core[i] for i in p.vertices)]
bvh = BVHTree.FromPolygons(co, polys)
J = {b.name: arm.matrix_world @ b.head_local for b in arm.data.bones}
report = {'legs': {}, 'joins': {}}
newco = list(co)
newW = W.copy()


def barycentric_weights(tri, p, verts):
    A, B, Cc = (verts[i] for i in tri)
    v0, v1, v2 = B - A, Cc - A, p - A
    d00, d01, d11, d20, d21 = v0.dot(v0), v0.dot(v1), v1.dot(v1), v2.dot(v0), v2.dot(v1)
    den = d00 * d11 - d01 * d01
    bv = (d11 * d20 - d01 * d21) / den
    bw = (d00 * d21 - d01 * d20) / den
    bary = (1 - bv - bw, bv, bw)
    return sum(bary[m] * W[tri[m]] for m in range(3))


def root(ids, j0, j1, tbvh, tpolys):
    """Stretch the piece's first segment (root cap to j1) back along j0 -> j1 until the cap is DEPTH inside the target
    surface; the extension takes the target's weights where it enters. Returns the report entry."""
    L1 = (j1 - j0).length
    a = (j1 - j0) / L1
    s = np.array([(co[i] - j0).dot(a) for i in ids])
    r = np.array([((co[i] - j0) - a * si).length for si, i in zip(s, ids)])
    first = (s < L1) & (r < 0.12)
    s_min = float(s[first].min())
    radius = float(np.median(r[first & (s > 0) & (s < 0.15)])) if (first & (s > 0) & (s < 0.15)).any() else 0.0
    cap = ids[first & (s < s_min + 0.02)]
    rooted = 0.0                                    # how deep the cap already is inside the target
    for i in cap:
        loc, nrm, _, d = tbvh.find_nearest(co[i])
        if (co[i] - loc).dot(nrm) < 0:
            rooted = max(rooted, d)
    loc, nrm, fi, h = tbvh.ray_cast(j0, -a, 1.0)
    if loc is None or rooted >= ROOTED_OK:
        return {'rooted_depth': round(rooted, 4), 'changed': False}
    s0 = -(h + DEPTH)
    stretch = (L1 - s0) / (L1 - s_min)
    if stretch <= 1.0:                              # the cap already reaches past the entry: the gap is sideways
        return {'rooted_depth': round(rooted, 4), 'changed': False, 'gap_along_axis': round(h, 4),
                'stretch_needed': round(stretch, 3)}
    Wb = barycentric_weights(tpolys[fi], loc, co)
    moved = 0
    for si, i, f in zip(s, ids, first):
        if not f:
            continue
        sn = s0 + (si - s_min) * stretch
        newco[i] = co[i] + a * (sn - si)
        moved += 1
        if sn < 0:
            t = smooth(-sn / (h + 0.5 * DEPTH))
            newW[i] = (1 - t) * W[i] + t * Wb
    return {'rooted_depth': round(rooted, 4), 'changed': True, 'gap_along_axis': round(h, 4), 'depth': DEPTH,
            'rod_radius': round(radius, 4), 'first_segment': round(L1, 4), 'stretch': round(stretch, 3),
            'moved': moved, 'target_weights': {groups[g]: round(float(Wb[g]), 3) for g in np.nonzero(Wb > 0.01)[0]}}


for k, ch in enumerate(C.LEGS):
    ids = np.nonzero((chain == k) & (piece == 0))[0]
    report['legs'][ch[0]] = root(ids, J[ch[0]], J[ch[1]], bvh, polys)


def dominant_component(bone):
    g = gidx[bone]
    best = None
    for c in np.unique(comp):
        m = comp == c
        share = W[m, g].mean()
        if W[m].sum(0).argmax() == g and (best is None or share > best[1]):
            best = (c, share)
    return best[0]


for child_bone, (parent_bone, next_bone) in JOINS.items():
    cc = dominant_component(child_bone)
    # the piece touches the shoulder piece and the body: its target is every other piece
    ppolys = [p.vertices[:] for p in me.polygons if comp[p.vertices[0]] != cc]
    pbvh = BVHTree.FromPolygons(co, ppolys)
    ids = np.nonzero(comp == cc)[0]
    entry = {'parent_piece_bone': parent_bone, **root(ids, J[child_bone], J[next_bone], pbvh, ppolys)}
    if not entry['changed']:
        # sideways gap (Bone21 sits beside the shoulder piece): its vertices near the parent take the parent's weights
        # at the nearest point (fully within REACH / 3, fading out at REACH), so the junction moves as one
        blended = 0
        for i in ids:
            loc, nrm, fi, d = pbvh.find_nearest(co[i])
            inside = (co[i] - loc).dot(nrm) < 0
            t = 1.0 if inside else smooth((REACH - d) / (REACH * 2 / 3))
            if t > 0:
                newW[i] = (1 - t) * newW[i] + t * barycentric_weights(ppolys[fi], loc, co)
                blended += 1
        entry['blended_to_parent'] = blended
    report['joins'][child_bone] = entry

for i in range(n):                                  # at most four influences, normalised
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
me.update()
report['changed_weights'] = int((np.abs(newW - W) > 1e-4).any(1).sum())
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(report, open(REP, 'w'), indent=1)
print('ROOTS ' + json.dumps(report))
