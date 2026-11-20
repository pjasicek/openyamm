"""Place the Meshy parts on the MM9 bind model (uniform scale to the MM9 height, floor and x centre, y by the pelvis-to-
chest band) and list each loose part with the MM9 bones under it.
Args: <parts blend> <mm9 glb> <out blend> <report json>"""
import bpy, sys, json
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
PARTS, MM9, OUT, REP = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=PARTS)
body = bpy.data.objects['Meshy']
for o in list(bpy.data.objects):
    if o is not body: bpy.data.objects.remove(o)
existing = {body}
bpy.ops.import_scene.gltf(filepath=MM9)
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
arm.name = 'MM9_Rig'
if arm.animation_data: arm.animation_data.action = None
for pb in arm.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
mesh = next(o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('d_skeleton'))
mesh.name = 'MM9_Mesh'
scim = next(o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('Scimitar'))
scim.name = 'MM9_Scimitar'
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o not in (mesh, scim, body): bpy.data.objects.remove(o)
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
em = mesh.evaluated_get(dg).to_mesh()
mv = np.array([tuple(mesh.matrix_world @ v.co) for v in em.vertices])
gn = {g.index: g.name for g in mesh.vertex_groups}
lab = np.array([max(v.groups, key=lambda g: g.weight).group for v in mesh.data.vertices])
print('MM9 bounds', mv.min(0), mv.max(0))
v = np.array([tuple(x.co) for x in body.data.vertices])
s = (mv[:, 2].max() - mv[:, 2].min()) / (v[:, 2].max() - v[:, 2].min())
print('scale', s)
v = v * s
v[:, 2] += mv[:, 2].min() - v[:, 2].min()
v[:, 0] += (mv[:, 0].mean() - v[:, 0].mean())
band = lambda p: (p[:, 2] > -0.1) & (p[:, 2] < 0.55)
v[:, 1] += mv[band(mv), 1].mean() - v[band(v), 1].mean()
body.data.vertices.foreach_set('co', v.ravel())
body.data.update()
part = np.zeros(len(v), int); next(a for a in body.data.attributes if a.data_type == 'INT' and a.name.startswith('part')).data.foreach_get('value', part)
kd = KDTree(len(mv))
for i, p in enumerate(mv): kd.insert(p, i)
kd.balance()
rows = []
for c in np.unique(part):
    idx = np.where(part == c)[0]
    votes = {}
    for i in idx[:: max(1, len(idx) // 200)]:
        _, j, _ = kd.find(v[i])
        n = gn[lab[j]]; votes[n] = votes.get(n, 0) + 1
    t = sum(votes.values())
    rows.append(dict(part=int(c), verts=int(len(idx)), lo=np.round(v[idx].min(0), 3).tolist(), hi=np.round(v[idx].max(0), 3).tolist(),
                     bones={k: round(x / t, 2) for k, x in sorted(votes.items(), key=lambda kv: -kv[1])[:3]}))
rows.sort(key=lambda r: -r['lo'][2])
for r in rows: print(r)
json.dump(rows, open(REP, 'w'), indent=0)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
