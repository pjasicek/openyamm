import bpy,sys,numpy as np,collections,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round2/body_lod0.blend'));C.reset();o=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];part=np.array([a.value for a in o.data.attributes['piece'].data]);co=np.array([v.co[:]for v in o.data.vertices]);ns=[g.name for g in o.vertex_groups]
for n in ['B_Pelvis','B_Spine','B_Spine1','B_Spine2','B_Neck','B_L_Clavicle','B_L_UpperArm','B_L_Forearm','B_L_Hand']:
 b=r.data.bones[n];print('BONE',n,tuple(b.head_local),tuple(b.tail_local))
for id in np.unique(part):print('PART',id,(part==id).sum(),co[part==id].min(0),co[part==id].max(0))
D=collections.defaultdict(list)
for i,c in enumerate(co):D[tuple(np.round(c,5))].append(i)
print('DUPLICATES',sum(len(v)-1 for v in D.values()))
W=[]
for v in o.data.vertices:W.append({ns[g.group]:round(g.weight,4)for g in v.groups if ns[g.group]in r.data.bones})
bad=[v for v in D.values()if len(v)>1 and any(W[x]!=W[v[0]]for x in v)]
print('WEIGHT SEAMS',len(bad));print([(v,[W[x]for x in v])for v in bad[:5]])
E=np.array([list(e.vertices)for e in o.data.edges]);L=np.linalg.norm(co[E[:,0]]-co[E[:,1]],axis=1)
for clip,t in [('Standing',0),('Attack',.4),('Death',1.3)]:
 C.activate(clip,t);ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();c=np.array([v.co[:]for v in me.vertices]);ev.to_mesh_clear();ratio=np.linalg.norm(c[E[:,0]]-c[E[:,1]],axis=1)/np.maximum(L,1e-6);take=np.where((part[E]==1).all(1))[0];ids=take[np.argsort(ratio[take])[-12:]]
 print('STRETCH',clip)
 for ei in ids:
  edge=E[ei];print(float(ratio[ei]),co[edge].tolist(),[W[i]for i in edge])
