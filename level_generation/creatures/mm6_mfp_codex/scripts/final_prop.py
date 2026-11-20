"""Rigid necklace ownership and measured reverse-grip knife fitting/edge orientation."""
import bpy,sys,math,json,runpy,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_equipped.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];k=bpy.data.objects['KnifeAsset'];sc=bpy.context.scene
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/before_prop_fit.blend'))
pv=np.array([x.value for x in b.data.attributes['piece'].data]);co=np.array([v.co[:]for v in b.data.vertices]);jewelry=[]
for part in sorted(set(pv)):
 if part<28:continue
 ids=np.flatnonzero(pv==part);z=co[ids,2].mean();bone='B_Head'if z>1.425 else 'B_Neck'if z>1.365 else 'B_Spine2'
 for g in b.vertex_groups:g.remove(ids.tolist())
 b.vertex_groups[bone].add(ids.tolist(),1,'REPLACE');jewelry.append({'piece':int(part),'bone':bone})
K=r.data.bones['Knife'].matrix_local.copy();local=np.array([tuple(K.inverted()@v.co)for v in k.data.vertices]);centers=[]
for z in np.linspace(-.04,.02,7):
 band=local[abs(local[:,2]-z)<.008]
 if len(band)>3:centers.append(band.mean(0))
centers=np.array(centers);axis=np.linalg.svd(centers-centers.mean(0))[2][0]
if axis[2]<0:axis=-axis
C=centers.mean(0)-axis*centers.mean(0)[2]/axis[2];Q=np.array(Vector(axis).rotation_difference(Vector((0,0,1))).to_matrix());local=(local-C)@Q.T
handle=(local[:,2]>-.040)&(local[:,2]<.025);radius=float(np.percentile(np.linalg.norm(local[handle,:2],axis=1),95));scale=.0088/radius;mix=np.clip((.065-local[:,2])/.035,0,1);local[:,:2]*=(1+(scale-1)*mix)[:,None]
mid=local[(local[:,2]>.07)&(local[:,2]<.17)];ed=np.linalg.svd(mid[:,:2]-mid[:,:2].mean(0))[2][0]
if mid[:,:2].mean(0)@ed>0:ed=-ed
edge=np.r_[ed,0];tip=local[np.argmax(local[:,2])];a=bpy.data.actions['Attack'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];matrices=[];times=np.linspace(0,float(a.frame_range[1])/30,49)
for t in times:sc.frame_set(int(t*30),subframe=float(t*30%1));matrices.append(np.array(r.pose.bones['Knife'].matrix))
M=np.array(matrices);candidates=[]
for degrees in range(0,360,5):
 R=np.array(Matrix.Rotation(math.radians(degrees),3,'Z'));tip2=R@tip;edge2=R@edge;tips=np.einsum('nij,j->ni',M[:,:3,:3],tip2)+M[:,:3,3];vel=np.diff(tips,axis=0)*48;directions=tips-M[:,:3,3];directions/=np.linalg.norm(directions,axis=1)[:,None];edges=np.einsum('nij,j->ni',M[:,:3,:3],edge2);speed=np.linalg.norm(vel,axis=1);lead=np.einsum('ni,ni->n',vel,edges[1:])/np.maximum(speed,1e-8);eligible=(times[1:]>.27)&(times[1:]<.65)&(vel[:,1]<0)&(-directions[1:,1]>.4)
 if not eligible.any():continue
 indices=np.flatnonzero(eligible);j=int(indices[np.argmax(speed[eligible])]);window=np.arange(max(0,j-1),min(len(lead),j+2));score=float(lead[window].mean());candidates.append((score,degrees,j,float(speed[j]),float(lead[j]),float(-directions[j+1,1])))
score,degrees,j,speed,lead,alignment=max(candidates);R=np.array(Matrix.Rotation(math.radians(degrees),3,'Z'));local=local@R.T
for v,c in zip(k.data.vertices,local):v.co=K@Vector(c)
r.animation_data.action=None
for pb in r.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update();bpy.context.view_layer.objects.active=r;bpy.ops.object.mode_set(mode='EDIT');bo=r.data.edit_bones['Socket_Knife_Tip'];bo.head=K@Vector(local[np.argmax(local[:,2])]);bo.tail=bo.head+K.to_3x3()@Vector((0,0,.02));bpy.ops.object.mode_set(mode='OBJECT')
report={'source_grip_axis':axis.tolist(),'source_grip_center':C.tolist(),'source_handle_radius_95_m':radius,'fitted_handle_radius_95_m':.0088,'handle_radial_scale':scale,'edge_roll_degrees':degrees,'blow_time':float(times[j+1]),'tip_speed_m_s':speed,'signed_edge_lead':lead,'mean_edge_lead_3_samples':score,'tip_target_alignment':alignment,'jewelry':jewelry};(P/'review/prop_fit.json').write_text(json.dumps(report,indent=2));print('PROP_FIT',json.dumps({k:v for k,v in report.items()if k!='jewelry'}),flush=True)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_equipped.blend'))
runpy.run_path(str(P/'scripts/probe_current.py'),run_name='__main__');runpy.run_path(str(P/'scripts/bind_textures.py'),run_name='__main__');runpy.run_path(str(P/'scripts/extra_metrics.py'),run_name='__main__')
