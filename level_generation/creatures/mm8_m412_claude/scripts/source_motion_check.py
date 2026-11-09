"""48Hz world rotation step/second difference, measured against the actual local library clips."""
import bpy,json,math,sys
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];repo=P.parents[2]
sel=json.loads((P/'references/motion_selection.json').read_text())['selected_sources']
map_={'B_Head':'Head','B_Neck':'Neck','B_Spine2':'Spine2','B_R_UpperArm':'RightArm','B_R_Forearm':'RightForeArm','B_R_Hand':'RightHand','B_L_UpperArm':'LeftArm','B_L_Forearm':'LeftForeArm','B_L_Hand':'LeftHand','B_R_Foot':'RightFoot','B_L_Foot':'LeftFoot'}
def measure(rig,act,names,fps):
 sc=bpy.context.scene;rig.animation_data.action=act
 if act.slots:rig.animation_data.action_slot=act.slots[0]
 f0,f1=act.frame_range;times=np.arange(f0,f1+1e-5,fps/48);qs={n:[] for n in names}
 for f in times:
  sc.frame_set(int(f),subframe=float(f%1))
  for n,real in names.items():qs[n].append((rig.matrix_world@rig.pose.bones[real].matrix).to_quaternion())
 report={}
 for n,q in qs.items():
  step=np.array([math.degrees(a.rotation_difference(b).angle) for a,b in zip(q,q[1:])]);step=np.minimum(step,360-step);d2=np.abs(np.diff(step));i=int(step.argmax());j=int(d2.argmax())
  report[n]={'step_deg':float(step[i]),'step_time_s':float((times[i]-f0)/fps),'d2_deg':float(d2[j]),'d2_time_s':float((times[j]-f0)/fps)}
 return report
out={}
for role,row in sel.items():
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=30;bpy.ops.import_scene.fbx(filepath=str(repo/row['path']))
 rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');prefix=next(b.name for b in rig.data.bones if b.name.endswith('Hips'))[:-4]
 out[role]={'source':measure(rig,rig.animation_data.action,{n:prefix+r for n,r in map_.items()},30)}
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=30
bpy.ops.import_scene.gltf(filepath=str(repo/'anim_library/humanoid_set/Unarmed.glb'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
act=next(a for a in bpy.data.actions if a.name.split('@')[-1].split('|')[-1]=='UnarmedGetHitF1')
out['Hit']={'source':measure(rig,act,{n:n for n in map_},30)}
bpy.ops.wm.open_mainfile(filepath=str(P/'work/master_knees.blend'));rig=bpy.data.objects['Rig']
for role in out:out[role]['fitted']=measure(rig,bpy.data.actions[role],{n:n for n in map_},30)
for role,r in out.items():
 print('SOURCE_COMPARISON',role,{n:[round(v['step_deg'],1),round(r['fitted'][n]['step_deg'],1),round(v['d2_deg'],1),round(r['fitted'][n]['d2_deg'],1)] for n,v in r['source'].items()})
(P/'review/source_motion_comparison.json').write_text(json.dumps(out,indent=2)+'\n')
