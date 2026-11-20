"""Clear the thigh during collapse; add restrained quiver swing and dense string release keys."""
from pathlib import Path
import bpy,sys,math,json,numpy as np
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import armik
bpy.ops.wm.open_mainfile(filepath=str(P/'work/grounded.blend'));r=bpy.data.objects['Rig'];sc=bpy.context.scene

def keys(pb,f,prev):
 q=pb.rotation_quaternion.copy()
 if pb.name in prev and q.dot(prev[pb.name])<0:q=-q
 prev[pb.name]=q;pb.rotation_quaternion=q
 for path in ['rotation_quaternion','location','scale']:pb.keyframe_insert(path,frame=float(f))
a=bpy.data.actions['Death'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];frames=np.arange(0,a.frame_range[1]+.001,.25);poses=[]
for f in frames:
 sc.frame_set(int(f),subframe=float(f%1));poses.append({pb.name:pb.matrix_basis.copy() for pb in r.pose.bones})
prev={};adjust=[]
for f,pose in zip(frames,poses):
 r.animation_data.action=None
 for n,M in pose.items():r.pose.bones[n].matrix_basis=M
 bpy.context.view_layer.update();w=math.sin(math.pi*max(0,min(1,(f-20)/24)))**2
 H=armik.W(r,'B_R_Hand').copy();R=r.pose.bones['B_Pelvis'].matrix.to_3x3()@r.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted();side=R@Vector((-1,0,0));side.z=0;side.normalize();target=H.translation+(side*.10+Vector((0,0,.16)))*w
 armik.solve(r,'R',target,hand_rot=H.to_3x3().normalized())
 hand=r.pose.bones['B_R_Hand'];swing,tw=armik.split_swing_twist(hand.rotation_quaternion,Vector((0,1,0)));deg=math.degrees(min(swing.angle,2*math.pi-swing.angle))
 if deg>60:
  limited=60+5*math.tanh((deg-60)/5);hand.rotation_quaternion=Quaternion((1,0,0,0)).slerp(swing,limited/deg)@Quaternion((0,1,0),tw);bpy.context.view_layer.update()
 def twist(q,axis):t=2*math.atan2(Vector((q.x,q.y,q.z)).dot(axis),q.w);return (t+math.pi)%(2*math.pi)-math.pi
 fb,hb=r.data.bones['B_R_Forearm'],r.data.bones['B_R_Hand'];axis=(fb.matrix_local.inverted()@hb.head_local).normalized();rel=(r.pose.bones[fb.name].matrix.inverted()@r.pose.bones[hb.name].matrix).to_quaternion();rest=(fb.matrix_local.inverted()@hb.matrix_local).to_quaternion();r.pose.bones['B_R_ForearmTwist'].rotation_quaternion=Quaternion(axis,.6*twist(rel@rest.inverted(),axis));ub=r.data.bones['B_R_UpperArm'];axis=(ub.matrix_local.inverted()@fb.head_local).normalized();r.pose.bones['B_R_UpperArmTwist'].rotation_quaternion=Quaternion(axis,-.5*twist(r.pose.bones[ub.name].rotation_quaternion,axis))
 adjust.append(armik.wrist_cost(r,'R',armik.W(r,'B_R_Hand').to_3x3().normalized()))
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
 for n in ['B_R_UpperArm','B_R_Forearm','B_R_Hand','B_R_ForearmTwist','B_R_UpperArmTwist']:keys(r.pose.bones[n],f,prev)
(P/'work/death_equipment_wrist.json').write_text(json.dumps({'swing_max':max(x[0] for x in adjust),'twist_max':max(abs(x[1]) for x in adjust)},indent=2))
# Remove the free-arm IK roll drift across the walking loop without changing its timing.
a=bpy.data.actions['Walking'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
end=float(a.frame_range[1]);names=['B_L_UpperArm','B_L_Hand','B_L_ForearmTwist','B_L_UpperArmTwist'];frames=np.arange(0,end+.001,.25);poses=[]
for f in frames:
 sc.frame_set(int(f),subframe=float(f%1));poses.append({n:r.pose.bones[n].rotation_quaternion.copy() for n in names})
delta={n:poses[0][n]@poses[-1][n].inverted() for n in names};prev={}
for f,pose in zip(frames,poses):
 sc.frame_set(int(f),subframe=float(f%1));t=f/end;w=t*t*(3-2*t)
 for n in names:
  pb=r.pose.bones[n];pb.rotation_quaternion=Quaternion((1,0,0,0)).slerp(delta[n],w)@pose[n];keys(pb,f,prev)
for name in ['Running','Hit','Walking','Death']:
 a=bpy.data.actions[name];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];end=float(a.frame_range[1]);frames=np.arange(0,end+.001,.25);desired=[];anchor=Vector((0,.07,.30))
 for f in frames:
  sc.frame_set(int(f),subframe=float(f%1));Q=r.pose.bones['Quiver'].matrix.copy();A=Q@anchor;R=r.pose.bones['B_Pelvis'].matrix.to_3x3()@r.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted();w=math.sin(math.pi*f/end)**2;side=R@Vector((-1,0,0));axis=R@Vector((0,1,0));desired.append(Matrix.Translation(A)@Quaternion(axis,(.24 if name in ('Walking','Running') else .12)*w).to_matrix().to_4x4()@Matrix.Translation(-A)@Q)
 prev={}
 for f,M in zip(frames,desired):
  sc.frame_set(int(f),subframe=float(f%1));pb=r.pose.bones['Quiver'];pb.rotation_mode='QUATERNION';pb.matrix=M;keys(pb,f,prev)
cfg=json.loads((P/'work/props.json').read_text());a=bpy.data.actions['Attack'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];prev={}
def smooth(x):x=max(0,min(1,x));return x*x*(3-2*x)
for f in np.arange(0,a.frame_range[1]+.001,.25):
 sc.frame_set(int(f),subframe=float(f%1));t=f/30;w=smooth((t-1)*30)*(1-smooth((t-1.40)/(.1666667)));nock=Vector(cfg['nock_drawn']).lerp(Vector(cfg['nock_released']),w);C=r.pose.bones['Crossbow'].matrix
 for i,s in enumerate('LR'):
  tip=Vector(cfg['string_tips'][i]);d=nock-tip;M=d.to_track_quat('Y','Z').to_matrix().to_4x4();M.translation=tip;M=M@Matrix.Diagonal((d.length,d.length,d.length,1));pb=r.pose.bones['String'+s];pb.matrix=C@M;pb.rotation_mode='QUATERNION';keys(pb,f,prev)
 pb=r.pose.bones['Bolt'];pb.scale=(1e-6,)*3 if 30<=f<47 else (1,)*3;keys(pb,f,prev)
for a in bpy.data.actions:
 for la in a.layers:
  for st in la.strips:
   for cb in st.channelbags:
    for fc in cb.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
# Match the runtime's four-influence skin before authoring checks and export.
body=bpy.data.objects['Body']
for v in body.data.vertices:
 weights=sorted(((g.weight,g.group) for g in v.groups if g.weight>0),reverse=True)[:4]
 total=sum(w for w,g in weights)
 assert total>0
 for g in list(v.groups):body.vertex_groups[g.group].remove([v.index])
 for w,g in weights:body.vertex_groups[g].add([v.index],w/total,'REPLACE')
r.animation_data.action=None;bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/ready_final.blend'))
