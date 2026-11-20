"""Close the see-through hole in the chest under the necklace (h65 review: "2 stray tris on his pecs" were the inside of
his back seen through it). The Codex Smart Topology mesh never had skin there; the fused pendants hid it, and the
installed model has the same hole (hole_probe.py). Every closed boundary loop bordered only by skin faces, with at
least MIN_EDGES edges (the mouth is in the head set and is skipped), is filled with a fan from a new centre vertex (the loop's
average weights), every triangle facing away from the body axis, labelled skin (fgarment/fpiece of the neighbours),
and each triangle takes the UV triangle of a plain open-chest neighbour below the hole (real skin texture). HeadUV is parked in the corner as for every body face. Run after transfer_uv.py, before uv_raster.py.
Args: -- <blend in> <blend out>"""
import bpy, bmesh, sys, os
from mathutils import Vector
src, out = sys.argv[sys.argv.index('--') + 1:][:2]
MIN_EDGES = 5
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
me = bpy.data.objects['Body'].data
bm = bmesh.new(); bm.from_mesh(me)
fgl = bm.faces.layers.int['fgarment']; fpl = bm.faces.layers.int['fpiece']; hdl = bm.faces.layers.int['head']
uvl = bm.loops.layers.uv['UVMap']; hul = bm.loops.layers.uv['HeadUV']
bnd = [e for e in bm.edges if len(e.link_faces) == 1 and e.link_faces[0][fgl] == 0 and not e.link_faces[0][hdl]]
left = set(bnd); loops = []
while left:
    e = left.pop(); comp = {e}; stack = [e]
    while stack:
        x = stack.pop()
        for v in x.verts:
            for y in v.link_edges:
                if y in left:
                    left.discard(y); comp.add(y); stack.append(y)
    vs = {v for x in comp for v in x.verts}
    if len(comp) >= MIN_EDGES and all(sum(1 for x in comp if v in x.verts) == 2 for v in vs):
        loops.append(comp)
filled = 0
for comp in loops:
    nbr = [e.link_faces[0] for e in comp]
    # outward = away from the body axis (the neighbours around a fold have mixed normals: the first fill faced inward)
    cen = sum((v.co for e in comp for v in e.verts), Vector()) / (2 * len(comp))
    n_ref = Vector((cen.x, cen.y + 0.05, 0)).normalized()
    # a fan from a new centre vertex (the loop is not planar: a plain fill folded one triangle backwards), each
    # triangle turned outward; the centre takes the loop's average weights
    order = [next(iter(next(iter(comp)).verts))]
    while len(order) < len(comp):
        nxt = [w for e in comp if order[-1] in e.verts for w in e.verts if w is not order[-1] and w not in order]
        if not nxt: break
        order.append(nxt[0])
    dl = bm.verts.layers.deform.active
    c = bm.verts.new(cen)
    acc = {}
    for v in order:
        for g, w in v[dl].items(): acc[g] = acc.get(g, 0) + w / len(order)
    for g, w in acc.items(): c[dl][g] = w
    tri = []
    for i in range(len(order)):
        f = bm.faces.new((c, order[i], order[(i + 1) % len(order)])); f.normal_update()
        if f.normal.dot(n_ref) < 0: f.normal_flip()
        tri.append(f)
    # UVs: a plain open-chest face below the hole, its own UV triangle copied onto every fan triangle (real skin
    # texture; a single texel came out darker than the chest)
    ref = min((f for f in nbr if f.normal.dot(n_ref) > 0.7), key=lambda f: f.calc_center_median().z, default=nbr[0])
    ruv = [l[uvl].uv.copy() for l in ref.loops]
    for f in tri:
        f[fgl] = ref[fgl]; f[fpl] = ref[fpl]; f[hdl] = 0; f.smooth = True
        for l, uv in zip(f.loops, ruv):
            l[uvl].uv = uv; l[hul].uv = (0.9995, 0.9995)
    filled += len(tri)
    c = sum((v.co for e in comp for v in e.verts), Vector()) / (2 * len(comp))
    print('FILL loop', len(comp), 'edges at', tuple(round(x, 3) for x in c), '->', len(tri), 'triangles')
bm.to_mesh(me); bm.free()
print('FILLED', len(loops), 'holes,', filled, 'triangles; body triangles', sum(len(p.vertices) - 2 for p in me.polygons))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
