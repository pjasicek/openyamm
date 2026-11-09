"""Blocky head closure -> smooth closed shell: voxel remesh, each vertex projected on the Meshy surface, decimated. Args: <blocks npz> <face npz> <out blend> <target tris>"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
BLK, ASM, OUT, TARGET = sys.argv[sys.argv.index('--') + 1:]
TARGET = int(TARGET)
Z = np.load(BLK); V, F, h = Z['V'], Z['F'], float(Z['h'])
A = np.load(ASM); co, tri, pa = A['co'], A['tri'], A['part']
bpy.ops.wm.read_factory_settings(use_empty=True)
me = bpy.data.meshes.new('Face'); me.from_pydata(V.tolist(), [], F.tolist()); me.update()
body = bpy.data.objects.new('Face', me); bpy.context.scene.collection.objects.link(body)
bpy.context.view_layer.objects.active = body; body.select_set(True)
m = body.modifiers.new('R', 'REMESH'); m.mode = 'VOXEL'; m.voxel_size = h; m.use_smooth_shade = True; m.adaptivity = 0
bpy.ops.object.modifier_apply(modifier=m.name)
print('REMESH verts', len(me.vertices), 'polys', len(me.polygons))
keep = pa[tri[:, 0]] == 10
bvh = BVHTree.FromPolygons([tuple(c) for c in co], tri[keep].tolist(), all_triangles=True)
bm = bmesh.new(); bm.from_mesh(me)
for it, (k, rel) in enumerate(((1.0, 3), (1.0, 2), (0.75, 2))):
    for _ in range(rel):
        nw = [(v, sum((e.other_vert(v).co for e in v.link_edges), Vector()) / max(len(v.link_edges), 1)) for v in bm.verts]
        for v, c in nw: v.co = v.co * 0.5 + c * 0.5
    far = 0
    for v in bm.verts:
        loc, nor, idx, dist = bvh.find_nearest(v.co)
        if dist < 2.5 * h: v.co = v.co.lerp(loc, k)
        else: far += 1
    print('PROJECT', it, 'far', far, 'of', len(bm.verts))
bm.to_mesh(me); bm.free()
m = body.modifiers.new('D', 'DECIMATE'); m.decimate_type = 'COLLAPSE'; m.ratio = TARGET / sum(len(p.vertices) - 2 for p in me.polygons); m.use_symmetry = True; m.symmetry_axis = 'X'
bpy.ops.object.modifier_apply(modifier=m.name)
bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.triangulate(bm, faces=bm.faces)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
def despike(bm, rounds, ang):
    # a vertex whose faces disagree with their neighbours sits in a fold: back to its neighbours' average
    for r in range(rounds):
        bm.normal_update(); bad = []
        for v in bm.verts:
            if not v.link_edges: continue
            c = sum((e.other_vert(v).co for e in v.link_edges), Vector()) / len(v.link_edges)
            L = sum(e.calc_length() for e in v.link_edges) / len(v.link_edges)
            if (v.co - c).length > 0.45 * L or min(f.normal.dot(v.normal) for f in v.link_faces) < ang: bad.append((v, c))
        for v, c in bad: v.co = c
        print('DESPIKE', r, len(bad))
despike(bm, 6, 0.2)
bd = [e for e in bm.edges if e.is_boundary]
if bd: bmesh.ops.holes_fill(bm, edges=bd, sides=8)
print('MAN nonmanifold', sum(1 for e in bm.edges if not e.is_manifold), 'tris', len(bm.faces))
bm.to_mesh(me); bm.free()
# eyes
ti = np.nonzero(pa == 13)[0]; mp = {int(i): k for k, i in enumerate(ti)}
tt = tri[pa[tri[:, 0]] == 13]
e = bpy.data.meshes.new('Eyes'); e.from_pydata(co[ti].tolist(), [], [[mp[int(a)], mp[int(b)], mp[int(c)]] for a, b, c in tt]); e.update()
bpy.context.scene.collection.objects.link(bpy.data.objects.new('Eyes', e))
for p in me.polygons: p.use_smooth = True
bpy.ops.wm.save_as_mainfile(filepath=OUT); print('HEADCLOSE', OUT)
