"""Fit the original Orc Walk ankle/toe trajectories, keeping the Ogre's measured leg lengths."""
from pathlib import Path
import bpy,sys,math,json,numpy as np
from mathutils import Vector,Matrix
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import armik,action_curves
bpy.ops.wm.open_mainfile(filepath=str(p/'work/full_repaired.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene;src=json.loads((p/'work/source_walk_paths.json').read_text());rows=src['frames'];rest=src['rest'];parts=np.array([a.value for a in body.data.attributes['piece'].data]);feet={s:np.flatnonzero(parts==k) for s,k in [('L',4),('R',5)]}
def act(a):
 rig.animation_data.action=a
 if a is not None:rig.animation_data.action_slot=a.slots[0]
def points():
 bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();x=np.array([tuple(v.co) for v in m.vertices]);ev.to_mesh_clear();return x
st=bpy.data.actions['Standing'];act(st);sc.frame_set(0);home=armik.W(rig,'B_Pelvis').translation.copy();target=bpy.data.actions['Walking'];N=36;frames=[];coef={};local={};min_toe={};rest_pitch={}
for side,long in [('L','Left'),('R','Right')]:
 our=[rig.data.bones[f'B_{side}_{n}'].head_local for n in ('Thigh','Calf','Foot')];their=[Vector(rest[long+n]) for n in ('UpLeg','Leg','Foot')];coef[side]=sum((our[i+1]-our[i]).length for i in (0,1))/sum((their[i+1]-their[i]).length for i in (0,1));F=rig.data.bones[f'B_{side}_Foot'].matrix_local;local[side]=[F.inverted()@body.data.vertices[int(i)].co for i in feet[side]];min_toe[side]=min(r[long+'ToeBase'][2] for r in rows);d=Vector(rest[long+'ToeBase'])-Vector(rest[long+'Foot']);rest_pitch[side]=math.atan2(d.z,math.hypot(d.x,d.y))
k=sum(coef.values())/2;offset_z=sum(rig.data.bones[f'B_{s}_Foot'].head_local.z-rest[l+'Foot'][2]*k for s,l in [('L','Left'),('R','Right')])/2;mean_xy=np.array([r['Hips'][:2] for r in rows]).mean(0);mean_z=float(np.mean([r['Hips'][2] for r in rows]))
for i,row in enumerate(rows):
 f=i/2;act(target);sc.frame_set(int(f),subframe=f-int(f));snap={b.name:b.matrix_basis.copy() for b in rig.pose.bones};act(None)
 for n,m in snap.items():rig.pose.bones[n].matrix_basis=m
 bpy.context.view_layer.update();P=armik.W(rig,'B_Pelvis');P.translation=Vector(((row['Hips'][0]-mean_xy[0])*k+home.x,(row['Hips'][1]-mean_xy[1])*k+home.y,home.z+.025+(row['Hips'][2]-mean_z)*k*.35));armik.set_world(rig,'B_Pelvis',P)
 targets={};rots={};poles={}
 for side,long in [('L','Left'),('R','Right')]:
  A=Vector(row[long+'Foot']);T=Vector(row[long+'ToeBase']);S=Vector(row[long+'UpLeg']);K=Vector(row[long+'Leg']);d=T-A;pitch=math.atan2(d.z,math.hypot(d.x,d.y))-rest_pitch[side];yaw=math.radians(8 if side=='L' else -8);R=Matrix.Rotation(yaw,3,'Z')@Matrix.Rotation(-pitch,3,'X')@rig.data.bones[f'B_{side}_Foot'].matrix_local.to_3x3();rots[side]=R;low=min((R@v).z for v in local[side]);lift=max(0,T.z-min_toe[side])*k*.5;delta=(A-Vector(row['Hips']))*k;targets[side]=Vector((P.translation.x+delta.x,P.translation.y+delta.y,lift-low+.004));u=(A-S).normalized();poles[side]=(K-S-u*(K-S).dot(u)).normalized()
 # A rotated bare foot has a different ankle-to-floor distance than the source's boot.
 dz=0
 for side in 'LR':
  H=armik.W(rig,f'B_{side}_Thigh').translation;K=armik.W(rig,f'B_{side}_Calf').translation;A=armik.W(rig,f'B_{side}_Foot').translation;L=(K-H).length+(A-K).length;d=targets[side]-H;horizontal=math.hypot(d.x,d.y);zmax=math.sqrt(max(0,(L*.995)**2-horizontal**2));dz=max(dz,H.z-targets[side].z-zmax)
 P=armik.W(rig,'B_Pelvis');P.translation.z-=max(0,dz);armik.set_world(rig,'B_Pelvis',P)
 for side in 'LR':
  un,fn,hn=[f'B_{side}_{n}' for n in ('Thigh','Calf','Foot')];U,F,H=[armik.W(rig,n) for n in (un,fn,hn)];S,E,A=[m.translation.copy() for m in (U,F,H)];a,b=(E-S).length,(A-E).length;d=targets[side]-S;dist=min(d.length,(a+b)*.999);u=d.normalized();v=(poles[side]-u*poles[side].dot(u)).normalized();ca=np.clip((a*a+dist*dist-b*b)/(2*a*dist),-1,1);K=S+a*(u*ca+v*math.sqrt(max(0,1-ca*ca)));q=(E-S).normalized().rotation_difference((K-S).normalized());armik.set_world(rig,un,armik.rot_world(U,q.to_matrix()@U.to_3x3()));F=armik.W(rig,fn);cur=armik.W(rig,hn).translation-F.translation;q=cur.normalized().rotation_difference((targets[side]-F.translation).normalized());armik.set_world(rig,fn,armik.rot_world(F,q.to_matrix()@F.to_3x3()));H=armik.W(rig,hn);armik.set_world(rig,hn,armik.rot_world(H,rots[side]));rig.pose.bones[f'B_{side}_Toe0'].matrix_basis=Matrix()
 x=points();low=min(x[ix,2].min() for ix in feet.values());P=armik.W(rig,'B_Pelvis');P.translation.z+=.004-float(low);armik.set_world(rig,'B_Pelvis',P);frames.append({b.name:b.matrix_basis.copy() for b in rig.pose.bones})
frames[-1]=frames[0];act(target);previous={}
for i,x in enumerate(frames):
 for n,m in x.items():
  b=rig.pose.bones[n];q=m.to_quaternion()
  if n in previous and q.dot(previous[n])<0:q=-q
  previous[n]=q.copy();b.rotation_quaternion=q;b.keyframe_insert('rotation_quaternion',frame=i/2)
  if n=='B_Pelvis':b.location=m.translation;b.keyframe_insert('location',frame=i/2)
action_curves.continuous(target);act(None);bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/full_repaired.blend'));print('SOURCE WALK leg ratios',coef)
