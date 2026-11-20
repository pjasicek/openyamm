"""Source-relative angular acceleration of upper arms, forearms and wrists at 48 Hz."""
import bpy,numpy as np,json,math,hashlib
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P.parents[2]
bones=[f'B_{s}_{b}'for s in 'LR'for b in ['UpperArm','Forearm','Hand']]
def measure(rig,action):
 rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0];sc=bpy.context.scene;f0,f1=action.frame_range
 values={n:[]for n in bones}
 for t in np.arange(f0,f1+1e-5,sc.render.fps/48):
  sc.frame_set(int(t),subframe=float(t%1))
  for n in bones:values[n].append((rig.matrix_world@rig.pose.bones[n].matrix).to_quaternion())
 result={}
 for n,qs in values.items():
  velocities=[]
  for before,after in zip(qs,qs[1:]):
   q=after@before.inverted()
   if q.w<0:q.negate()
   velocities.append(np.array(q.axis)*math.degrees(q.angle))
  v=np.array(velocities);a=np.linalg.norm(np.diff(v,axis=0),axis=1)
  result[n]={'maximum_deg_per_sample2':float(a.max(initial=0)),'p99_deg_per_sample2':float(np.percentile(a,99))if len(a)else 0,'peak_sample':int(a.argmax())if len(a)else 0}
 return result
refs={};hashes={}
mapping={'Standing':'2HandBowIdle','Fidget':'2HandBowIdle','Walking':'2HandBowWalk','Attack':'2HandBowAttack1','Cast':'2HandBowAttack1','Death':'2HandBowDeath1','Dead':'2HandBowDeath1','Hit':'2HandBowGetHitF1','Running':'RelaxRunForward'}
for name in ['2Hand Bow','Relax']:
 path=R/f'anim_library/humanoid_set/{name}.glb';hashes[str(path.relative_to(R))]=hashlib.sha256(path.read_bytes()).hexdigest();bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(path));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');actions={a.name.split('@')[-1].split('|')[-1]:a for a in bpy.data.actions}
 for role,clip in mapping.items():
  if clip in actions:refs[role]=measure(rig,actions[clip])
bpy.ops.wm.open_mainfile(filepath=str(P/'work/master_export.blend'));rig=bpy.data.objects['Rig'];rows={};issues=[]
for action in bpy.data.actions:
 measured=measure(rig,action);source=refs[action.name]
 for bone,value in measured.items():
  category='Hand'if bone.endswith('Hand')else'Arm'
  comparable=[v['maximum_deg_per_sample2']for n,v in source.items()if n.endswith('Hand')==(category=='Hand')]
  limit=max(comparable)+10
  value.update(source_group_max=max(comparable),limit=limit,passed=value['maximum_deg_per_sample2']<=limit)
  if not value['passed']:issues.append([action.name,bone])
 rows[action.name]=measured
result={'passed':not issues,'issues':issues,'sample_rate_hz':48,'unit':'degrees per 48 Hz sample squared; multiply by 2304 for degrees/s^2','limit_rule':'Source arm/hand group maximum plus 10 degrees per sample squared; explicit authored source peaks retained','sources':hashes,'clips':rows}
(P/'review/angular_acceleration.json').write_text(json.dumps(result,indent=2));print('ACCELERATION',result['passed'],issues,flush=True)
