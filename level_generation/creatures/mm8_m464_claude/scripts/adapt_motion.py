"""Retain accepted locomotion/fall; fit a native left-hand-on-hip idle and peasant reactions."""
import bpy,sys,math,json,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
sys.path.insert(0,str(P.parent/'mm8_m480_claude/scripts'));import armik
sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as G
sys.path.insert(0,str(P.parent/'mm6_mfp_codex/scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_uv.blend'));r=bpy.data.objects['Rig'];sc=bpy.context.scene;sc.render.fps=30
cfg=json.loads((P.parent/'mm6_mfp_codex/gates.json').read_text());rest={n:b.matrix_local.copy() for n,b in r.data.bones.items()}
def activate(a,t=0):
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc.frame_set(int(t),subframe=t%1)
def snap():return {p.name:(p.location.copy(),p.rotation_quaternion.copy(),p.scale.copy()) for p in r.pose.bones}
def put(row):
 for n,(l,q,s) in row.items():p=r.pose.bones[n];p.location=l;p.rotation_quaternion=q;p.scale=s
 bpy.context.view_layer.update()
def mix(a,b,w):return {n:(a[n][0].lerp(b[n][0],w),a[n][1].slerp(b[n][1],w),a[n][2].lerp(b[n][2],w)) for n in a}
def ease(x):x=max(0,min(1,x));return x*x*x*(x*(x*6-15)+10)
activate(bpy.data.actions['Standing']);original=snap();pelvis=r.pose.bones['B_Pelvis'].matrix.copy()
U,F,H=[rest['B_L_'+n] for n in ['UpperArm','Forearm','Hand']];finger=(sum((rest[f'B_L_Finger{i}'].translation for i in range(1,5)),Vector())/4-H.translation).normalized();palm=H.to_3x3()@Vector(cfg['hands']['L']['palm_axis']);palm=(palm-finger*palm.dot(finger)).normalized();local=Matrix((H.to_3x3().inverted()@finger,H.to_3x3().inverted()@palm,H.to_3x3().inverted()@finger.cross(palm))).transposed()
def metrics():
 u,f,h=[r.pose.bones['B_L_'+n].matrix for n in ['UpperArm','Forearm','Hand']];parent=r.pose.bones['B_L_UpperArm'].parent
 ur=G.swing_twist(np.array((parent.matrix.to_3x3()@rest[parent.name].to_3x3().inverted()@U.to_3x3()).inverted()@u.to_3x3()),np.array(U.to_3x3().inverted()@(F.translation-U.translation).normalized()))[1]
 fr=G.swing_twist(np.array((u.to_3x3()@U.to_3x3().inverted()@F.to_3x3()).inverted()@f.to_3x3()),np.array(F.to_3x3().inverted()@(H.translation-F.translation).normalized()))[1]
 wf,wr=G.swing_twist(np.array((f.to_3x3()@F.to_3x3().inverted()@H.to_3x3()).inverted()@h.to_3x3()),np.array(H.to_3x3().inverted()@finger))
 return ur,fr,wf,wr
