"""Thin-flap probe: body faces whose inward ray meets the opposite surface within THIN (a flat two-sided shard), grouped
into clusters by edge adjacency. Args: <blend> <out json> [thin m]"""
import bpy, bmesh, sys, json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
argv = sys.argv[sys.argv.index('--') + 1:]
THIN = float(argv[2]) if len(argv) > 2 else 0.012
bpy.ops.wm.open_mainfile(filepath=argv[0])
ob = bpy.data.objects['Body']
bm = bmesh.new(); bm.from_mesh(ob.data); bm.faces.ensure_lookup_table(); bm.verts.index_update(); bm.faces.index_update()
pl = bm.verts.layers.int['piece']
dl = bm.verts.layers.deform.active
gi = {g.name: g.index for g in ob.vertex_groups}
legs = {gi[n] for n in ('Bone10', 'Bone11', 'Bone12', 'Bone13', 'Bone21', 'Bone22', 'Bone23', 'Bone24',
                        'Bone15', 'Bone16', 'Bone17', 'Bone18', 'Bone19', 'Bone26', 'Bone27', 'Bone28', 'Bone29',
                        'Bone30') if n in gi}
bvh = BVHTree.FromBMesh(bm)
thin = set()
for f in bm.faces:
    if not all(v[pl] == 0 for v in f.verts):
        continue
    c = f.calc_center_median(); n = f.normal
    hit = bvh.ray_cast(c - n * 1e-4, -n, THIN)
    if hit[0] is not None and hit[2] != f.index:
        thin.add(f)
seen, clusters = set(), []
for f in thin:
    if f in seen:
        continue
    st, cl = [f], [f]; seen.add(f)
    while st:
        x = st.pop()
        for e in x.edges:
            for g in e.link_faces:
                if g in thin and g not in seen:
                    seen.add(g); st.append(g); cl.append(g)
    c = sum((g.calc_center_median() for g in cl), Vector()) / len(cl)
    legw = sum(sum(v[dl].get(j, 0) for j in legs) for g in cl for v in g.verts) / (3 * len(cl))
    area = sum(g.calc_area() for g in cl)
    clusters.append({'faces': len(cl), 'centre': [round(x, 3) for x in c], 'area_cm2': round(area * 1e4, 1),
                     'limb_weight': round(legw, 2), 'ids': [g.index for g in cl]})
clusters.sort(key=lambda c: -c['area_cm2'])
json.dump(clusters, open(argv[1], 'w'), indent=1)
for c in clusters[:40]:
    print('THIN', {k: v for k, v in c.items() if k != 'ids'})
