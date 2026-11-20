"""Root the dorsal tail fins (2026-10-30 review: "fins are not attached to the tail"). Runs on the UV'd body after
uv_atlas_v2.py; it only translates the fin pieces, so the xatlas UVs and the 4K retexture stay valid.

Args: <uv blend> <out blend> <report json>

Meshy placed the row of fin plates along the top of the tail 7-20 cm above the tail surface (in the bind pose; the
detached-parts audit passed them because each plate touches the next and the first two touch the back). Each fin
piece (piece 2 behind the head) is moved straight down, each vertex by the base gap at its place along the tail, until
its whole base edge (the lowest vertex of every 2 cm slice
along the tail) sits EMBED inside the main body (the sail excluded): the depth is measured per slice by a ray down, so
the whole base length is covered, not only its nearest point. Spikes hanging sideways off a plate (further than SIDE_X
from the midline) are dropped first. Every fin vertex then takes the weights of its nearest body vertex, so the fin bends with the
tail skin under it. Fin faces entirely under the tail's top surface (buried, or a Meshy spike poking out below the
tail) are removed.
"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP = argv[:3]
SLICE, BAND, EMBED, HEAD_Y, SIDE_X = 0.02, 0.35, 0.03, -1.3, 0.07   # EMBED covers the tail bending in Hit
bpy.ops.wm.open_mainfile(filepath=IN)
ob = bpy.data.objects['Body']
bm = bmesh.new()
bm.from_mesh(ob.data)
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
bm.verts.index_update()
pl = bm.verts.layers.int['piece']
dl = bm.verts.layers.deform.active
# the main body component only (not the dorsal sail, which is a separate piece above the back)
cand = {f for f in bm.faces if all(v[pl] == 0 for v in f.verts)}
seen_f, comps_f = set(), []
for f in cand:
    if f in seen_f:
        continue
    st, cf = [f], [f]
    seen_f.add(f)
    while st:
        x = st.pop()
        for e in x.edges:
            for g in e.link_faces:
                if g in cand and g not in seen_f:
                    seen_f.add(g); st.append(g); cf.append(g)
    comps_f.append(cf)
body_faces = max(comps_f, key=len)
bvh = BVHTree.FromPolygons([v.co for v in bm.verts], [[v.index for v in f.verts] for f in body_faces])
skin = list({v for f in body_faces for v in f.verts})
kd = KDTree(len(skin))
for j, v in enumerate(skin):
    kd.insert(v.co, j)
kd.balance()


def depth_along(p, d):
    """How far p must move along d to sit on the body surface (0 when already inside)."""
    co, nrm, _, _ = bvh.find_nearest(p)
    if co is not None and (p - co).dot(nrm) < 0:
        return 0.0
    hit = bvh.ray_cast(p, d, 2.0)
    if hit[0] is not None:
        return (p - hit[0]).length
    return (p - co).length if co is not None else 0.0


def base_edge(comp):
    """The fin's base along its whole length: the lowest vertex of every SLICE-long slice along y, among the vertices in
    the lowest BAND of the fin's height (a raked tip overhanging the tail is not base)."""
    zs = [v.co.z for v in comp]
    zcut = min(zs) + BAND * (max(zs) - min(zs))
    slices = {}
    for v in comp:
        if v.co.z > zcut:
            continue                  # the raked tip overhangs the tail: not base
        k = int(v.co.y // SLICE)
        if k not in slices or v.co.z < slices[k].co.z:
            slices[k] = v
    return list(slices.values())


cx = float(np.median([v.co.x for f in body_faces for v in f.verts]))
seen, report = set(), []
for v0 in list(bm.verts):
    if not v0.is_valid or v0 in seen or v0[pl] != 2:
        continue
    comp, st = [v0], [v0]
    seen.add(v0)
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if y not in seen:
                seen.add(y); st.append(y); comp.append(y)
    c = sum((v.co for v in comp), Vector()) / len(comp)
    if c.y < HEAD_Y or c.z < 0.2:
        continue                      # teeth, eyes (head) and anything under the body
    # Meshy spikes hanging off a dorsal plate sideways (one plate had one through the tail's flank): drop them
    side = [v for v in comp if abs(v.co.x - cx) > SIDE_X]
    if not side or len(side) >= len(comp) // 2:
        side = []
    n_side = len(side)
    if side:
        bmesh.ops.delete(bm, geom=side, context='VERTS')
        comp = [v for v in comp if v.is_valid]
    d = Vector((0, 0, -1))
    base = base_edge(comp)
    gaps = [depth_along(v.co, d) for v in base]
    # each fin vertex moves down by the base gap at its position along the tail (interpolated between base slices):
    # the base follows the tail's curve instead of one end sinking deep while the other just touches
    order = sorted(range(len(base)), key=lambda i: base[i].co.y)
    by = [base[i].co.y for i in order]
    bg = [gaps[i] + EMBED if max(gaps) > 0.003 else 0.0 for i in order]
    for v in comp:
        v.co += d * float(np.interp(v.co.y, by, bg))
    move = max(bg)
    for v in comp:
        src = skin[kd.find(v.co)[1]]
        for g in list(v[dl].keys()):
            del v[dl][g]
        for g, w in src[dl].items():
            v[dl][g] = w
    report.append({'centre': [round(x, 3) for x in c], 'verts': len(comp), 'base_verts': len(base),
                   'side_spike_verts_removed': n_side,
                   'base_gap_min_med_max': [round(min(gaps), 3), round(float(np.median(gaps)), 3),
                                            round(max(gaps), 3)],
                   'moved': round(move, 3), 'direction': [round(x, 2) for x in d],
                   'after_max_base_gap': round(max(depth_along(v.co, d) for v in base), 4)})
# fin faces left entirely under the tail's top surface are buried or poke out below it (one plate carried a thin
# Meshy spike straight through the tail): remove them; the faces crossing the surface keep the base rooted
fin_faces = [f for f in bm.faces if all(v[pl] == 2 for v in f.verts)]
removed = []
for f in fin_faces:
    c = f.calc_center_median()
    if c.y < HEAD_Y:
        continue
    below = 0
    for v in f.verts:
        hit = bvh.ray_cast(Vector((v.co.x, v.co.y, 3.0)), Vector((0, 0, -1)), 6.0)
        below += hit[0] is not None and v.co.z < hit[0].z - 0.002
    if below == len(f.verts):
        removed.append(f)
bmesh.ops.delete(bm, geom=removed, context='FACES')
report.append({'buried_fin_faces_removed': len(removed)})
bm.to_mesh(ob.data)
bm.free()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump({'fins': report}, open(REP, 'w'), indent=1)
print('FINS ' + json.dumps(report))
