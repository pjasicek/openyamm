"""Step 0 cleanup of the Vampire Smart Topology return (work/st_v1_parts.blend, loose parts P00..P26, 1.7 m, faces -Y),
before prepare_rig.py. Writes work/st_v1_clean.blend.
- P26 (one stray triangle) is deleted.
- Two thin sticks hang from the mouth (P01) and the neck ornament (P10) down to one point on the chest (Smart Topology
  artefact): every long sliver triangle of those parts (longest edge > 4 cm with shortest/longest < 0.2, or any edge > 12 cm) is deleted, then
  loose vertices, and each part keeps only its largest connected piece.
- The coat (P00) is ONE shell with the cape and the collar. Per-vertex piece override 'piece_ov' (read by prepare_rig):
  the cape = the connected component behind the body when the shell is cut below CAPE_TOP (it stays separate from the
  coat up to the shoulders) -> piece 27; everything above CAPE_TOP (the stand-up collar round the neck) -> piece 28;
  the coat's torso component below WAIST (the skirt) -> piece 29; the rest (coat top and sleeves) stays piece 0.
Args: none"""
import bpy, bmesh, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common, cfg
CAPE_TOP = float(cfg.C.get('cape_top_z', 1.40))
WAIST = float(cfg.C.get('skirt_top_z', 0.95))
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'st_v1_parts.blend'))
P = {o.name: o for o in bpy.data.objects if o.type == 'MESH'}
bpy.data.objects.remove(P.pop('P26'), do_unlink=True)


def components(n, tri, keep):
    e = np.vstack([tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]])
    e = e[keep[e[:, 0]] & keep[e[:, 1]]]
    par = np.arange(n)

    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]; x = par[x]
        return x
    for a, b in e:
        ra, rb = find(a), find(b)
        if ra != rb:
            par[ra] = rb
    return np.array([find(i) for i in range(n)])


TIPS = []
for name in ('P01', 'P10'):
    o = P[name]; bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bad = []
    for f in bm.faces:
        L = [e.calc_length() for e in f.edges]
        if (max(L) > 0.04 and min(L) / max(L) < 0.2) or max(L) > 0.12:     # no real head/ornament edge exceeds 7 cm
            bad.append(f)
    bmesh.ops.delete(bm, geom=bad, context='FACES_ONLY')
    loose = [v for v in bm.verts if not v.link_faces]
    TIPS.extend(tuple(v.co) for v in loose)
    bmesh.ops.delete(bm, geom=loose, context='VERTS')
    bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    tri = np.array([[v.index for v in f.verts] for f in bm.faces])
    lab = components(len(bm.verts), tri, np.ones(len(bm.verts), bool))
    big = np.bincount(lab).argmax()
    small = [v for v in bm.verts if lab[v.index] != big]
    bmesh.ops.delete(bm, geom=small, context='VERTS')
    print('CLEAN', name, 'slivers', len(bad), 'loose', len(loose), 'other pieces verts', len(small), 'left', len(bm.verts))
    bm.to_mesh(o.data); bm.free(); o.data.update()
# the same stick ends in the coat shell too: a fan of long triangles from the stick's tip vertices (inside the chest,
# 8-10 cm behind the surface) to the belt and the collar (user review 1). Moving the tips onto the surface (first fix)
# made spikes above the belt sides. The fan is an internal structure: its faces are deleted (faces touching a tip
# vertex with an edge > 12 cm), then loose vertices; the holes this opens in the chest surface (the fan was partly the
# surface beside the ornament: a see-through gap above the belt) are filled like the cape's below.
o = P['P00']; bm = bmesh.new(); bm.from_mesh(o.data)
tips = np.array(TIPS) if TIPS else np.zeros((0, 3))
near = [v for v in bm.verts if len(tips) and np.min(np.linalg.norm(tips - np.array(v.co), axis=1)) < 0.005
        and max(e.calc_length() for e in v.link_edges) > 0.12]
