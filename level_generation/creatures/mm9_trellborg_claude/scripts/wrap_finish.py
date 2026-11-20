"""Blocky wrap -> smooth closed skin: voxel remesh, each vertex projected on the nearest assembled surface (detail back), light relax. Teeth appended as separate pieces. Attribute part: 0 skin (body, head, mane, horns), 13 eyes, 14 teeth.
Args: <blocks npz> <assembled npz> <out blend> <target tris>"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
BLK, ASM, OUT, TARGET = sys.argv[sys.argv.index('--') + 1:]
TARGET = int(TARGET)
Z = np.load(BLK); V, F, h = Z['V'], Z['F'], float(Z['h'])
A = np.load(ASM); co, tri, pa = A['co'], A['tri'], A['part']
bpy.ops.wm.read_factory_settings(use_empty=True)
me = bpy.data.meshes.new('Body'); me.from_pydata(V.tolist(), [], F.tolist()); me.update()
body = bpy.data.objects.new('Body', me); bpy.context.scene.collection.objects.link(body)
bpy.context.view_layer.objects.active = body; body.select_set(True)
m = body.modifiers.new('R', 'REMESH'); m.mode = 'VOXEL'; m.voxel_size = h; m.use_smooth_shade = True; m.adaptivity = 0
bpy.ops.object.modifier_apply(modifier=m.name)
print('REMESH verts', len(me.vertices), 'polys', len(me.polygons))
keep = np.isin(pa[tri[:, 0]], (0, 10))
bvh = BVHTree.FromPolygons([tuple(c) for c in co], tri[keep].tolist(), all_triangles=True)
bm = bmesh.new(); bm.from_mesh(me)
LIM = 2.5 * h
for it, (k, rel) in enumerate(((1.0, 4), (1.0, 3), (0.65, 2))):
    for _ in range(rel):
        nw = [(v, sum((e.other_vert(v).co for e in v.link_edges), Vector()) / max(len(v.link_edges), 1)) for v in bm.verts]
        for v, c in nw: v.co = v.co * 0.5 + c * 0.5
    far = 0
    for v in bm.verts:
        loc, nor, idx, dist = bvh.find_nearest(v.co)
        if loc is None: continue
        if dist < LIM: v.co = v.co.lerp(loc, k)
        else: far += 1
    print('PROJECT', it, 'far', far, 'of', len(bm.verts))
bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table(); bm.verts.index_update()
Pv = np.array([v.co[:] for v in bm.verts]); Eg = np.array([[e.verts[0].index, e.verts[1].index] for e in bm.edges])
deg = np.bincount(Eg.ravel(), minlength=len(Pv)).astype(float)
def avg(Q):
    s_ = np.zeros_like(Q); np.add.at(s_, Eg[:, 0], Q[Eg[:, 1]]); np.add.at(s_, Eg[:, 1], Q[Eg[:, 0]])
    return s_ / deg[:, None]
zm = (Pv[:, 2] > -0.98) & (Pv[:, 2] < 0.66)
for _ in range(6): Pv[zm] = 0.5 * Pv[zm] + 0.5 * avg(Pv)[zm]
# slits and pits left by Meshy's folds: narrow dents against a smoothed copy relax, the belt and the big forms stay
for v, q in zip(bm.verts, Pv): v.co = Vector(q)
bm.normal_update(); Nv = np.array([v.normal[:] for v in bm.verts])
for rnd in range(3):
    Ps = Pv.copy()
    for _ in range(25): Ps = 0.5 * Ps + 0.5 * avg(Ps)
    dent = -((Pv - Ps) * Nv).sum(1)
    hot = zm & (dent > 0.0035) & ~((Pv[:, 2] > 0.1) & (Pv[:, 2] < 0.3) & (np.abs(Pv[:, 0]) < 0.32))
    grow = hot.copy()
    for _ in range(4):
        g2 = grow.copy(); g2[Eg[grow[Eg[:, 0]], 1]] = True; g2[Eg[grow[Eg[:, 1]], 0]] = True; grow = g2
    grow &= zm
    print('SLIT', rnd, int(hot.sum()), int(grow.sum()), round(float(dent[zm].max()), 4))
    for _ in range(25): Pv[grow] = 0.4 * Pv[grow] + 0.6 * avg(Pv)[grow]
for v, q in zip(bm.verts, Pv): v.co = Vector(q)
# the join of neck and shoulders: a long smooth over the fold, jaw and hair kept
def jz(v): return v.co.z > 0.62 and v.co.z < 0.86 and not (v.co.y < -0.075 and v.co.z > 0.68 and abs(v.co.x) < 0.17) and not (v.co.z > 0.76 and abs(v.co.x) < 0.2 and v.co.y > 0.02) and not (v.co.z > 0.78 and abs(v.co.x) < 0.2)
nk = np.array([jz(v) for v in bm.verts])
Pv = np.array([v.co[:] for v in bm.verts])
for _ in range(60): Pv[nk] = 0.4 * Pv[nk] + 0.6 * avg(Pv)[nk]
for v, q in zip(bm.verts, Pv): v.co = Vector(q)
print('NECK', int(nk.sum()))
bm.to_mesh(me); bm.free()
print('SMOOTH done')
m = body.modifiers.new('D', 'DECIMATE'); m.decimate_type = 'COLLAPSE'; m.ratio = TARGET / sum(len(p.vertices) - 2 for p in me.polygons); m.use_symmetry = True; m.symmetry_axis = 'X'
bpy.ops.object.modifier_apply(modifier=m.name)
print('DECIM tris', sum(len(p.vertices) - 2 for p in me.polygons))
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.triangulate(bm, faces=bm.faces)
# folded spots: edges bent past 75 degrees on the body relax with a ring round them
for rnd in range(8):
    bm.normal_update()
    hot = set()
    for e in bm.edges:
        if len(e.link_faces) == 2 and e.calc_face_angle(0.0) > 1.3 and -0.98 < e.verts[0].co.z < 0.66 and abs(e.verts[0].co.x) < 0.5:
            hot.update(e.verts)
    print('FOLD', rnd, len(hot))
    if not hot: break
    gr = set(hot)
    for _ in range(2): gr |= {e.other_vert(v) for v in gr for e in v.link_edges}
    for _ in range(6):
        nw = [(v, sum((e.other_vert(v).co for e in v.link_edges), Vector()) / max(len(v.link_edges), 1)) for v in gr]
        for v, c in nw: v.co = v.co * 0.4 + c * 0.6
for e in [e for e in bm.edges if not e.is_manifold]:
    print('NONMAN at', [round(x, 3) for x in e.verts[0].co], len(e.link_faces))
lay = bm.verts.layers.int.new('part')
print('MAN nonmanifold', sum(1 for e in bm.edges if not e.is_manifold), 'loose', sum(1 for v in bm.verts if not v.link_edges))
for pid in (14,):
    ti = np.nonzero(pa == pid)[0]; mp = {int(i): k for k, i in enumerate(ti)}
    tt = tri[pa[tri[:, 0]] == pid]
    nv = [bm.verts.new(co[i].tolist()) for i in ti]
    for v in nv: v[lay] = pid
    for a, b, c in tt:
        try: bm.faces.new((nv[mp[int(a)]], nv[mp[int(b)]], nv[mp[int(c)]]))
        except ValueError: pass
bm.to_mesh(me); bm.free()
for p in me.polygons: p.use_smooth = True
print('FINAL verts', len(me.vertices), 'tris', len(me.polygons))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
