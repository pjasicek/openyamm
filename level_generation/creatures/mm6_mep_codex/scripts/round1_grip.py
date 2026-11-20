import bpy,json,sys,math,numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import pose_helpers as ph,common
bpy.ops.wm.open_mainfile(filepath=str(P/'review/round1/before/mm6_mep.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Mep'];ph.init(r);ph.setact(None)
for pb in r.pose.bones:pb.matrix_basis.identity()
shift_local=Vector((0,.001725,.01137));delta=r.data.bones['B_R_Hand'].matrix_local.to_3x3()@shift_local
for v in b.data.vertices:
 if b.data.attributes['piece'].data[v.index].value==100:v.co+=delta
bpy.context.view_layer.objects.active=r;bpy.ops.object.mode_set(mode='EDIT')
for name in ['Staff','Socket_Staff_Head']:
 eb=r.data.edit_bones[name];eb.head+=delta;eb.tail+=delta
bpy.ops.object.mode_set(mode='OBJECT')
M=r.data.bones['Staff'].matrix_local;inv=M.inverted();handgroup=b.vertex_groups['B_R_Hand'].index
for v in b.data.vertices:
 if sum(g.weight for g in v.groups if g.group==handgroup)<.75:continue
 x=inv@v.co;radius=math.hypot(x.x,x.z)
 if abs(x.y)<.065 and .012<radius<.04:
  shift=min(radius-.012,.0025*max(0,min(1,(.04-radius)/.018)));factor=(radius-shift)/radius;x.x*=factor;x.z*=factor;v.co=M@x
ph.setact(bpy.data.actions['Standing']);bpy.context.scene.frame_set(0);base=ph.capture();ph.apply(base)
lab=np.array([v.value for v in b.data.attributes['finger'].data]);piece=np.array([v.value for v in b.data.attributes['piece'].data]);rest=np.array([v.co[:] for v in b.data.vertices]);inv=r.pose.bones['Staff'].matrix.inverted();axis=r.pose.bones['Staff'].matrix.to_3x3()@Vector((0,1,0));FJ=json.loads((P/'work/finger_joints.json').read_text())['R']
chains={i:[f'B_R_Finger{i}',f'B_R_Finger{i}1',f'B_R_Finger{i}2'] for i in range(1,5)};chains[0]=['B_R_Finger0','B_R_Finger0.001','B_R_Finger0.002']
def turn(n,axis,ang):
 pb=r.pose.bones[n];m=pb.matrix.copy();q=Quaternion(axis,ang)@m.to_quaternion();m2=q.to_matrix().to_4x4();m2.translation=m.translation;pb.matrix=m2;ph.update()
def score(i):
 ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();ids=np.flatnonzero((lab==i+1)&(piece==3));pts=np.array([inv@me.vertices[int(j)].co for j in ids]);ev.to_mesh_clear();rad=np.linalg.norm(pts[:,[0,2]],axis=1);lo=rad.min();ch=chains[i];pb=r.pose.bones[ch[-1]];tip=inv@(pb.matrix@pb.bone.matrix_local.inverted()@Vector(FJ[ch[-1]+'_tip']));tiprad=np.linalg.norm(np.array(tip)[[0,2]])
 centers=[inv@r.pose.bones[n].head for n in ch[1:]]+[tip];cr=np.linalg.norm(np.array(centers)[:,[0,2]],axis=1)
 return 800*max(0,.0115-lo)**2+80*(lo-.012)**2+12*(tiprad-.018)**2+2*np.mean((cr-.022)**2)
for i,ch in chains.items():
 for step in [15,8,4,2,1]:
  for repeat in range(3):
   changed=False
   for n in ch:
    axes=[axis] if i else [axis,Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1))] if n==ch[0] else [axis,Vector((1,0,0))]
    for ax in axes:
     old=r.pose.bones[n].rotation_quaternion.copy();best=(score(i),old)
     for d in [-step,step]:
      r.pose.bones[n].rotation_quaternion=old;ph.update();turn(n,ax,math.radians(d));value=score(i)
      if value<best[0]-1e-10:best=(value,r.pose.bones[n].rotation_quaternion.copy());changed=True
     r.pose.bones[n].rotation_quaternion=best[1];ph.update()
   if not changed:break
 print('FITTED_DIGIT',i,'objective',score(i),flush=True)
G=json.loads((P/'work/grip_pose.json').read_text());G['shift_hand_local']=list(shift_local);G['finger_local']={n:list(r.pose.bones[n].rotation_quaternion) for ch in chains.values() for n in ch};(P/'work/round1_grip.json').write_text(json.dumps(G,indent=2))
# Save an editable contact study; runtime gate measurements come only from the shared runner.
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round1_grip.blend'));common.workbench_clay(bpy.context.scene,True);center=r.pose.bones['Staff'].head
for view,delta in [('front',(0,-1,0)),('back',(0,1,0)),('side',(-1,0,0))]:
 d=Vector(delta);cam=common.ortho_camera('GripCamera',center+d,(0,0,0),.28);cam.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler();sc=bpy.context.scene;sc.camera=cam;sc.render.resolution_x=sc.render.resolution_y=650;sc.render.filepath=str(P/f'review/round1/grip_{view}.png');bpy.ops.render.render(write_still=True)
