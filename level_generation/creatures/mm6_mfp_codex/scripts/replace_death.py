import bpy,sys,runpy,json,math,numpy as np
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
P=Path(__file__).resolve().parents[1]
sys.argv=['retarget_mixamo.py','--',str(P/'work/rig_motion.blend'),str(P/'work/death_mixamo.blend'),str(P.parents[2]/'anim_library/mixamo/Falling Forward Death.fbx')+':DeathNew:turn'];runpy.run_path(str(P/'scripts/retarget_mixamo.py'),run_name='__main__')
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_equipped.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene;names=[b.name for b in rig.pose.bones]
code=(P/'scripts/motion.py').read_text();exec(code[code.index('def action'):code.index('baseline=')])
with bpy.data.libraries.load(str(P/'work/death_mixamo.blend'),link=False)as(src,dst):dst.actions=['DeathNew']
raw=dst.actions[0];a=bpy.data.actions['Standing'];native=sample(a,0);nf=int(raw.frame_range[1]);poses=[]
for f in range(nf+1):
 p=sample(raw,f)
 for n in names:
  if n not in json.loads(sc['rig_offsets']):p[n]=native[n]
 w=smooth(f/8);put(blend(native,p,w))
 for pb in rig.pose.bones:
  if 'Finger'in pb.name:pb.rotation_quaternion=Quaternion()
 for sd in 'LR':anatomical(sd)
 poses.append(get())
action(None)
for name in ['Death','Dead','DeathNew']:
 if name in bpy.data.actions:bpy.data.actions.remove(bpy.data.actions[name])
def write(name,frames):
 a=bpy.data.actions.new(name);a.use_fake_user=True;action(a);prev={}
 for f,p in enumerate(frames):
  for n,(q,l,s)in p.items():
   pb=rig.pose.bones[n]
   if n in prev and q.dot(prev[n])<0:q=-q
   prev[n]=q;pb.rotation_quaternion=q;pb.location=l;pb.scale=s;pb.keyframe_insert('rotation_quaternion',frame=f)
   if n=='B_Pelvis':pb.keyframe_insert('location',frame=f)
   if n=='Knife':pb.keyframe_insert('scale',frame=f)
 a.use_frame_range=True;a.frame_start=0;a.frame_end=len(frames)-1;action(None)
write('Death',poses);write('Dead',[poses[-1]]*31)
# The free arm balances outside the skirt while the source right arm performs the knife slash.
a=bpy.data.actions['Attack'];out=[]
for f in range(int(a.frame_range[1])+1):
 p=sample(a,f);put(p)
 for n in names:
  if n.startswith('B_L_')and any(x in n for x in ['Clavicle','UpperArm','Forearm','Hand','Finger']):pb=rig.pose.bones[n];pb.rotation_quaternion=native[n][0]
 bpy.context.view_layer.update();n='B_L_UpperArm';w=math.sin(math.pi*f/a.frame_range[1])**2;rotation(n,Quaternion(Vector((1,0,0)),math.radians(-14)*w).to_matrix()@wm(n).to_3x3());out.append(get())
write('Attack',out)
# Record the deliberate switch after the long-skirt gate exposed the lay-down clip's tucked calves.
(P/'review/death_source_choice.json').write_text(json.dumps({'selected':'anim_library/mixamo/Falling Forward Death.fbx','rejected':['RelaxLaydownLayDown: tucked calves invert skirt during middle phase','UnarmedDeath1: backward fall','Standing Death Forward 01/02: long kneeling/tucked-leg phases'],'source_frames':nf+1,'fps':30},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_equipped.blend'))
runpy.run_path(str(P/'scripts/finish_cloth.py'),run_name='__main__')
