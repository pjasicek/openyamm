"""Tunic skirt: the outside alone (user review 2026-10-14 (3): dark and light shards on the front of the robe in the
library Attack and Walking). Smart Topology made the skirt two-sided: an outer surface and an inward-facing lining
3-8 mm behind it (SkirtF 132 of 328 faces, SkirtB 98 of 230), each weighted by its own distance to the legs, so a
stepping leg pushed the lining through the outside, and the walk folds the panel's edges over (the source skinning,
unreduced too), where the lining showed as light or dark shards. The lining faces are removed at export
(export_runtime.py; the body material is double-sided, so the outside shows its own back from inside).
Here: the sides are fold components (faces joined across edges whose normals agree within FOLD) labelled by their
area-weighted vote of normal against the radial direction from the body axis; the outside's weights are smoothed a
little; the lining vertices (some stay on the hem rim) take their nearest outer point's weights (barycentric blend,
top 4) without moving; any other vertex under the outside (the waist and hips below the belt) blends toward those
weights by depth (UNDER_FULL..UNDER_MAX) and sits at least MIN_THICK inside.
`apply(mesh_obj, skirt, inner, deform)` works on any skinned mesh (the reduction's candidates use it with labels taken
from the master). Master: -- <blend in work/> (in place, after shell_weights.py); writes work/skirt_sides.json and
work/skirt_faces.npz (rest centroids, normals, labels, triangles)."""
import bpy, bmesh, sys, os, json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform

FOLD, MAX_DIST = 0.85, 0.05
MIN_THICK = float(os.environ.get("SKIRT_MIN_THICK", 0.008))
# anything else under the outside (the waist and hips below the belt, lining the reduction's labels missed) within
# UNDER_FULL takes the outside's weights fully, fading to its own at UNDER_MAX; lower legs keep theirs
UNDER_FULL, UNDER_MAX = 0.012, 0.03
# the outside's weights are smoothed first (SMOOTH rounds of half toward the neighbours' mean; vertices on faces other
# than the skirt stay fixed): the reduced front panel went from 86 % right thigh to half-and-half between neighbouring
# corners
SMOOTH = int(os.environ.get('SKIRT_SMOOTH', 6))
OWN_BONES = ('LeftLeg', 'RightLeg', 'LeftFoot', 'RightFoot', 'LeftToeBase', 'RightToeBase')
SKIRT = {'SkirtF', 'SkirtB'}
AXIS_Y = -0.03                  # body axis (x = 0, y = AXIS_Y): the radial direction is measured from it


INSIDE_OFFSET = 0.004


def add_inside(bm, faces, uv_layer, uv):
    """the skirt's inside as an exact copy of its outside: each copied vertex keeps its twin's weights (bmesh duplicate
    carries the deform layer) and sits INSIDE_OFFSET behind it along the outside's vertex normal, so the inside
    follows the outside exactly under any pose (the Meshy lining, weighted on its own, crossed it as shards); faces
    flipped, every corner on the flat inside swatch (uv). Returns the new faces."""
    fset = set(faces)
    normal = {}
    for f in faces:
        for v in f.verts:
            normal[v] = normal.get(v, Vector()) + f.normal * f.calc_area()
    out = bmesh.ops.duplicate(bm, geom=list(faces))
    vmap = out['vert_map']
    for v, n in normal.items():
        vmap[v].co = v.co - n.normalized() * INSIDE_OFFSET
    new = [g for g in out['geom'] if isinstance(g, bmesh.types.BMFace)]
    bmesh.ops.reverse_faces(bm, faces=new)
    for f in new:
        for l in f.loops:
            l[uv_layer].uv = uv
    return new


def sides(me, skirt):
    """inner polygon indices among `skirt` (fold components voted by normal against the radial direction)"""
    bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
    sk = set(skirt); comp = {}
    for f0 in skirt:
        if f0 in comp:
            continue
        stack, cid = [f0], len(set(comp.values()))
        comp[f0] = cid
        while stack:
            f = bm.faces[stack.pop()]
            for e in f.edges:
                for g in e.link_faces:
                    if g.index in sk and g.index not in comp and g.normal.dot(f.normal) > FOLD:
                        comp[g.index] = cid; stack.append(g.index)
    vote = {}
    for i in skirt:
        f = bm.faces[i]; c = f.calc_center_median()
        rad = Vector((c.x, c.y - AXIS_Y, 0.0)).normalized()
        vote[comp[i]] = vote.get(comp[i], 0.0) + f.calc_area() * (1 if f.normal.dot(rad) > 0 else -1)
    bm.free()
    return sorted(i for i in skirt if vote[comp[i]] < 0)


def smooth_outer(mesh, skirt, inner, ovset, names, deform):
    me = mesh.data
    fixed = {v for p in me.polygons if p.index not in skirt for v in p.vertices}
    free = sorted(ovset - fixed)
    nbr = {v: set() for v in free}
    for e in me.edges:
        a, b = e.vertices
        if a in nbr and b in ovset:
            nbr[a].add(b)
        if b in nbr and a in ovset:
            nbr[b].add(a)
    W = {v: {names[g.group]: g.weight for g in me.vertices[v].groups if names[g.group] in deform} for v in ovset}
    for _ in range(SMOOTH):
        nxt = {}
        for v in free:
            if not nbr[v]:
                continue
            acc = {n: 0.5 * x for n, x in W[v].items()}
            for u in nbr[v]:
                for n, x in W[u].items():
                    acc[n] = acc.get(n, 0.0) + 0.5 * x / len(nbr[v])
            top = sorted(acc.items(), key=lambda x: -x[1])[:4]; s = sum(x for _, x in top)
            nxt[v] = {n: x / s for n, x in top}
        W.update(nxt)
    for v in free:
        for g in list(me.vertices[v].groups):
            if names[g.group] in deform:
                mesh.vertex_groups[g.group].remove([v])
        for n, x in W[v].items():
            mesh.vertex_groups[n].add([v], x, 'REPLACE')
    return len(free)