nb0 = sum(1 for e in bm.edges if e.is_boundary)
fan = list({f for v in near for f in v.link_faces})
FAN_BORDER = {tuple(round(c, 5) for c in v.co) for f in fan for v in f.verts if v not in near}
bmesh.ops.delete(bm, geom=fan, context='FACES_ONLY')
lv = [v for v in bm.verts if not v.link_faces]; bmesh.ops.delete(bm, geom=lv, context='VERTS')
print('CLEAN P00 stick fan faces deleted', len(fan), 'loose verts', len(lv), 'boundary edges', nb0, '->', sum(1 for e in bm.edges if e.is_boundary))
bm.to_mesh(o.data); bm.free(); o.data.update()
# user review 1 (flat light patches on the walking coat front): the coat front below the chest has a hidden INNER
# layer (faces turned toward the body axis behind the outer surface, painted flat by Meshy). In the walk its faces
# came through the outer coat, and the double-sided viewer showed their flat paint (the engine culls them: holes).
# Hidden inner faces are deleted: P00 faces in front of the body (y < -0.05, |x| < 0.22) between INNER_Z whose normal points toward
# the body axis and whose outward radial ray meets an outward-facing coat face within 5 cm.
INNER_Z = (0.25, 1.12)
o = P['P00']; bm = bmesh.new(); bm.from_mesh(o.data); bm.faces.ensure_lookup_table()
from mathutils.bvhtree import BVHTree as _BVH
from mathutils import Vector as _V
tree = _BVH.FromBMesh(bm)
axis = _V((0.0, -0.10, 0.0))
dead = []
for f in bm.faces:
    c = f.calc_center_median()
    if not (INNER_Z[0] < c.z < INNER_Z[1]) or c.y > -0.05 or abs(c.x) > 0.22:
        continue
    r = _V((c.x - axis.x, c.y - axis.y, 0.0))
    if r.length < 1e-4 or f.normal.dot(r.normalized()) > -0.2:
        continue
    r.normalize(); h = tree.ray_cast(c + r * 0.002, r, 0.05)
    # covered by an OUTWARD-facing coat face (the outer surface), not by a sleeve or another fold
    if h[0] is not None and h[2] != f.index and h[1].dot(r) > 0.2 and bm.faces[h[2]].calc_center_median().y < -0.05:
        dead.append(f)
bmesh.ops.delete(bm, geom=dead, context='FACES_ONLY')
lv = [v for v in bm.verts if not v.link_faces]; bmesh.ops.delete(bm, geom=lv, context='VERTS')
print('CLEAN P00 hidden inner coat faces deleted', len(dead), 'loose verts', len(lv))
bm.to_mesh(o.data); bm.free(); o.data.update()
# the cape's INNER face (towards the coat back) is OPEN (Smart Topology never saw it): one 42-vertex hole at z 0.51-0.88
# and a small 4-vertex one beside it; through it the back-face-culled cape would turn see-through whenever its inside
# shows. Fill every boundary loop of the shell whose centre lies behind the body (y > 0.05) between FILL_Z with one
# n-gon (wound like its neighbours), triangulate, refine the patch (3 cuts per inner edge) and relax the new vertices
# with the border fixed. (The front loops behind the buckle, the ornament and the neckline stay open: covered.)
FILL_Z = (0.45, 0.92)
o = P['P00']; bm = bmesh.new(); bm.from_mesh(o.data)
bnd = [e for e in bm.edges if e.is_boundary]
loops, seen = [], set()
for e0 in bnd:
    if e0 in seen:
        continue
    st, comp = [e0], []
    while st:
        e = st.pop()
        if e in seen:
            continue
        seen.add(e); comp.append(e)
        st += [x for v in e.verts for x in v.link_edges if x.is_boundary and x not in seen]
    loops.append(comp)
