"""Stage 1 of the fish body clean: the Meshy Smart Topology fish scaled to the MM9 FISH.abc bind (snout to tail-fin
tip length, centred in x, snout on the MM9 snout), its main shell turned into a signed distance grid (openvdb level
set, 1 mm voxels, metres), and the separate pieces (2 eyes, 2 pectoral fins) kept for later.

Args: <mm9 rig blend> <meshy glb> <out npz> <out pieces blend> <report json>
"""
import bpy, bmesh, sys, json
import numpy as np
import openvdb as vdb
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index('--') + 1:]
SRC, MESHY, OUT, PIECES, REP = argv
VOX = 0.001

bpy.ops.wm.open_mainfile(filepath=SRC)
A = []
for o in bpy.data.objects:
    if o.type == 'MESH':
        A += [tuple(o.matrix_world @ v.co) for v in o.data.vertices]
A = np.array(A)
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=MESHY)
new = [o for o in bpy.data.objects if o not in before]
src = next(o for o in new if o.type == 'MESH')
bm = bmesh.new(); bm.from_mesh(src.data); bm.transform(src.matrix_world)
for o in new:
    bpy.data.objects.remove(o)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
# components by faces
comp = {}
k = 0
for f in bm.faces:
    if f.index in comp:
        continue
    st = [f]; comp[f.index] = k
    while st:
        x = st.pop()
        for e in x.edges:
            for y in e.link_faces:
                if y.index not in comp:
                    comp[y.index] = k; st.append(y)
    k += 1
sizes = np.bincount([comp[f.index] for f in bm.faces])
main = int(np.argmax(sizes))
B = np.array([tuple(v.co) for v in bm.verts])
s = (A[:, 1].max() - A[:, 1].min()) / (B[:, 1].max() - B[:, 1].min())
mainv = sorted({v.index for f in bm.faces if comp[f.index] == main for v in f.verts})
Bm = B[mainv]
t = np.array([-s * (Bm[:, 0].min() + Bm[:, 0].max()) / 2, A[:, 1].min() - s * B[:, 1].min(), 0.0])
# z: the body's mid-depth (between the throat and the back, excluding fins) on the MM9 Xbody height
yy = Bm[:, 1] * s + t[1]
mid = np.abs(yy - 0.0) < 0.02
z = Bm[mid, 2] * s
xs = np.abs(Bm[mid, 0] * s + t[0])
core = xs > 0.008     # body surface away from the midline fin sheets
t[2] = 0.0028 + 0.0722 - (z[core].min() + z[core].max()) / 2
M = Matrix.Translation(Vector(t)) @ Matrix.Scale(s, 4)
bm.transform(M)
P = np.array([tuple(v.co) for v in bm.verts])
tris = []
for f in bm.faces:
    if comp[f.index] != main:
        continue
    vs = [v.index for v in f.verts]
    for i in range(1, len(vs) - 1):
        tris.append((vs[0], vs[i], vs[i + 1]))
tris = np.array(tris, np.int32)
xf = vdb.createLinearTransform(voxelSize=VOX)
grid = vdb.FloatGrid.createLevelSetFromPolygons(P.astype(np.float32), triangles=tris, transform=xf, halfWidth=40.0)
lo = np.floor(P[mainv].min(0) / VOX).astype(int) - 8
hi = np.ceil(P[mainv].max(0) / VOX).astype(int) + 8
# x box symmetric about 0 so the grid can be mirrored
hx = max(-lo[0], hi[0]); lo[0], hi[0] = -hx, hx
shape = tuple((hi - lo + 1).tolist())
arr = np.zeros(shape, np.float32)
grid.copyToArray(arr, ijk=tuple(lo.tolist()))
np.savez(OUT, sdf=arr, lo=lo, vox=VOX)
# separate pieces: keep as their own objects
pieces = []
for c in range(k):
    if c == main:
        continue
    vs = sorted({v.index for f in bm.faces if comp[f.index] == c for v in f.verts})
    q = P[vs]
    pieces.append({'comp': c, 'faces': int(sizes[c]), 'centre': q.mean(0).round(4).tolist(),
                   'min': q.min(0).round(4).tolist(), 'max': q.max(0).round(4).tolist()})
bpy.ops.wm.read_factory_settings(use_empty=True)
me = bpy.data.meshes.new('meshy_fit')
bm.to_mesh(me)
ob = bpy.data.objects.new('meshy_fit', me)
bpy.context.scene.collection.objects.link(ob)
cl = me.attributes.new('comp', 'INT', 'FACE')
for f in me.polygons:
    cl.data[f.index].value = comp[f.index]
bpy.ops.wm.save_as_mainfile(filepath=PIECES)
rep = {'scale': s, 'translate': t.tolist(), 'main': main, 'sizes': sizes.tolist(), 'grid_shape': shape,
       'lo': lo.tolist(), 'pieces': pieces, 'sdf_min': float(arr.min()), 'sdf_max': float(arr.max()),
       'mm9_bounds': [A.min(0).round(4).tolist(), A.max(0).round(4).tolist()],
       'fit_bounds': [P.min(0).round(4).tolist(), P.max(0).round(4).tolist()]}
json.dump(rep, open(REP, 'w'), indent=1)
print('VOLUME ' + json.dumps(rep))
