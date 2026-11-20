"""Fit the inner collar to the neck and add shoulder-blade ease to the cape."""
from pathlib import Path
import bpy,json,numpy as np
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/full_actions.blend'))
body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];me=body.data;rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update();P=np.array([tuple(v.co) for v in me.vertices]);pv=np.array([v.value for v in me.attributes['piece'].data]);names=[g.name for g in body.vertex_groups]
W=np.zeros((len(P),len(names)))
for v in me.vertices:
 for e in v.groups:W[v.index,e.group]=e.weight
spines=['B_Pelvis','B_Spine','B_Spine1','B_Spine2'];zs=np.array([rig.data.bones[n].head_local.z for n in spines]);gi={n:i for i,n in enumerate(names)}
for i in np.where((pv==0)&(abs(P[:,0])<.26)&(P[:,2]>.98)&(P[:,2]<1.25))[0]:
 z=P[i,2];j=int(np.clip(np.searchsorted(zs,z)-1,0,2));u=float(np.clip((z-zs[j])/(zs[j+1]-zs[j]),0,1))
 amount=float(np.clip((.26-abs(P[i,0]))/.04,0,1)*np.clip((z-.98)/.06,0,1)*np.clip((1.25-z)/.06,0,1))
 row=W[i]*(1-amount);row[gi[spines[j]]]+=amount*(1-u);row[gi[spines[j+1]]]+=amount*u;W[i]=row
 for group in body.vertex_groups:group.remove([int(i)])
 for k in np.where(row>.0001)[0]:body.vertex_groups[k].add([int(i)],float(row[k]/sum(row)),'REPLACE')
# Smooth the small axilla transition; torso ownership must not create an abrupt skin hinge.
adj=[[] for _ in P]
for e in me.edges:
 a,b=e.vertices
 if pv[a]==0 and pv[b]==0:adj[a].append(b);adj[b].append(a)
smooth_ids=np.where((pv==0)&(abs(P[:,0])>.16)&(abs(P[:,0])<.36)&(P[:,2]>.97)&(P[:,2]<1.32))[0]
for _ in range(7):
 old=W.copy()
 for i in smooth_ids:
  if adj[i]:W[i]=.5*old[i]+.5*old[adj[i]].mean(0)
for i in smooth_ids:
 row=W[i]
 for group in body.vertex_groups:group.remove([int(i)])
 for k in np.where(row>.0001)[0]:body.vertex_groups[k].add([int(i)],float(row[k]/sum(row)),'REPLACE')
me.calc_loop_triangles();tris=[tuple(t.vertices) for t in me.loop_triangles if all(pv[i]==0 for i in t.vertices)]
tree=BVHTree.FromPolygons(P.tolist(),tris,all_triangles=True);count=0
for i in np.where((pv==1)&(P[:,2]>.98)&(P[:,2]<1.46))[0]:
 loc,n,fi,d=tree.find_nearest(Vector(P[i]));amount=float(np.clip((.05-d)/.02,0,1)*np.clip((P[i,2]-.98)/.05,0,1)*np.clip((1.46-P[i,2])/.04,0,1))
 if me.attributes['cape'].data[int(i)].value:continue
 if amount<=0:continue
 tri=tris[fi];bc=barycentric_transform(loc,*[Vector(P[j]) for j in tri],Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)))
 bc=np.maximum(bc,0);bc/=sum(bc);row=W[i]*(1-amount)+sum(W[j]*w for j,w in zip(tri,bc))*amount
 for g in body.vertex_groups:g.remove([int(i)])
 for j in np.where(row>.0001)[0]:body.vertex_groups[j].add([int(i)],float(row[j]/sum(row)),'REPLACE')
 count+=1
 if P[i,2]>1.30:
  ease=float(np.clip((P[i,2]-1.30)/.04,0,1)*np.clip((1.46-P[i,2])/.04,0,1))
  outward=Vector((P[i,0]+.012,P[i,1]+.02,0)).normalized()
  me.vertices[int(i)].co+=outward*(.008*ease)
# Extra ease under the left shoulder blade prevents a 4 mm contact during the fall.
cape=np.array([v.value for v in me.attributes['cape'].data])>0
centre=Vector((.213815,.149213,1.123014));a=bpy.data.actions['Death'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(14)
ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh();posed=[v.co.copy() for v in em.vertices];ev.to_mesh_clear()
skin=BVHTree.FromPolygons(posed,tris,all_triangles=True);i=int(np.argmin(np.linalg.norm(P-np.array(centre),axis=1)));loc,n,fi,d=skin.find_nearest(posed[i])
delta=Vector((0,0,0))
if (posed[i]-loc).dot(n)<0:
 deform=Matrix(((0,0,0),(0,0,0),(0,0,0)))
 for e in me.vertices[i].groups:
  b=rig.pose.bones[names[e.group]];deform+=e.weight*(b.matrix@b.bone.matrix_local.inverted()).to_3x3()
 delta=deform.inverted()@(n*(d+.006));print('CAPE_EASE_PROBE',d,list(delta),flush=True);assert delta.length<.025
 for j in np.where(cape)[0]:
  amount=max(0,1-(Vector(P[j])-centre).length/.09)**2
  me.vertices[int(j)].co+=delta*amount
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/full_actions.blend'))
(p/'review/garment_finish.json').write_text(json.dumps({'inner_collar_vertices':count,'cape_ease_rest_delta':list(delta)},indent=2)+'\n')
print('GARMENT_FINISH',count,list(delta),flush=True)
