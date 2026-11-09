"""Inner twin of the tunic shell (see-through gate r1, 2026-11-02): with the waist and boot rims lined, the remaining holes
were the tunic shell itself, not a rim: in Cower the torso flank (rest height 1.18-1.22 m, x +-0.15-0.19) folds
inside-out where the arm presses in (231 px), and in Death frame 18 the view from the front passes the chest and meets
the inside of the upper back (168 px). PeasantDM2 covered the same area by lining its sleeve band from the cuff rim
(rim_lining.py); here the grafted hands close the cuffs, so there is no rim to start from.

Every face of the main body shell (the largest loose part of the body material: torso, sleeves, neck below the head
set) that is not head, hand or already lined gets a twin OFFSET behind itself along the vertex normal, flipped, with the
face's own UVs (an own-paint twin as rim_lining.py uses for inner-layer faces: where a pose pokes it through the outer
layer it shows cloth paint, not a dark blotch) and the same vertex weights (the twins move with the cloth); offsets are
capped at 40 % of the distance to other geometry behind within 2 cm. Face attribute `lined` = 1 on the twins.
Positions/faces only: existing faces, UVs and weights are unchanged, so the paid paints stay valid.
Second run (rank=2 zmin=-0.06): the skirt+breeches piece above the hem (Blender rest z > -0.06 m), where the view
entered at the waist in Death and on the corpse (r2: 47 / 23 px).
Args (Blender): <in blend> <out blend> [offset 0.0015] [rank=1] [zmin=-9]"""
import bpy, bmesh, sys, json
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT = a[0], a[1]
OFFSET = float(a[2]) if len(a) > 2 else 0.0015
OPT = dict(x.split('=', 1) for x in a[3:])
RANK, ZMIN = int(OPT.get('rank', 1)), float(OPT.get('zmin', -9))
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; me = body.data
bm = bmesh.new(); bm.from_mesh(me)
bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table()
lay = {n: bm.faces.layers.int.get(n) for n in ('head', 'hand', 'lined')}
if lay['lined'] is None:
    lay['lined'] = bm.faces.layers.int.new('lined')
# loose parts by vertex connectivity
comp = {}; cid = 0
for v in bm.verts:
    if v.index in comp:
        continue
    st = [v]; comp[v.index] = cid
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in comp:
                comp[y.index] = cid; st.append(y)
    cid += 1


def plain(f):
    return all(lay[k] is None or not f[lay[k]] for k in ('head', 'hand', 'lined'))


count = {}
for f in bm.faces:
    if plain(f):
        count[comp[f.verts[0].index]] = count.get(comp[f.verts[0].index], 0) + 1
main = sorted(count, key=count.get, reverse=True)[RANK - 1]
sel = [f for f in bm.faces if plain(f) and comp[f.verts[0].index] == main
       and f.calc_center_median().z > ZMIN]
tree = BVHTree.FromBMesh(bm)
ret = bmesh.ops.duplicate(bm, geom=sel)
new_faces = [g for g in ret['geom'] if isinstance(g, bmesh.types.BMFace)]
new_verts = [g for g in ret['geom'] if isinstance(g, bmesh.types.BMVert)]
vmap = ret['vert_map']
capped = 0
for nv in new_verts:
    ov = next((o for o, n in vmap.items() if n is nv and isinstance(o, bmesh.types.BMVert)), None)
    n = (ov.normal if ov is not None else nv.normal).copy()
    off = OFFSET
    hit = tree.ray_cast(nv.co - n * 1e-4, -n, 0.02)
    if hit[0] is not None:
        off = min(off, 0.4 * (hit[0] - nv.co).length)
        capped += off < OFFSET
    nv.co = nv.co - n * off
for f in new_faces:
    f[lay['lined']] = 1
bmesh.ops.reverse_faces(bm, faces=new_faces)
bm.to_mesh(me); bm.free()
me.update()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('TWIN_SHELL ' + json.dumps({'main_part_faces': len(sel), 'twin_faces': len(new_faces), 'offset': OFFSET,
                                  'capped_vertices': int(capped)}))