options=[];trials=[]
for x in [.15,.17,.19]:
 for y in [-.174,-.194,-.214]:
  for py in [.25,.4,.6,1.0]:
   for tilt in [10,25,40]:
    put(original);d=Vector((-math.sin(math.radians(tilt)),0,-math.cos(math.radians(tilt))));n=Vector((-1,1.4,0));n=(n-d*n.dot(d)).normalized();R=Matrix((d,n,d.cross(n))).transposed()@local.transposed();w=Vector((x,y,1.03));pole=Vector((.40,py,1.13));armik.solve(r,'L',w,pole=pole,hand_rot=R);ur,fr,wf,wr=metrics()
    # Share pronation with the forearm while holding the palm fixed.
    excess=wr-max(-35,min(35,wr));fa=r.pose.bones['B_L_Forearm'];hand=r.pose.bones['B_L_Hand'];hm=hand.matrix.copy();axis=(hm.translation-fa.matrix.translation).normalized();M=(Quaternion(axis,math.radians(excess)).to_matrix()@fa.matrix.to_3x3()).to_4x4();M.translation=fa.matrix.translation;fa.matrix=M;bpy.context.view_layer.update();hand.matrix=hm;bpy.context.view_layer.update();ur,fr,wf,wr=metrics()
    trials.append((max(abs(ur)/58,abs(fr)/88,wf/68,abs(wr)/43),x,y,py,tilt,ur,fr,wf,wr))
    if max(abs(ur)/58,abs(fr)/88,wf/68,abs(wr)/43)<=1:
     options.append((abs(ur)+abs(fr)*.2+wf*.3+abs(wr)*.3+1000*abs(x-.15),snap(),w,pole,R,(ur,fr,wf,wr)))
print('CLOSEST',sorted(trials)[:6],flush=True)
assert options,'No anatomically feasible hip pose'
best=min(options,key=lambda v:v[0]);put(best[1]);hip=snap();print('HIP_SOLUTION',list(best[2]),list(best[3]),best[5],flush=True)
left=[n for n in hip if n.startswith('B_L_') and any(k in n for k in ['UpperArm','Forearm','Hand','Finger'])]
# The local arm correction follows breathing and torso motion without introducing elbow solver jumps.
delta={n:original[n][1].inverted()@hip[n][1] for n in left}
rows={};durations={}
for role in ['Standing','Fidget','Hit','Death']:
 a=bpy.data.actions[role];end=float(a.frame_range[1]);duration=.75 if role=='Hit' else end/30;durations[role]=duration;times=np.linspace(0,duration,round(duration*48)+1);data=[]
 for t in times:
  activate(a,t/duration*end);row=snap()
  if role in ['Standing','Fidget']:
   for n in left:row[n]=(row[n][0],row[n][1]@delta[n],row[n][2])
  data.append((float(t*30),row))
 rows[role]=data
stand=rows['Standing'][0][1]
for role in ['Hit','Death']:
 duration=durations[role]
 for i,(f,row) in enumerate(rows[role]):
  w=ease((f/30)/(.24 if role=='Hit' else .24))
  if role=='Hit':w=min(w,ease((duration-f/30)/.24))
  row=mix(stand,row,w)
  if role=='Hit':
   # A smaller unarmed recoil keeps the fitted jacket from overstretching at the right axilla.
   n='B_R_UpperArm';row[n]=(row[n][0],stand[n][1].slerp(row[n][1],.85),row[n][2])
  rows[role][i]=(f,row)
for role,data in rows.items():
 old=bpy.data.actions[role];old.name=role+'_source';a=bpy.data.actions.new(role);a.use_fake_user=True;r.animation_data.action=a
 for f,row in data:
  put(row)
  for pb in r.pose.bones:
   for prop in ['location','rotation_quaternion','scale']:pb.keyframe_insert(prop,frame=f,group=pb.name)
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for key in fc.keyframe_points:key.interpolation='LINEAR'
 bpy.data.actions.remove(old)
if 'Attack' in bpy.data.actions:bpy.data.actions.remove(bpy.data.actions['Attack'])
activate(bpy.data.actions['Standing']);bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/animated_master.blend'))
(P/'review/motion_adaptation.json').write_text(json.dumps({'hip_wrist':list(best[2]),'hip_angles':best[5],'retained':['Walking','Running','Death body and fall','Dead'],'removed':'Assassin Attack; both native peasant attack bindings intentionally use Walking','durations_s':durations},indent=2))
common.workbench_clay(sc)
for role,f in [('Standing',0),('Fidget',30),('Hit',10),('Death',8)]:
 activate(bpy.data.actions[role],f);common.render_views(str(P/'review'/f'posed_{role}'),.84,1.9,views=('front','left','three_quarter'),resolution=(520,700))