def apply(mesh, skirt, inner, deform):
    me = mesh.data; me.calc_loop_triangles()
    inner = set(inner)
    otris = [t for t in me.loop_triangles if t.polygon_index in skirt and t.polygon_index not in inner]
    ovset = {v for t in otris for v in t.vertices}
    lining = {v for p in me.polygons if p.index in inner for v in p.vertices} - ovset
    iverts = sorted(set(range(len(me.vertices))) - ovset)
    R = [v.co.copy() for v in me.vertices]
    tree = BVHTree.FromPolygons(R, [tuple(t.vertices) for t in otris])
    names = {g.index: g.name for g in mesh.vertex_groups}
    smoothed = smooth_outer(mesh, skirt, inner, ovset, names, deform)
    new, moved, gaps, under = {}, 0, [], 0

    def own(v):
        return {names[g.group]: g.weight for g in me.vertices[v].groups if names[g.group] in deform and g.weight > 0}

    for v in iverts:
        loc, _, fi, dist = tree.find_nearest(R[v])
        if fi is None or dist > (MAX_DIST if v in lining else UNDER_MAX):
            continue
        a, b, c = otris[fi].vertices
        normal = (R[b] - R[a]).cross(R[c] - R[a]).normalized()
        offset = (R[v] - loc).dot(normal)
        w = barycentric_transform(loc, R[a], R[b], R[c], Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)))
        if v in lining:
            k = 1.0; gaps.append(-offset)
        else:
            mine = own(v)
            if offset > 0 or min(w) < -0.05 or not mine or max(mine, key=mine.get) in OWN_BONES:
                continue                                  # in front of the outside, beside it, or a lower leg
            k = min(1.0, max(0.0, (UNDER_MAX + offset) / (UNDER_MAX - UNDER_FULL)))
            if k <= 0:
                continue
            under += 1
        if v not in lining and offset > -MIN_THICK:      # the lining faces are removed at export; its vertices left
            me.vertices[v].co = R[v] + normal * (-MIN_THICK - offset); moved += 1   # on the hem rim stay put
        acc = {}
        for corner, share in zip((a, b, c), (max(w.x, 0), max(w.y, 0), max(w.z, 0))):
            for g in me.vertices[corner].groups:
                n = names[g.group]
                if n in deform and g.weight > 0:
                    acc[n] = acc.get(n, 0.0) + share * g.weight
        if k < 1.0:
            acc = {n: k * x for n, x in acc.items()}
            for n, x in own(v).items():
                acc[n] = acc.get(n, 0.0) + (1 - k) * x
        top = sorted(acc.items(), key=lambda x: -x[1])[:4]; s = sum(x for _, x in top)
        if s > 0:
            new[v] = {n: x / s for n, x in top}
    for v, ws in new.items():
        for g in list(me.vertices[v].groups):
            if names[g.group] in deform:
                mesh.vertex_groups[g.group].remove([v])
        for n, x in ws.items():
            mesh.vertex_groups[n].add([v], x, 'REPLACE')
    me.update()
    gaps.sort()
    return dict(smoothed_outside=smoothed, lining_vertices=len(lining), under_vertices=under, reweighted=len(new), moved=moved,
                gap_mm_p10_50_90=[round(gaps[int(len(gaps) * q)] * 1000, 1) for q in (0.1, 0.5, 0.9)] if gaps else [])


if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common
    path = os.path.join(common.WORK, sys.argv[sys.argv.index('--') + 1])
    bpy.ops.wm.open_mainfile(filepath=path)
    arm = bpy.data.objects['Cleric_Rig']; mesh = bpy.data.objects['Cleric']; me = mesh.data
    REG = json.loads(bpy.context.scene['cle_uv_regions'])
    ureg = [0] * len(me.polygons); me.attributes['uv_region'].data.foreach_get('value', ureg)
    skirt = sorted(p.index for p in me.polygons if REG[ureg[p.index]] in SKIRT)
    inner = sides(me, skirt)
    uvl = me.uv_layers['UVMap'].data
    inner_uv = [[tuple(uvl[l].uv) for l in me.polygons[i].loop_indices] for i in inner]
    json.dump({'skirt': skirt, 'inner': inner, 'inner_uv': inner_uv},
              open(os.path.join(common.WORK, 'skirt_sides.json'), 'w'))
    # rest face centroids, normals and labels (0 not skirt, 1 outside, 2 lining) for labelling reduced candidates
    import numpy as np
    lab = np.zeros(len(me.polygons), np.int8); lab[skirt] = 1; lab[inner] = 2
    me.calc_loop_triangles()
    np.savez(os.path.join(common.WORK, 'skirt_faces.npz'), cen=np.array([p.center[:] for p in me.polygons]),
             nrm=np.array([p.normal[:] for p in me.polygons]), label=lab,
             verts=np.array([v.co[:] for v in me.vertices]),
             tris=np.array([t.vertices[:] for t in me.loop_triangles]),
             tri_poly=np.array([t.polygon_index for t in me.loop_triangles]))
    rep = apply(mesh, set(skirt), inner, {b.name for b in arm.data.bones if b.use_deform})
    print('SKIRT_SHELL', len(skirt), 'skirt faces,', len(inner), 'lining', json.dumps(rep))
    bpy.ops.wm.save_mainfile(filepath=path)
