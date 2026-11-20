"""Mirror symmetry about MM9's symmetry plane x = 0 (rework 2026-10-30; after ../mm9_icky_claude/scripts/fit_icky.py d.).

The MM9 harpy is exactly symmetric; the Meshy body was not (median 1.2 %, p90 3.2 %, max 7.9 % of the model size:
the tail meanders up to 4.4 cm off the plane, hair strands and small hair pieces on one side only, the wings and
legs fitted differently). On the rigged, UV-mapped body (weights and UVs kept):
1. Tail: its centre line (the mid x of the tail vertices per 2.5 cm of length, smoothed) is moved onto x = 0, weighted
   by the vertex's Xtail* weight, faded in from the tail root.
2. Keep side (config KEEP = +1: the +x half, the creature's left; it fits the MM9 surface closer: wing 3.6 vs 3.9 cm,
   leg 2.2 vs 2.5 cm, and has the front hair strands): separate pieces lying wholly on the other side are dropped,
   the rest is bisected at x = 0 and the other half deleted.
3. The kept half is duplicated, mirrored, its faces reversed and its weights moved to the mirror bones (the MM9
   bones mirrored by rest position: Ywing*01 <-> Ywing*, Bip01 L <-> R, Xhairrit <-> Xhairleft, foot claws).
   UVs are copied, so both halves share the kept half's texels (the engine's derivative tangent frame handles the
   mirrored normal map).
4. Seam vertices on the plane are welded; their weights are the average of their own and their mirror bones', so the
   centre line deforms symmetrically.
Args: -- <in blend> <out blend> <report json> [keep_side +1|-1]"""
import bpy, bmesh, sys, json
import numpy as np

a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP = a[:3]
KEEP = int(a[3]) if len(a) > 3 else 1
EPS = 1e-6
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']
rig = body.parent
me = body.data
rep = {'keep_side': KEEP}

# --- bone mirror map (by mirrored rest head position)
B = {b.name: np.array(b.head_local) for b in rig.data.bones}
bmap = {}
for n, h in B.items():
    hm = h * [-1, 1, 1]
    best = min(B, key=lambda k: np.linalg.norm(B[k] - hm))
    bmap[n] = best if np.linalg.norm(B[best] - hm) < 0.01 else n
gidx = {g.name: g.index for g in body.vertex_groups}
for n in set(bmap.values()):
    if n not in gidx:
        gidx[n] = body.vertex_groups.new(name=n).index
gname = {i: n for n, i in gidx.items()}
gmap = {gidx[n]: gidx[bmap.get(n, n)] for n in gidx}
rep['mirror_pairs'] = sorted({tuple(sorted((k, v))) for k, v in bmap.items() if k != v})

bm = bmesh.new()
bm.from_mesh(me)
bm.verts.ensure_lookup_table()
dl = bm.verts.layers.deform.active


def weight_of(v, pred):
    return sum(w for g, w in v[dl].items() if pred(gname[g]))


# --- 1. tail centre line onto the plane
tail = [(v, weight_of(v, lambda n: n.startswith('Xtail'))) for v in bm.verts]
tail = [(v, w) for v, w in tail if w > 0.02]
T = np.array([tuple(v.co) for v, w in tail if w > 0.5])
y0 = B['XtailA'][1]                     # fade-in from the root (the pelvis vertices on Xtailbase stay)
bins = np.arange(T[:, 1].min() - 0.025, T[:, 1].max() + 0.05, 0.05)
cy, cx = [], []
for lo in bins:
    s = T[(T[:, 1] >= lo) & (T[:, 1] < lo + 0.05)]
    if len(s) >= 2:
        cy.append(lo + 0.025); cx.append((s[:, 0].min() + s[:, 0].max()) / 2)
cy, cx = np.array(cy), np.array(cx)
cxs = np.array([np.average(cx, weights=np.exp(-((cy - y) / 0.06) ** 2)) for y in cy])
moved = 0
for v, w in tail:
    fade = np.clip((v.co.y - y0 + 0.1) / 0.1, 0, 1)
    v.co.x -= w * fade * float(np.interp(v.co.y, cy, cxs))
    moved += 1
rep['tail_centre_offset_cm'] = [round(float(x) * 100, 2) for x in cxs]
rep['tail_verts_moved'] = moved

# --- 2. drop pieces wholly on the other side, bisect, delete the other half
comp = {}
for v in bm.verts:
    if v in comp:
        continue
    st, c = [v], len(set(comp.values()))
    comp[v] = c
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if y not in comp:
                comp[y] = c; st.append(y)
pieces = {}
for v, c in comp.items():
    pieces.setdefault(c, []).append(v)
drop = []
for c, vs in pieces.items():
    xs = np.array([v.co.x for v in vs]) * KEEP
    if xs.max() < 0.002:
        drop += vs
rep['dropped_pieces'] = [len(vs) for c, vs in pieces.items() if (np.array([v.co.x for v in vs]) * KEEP).max() < 0.002]
bmesh.ops.delete(bm, geom=drop, context='VERTS')
geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-5, plane_co=(0, 0, 0), plane_no=(-KEEP, 0, 0), clear_outer=True)
for v in bm.verts:
    if abs(v.co.x) < 1e-4:          # bisect twins land within 0.1 mm of the plane
        v.co.x = 0.0
bm.verts.ensure_lookup_table()

# --- 3. mirror the kept half
half_v = list(bm.verts)
half_f = list(bm.faces)
half_e = list(bm.edges)
dup = bmesh.ops.duplicate(bm, geom=half_v + half_e + half_f)
nv = [g for g in dup['geom'] if isinstance(g, bmesh.types.BMVert)]
nf = [g for g in dup['geom'] if isinstance(g, bmesh.types.BMFace)]
for v in nv:
    v.co.x = -v.co.x
    old = dict(v[dl].items())
    v[dl].clear()
    for g, w in old.items():
        v[dl][gmap.get(g, g)] = v[dl].get(gmap.get(g, g), 0) + w
bmesh.ops.reverse_faces(bm, faces=nf)

# --- 4. weld the seam, symmetric seam weights
seam = [v for v in bm.verts if v.co.x == 0.0]
bmesh.ops.remove_doubles(bm, verts=seam, dist=1e-4)     # bisect twins 0.04 mm apart are welded too
nseam = 0
for v in bm.verts:
    if v.co.x == 0.0:
        old = dict(v[dl].items())
        v[dl].clear()
        for g, w in old.items():
            for gg in (g, gmap.get(g, g)):
                v[dl][gg] = v[dl].get(gg, 0) + 0.5 * w
        nseam += 1
rep['seam_verts'] = nseam
rep['boundary_edges'] = sum(1 for e in bm.edges if e.is_boundary)
rep['nonmanifold_edges'] = sum(1 for e in bm.edges if len(e.link_faces) > 2)
bm.to_mesh(me)
bm.free()
for p in me.polygons:
    p.use_smooth = True
# 'side' attribute (rig_mm9.py input) follows the new x
if 'side' in me.attributes:
    s = me.attributes['side']
    for i, v in enumerate(me.vertices):
        s.data[i].value = int(np.sign(round(v.co.x, 4)))
rep['verts'] = len(me.vertices)
rep['tris'] = sum(len(p.vertices) - 2 for p in me.polygons)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1, default=str)
print('SYMMETRIZED', json.dumps({k: v for k, v in rep.items() if k != 'mirror_pairs'}))