nf = 0
for comp in loops:
    c = np.mean([v.co[:] for e in comp for v in e.verts], 0)
    fanloop = all(tuple(round(x, 5) for x in v.co) in FAN_BORDER for e in comp for v in e.verts)
    if (c[1] > 0.05 and FILL_Z[0] < c[2] < FILL_Z[1]) or fanloop:
        # order the loop (bmesh.ops.holes_fill created no face here) and make one n-gon, wound like its neighbours
        adj = {}
        for e in comp:
            a_, b_ = e.verts
            adj.setdefault(a_, []).append(b_); adj.setdefault(b_, []).append(a_)
        assert all(len(x) == 2 for x in adj.values()), 'boundary loop is not simple'
        start = comp[0].verts[0]; ring = [start]; prevv = None
        while True:
            nxt = [x for x in adj[ring[-1]] if x is not prevv][0]
            if nxt is start:
                break
            prevv = ring[-1]; ring.append(nxt)
        e0 = comp[0]; f0 = e0.link_faces[0]
        lv = list(f0.verts); i0 = lv.index(e0.verts[0])
        # the neighbour face runs v0 -> v1 along the shared edge iff v1 follows v0 in it; the new face must run opposite
        fwd = lv[(i0 + 1) % len(lv)] is e0.verts[1]
        if (ring[0] is e0.verts[0] and ring[1] is e0.verts[1]) == fwd:
            ring.reverse()
        new = [bm.faces.new(ring)]
        print('CLEAN hole faces', len(new), 'ring', len(ring))
        r = bmesh.ops.triangulate(bm, faces=new, quad_method='BEAUTY', ngon_method='BEAUTY')
        new = r['faces']
        nset = set(new)
        inner = list({e for f in new for e in f.edges if all(x in nset for x in e.link_faces)})
        print('CLEAN hole triangles', len(new), 'inner edges', len(inner))
        border = {v for e in comp for v in e.verts}
        r2 = bmesh.ops.subdivide_edges(bm, edges=inner, cuts=3, use_grid_fill=True)
        newv = list({v for g in (r2['geom_inner'], r2['geom_split']) for v in g if isinstance(v, bmesh.types.BMVert)} - border)
        for it in range(30):
            for v in newv:
                nb = [x.other_vert(v) for x in v.link_edges]
                v.co = v.co * 0.5 + sum((n.co for n in nb), v.co * 0) / len(nb) * 0.5
        bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3], quad_method='BEAUTY', ngon_method='BEAUTY')
        nf += 1
        print('CLEAN filled', 'stick-fan hole' if fanloop else 'cape inner hole', ': border verts', len(comp), 'centre', np.round(c, 3), 'new verts', len(newv))
bm.to_mesh(o.data); bm.free(); o.data.update()
# renumber nothing: part names stay P00..P25 (piece = part index), cape/collar/skirt by override
me = o.data
co = np.array([v.co[:] for v in me.vertices]); n = len(co)
me.calc_loop_triangles(); tri = np.array([t.vertices[:] for t in me.loop_triangles])
below = co[:, 2] < CAPE_TOP
lab = components(n, tri, below)
ov = np.zeros(n, np.int32)
comps = [c for c in np.unique(lab[below]) if (lab[below] == c).sum() > 50]
cape = max(comps, key=lambda c: co[(lab == c) & below, 1].mean())          # the component furthest behind (+Y)
assert co[(lab == cape) & below, 1].mean() > 0.1
ov[(lab == cape) & below] = 27
ov[~below] = 28
lab2 = components(n, tri, co[:, 2] < 1.15)
torso = [c for c in np.unique(lab2[co[:, 2] < 1.15]) if (np.abs(co[(lab2 == c) & (co[:, 2] < 1.15), 0]) < 0.05).any()
         and co[(lab2 == c) & (co[:, 2] < 1.15), 1].mean() < 0.05]
skirt = np.isin(lab2, torso) & (co[:, 2] < WAIST) & (ov == 0)
ov[skirt] = 29
o.data.attributes.new('piece_ov', 'INT', 'POINT').data.foreach_set('value', ov.tolist())
print('CLEAN coat split: cape', int((ov == 27).sum()), 'collar', int((ov == 28).sum()), 'skirt', int((ov == 29).sum()),
      'top+sleeves', int((ov == 0).sum()))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'st_v1_clean.blend'))
