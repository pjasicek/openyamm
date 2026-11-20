"""Refine the fitted fist against the actual skinned triangles, not just finger centrelines."""
import bpy,sys,json,math,os,runpy
from pathlib import Path
import numpy as np
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];os.chdir(P);sys.path.insert(0,str(P/'scripts'))
import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_grip.blend1'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data
act=bpy.data.actions['GripRef'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];bpy.context.scene.frame_set(8)
G=json.loads((P/'work/grip_pose.json').read_text());G['finger_local']={n:list(rig.pose.bones[n].rotation_quaternion) for n in G['finger_local']};(P/'work/grip_pose_initial.json').write_text(json.dumps(G,indent=2));rig.animation_data.action=None
for n,q in G['finger_local'].items():rig.pose.bones[n].rotation_quaternion=Quaternion(q)
bpy.context.view_layer.update()
H=rig.pose.bones['B_R_Hand'].matrix.copy();C=np.array(H@Vector(G['handle_centre_hand_local']));A=np.array((H.to_3x3()@Vector(G['handle_axis_hand_local'])).normalized());radius=.0157
co=np.array([tuple(v.co) for v in me.vertices]);lab=np.array([d.value for d in me.attributes['finger'].data]);bones=list(rig.data.bones);bn=[b.name for b in bones];bi={n:i for i,n in enumerate(bn)}
rest={b.name:b.matrix_local.copy() for b in bones};pose0={pb.name:pb.matrix.copy() for pb in rig.pose.bones};q0={pb.name:pb.rotation_quaternion.copy() for pb in rig.pose.bones}
weights=np.zeros((len(co),len(bn)))
for v in me.vertices:
 for g in v.groups:
  n=body.vertex_groups[g.group].name
  if n in bi:weights[v.index,bi[n]]=g.weight
me.calc_loop_triangles();tri=np.array([list(t.vertices) for t in me.loop_triangles]);ids=np.where((co[:,0]<0)&((lab>0)|(np.linalg.norm(co-np.array(rest['B_R_Hand'].translation),axis=1)<.15)))[0]
tris=tri[np.all(np.isin(tri,ids),axis=1)]
bary=np.array([[1,0,0],[0,1,0],[0,0,1],[.5,.5,0],[.5,0,.5],[0,.5,.5],[1/3]*3])
Q={n:q.copy() for n,q in q0.items()}
def skin(qs):
 mats={};D=[]
 for b in bones:
  n=b.name
  if n in G['finger_local']:
   parent=b.parent.name;basis=qs[n].to_matrix().to_4x4();m=mats[parent]@rest[parent].inverted()@rest[n]@basis
  else:m=pose0[n]
  mats[n]=m;D.append(np.array(m@rest[n].inverted()))
 v=np.einsum('nj,jab,nb->na',weights,np.array(D),np.c_[co,np.ones(len(co))])[:,:3]
 return v,mats
initial,_=skin(Q)
v,m=skin(Q)
rel=v-C;al=rel@A;rad=np.linalg.norm(rel-np.outer(al,A),axis=1)
for i in np.where((co[:,0]<0)&(lab>0)&(rad<.02)&(np.abs(al)<.075))[0]:
 print('NEAR',int(i),'label',lab[i],'radius',rad[i],'groups',[(bn[j],float(weights[i,j])) for j in np.where(weights[i]>.001)[0]],flush=True)
for i in range(5):
 ch=[n for n in G['finger_local'] if n.startswith(f'B_R_Finger{i}')]
 print('FINGER',i,[(n,tuple(m[n].translation),list(Q[n])) for n in ch],flush=True)
