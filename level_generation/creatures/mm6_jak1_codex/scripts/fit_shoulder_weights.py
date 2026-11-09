"""Fit the shoulder's existing eight local influences against library-pose edge strain."""
import bpy,numpy as np,json,sys,hashlib
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
from shoulder_weights import repair_shoulders
bpy.ops.wm.open_mainfile(filepath=str(P/'work/production_body.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];sc=bpy.context.scene;repair_shoulders(body);me=body.data
co=np.array([tuple(v.co) for v in me.vertices]);pieces=np.array([a.value for a in me.attributes['piece'].data]);ids=np.where((pieces==0)&(np.abs(co[:,0])>.075)&(np.abs(co[:,0])<.49)&(co[:,2]>1.16)&(co[:,2]<1.55))[0];lookup=np.full(len(co),-1);lookup[ids]=np.arange(len(ids));edges=np.array([tuple(e.vertices) for e in me.edges]);edges=edges[(lookup[edges]>=0).any(1)];length=np.linalg.norm(co[edges[:,1]]-co[edges[:,0]],axis=1);keep=length>.002;edges=edges[keep];length=length[keep];groupnames={g.index:g.name for g in body.vertex_groups};allowed=[];initial=[]
for i in ids:
 w={groupnames[g.group]:g.weight for g in me.vertices[int(i)].groups if g.weight>1e-8};side='L' if co[i,0]>0 else 'R';names=sorted(w,key=w.get,reverse=True)
 for n in ['B_Spine2','B_Neck','B_Head',f'B_{side}_Clavicle',f'B_{side}_UpperArm',f'B_{side}_UpperArmTwist',f'B_{side}_Forearm',f'B_{side}_ForearmTwist']:
  if n not in names:names.append(n)
 names=names[:8];row=np.array([w.get(n,0) for n in names]);row/=row.sum();allowed.append(names);initial.append(row)
initial=np.array(initial);bone_names=list(rig.data.bones.keys());bi=np.array([[bone_names.index(n) for n in row] for row in allowed]);rest_inv={n:rig.data.bones[n].matrix_local.inverted() for n in bone_names};transforms=[];base=[];poses=[]
for name,step in [('Standing',1),('Walking',.1),('Attack',.08),('Cast',.15),('Hit',.1),('Death',.12),('Fidget',.4)]:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
 for t in np.linspace(0,a.frame_range[1]/sc.render.fps,max(2,int(a.frame_range[1]/sc.render.fps/step)+1)):
  f=t*sc.render.fps;sc.frame_set(int(f),subframe=f-int(f));mats=np.array([np.array(rig.matrix_world@rig.pose.bones[n].matrix@rest_inv[n]@rig.matrix_world.inverted()@body.matrix_world) for n in bone_names]);T=np.einsum('vbcd,vd->vbc',mats[bi],np.c_[co[ids],np.ones(len(ids))])[...,:3];ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();bp=np.array([tuple(body.matrix_world@v.co) for v in mesh.vertices]);ev.to_mesh_clear();assert np.max(np.abs(np.einsum('vb,vbc->vc',initial,T)-bp[ids]))<2e-5
  transforms.append(T);base.append(bp);poses.append([name,float(t)])
T=np.array(transforms);Tc=T-T.mean(2,keepdims=True);base=np.array(base);W=initial.copy();moment=np.zeros_like(W);variance=np.zeros_like(W);history=[]
def project_simplex(v):
 u=-np.sort(-v,axis=1);css=np.cumsum(u,axis=1)-1;rho=(u-css/np.arange(1,9)>0).sum(1)-1;threshold=css[np.arange(len(v)),rho]/(rho+1);return np.maximum(v-threshold[:,None],0)
for iteration in range(300):
 posed=base.copy();posed[:,ids]+=np.einsum('vb,kvbc->kvc',W-initial,T);delta=posed[:,edges[:,1]]-posed[:,edges[:,0]];dist=np.linalg.norm(delta,axis=2);excess=np.maximum(0,dist/length-1.75);force=delta*(2*excess/np.maximum(dist,1e-8)/length)[...,None];gp=np.zeros_like(posed)
 for k in range(len(poses)):
  np.add.at(gp[k],edges[:,1],force[k]);np.add.at(gp[k],edges[:,0],-force[k])
 gradient=np.einsum('kvbc,kvc->vb',Tc,gp[:,ids])+.02*(W-initial);moment=.9*moment+.1*gradient;variance=.999*variance+.001*gradient*gradient;rate=.008*(.3 if iteration>600 else 1);W=project_simplex(W-rate*(moment/(1-.9**(iteration+1)))/(np.sqrt(variance/(1-.999**(iteration+1)))+1e-8))
 if iteration%100==0 or iteration==299:
  row={'iteration':iteration,'p99':float(np.percentile(dist/length,99)),'max':float((dist/length).max()),'loss':float(np.mean(excess*excess))};history.append(row);print('SHOULDER FIT',row,flush=True)
 if iteration>100 and np.max(excess)<.02:break
rows=[{'index':int(i),'weights':{n:float(w) for n,w in zip(names,row) if w>1e-7}} for i,names,row in zip(ids,allowed,W)];report={'vertices':rows,'poses':poses,'history':history,'triangles_unchanged':sum(len(f.vertices)-2 for f in me.polygons),'coordinate_sha256':hashlib.sha256(co.astype('<f4').tobytes()).hexdigest()};(P/'work/round2_fitted_weights.json').write_text(json.dumps(report))
for file in ['production_body','textured_master']:
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/{file}.blend'));body=bpy.data.objects['Body'];current=np.array([tuple(v.co) for v in body.data.vertices]);assert np.allclose(current,co,atol=1e-7)
 for row in rows:
  i=row['index'];weights=row['weights'];total=sum(weights.values())
  for g in list(body.data.vertices[i].groups):body.vertex_groups[g.group].remove([i])
  for name,w in weights.items():body.vertex_groups[name].add([i],w/total,'REPLACE')
  assert len(body.data.vertices[i].groups)<=8 and abs(sum(g.weight for g in body.data.vertices[i].groups)-1)<1e-6
 bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/{file}.blend'))
print('SHOULDER FIT SAVED',len(rows),'vertices',flush=True)
