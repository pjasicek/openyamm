import bpy,sys,math,json,runpy
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];W=P/'work';sys.path.insert(0,str(P/'scripts'));import armik
bpy.ops.wm.open_mainfile(filepath=str(W/'gate_repair_attack.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
# Put the fist on the plain round shaft, clear of a raised decorative band.
prop=bpy.data.objects['TridentMesh'];B=rig.data.bones['Trident'].matrix_local;inv=B.inverted()
for v in prop.data.vertices:
 q=inv@v.co
 if q.y<.42:q.z*=1.75
 q.y-=.12;v.co=B@q
names=[b.name for b in rig.data.bones];groups=[g.name for g in body.vertex_groups]
rest=np.array([tuple(v.co) for v in body.data.vertices]);soles={}
for side in 'LR':
 mask=np.array([sum(e.weight for e in v.groups if groups[e.group] in (f'B_{side}_Foot',f'B_{side}_Toe0'))>.3 for v in body.data.vertices]);ids=np.flatnonzero(mask);ids=ids[rest[ids,2]<=rest[ids,2].min()+.005];along=-rest[ids,1];soles[side]=(ids,ids[along<=np.quantile(along,.3)],ids[along>=np.quantile(along,.7)])
def act(a):
 rig.animation_data.action=a
 if a is not None and len(a.slots):rig.animation_data.action_slot=a.slots[0]
def pos():
 bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();out=np.array([tuple(body.matrix_world@v.co) for v in me.vertices]);ev.to_mesh_clear();return out
def leg(s,dz):
    th,ca,ft=[f'B_{s}_{n}' for n in ('Thigh','Calf','Foot')]
    H,K,A=[armik.W(rig,n).translation.copy() for n in (th,ca,ft)];Rf=armik.W(rig,ft).to_3x3().normalized()
    a,b=(K-H).length,(A-K).length;T=A+Vector((0,0,dz));D=T-H;dist=min(D.length,(a+b)*.9999);u=D.normalized()
    v=K-H;v-=u*v.dot(u)
    if v.length<1e-5:v=Vector((0,-1,0))-u*u.dot(Vector((0,-1,0)))
    v.normalize();c=np.clip((a*a+dist*dist-b*b)/(2*a*dist),-1,1);Kn=H+a*(u*float(c)+v*math.sqrt(max(0,1-c*c)))
    M=armik.W(rig,th);q=(K-H).rotation_difference(Kn-H);armik.set_world(rig,th,armik.rot_world(M,q.to_matrix()@M.to_3x3().normalized()))
    M=armik.W(rig,ca);cur=armik.W(rig,ft).translation-M.translation;q=cur.rotation_difference(H+u*dist-M.translation)
    armik.set_world(rig,ca,armik.rot_world(M,q.to_matrix()@M.to_3x3().normalized()));armik.set_world(rig,ft,armik.rot_world(armik.W(rig,ft),Rf))
    assert abs((armik.W(rig,ca).translation-armik.W(rig,th).translation).length-a)<1e-5

for name in ('Standing','Walking','Running','Attack','Hit','Fidget','Death'):
 a=bpy.data.actions[name];end=float(a.frame_range[1]);frames=np.arange(0,end+.001,.25);saved=[]
 for f in frames:
  act(a);sc.frame_set(int(f),subframe=float(f%1));saved.append({n:rig.pose.bones[n].matrix_basis.copy() for n in names})
 rows=[];origin=None
 for f,snap in zip(frames,saved):
  act(None)
  for n,m in snap.items():rig.pose.bones[n].matrix_basis=m
  bpy.context.view_layer.update()
  if name in ('Walking','Running'):
   M=armik.W(rig,'B_Pelvis')
   if origin is None:origin=M.translation.copy()
   M.translation.x=origin.x;M.translation.y=origin.y;armik.set_world(rig,'B_Pelvis',M)
  if name=='Death':
   # Hold the fork outside the hip during the backward fall.
   w=min(1,float(f)/18);w=w*w*(3-2*w)
   chest=armik.W(rig,'B_Spine2').to_3x3()@rig.data.bones['B_Spine2'].matrix_local.to_3x3().inverted();axis=chest@Vector((0,-1,0));M=armik.W(rig,'B_L_UpperArm');origin_arm=M.translation.copy();M=Matrix.Rotation(math.radians(18)*w,4,axis)@M;M.translation=origin_arm;armik.set_world(rig,'B_L_UpperArm',M)
  else:
   if name in ('Standing','Attack','Fidget','Hit'):
    for side in 'LR':rig.pose.bones[f'B_{side}_Toe0'].matrix_basis.identity()
   for _ in range(2):
    V=pos()
    for side,(ids,heel,toe) in soles.items():
     foot=f'B_{side}_Foot';M=armik.W(rig,foot);pivot=M.translation.copy()
     if name in ('Standing','Attack','Fidget','Hit'):
      patch=V[ids];_,_,vv=np.linalg.svd(patch-patch.mean(0),full_matrices=False);normal=Vector(vv[-1]);normal=normal if normal.z>=0 else -normal;M=normal.rotation_difference(Vector((0,0,1))).to_matrix().to_4x4()@M;M.translation=pivot;armik.set_world(rig,foot,M);V=pos()
     d=Vector(V[toe].mean(0)-V[heel].mean(0));d.z=0
     desired=Vector((math.sin(math.radians(0))*(1 if side=='L' else -1),-math.cos(math.radians(0)),0));yaw=math.atan2(d.cross(desired).z,d.dot(desired));M=Matrix.Rotation(yaw,4,'Z')@armik.W(rig,foot);M.translation=pivot;armik.set_world(rig,foot,M)
   if name=='Walking':
    V=pos()
    for side,(ids,_,_) in soles.items():
     low=float(V[ids,2].min());w=float(np.clip((low-.003)/.035,0,1));leg(side,.065*w*w*(3-2*w))
  for side in ('R',):
   ua,fa,hd=[f'B_{side}_{n}' for n in ('UpperArm','Forearm','Hand')];M=armik.W(rig,fa);H=armik.W(rig,hd).to_3x3().normalized();u=armik.W(rig,ua).to_3x3()@Vector((0,0,-1));u.normalize();fdir=armik.W(rig,hd).translation-M.translation;projected=fdir-u*fdir.dot(u)
   q=fdir.rotation_difference(projected);armik.set_world(rig,fa,armik.rot_world(M,q.to_matrix()@M.to_3x3().normalized()));armik.set_world(rig,hd,armik.rot_world(armik.W(rig,hd),H))
  rows.append({n:rig.pose.bones[n].matrix_basis.copy() for n in names})
 bpy.data.actions.remove(a);a=bpy.data.actions.new(name);a.use_fake_user=True;a.use_frame_range=True;a.frame_start=0;a.frame_end=end;act(a);prev={}
 for f,snap in zip(frames,rows):
  for n,m in snap.items():
   pb=rig.pose.bones[n];q=m.to_quaternion()
   if n in prev and q.dot(prev[n])<0:q=-q
   prev[n]=q;pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=float(f))
   if n=='B_Pelvis':pb.location=m.translation;pb.keyframe_insert('location',frame=float(f))
 print('POSE REPAIR',name,flush=True)
# Recompute twist helper rotations only; existing weighted geometry and UVs remain authoritative.
FA=.6;UA=.5
source=(P/'scripts/twist_bones.py').read_text();code=source[source.index('def twist_about('):source.index("for act in [a for a in bpy.data.actions if a.use_fake_user]:")];exec(code)
for a in bpy.data.actions:
 if a.name in ('Standing','Walking','Running','Attack','Hit','Fidget','Death'):bake_twist(a)
bpy.ops.wm.save_as_mainfile(filepath=str(W/'gate_repair_feet.blend'))
sys.argv=['pauldrons.py','--',str(W/'gate_repair_feet.blend'),str(W/'gate_repair_helpers.blend')];runpy.run_path(str(P/'scripts/pauldrons.py'),run_name='__main__')
