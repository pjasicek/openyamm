import bpy,json,math,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];out={}
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round7/running_author.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene
for name in ['Standing','Running']:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];zs=[]
 for f in np.linspace(*a.frame_range,97):
  sc.frame_set(int(f),subframe=f%1);zs.append(rig.pose.bones['B_Pelvis'].head.z)
 out[name]={'min':min(zs),'mean':float(np.mean(zs)),'max':max(zs)}
for filename in ['anim_library/mixamo/Standard Run.fbx','anim_library/mixamo/packs/Male Locomotion Pack/standard run.fbx']:
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(Path(filename).resolve()));r=next(o for o in bpy.data.objects if o.type=='ARMATURE');sc=bpy.context.scene;a=r.animation_data.action;rows=[]
 names={b.name.split(':')[-1]:b.name for b in r.pose.bones}
 def pos(n):return r.matrix_world@r.pose.bones[names[n]].head
 def rest(n):return r.matrix_world@r.data.bones[names[n]].head_local
 for f in np.linspace(*a.frame_range,97):
  sc.frame_set(int(f),subframe=f%1);d={'frame':float(f)}
  for n in ['Hips','LeftUpLeg','LeftLeg','LeftFoot','LeftToeBase','RightUpLeg','RightLeg','RightFoot','RightToeBase']:d[n]=list(pos(n))
  for sd in ['Left','Right']:
   h,k,t=[pos(sd+n)for n in ['UpLeg','Leg','Foot']];d[sd+'Knee']=180-math.degrees((h-k).angle(t-k))
  rows.append(d)
 out[filename]={'fps':sc.render.fps,'frames':list(a.frame_range),'rest':{n:list(rest(n))for n in names if n in ['Hips','LeftUpLeg','LeftLeg','LeftFoot','LeftToeBase']},'samples':rows}
(P/'review/round8/source_probe.json').write_text(json.dumps(out,indent=2))
print('TARGET',out['Standing'],out['Running'])
for filename,d in out.items():
 if 'samples'not in d:continue
 print(filename,d['fps'],d['frames'],'rest',d['rest'])
 for n in ['Hips','LeftFoot','LeftToeBase','LeftKnee']:
  x=np.array([r[n]for r in d['samples']]);print(n,'min',x.min(axis=0),'mean',x.mean(axis=0),'max',x.max(axis=0),'end delta',x[-1]-x[0])
