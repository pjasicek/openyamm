"""Fit the closed robe around the evaluated leg centreline during the fall."""
import bpy,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_contacts.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene;me=body.data
pv=np.array([a.value for a in me.attributes['piece'].data]);ci=np.where(pv==100)[0];rest=np.array([v.co[:] for v in me.vertices]);bones=[b.name for b in rig.data.bones if b.name.startswith('Robe_')];idx={n:i for i,n in enumerate(bones)};W=np.zeros((len(ci),len(bones)))
for j,i in enumerate(ci):
 for g in me.vertices[int(i)].groups:
  n=body.vertex_groups[g.group].name
  if n in idx:W[j,idx[n]]=g.weight
pinv=np.linalg.solve(W.T@W+.005*np.eye(len(bones)),W.T)
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
a=bpy.data.actions['Death'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];samples=[]
restPelvis=rig.data.bones['B_Pelvis'].matrix_local
z=rest[ci,2];u=np.clip((1.09-z)/.97,0,1);x=rest[ci,0];y=rest[ci,1]+.02
# Hermite interpolation rounds the knee corner without creating an oscillating physical simulation.
def hermite(points,knots,t):
 out=np.zeros((len(t),3));der=np.zeros_like(out)
 slopes=np.empty_like(points);slopes[0]=(points[1]-points[0])/(knots[1]-knots[0]);slopes[-1]=(points[-1]-points[-2])/(knots[-1]-knots[-2]);slopes[1]=(points[2]-points[0])/(knots[2]-knots[0])
 for j in range(2):
  use=(t>=knots[j])&(t<=knots[j+1]);h=knots[j+1]-knots[j];q=((t[use]-knots[j])/h)[:,None]
  out[use]=(2*q**3-3*q**2+1)*points[j]+(q**3-2*q**2+q)*h*slopes[j]+(-2*q**3+3*q**2)*points[j+1]+(q**3-q**2)*h*slopes[j+1]
  der[use]=(6*q*q-6*q)/h*points[j]+(3*q*q-4*q+1)*slopes[j]+(-6*q*q+6*q)/h*points[j+1]+(3*q*q-2*q)*slopes[j+1]
 return out,der
for f in range(int(a.frame_range[1])+1):
 scene.frame_set(f)
 delta=rig.pose.bones['B_Pelvis'].matrix@restPelvis.inverted()
 for n in bones:
  rig.pose.bones[n].matrix=delta@rig.data.bones[n].matrix_local;bpy.context.view_layer.update()
 raw=[rig.pose.bones[n].matrix.copy() for n in bones];ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh();base=np.array([v.co[:] for v in em.vertices]);ev.to_mesh_clear()
 delta=rig.pose.bones['B_Pelvis'].matrix@restPelvis.inverted();top=np.array(delta@Vector((0,-.02,1.09)));knees=np.array([rig.pose.bones['B_'+s+'_Calf'].head[:] for s in 'LR']);feet=np.array([rig.pose.bones['B_'+s+'_Foot'].head[:] for s in 'LR']);middle=knees.mean(0);end=feet.mean(0)
 centre,tangent=hermite(np.array([top,middle,end]),np.array([0,.57,1]),u);up=-tangent/np.linalg.norm(tangent,axis=1)[:,None];right=np.array(delta.to_3x3()@Vector((1,0,0)));across=right-(up@right)[:,None]*up;across/=np.linalg.norm(across,axis=1)[:,None];back=np.cross(up,across)
 # The native skirt broadens toward the hem and encloses both legs, including their separation during the fall.
 left,_=hermite(np.array([top,knees[0],feet[0]]),np.array([0,.57,1]),u);rightPath,_=hermite(np.array([top,knees[1],feet[1]]),np.array([0,.57,1]),u)
 separation=left-rightPath
 nativeX=np.interp(z,[.12,.3,.6,.95,1.09],[.30,.28,.245,.205,.17]);nativeY=np.interp(z,[.12,.3,.6,.95,1.09],[.255,.235,.205,.155,.12])
 widths=np.maximum(nativeX,abs(np.sum(separation*across,axis=1))*.5+.15)
 depths=np.maximum(nativeY,abs(np.sum(separation*back,axis=1))*.5+.15)
 target=centre+across*(x*widths/nativeX)[:,None]+back*(y*depths/nativeY)[:,None]
 target[:,2]=np.maximum(target[:,2],.024)
 correction=pinv@(target-base[ci]);samples.append((f,raw,correction))
for f,raw,correction in samples:
 scene.frame_set(f)
 for j,n in enumerate(bones):
  M=raw[j].copy();M.translation+=Vector(correction[j]);rig.pose.bones[n].matrix=M;bpy.context.view_layer.update();rig.pose.bones[n].keyframe_insert('location',frame=f);rig.pose.bones[n].keyframe_insert('rotation_quaternion',frame=f)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_death_drape.blend'))
