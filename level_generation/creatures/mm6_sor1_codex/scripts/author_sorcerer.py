import bpy,bmesh,math,json,sys
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'))
bpy.ops.wm.open_mainfile(filepath=str(p/'work/motion_clean.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene
scene.render.fps=30
import arm_solver as sol
right=sol.Side('B_R_');left=sol.Side('B_L_');G=sol.G
names=[b.name for b in rig.data.bones]
def action(a):
 rig.animation_data_create();rig.animation_data.action=a
 if a.slots:rig.animation_data.action_slot=a.slots[0]
def sample(a,f):
 action(a);scene.frame_set(int(f),subframe=f-int(f))
 return {n:rig.pose.bones[n].matrix_basis.copy() for n in names}
def setpose(d):
 rig.animation_data.action=None
 for n,m in d.items():rig.pose.bones[n].matrix_basis=m
 bpy.context.view_layer.update()
def key(a,f):
 d={n:rig.pose.bones[n].matrix_basis.copy() for n in names}
 action(a)
 for n,m in d.items():
  pb=rig.pose.bones[n];pb.matrix_basis=m;pb.rotation_mode='QUATERNION'
  pb.keyframe_insert('rotation_quaternion',frame=f)
  if n=='B_Pelvis':pb.keyframe_insert('location',frame=f)
 rig.animation_data.action=None

def curve(keys,t):
 for (a,x),(b,y) in zip(keys,keys[1:]):
  if a<=t<=b:
   u=(t-a)/(b-a);u=u*u*(3-2*u);return Vector(x).lerp(Vector(y),u)
 return Vector(keys[-1][1])

def free_arm(side,W,pole,Rh=None):
 S=rig.pose.bones[side.s+'UpperArm'].head.copy();Rsh=rig.pose.bones[side.s+'Clavicle'].matrix.to_3x3()
 E,W2=side.ik(S,W,pole)
 Ra=Rsh@side.rel['UpperArm'];Ra=(Ra@side.uA).rotation_difference((E-S).normalized()).to_matrix()@Ra
 Rf=Ra@side.rel['Forearm'];Rf=(Rf@side.uF).rotation_difference((W2-E).normalized()).to_matrix()@Rf
 if Rh is None:Rh=Rf@side.rel['Hand']
 side.apply(dict(Ra=Ra,Rf=Rf,Rh=Rh,S=S,E=E,W=W2))
 return (W-W2).length

def leg_ik(sd,target):
 up,lo,foot=[rig.pose.bones[f'B_{sd}_{n}'] for n in ['Thigh','Calf','Foot']]
 A=up.head.copy();W=target.translation;L1=(rig.data.bones[lo.name].head_local-rig.data.bones[up.name].head_local).length;L2=(rig.data.bones[foot.name].head_local-rig.data.bones[lo.name].head_local).length
 d=W-A;dist=min(d.length,(L1+L2)*.999);u=d.normalized();q=(L1*L1+dist*dist-L2*L2)/(2*dist)
 pole=Vector((0,-1,0));pole=(pole-u*pole.dot(u)).normalized();E=A+u*q+pole*math.sqrt(max(0,L1*L1-q*q));W2=A+u*dist
 for pb,dst,child in [(up,E,lo),(lo,W2,foot)]:
  R=pb.matrix.to_3x3();old=(child.head-pb.head).normalized();R=old.rotation_difference((dst-pb.head).normalized()).to_matrix()@R
  M=R.to_4x4();M.translation=pb.head;pb.matrix=M;bpy.context.view_layer.update()
 M=target.copy();M.translation=W2;foot.matrix=M;bpy.context.view_layer.update()
 return (W2-W).length

src={n:bpy.data.actions[n] for n in ['Standing','Walking','Attack','Cast','Hit','Death','Fidget']}
standing=sample(src['Standing'],0);setpose(standing)
standfoot={sd:rig.pose.bones[f'B_{sd}_Foot'].matrix.copy() for sd in ['L','R']}
standpel=rig.pose.bones['B_Pelvis'].head.copy()
# Save source samples before replacing actions. Timing stays 30 fps and native roles remain separate.
data={n:[sample(a,f) for f in range(int(a.frame_range[1])+1)] for n,a in src.items()}
for n,a in src.items():a.name='Source_'+n;a.use_fake_user=False
report={}
for role in data:
 N={'Standing':60,'Walking':24,'Attack':36,'Cast':33,'Hit':21,'Death':len(data[role])-1,'Fidget':72}[role]
 out=bpy.data.actions.new(role);out.use_fake_user=True;out.use_frame_range=True;out.frame_start=0;out.frame_end=N
 prevphi=None;miss=0;legmiss=0
 for f in range(N+1):
  t=f/N;i=round(t*(len(data[role])-1));d=data[role][i]
  if role=='Death':
   blend=min(1.,f/6);blend=blend*blend*(3-2*blend)
   pose={n:(standing[n].lerp(d[n],blend) if n=='B_Pelvis' or any(k in n for k in ['Thigh','Calf','Foot','Toe']) else authored_stand[n].copy()) for n in names}
  elif role in ['Standing','Walking']:pose={n:m.copy() for n,m in d.items()}
  else:
   pose={n:m.copy() for n,m in standing.items()}
   amount=.40 if role=='Hit' else .25
   for n in ['B_Spine','B_Spine1','B_Spine2','B_Neck','B_Head']:
    pose[n]=standing[n].to_quaternion().slerp(d[n].to_quaternion(),amount).to_matrix().to_4x4()
  setpose(pose)
  # Discrete left-foot steps, 2 cm (roughly one fifth of the source stance travel), with a 1 cm lift.
  if role in ['Attack','Cast','Fidget']:
   step=curve([(0,(0,0,0)),(.2,(0,0,0)),(.32,(0,-.01,.01)),(.43,(0,-.02,0)),(.68,(0,-.02,0)),(.80,(0,-.01,.01)),(.91,(0,0,0)),(1,(0,0,0))],t)
   for sd in ['L','R']:
    target=standfoot[sd].copy()
    if sd=='L':target.translation+=step
    legmiss=max(legmiss,leg_ik(sd,target))
  pelvis=rig.pose.bones['B_Pelvis'].head.copy();delta=pelvis-standpel
  D=rig.pose.bones['B_Spine2'].matrix@rig.data.bones['B_Spine2'].matrix_local.inverted()
  if role!='Death':
   axis=Vector((-.035,-.10,1)).normalized()
   grip=Vector((-.35,-.23,1.09))+delta
   grip.z=max(grip.z,1.05*axis.z+.015)
   pole=Vector((-.6,-.2,-1))
   r=right.solve(grip,axis,pole,prevphi,steps=144);prevphi=r['phi'];miss=max(miss,r['miss']);right.apply(r)
  for n,q in G['finger_local'].items():
   rig.pose.bones[n].rotation_mode='QUATERNION';rig.pose.bones[n].rotation_quaternion=q
  if role=='Death':
   H=rig.pose.bones['B_R_Hand'].matrix.copy();armD=rig.pose.bones['B_Spine2'].matrix@rig.data.bones['B_Spine2'].matrix_local.inverted()
   amount=.075*min(1.,t*3)
   free_arm(right,H.translation+armD.to_3x3()@Vector((-amount,0,0)),armD.to_3x3()@Vector((-.6,-.2,-1)),H.to_3x3())
  if role!='Death':
   idle=(.28,-.075,1.005)
   if role=='Attack':
    W=curve([(0,idle),(.16,(.29,-.15,1.20)),(.43,(.26,-.26,1.60)),(.55,(.29,-.32,1.56)),(.70,(.29,-.43,1.40)),(1,idle)],t)
   elif role=='Cast':
    W=curve([(0,idle),(.25,(.24,-.19,1.39)),(.55,(.27,-.43,1.42)),(.73,(.27,-.43,1.42)),(1,idle)],t)
   elif role=='Hit':
    W=curve([(0,idle),(.27,(.22,-.25,1.42)),(.48,(.23,-.25,1.43)),(1,idle)],t)
   elif role=='Fidget':
    W=curve([(0,idle),(.25,(.19,-.20,1.40)),(.45,(.185,-.195,1.425)),(.58,(.195,-.19,1.405)),(.70,(.19,-.195,1.42)),(1,idle)],t)
   else:
    W=Vector(idle)
    if role=='Walking':W.y+=.025*math.sin(2*math.pi*t)
   free_arm(left,W+delta,Vector((.4,0,-1)))
   # Open casting fingers; the native left hand presents the palm and never grips a weapon.
   for n in names:
    if n.startswith('B_L_Finger'):rig.pose.bones[n].matrix_basis=Matrix()
  bpy.context.view_layer.update()
  # Ground the support surface as a whole. No limb translations or bone scaling.
  ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh()
  pieces=body.data.attributes['piece'].data
  low=min(v.co.z for v in em.vertices if pieces[v.index].value!=100)
  ev.to_mesh_clear()
  if role=='Death':
   H=rig.pose.bones['B_R_Hand'].matrix;C=H@Vector(G['handle_centre_hand_local']);A=(H.to_3x3()@Vector(G['handle_axis_hand_local'])).normalized()
   low=min(low,(C-A*1.05).z-.012,(C+A*.71).z-.035)
  pb=rig.pose.bones['B_Pelvis'];M=pb.matrix.copy();M.translation.z+=.004-low;pb.matrix=M
  bpy.context.view_layer.update();key(out,f)
  if role=='Standing' and f==0:authored_stand={n:rig.pose.bones[n].matrix_basis.copy() for n in names}
 report[role]={'frames':N+1,'seconds':N/30,'staff_ik_miss_mm':miss*1000,'step_ik_miss_mm':legmiss*1000}
 print('AUTHOR',role,report[role])
# No helper source actions in the runtime.
rig.animation_data.action=None
for a in list(bpy.data.actions):
 if a.name.startswith('Source_'):bpy.data.actions.remove(a)
for pb in rig.pose.bones:pb.matrix_basis=Matrix()
bpy.context.view_layer.update()
# Simple native staff: wood shaft, gilded crown and red gem. All geometry is original, about 650 triangles.
H=rig.data.bones['B_R_Hand'].matrix_local
C=H@Vector(G['handle_centre_hand_local']);axis=(H.to_3x3()@Vector(G['handle_axis_hand_local'])).normalized();Q=Vector((0,0,1)).rotation_difference(axis)
bm=bmesh.new();parts=[]
def cone(z0,z1,r0,r1,mat,xy=(0,0),sides=10):
 ret=bmesh.ops.create_cone(bm,cap_ends=True,segments=sides,radius1=r0,radius2=r1,depth=z1-z0)
 for v in ret['verts']:v.co+=Vector((xy[0],xy[1],(z0+z1)/2))
 for face in {f for v in ret['verts'] for f in v.link_faces}:face.material_index=mat
cone(0,1.64,.0105,.0105,0)
cone(0,.035,.014,.014,1);cone(1.57,1.65,.025,.017,1)
for z in [.90,1.10,1.46]:cone(z,z+.022,.013,.013,1)
for k in range(4):
 a=k*math.pi/2;xy=(.028*math.cos(a),.028*math.sin(a));cone(1.63,1.76,.011,.002,1,xy,6)
ret=bmesh.ops.create_icosphere(bm,subdivisions=2,radius=.035)
for v in ret['verts']:v.co.z*=1.45;v.co.z+=1.705
for face in {f for v in ret['verts'] for f in v.link_faces}:face.material_index=2
for v in bm.verts:v.co=C+Q@(v.co-Vector((0,0,1.05)))
bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bmesh.ops.triangulate(bm,faces=bm.faces)
me=bpy.data.meshes.new('Staff');bm.to_mesh(me);bm.free();staff=bpy.data.objects.new('Staff',me);scene.collection.objects.link(staff)
for name,col in [('StaffWood',(.16,.055,.018,1)),('StaffGold',(.65,.36,.055,1)),('StaffGem',(.55,.012,.018,1))]:
 m=bpy.data.materials.new(name);m.diffuse_color=col;me.materials.append(m)
for obj in scene.objects:obj.select_set(obj==rig)
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT');b=rig.data.edit_bones.new('B_Staff');b.head=C;b.tail=C+axis*.2;b.parent=rig.data.edit_bones['B_R_Hand'];bpy.ops.object.mode_set(mode='OBJECT')
staff.vertex_groups.new(name='B_Staff').add(list(range(len(me.vertices))),1,'REPLACE');m=staff.modifiers.new('Armature','ARMATURE');m.object=rig;staff.parent=rig
scene['staff']=json.dumps({'length':1.76,'grip_from_foot':1.05,'radius':.0105,'centre':list(C),'axis':list(axis)})
scene['author_report']=json.dumps(report);(p/'work/author_report.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/motion_staff.blend'))
