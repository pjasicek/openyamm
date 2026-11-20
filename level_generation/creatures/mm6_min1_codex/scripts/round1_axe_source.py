import bpy,json,math
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/round1_sources.blend'));r=bpy.data.objects['Rig'];sc=bpy.context.scene;sc.render.fps=30
sf={n:Matrix(v['rot']) for n,v in json.loads((P/'work/source_rest.json').read_text()).items()};names=list(r.pose.bones.keys());S=Matrix.Diagonal((-1,1,1));TURN=Matrix.Rotation(math.pi,4,'Z')
r.animation_data.action=bpy.data.actions['Standing'];r.animation_data.action_slot=r.animation_data.action.slots[0];sc.frame_set(0);standing={n:pb.matrix_basis.copy() for n,pb in r.pose.bones.items()};pelvis=r.pose.bones['B_Pelvis'].matrix.copy();chest=r.pose.bones['B_Spine2'].matrix.copy();r.animation_data.action=None
before=set(bpy.data.objects);acts=set(bpy.data.actions);bpy.ops.import_scene.gltf(filepath=str(P.parents[2]/'anim_library/humanoid_set/2Hand Axe.glb'));src=next(o for o in set(bpy.data.objects)-before if o.type=='ARMATURE');W=TURN@src.matrix_world;rate=sc.render.fps
acts2={a.name.split('@')[-1].split('|')[-1]:a for a in set(bpy.data.actions)-acts};a=acts2['2HandAxeAttack5'];src.animation_data.action=a;src.animation_data.action_slot=a.slots[0];f0,f1=a.frame_range;count=round((f1-f0)/rate*30);ratio=pelvis.translation.z/(W@src.data.bones['B_Pelvis'].head_local).z
raw=[]
for i in range(count+1):
 f=f0+i/30*rate;sc.frame_set(int(f),subframe=f%1);raw.append({n:(W@src.pose.bones[n].matrix).copy() for n in sf})
for o in set(bpy.data.objects)-before:bpy.data.objects.remove(o,do_unlink=True)
for a in set(bpy.data.actions)-acts:bpy.data.actions.remove(a)
legs=[n for n in names if any(k in n for k in ['Thigh','Calf','Foot','Toe'])]
def other(n):return n.replace('B_R_','B_L_') if n.startswith('B_R_') else n.replace('B_L_','B_R_') if n.startswith('B_L_') else n
out=[]
for i,row in enumerate(raw):
 for n in names:r.pose.bones[n].matrix_basis=standing[n]
 bpy.context.view_layer.update()
 for n in names:
  if n not in sf or 'Finger' in n:continue
  sn=other(n);R=S@(row[sn].to_3x3().normalized()@sf[sn].inverted())@S@sf[n];m=R.to_4x4();m.translation=S@row[sn].translation*ratio if n=='B_Pelvis' else r.pose.bones[n].head
  r.pose.bones[n].matrix=m;bpy.context.view_layer.update()
 out.append({n:pb.matrix_basis.copy() for n,pb in r.pose.bones.items()})
for mode in ['plant','turn']:
 a=bpy.data.actions.new('Axe5'+mode);a.use_fake_user=True
 for i,row in enumerate(out):
  r.animation_data.action=None
  for n in names:r.pose.bones[n].matrix_basis=row[n]
  bpy.context.view_layer.update();sp=r.pose.bones['B_Spine'].matrix.copy()
  if mode=='plant':
   for n in ['B_Pelvis']+legs:r.pose.bones[n].matrix_basis=standing[n]
   bpy.context.view_layer.update();sp.translation=r.pose.bones['B_Spine'].head;r.pose.bones['B_Spine'].matrix=sp;bpy.context.view_layer.update()
  r.animation_data.action=a
  for n in names:
   pb=r.pose.bones[n];pb.rotation_mode='QUATERNION';pb.keyframe_insert('rotation_quaternion',frame=i);pb.keyframe_insert('location',frame=i)
 a.use_frame_range=True;a.frame_start=0;a.frame_end=count
sc.render.fps=30;bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round1_sources.blend'));print('AXE5 LENGTH',count)
