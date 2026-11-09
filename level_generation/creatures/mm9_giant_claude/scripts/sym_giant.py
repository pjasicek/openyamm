"""(giant, from mm9_bigfoot_claude/sym_bf.py; adds a clean-up of non-manifold skin edges) Exact left-right symmetry after the reduction: MM9's mesh is symmetric. The x > 0 half kept and mirrored, weights to the matching L/R bones. Args: <in blend> <out blend>"""
import bpy, bmesh, sys
import numpy as np
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; me = body.data
names = [g.name for g in body.vertex_groups]; idx = {n: i for i, n in enumerate(names)}
def swap(n):
    return n.replace(' L ', ' @ ').replace(' R ', ' L ').replace(' @ ', ' R ')
for n in names:
    if swap(n) not in idx: body.vertex_groups.new(name=swap(n)); idx[swap(n)] = len(idx); print('NEWGROUP', swap(n))
names = [g.name for g in body.vertex_groups]; sw = {i: idx[swap(n)] for i, n in enumerate(names)}
bm = bmesh.new(); bm.from_mesh(me)
dl = bm.verts.layers.deform.active; pl = bm.verts.layers.int['part']
n0 = len(bm.verts)
bmesh.ops.bisect_plane(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces), plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_inner=True, dist=1e-5)
for v in bm.verts:
    if abs(v.co.x) < 1e-4: v.co.x = 0
before = set(bm.verts); bf = set(bm.faces)
bmesh.ops.mirror(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces), axis='X', merge_dist=1e-4)
bmesh.ops.reverse_faces(bm, faces=[f for f in bm.faces if f not in bf])
nw = 0
for v in bm.verts:
    d = v[dl]
    if v.co.x < -1e-5:
        w = dict(d.items()); d.clear()
        for k, a in w.items(): d[sw[k]] = a
        nw += 1
    elif abs(v.co.x) < 1e-5:
        w = dict(d.items()); d.clear()
        out = {}
        for k, a in w.items():
            out[k] = out.get(k, 0) + a / 2; out[sw[k]] = out.get(sw[k], 0) + a / 2
        for k, a in out.items(): d[k] = a
bd = [e for e in bm.edges if not e.is_manifold]
print('SYM open', [tuple(round(x, 3) for x in ((e.verts[0].co + e.verts[1].co) / 2)) for e in bd][:30])
mid = [v for v in bm.verts if abs(v.co.x) < 1e-5 or any(not e.is_manifold for e in v.link_edges)]
bmesh.ops.remove_doubles(bm, verts=mid, dist=2e-3)
bd = [e for e in bm.edges if e.is_boundary]
if bd: bmesh.ops.holes_fill(bm, edges=bd, sides=6)
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
# skin clean-up (the head union's crease where a hair lock meets the shoulder): faces on edges with more than two faces go, the holes are filled
for it in range(4):
    bad = [e for e in bm.edges if len(e.link_faces) > 2 and all(v[pl] == 0 for v in e.verts)]
    if not bad: break
    kill = set()
    for e in bad:
        fs = sorted(e.link_faces, key=lambda f: f.calc_area()); kill.update(fs[:len(fs) - 2])
    bmesh.ops.delete(bm, geom=list(kill), context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bd = [e for e in bm.edges if e.is_boundary and all(v[pl] == 0 for v in e.verts)]
    if bd: bmesh.ops.holes_fill(bm, edges=bd, sides=12)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
    bmesh.ops.recalc_face_normals(bm, faces=[f for f in bm.faces if all(v[pl] == 0 for v in f.verts)])
    print('SYM cleanup', it, len(bad), len(kill))
skin_open = sum(1 for e in bm.edges if not e.is_manifold and all(v[pl] == 0 for v in e.verts))
print('SYM skin non-manifold edges', skin_open)
print('SYM verts', n0, '->', len(bm.verts), 'tris', len(bm.faces), 'mirrored', nw, 'no weight', sum(1 for v in bm.verts if not len(v[dl])), 'boundary', sum(1 for e in bm.edges if e.is_boundary), 'nonman', sum(1 for e in bm.edges if not e.is_manifold))
bm.to_mesh(me); bm.free()
for p in me.polygons: p.use_smooth = True
bpy.ops.wm.save_as_mainfile(filepath=OUT)
