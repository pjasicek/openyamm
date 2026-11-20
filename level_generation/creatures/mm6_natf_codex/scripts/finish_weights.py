import bpy,json,sys,numpy as np,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_cloth.blend'));body=bpy.data.objects['Body'];me=body.data;rig=bpy.data.objects['Rig'];co=np.array([tuple(v.co)for v in me.vertices]);pv=np.array([a.value for a in me.attributes['piece'].data]);cloth=np.array([a.value for a in me.attributes['cloth'].data]);names=[g.name for g in body.vertex_groups];W=np.zeros((len(co),len(names)));ix={n:i for i,n in enumerate(names)}
for v in me.vertices:
 for g in v.groups:W[v.index,g.group]=g.weight
zs=[1.075,1.135,1.205,1.29,1.36,1.43];bones=['B_Pelvis','B_Spine','B_Spine1','B_Spine2','B_Neck','B_Head'];changed=[]
for i,(x,y,z)in enumerate(co):
 if pv[i]==0 and not cloth[i] and z<1.45 and abs(x)<.18:
  t=float(np.clip((.18-abs(x))/.05,0,1));w=np.zeros(len(names));k=int(np.clip(np.searchsorted(zs,z)-1,0,4));u=float(np.clip((z-zs[k])/(zs[k+1]-zs[k]),0,1));w[ix[bones[k]]]=1-u;w[ix[bones[k+1]]]=u;W[i]=(1-t)*W[i]+t*w;changed.append(i)
 if pv[i]==1 and z>.865:
  # Hidden hip surface fits inside the closed wrap; exposed legs retain the generated shape.
  t=float(np.clip((z-.865)/.10,0,1));me.vertices[i].co.x*=1-.12*t;me.vertices[i].co.y*=1-.22*t;W[i]*=1-t;W[i,ix['B_Pelvis']]+=t
adj=[[]for v in co]
for e in me.edges:
 a,b=e.vertices
 if pv[a]==0 and pv[b]==0:adj[a].append(b);adj[b].append(a)
for it in range(3):
 old=W.copy()
 for i in changed:
  if adj[i] and co[i,2]>1.15:W[i]=.65*old[i]+.35*old[adj[i]].mean(0)
for i,w in enumerate(W):
 ids=np.argsort(w)[-4:];total=w[ids].sum();assert total>0
 for g in list(me.vertices[i].groups):body.vertex_groups[g.group].remove([i])
 for j in ids:
  if w[j]>1e-7:body.vertex_groups[j].add([i],float(w[j]/total),'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_weights.blend'));(P/'work/weights_finish.json').write_text(json.dumps({'torso_vertices':len(changed),'hidden_hip_inset_max_x_fraction':.12,'hidden_hip_inset_max_y_fraction':.22,'hip_threshold_m':.865},indent=2))
sys.argv=['twist','--',str(P/'work/rig_weights.blend'),str(P/'work/rig_finished.blend')];runpy.run_path(str(P/'scripts/twist_bones.py'),run_name='__main__')
