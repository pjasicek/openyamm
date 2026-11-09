"""Rest-pose triangles of the hydra -> work/uv3d.npz for compose_hyd.py: per triangle its UVs (UVMap; body faces in
the body texture, head faces in the head texture), rest 3D positions, part (face attribute 'part': 0 body, k head k),
appendage (k on head k's separate pieces), graft source (graft_heads.py: 2 = loft), per corner the loft coordinates (loft_s, loft_ref), and per corner the vertex's chain (strongest bone weight) and head_skull flag (graft_heads.py: 1 on a rigid skull)."""
import bpy, json, os, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rig = bpy.data.objects['Hydra_Rig']
if rig.animation_data:
    rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
obj = bpy.data.objects['Hydra']; me = obj.data
chains = json.load(open(os.path.join(HERE, 'work', 'rig.json')))['chains']
bone_chain = {nm: ci for ci, c in enumerate(chains) for nm in c['names']}
gname = {g.index: g.name for g in obj.vertex_groups}
owner = np.array([bone_chain[gname[max(v.groups, key=lambda x: x.weight).group]] for v in me.vertices])
skull = np.zeros(len(me.vertices))
if 'head_skull' in me.attributes:
    me.attributes['head_skull'].data.foreach_get('value', skull)
part = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', part)
src = np.zeros(len(me.polygons), int)
if 'graft_src' in me.attributes:
    me.attributes['graft_src'].data.foreach_get('value', src)
app = np.zeros(len(me.polygons), int)
if 'appendage' in me.attributes:
    me.attributes['appendage'].data.foreach_get('value', app)
ls = np.zeros(len(me.vertices)); lr = np.zeros(len(me.vertices) * 3)
if 'loft_s' in me.attributes:
    me.attributes['loft_s'].data.foreach_get('value', ls); me.attributes['loft_ref'].data.foreach_get('vector', lr)
lr = lr.reshape(-1, 3)
me.calc_loop_triangles(); uv = me.uv_layers['UVMap'].data
tris = list(me.loop_triangles)
U = np.array([[tuple(uv[l].uv) for l in t.loops] for t in tris], dtype=np.float32)
X = np.array([[tuple(me.vertices[v].co) for v in t.vertices] for t in tris], dtype=np.float32)
P = np.array([part[t.polygon_index] for t in tris], np.int32)
O = np.array([[owner[v] for v in t.vertices] for t in tris], np.int32)
S = np.array([[skull[v] for v in t.vertices] for t in tris], np.float32)
F = np.array([t.polygon_index for t in tris], np.int32)
A = np.array([app[t.polygon_index] for t in tris], np.int32)
G = np.array([src[t.polygon_index] for t in tris], np.int32)
LS = np.array([[ls[v] for v in t.vertices] for t in tris], np.float32)
LR = np.array([[lr[v] for v in t.vertices] for t in tris], np.float32)
np.savez(os.path.join(HERE, 'work', 'uv3d.npz'), uv=U, xyz=X, part=P, owner=O, skull=S, face=F, appendage=A, src=G,
         loft_s=LS, loft_ref=LR)
print('DUMPED', len(U), 'triangles; per part', np.bincount(P).tolist())
