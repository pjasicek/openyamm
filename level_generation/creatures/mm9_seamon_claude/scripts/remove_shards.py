"""Remove the flat shards hanging under the tail (2026-10-30 review: "there are some stray polygons"). Runs after
root_fins.py on the UV'd body; it only merges vertices, so the xatlas UVs and the retexture stay valid.

Args: <in blend> <out blend> <report json>

Meshy left two thin two-sided flaps on the underside of the tail (one by the hind legs, one mid-tail; MM9's tail has
no ventral fins, only the dorsal ridge and the forked tail fin). A flap is found as body faces whose inward ray meets
the opposite surface within THIN (flat, two-sided), behind the head and before the tail fin, not on the legs; its tip
vertices are those further from the tail's bone chain than TIP_RATIO x the median radius of the tail around them and
below the chain. Each tip is welded onto its neighbour nearest the chain, so the flap collapses into the tail surface;
degenerate faces and loose geometry are removed.
"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP = argv[:3]
THIN, TIP_RATIO, Y0, Y1 = 0.012, 2.0, 0.3, 4.0
CHAIN = ['Bone01', 'Bone02', 'Bone38', 'Bone39', 'Bone03', 'Bone04', 'Bone40', 'Bone05']
LIMBS = ['Bone10', 'Bone11', 'Bone12', 'Bone13', 'Bone21', 'Bone22', 'Bone23', 'Bone24']
bpy.ops.wm.open_mainfile(filepath=IN)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
ob = bpy.data.objects['Body']
pts = [rig.matrix_world @ rig.data.bones[b].head_local for b in CHAIN]
axis = [pts[i].lerp(pts[i + 1], t / 20) for i in range(len(pts) - 1) for t in range(21)]


def to_axis(p):
    q = min(axis, key=lambda a: (a - p).length)
    return (p - q).length, q


gi = {g.name: g.index for g in ob.vertex_groups}
limb = {gi[n] for n in LIMBS if n in gi}
bm = bmesh.new()
bm.from_mesh(ob.data)
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table(); bm.verts.index_update(); bm.faces.index_update()
pl = bm.verts.layers.int['piece']
dl = bm.verts.layers.deform.active
bvh = BVHTree.FromBMesh(bm)
tail = [v for v in bm.verts if v[pl] == 0 and Y0 < v.co.y < Y1 and sum(v[dl].get(j, 0) for j in limb) < 0.3]
rad = {v: to_axis(v.co) for v in tail}
thin_verts = set()
for f in bm.faces:
    if not all(v in rad for v in f.verts):
        continue
    c, n = f.calc_center_median(), f.normal
    hit = bvh.ray_cast(c - n * 1e-4, -n, THIN)
    if hit[0] is not None and hit[2] != f.index and not all(v[pl] == 2 for v in bm.faces[hit[2]].verts):
        thin_verts.update(f.verts)
tips = []
for v in thin_verts:
    r, q = rad[v]
    local = [rad[w][0] for w in tail if abs(w.co.y - v.co.y) < 0.1]
    med = float(np.median(local))
    if r > TIP_RATIO * med and r > med + 0.03 and v.co.z < q.z:
        tips.append(v)
weld, info = {}, []
for v in tips:
    nb = [e.other_vert(v) for e in v.link_edges if e.other_vert(v) not in tips]
    if not nb:
        continue
    tgt = min(nb, key=lambda w: to_axis(w.co)[0])
    weld[v] = tgt
    info.append({'tip': [round(x, 3) for x in v.co], 'radius': round(rad[v][0], 3), 'onto': [round(x, 3) for x in tgt.co]})
faces_before = len(bm.faces)
bmesh.ops.weld_verts(bm, targetmap=weld)
bmesh.ops.dissolve_degenerate(bm, dist=1e-5, edges=bm.edges[:])
bmesh.ops.delete(bm, geom=[e for e in bm.edges if not e.link_faces], context='EDGES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_edges], context='VERTS')
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
rep = {'thin_tail_verts': len(thin_verts), 'tips': info, 'faces': [faces_before, len(bm.faces)]}
bm.to_mesh(ob.data)
bm.free()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('SHARDS ' + json.dumps(rep))
