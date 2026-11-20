"""Fill the eye sockets of the head shell (2026-11-01, viewer shot: from a camera at or above eye level the eyes read
as closed - the brow overhang hides the deep sockets Meshy left for its separate eyeball cups, which
build_export_v2.py's export_fix drops because they cross the lids, Annud's lesson).

Every head-shell vertex behind an eyeball cup (a ray toward the face, -Y, hits the cup) moves forward onto the cup's
outer surface, so the shell's own painted iris sits on an eyeball-shaped surface level with the lids. UVs, weights
and topology are unchanged (only positions), so the paid paints stay valid; the cups themselves are still dropped at
export. A one-ring Laplacian blend softens the step at the socket rim.
Args (Blender): <in blend> <out blend> <eye part,...> (part numbers as head_split.py: loose parts by lowest vertex)"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, EYES = a[0], a[1], [int(x) for x in a[2].split(',')]
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']
rig = body.parent
if rig.animation_data:
    rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
me = body.data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
comp = -np.ones(len(bm.verts), np.int32); cid = 0
for v in bm.verts:
    if comp[v.index] >= 0:
        continue
    st = [v]; comp[v.index] = cid
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if comp[y.index] < 0:
                comp[y.index] = cid; st.append(y)
    cid += 1
hd = np.zeros(len(me.polygons), np.int32)
me.attributes['head'].data.foreach_get('value', hd)
CO = np.array([v.co[:] for v in bm.verts])
rep = {}
moved_all = set()
for e in EYES:
    fi = [f.index for f in bm.faces if comp[f.verts[0].index] == e]
    vs = sorted({v.index for i in fi for v in bm.faces[i].verts})
    remap = {v: k for k, v in enumerate(vs)}
    bvh = BVHTree.FromPolygons([Vector(CO[v]) for v in vs], [[remap[v.index] for v in bm.faces[i].verts] for i in fi])
    lo, hi = CO[vs].min(0), CO[vs].max(0)
    moved = 0
    shell = {v.index for f in bm.faces if hd[f.index] and comp[f.verts[0].index] not in EYES for v in f.verts}
    for vi in shell:
        p = CO[vi]
        if not (lo[0] - 0.003 < p[0] < hi[0] + 0.003 and lo[2] - 0.003 < p[2] < hi[2] + 0.003):
            continue
        loc, nrm, idx, dist = bvh.ray_cast(Vector(p), Vector((0, -1, 0)), 0.05)
        if loc is not None:
            bm.verts[vi].co = loc + Vector((0, -0.0004, 0))
            moved += 1
            moved_all.add(vi)
    rep[e] = {'cup_verts': len(vs), 'moved_shell_verts': moved, 'cup_bbox': [lo.round(3).tolist(), hi.round(3).tolist()]}
# one-ring blend at the rim: neighbours of moved vertices (not moved themselves) take half their Laplacian step
rim = {n.index for vi in moved_all for e in bm.verts[vi].link_edges for n in [e.other_vert(bm.verts[vi])]} - moved_all
rim = {r for r in rim if comp[r] not in EYES}
new = {}
for r in rim:
    v = bm.verts[r]
    nb = [e.other_vert(v).co for e in v.link_edges]
    avg = sum(nb, Vector()) / len(nb)
    new[r] = v.co.lerp(avg, 0.5)
for r, c in new.items():
    bm.verts[r].co = c
bm.to_mesh(me); bm.free(); me.update()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('EYEFILL', json.dumps({'eyes': rep, 'rim_relaxed': len(rim)}))
