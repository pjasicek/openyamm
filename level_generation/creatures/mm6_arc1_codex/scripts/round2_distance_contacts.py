"""Restore physical grip and sole surfaces on the capped distance candidates without adding triangles."""
import bpy,json,sys,math,numpy as np,subprocess
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];W=P/'work/round2';D=P/'review/round2/reduction';sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
from round2_reduce import render
records=[]
for level in [1,2,3]:
 path=W/(f'body_l{level}_distance.blend'if level<3 else'body_l3_exact.blend');bpy.ops.wm.open_mainfile(filepath=str(path));ob=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0)
 ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();posed=np.array([v.co[:]for v in me.vertices]);ev.to_mesh_clear();original=posed.copy();pieces=np.array([v.value for v in ob.data.attributes['piece'].data]);names={g.index:g.name for g in ob.vertex_groups};trans=[]
 for v in ob.data.vertices:trans.append(sum((np.array(rig.pose.bones[names[g.group]].matrix@rig.data.bones[names[g.group]].matrix_local.inverted())*g.weight for g in v.groups),np.zeros((4,4))))
 trans=np.array(trans);bow=np.array(rig.pose.bones['Bow'].matrix);inv=np.linalg.inv(bow);local=(np.c_[posed,np.ones(len(posed))]@inv.T)[:,:3];before=local.copy();ob.data.calc_loop_triangles();tri=[list(t.vertices)for t in ob.data.loop_triangles if all(pieces[i]==2 for i in t.vertices)]
 weights=np.array([[i/8,j/8,(8-i-j)/8]for i in range(9)for j in range(9-i)])
 for iteration in range(300):
  worst=0
  for ids in tri:
   points=weights@local[ids];valid=np.flatnonzero(abs(points[:,2])<.052)
   if not len(valid):continue
   ix=valid[np.linalg.norm(points[valid,:2],axis=1).argmin()];p=points[ix];rad=np.linalg.norm(p[:2])
   if rad>=.00825:continue
   w=weights[ix];direction=p[:2]/rad if rad>1e-7 else local[ids,:2].mean(0)
   direction/=max(1e-9,np.linalg.norm(direction));correction=(.0083-rad)*direction
   for i,weight in zip(ids,w):local[i,:2]+=correction*weight/max(.05,float(w@w))
   worst=max(worst,.0083-rad)
  if worst<1e-5:break
 ids=np.flatnonzero(pieces==2);posed[ids]=(np.c_[local[ids],np.ones(len(ids))]@bow.T)[:,:3]
 # Coarse soles still use the same planted rig. Fit their bottom surface to the accepted rest floor.
 soles={}
 for side in 'LR':
  ids=[v.index for v in ob.data.vertices if v.co.z<.025 and sum(g.weight for g in v.groups if names[g.group]in[f'B_{side}_Foot',f'B_{side}_Toe0'])>.8]
  soles[side]=ids
  for i in ids:posed[i,2]=.002
 for i,v in enumerate(ob.data.vertices):
  if np.linalg.norm(posed[i]-original[i])>1e-9:v.co=np.array(v.co)+np.linalg.solve(trans[i,:3,:3],posed[i]-original[i])
 ob.data.update();path=W/f'body_l{level}_contact_fit.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path));tag=f'body_l{level}_contact_fit';render(ob,rig,'body',level,tag,P/'work/round2/metric_tiers/baked/arc1_a')
 result=json.loads(subprocess.check_output(['/usr/bin/python3',str(P/'scripts/round2_reduction_metrics.py'),str(D),f'body_l{level}_arc1_a_high',tag],text=True));row={'part':'body','lod':level,'triangles':sum(len(f.vertices)-2 for f in ob.data.polygons),'blend':str(path.relative_to(P)),'grip_iterations':iteration+1,'max_grip_correction_m':float(np.linalg.norm(local-before,axis=1).max()),'sole_vertices':soles,**result};records.append(row);(D/'distance_contact_fit.json').write_text(json.dumps(records,indent=2));print('CONTACT_FIT',level,result['pooled_iou'],row['max_grip_correction_m'],{k:len(v)for k,v in soles.items()},flush=True)
