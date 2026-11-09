import bpy, numpy as np, json
from pathlib import Path
P = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'master_head_uv.blend'))
body = bpy.data.objects['Lizardman_Body']; rig = bpy.data.objects['Lizardman_Rig']
mesh=body.data; names=[g.name for g in body.vertex_groups]
xyz=np.array([v.co[:] for v in mesh.vertices]); W=np.zeros((len(xyz),len(names)))
for v in mesh.vertices:
    for g in v.groups: W[v.index,g.group]=g.weight
adj=[[] for _ in xyz]
for e in mesh.edges:
    a,b=e.vertices;adj[a].append(b);adj[b].append(a)
# The old ownership pass made abrupt weight steps at the neck, ankles and garment border.
# Smooth only those boundaries; retain measured finger chains and the rest of the rig.
z=xyz[:,2]
mask=((z>.64)&(z<1.17)&(abs(xyz[:,0])<.30))|((z>.06)&(z<.25))|((z>.37)&(z<.50))|((z>1.31)&(z<1.46))
for _ in range(12):
    changed=W.copy()
    for i in np.flatnonzero(mask):
        if adj[i]: changed[i]=.5*W[i]+.5*W[adj[i]].mean(axis=0)
    W=changed
for i in np.flatnonzero(mask):
    keep=np.argsort(W[i])[-8:]; values=W[i,keep];values/=values.sum()
    for group in body.vertex_groups: group.remove([int(i)])
    for k,value in zip(keep,values):
        if value>1e-6: body.vertex_groups[int(k)].add([int(i)],float(value),'REPLACE')
assert np.all(np.isfinite(W))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'master_weights.blend'))
print('Corrected transition weights on',int(mask.sum()),'vertices',flush=True)

exec(compile((P/'scripts/probe_corrected.py').read_text(), str(P/'scripts/probe_corrected.py'), 'exec'))
