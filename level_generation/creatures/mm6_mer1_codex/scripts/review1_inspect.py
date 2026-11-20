import bpy,bmesh,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for path in ['work/reduction_master.blend','work/reduction/body_lod0_4_final.blend']:
 bpy.ops.wm.open_mainfile(filepath=str(P/path));o=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];r.animation_data.action=None
 for b in r.pose.bones:b.matrix_basis.identity()
 bm=bmesh.new();bm.from_mesh(o.data);part=bm.verts.layers.int['piece']
 print('FILE',path,flush=True)
 for pid in [1,2,3,4,8,9,12]:
  vs=[v for v in bm.verts if v[part]==pid];es=[e for e in bm.edges if e.is_boundary and all(v[part]==pid for v in e.verts)];groups=[]
  while es:
   group={es.pop()};done=False
   while not done:
    verts={v for e in group for v in e.verts};extra={e for e in es if any(v in verts for v in e.verts)};done=not extra;group|=extra;es=[e for e in es if e not in extra]
   co=np.array([tuple(v.co)for v in {v for e in group for v in e.verts}]);groups.append({'edges':len(group),'min':co.min(0).tolist(),'max':co.max(0).tolist(),'centre':co.mean(0).tolist()})
  co=np.array([tuple(v.co)for v in vs]);print('PIECE',pid,len(vs),'bounds',co.min(0),co.max(0),'BOUND',groups,flush=True)
 print('BONES',[(n,list(r.data.bones[n].head_local))for n in ['B_R_UpperArm','B_L_UpperArm','B_Pelvis','Club']],flush=True)
 print('MATS',[(m.name,[(n.name,n.image.filepath)for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image])for m in o.data.materials],flush=True)
