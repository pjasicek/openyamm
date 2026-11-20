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
keep = np.isin(pa[tri[:, 0]], (0, 10, 12, 15))
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
zone = [v for v in bm.verts if v.co.z < 0.72 and not (v.co.z < -1.06) or (v.co.y > -0.05 and v.co.z > 0.72)]      # voxel steps out of the body and the mane (not the face, not the hooves)
for _ in range(7):
    nw = [(v, sum((e.other_vert(v).co for e in v.link_edges), Vector()) / max(len(v.link_edges), 1)) for v in zone]
    for v, c in nw: v.co = v.co * 0.5 + c * 0.5
nape = [v for v in bm.verts if abs(v.co.x) < 0.3 and v.co.y > 0.06 and 0.45 < v.co.z < 0.78]
for _ in range(12):
    nw = [(v, sum((e.other_vert(v).co for e in v.link_edges), Vector()) / max(len(v.link_edges), 1)) for v in nape]
    for v, c in nw: v.co = v.co * 0.4 + c * 0.6
bm.to_mesh(me); bm.free()
print('SMOOTH done', len(nape))
m = body.modifiers.new('D', 'DECIMATE'); m.decimate_type = 'COLLAPSE'; m.ratio = TARGET / sum(len(p.vertices) - 2 for p in me.polygons); m.use_symmetry = True; m.symmetry_axis = 'X'
bpy.ops.object.modifier_apply(modifier=m.name)
print('DECIM tris', sum(len(p.vertices) - 2 for p in me.polygons))
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.triangulate(bm, faces=bm.faces)
lay = bm.verts.layers.int.new('part')
print('MAN nonmanifold', sum(1 for e in bm.edges if not e.is_manifold), 'loose', sum(1 for v in bm.verts if not v.link_edges))
for pid in (13, 14):
    ti = np.nonzero(pa == pid)[0]; mp = {int(i): k for k, i in enumerate(ti)}
    tt = tri[pa[tri[:, 0]] == pid]
    nv = [bm.verts.new(co[i].tolist()) for i in ti]
    for v in nv: v[lay] = pid
    for a, b, c in tt:
        try: bm.faces.new((nv[mp[int(a)]], nv[mp[int(b)]], nv[mp[int(c)]]))
        except ValueError: pass
    if pid == 14:       # the wrap's gums stand 4 mm proud: each tooth a quarter larger and 6 mm forward, so the row reads
        seen = set()
        for v0 in nv:
            if v0 in seen: continue
            st = [v0]; seen.add(v0); cc = [v0]
            while st:
                x = st.pop()
                for e in x.link_edges:
                    y = e.other_vert(x)
                    if y not in seen: seen.add(y); st.append(y); cc.append(y)
            c = sum((v.co for v in cc), Vector()) / len(cc)
            for v in cc: v.co = c + (v.co - c) * 1.25 + Vector((0, -0.006, 0))
bm.to_mesh(me); bm.free()
for p in me.polygons: p.use_smooth = True
print('FINAL verts', len(me.vertices), 'tris', len(me.polygons))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
