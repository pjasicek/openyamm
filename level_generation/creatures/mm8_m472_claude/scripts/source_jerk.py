from pathlib import Path
import bpy,json,math
import numpy as np
p=Path(__file__).resolve().parents[1];report={}
for file,clips in [('Armed',['ArmedWalk']),('Unarmed',['UnarmedRunForward','UnarmedCastDualAttack2','UnarmedGetHitF1','UnarmedDeath1'])]:
 bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene;sc.render.fps=30
 bpy.ops.import_scene.gltf(filepath=str(p.parents[2]/'anim_library/humanoid_set'/f'{file}.glb'))
 rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
 for name in clips:
  a=next(a for a in bpy.data.actions if a.name.endswith(name));rig.animation_data.action=a
  if a.slots:rig.animation_data.action_slot=a.slots[0]
  vals={};last={}
  for f in np.arange(a.frame_range[0],a.frame_range[1]+.01,.5):
   sc.frame_set(int(f),subframe=float(f-int(f)))
   for n in ('B_Head','B_R_Hand','B_L_Hand','B_L_Foot','B_R_Foot'):
    q=rig.pose.bones[n].matrix.to_quaternion().normalized()
    if n in last:vals[n]=max(vals.get(n,0),math.degrees(2*math.acos(min(1.,abs(q.dot(last[n]))))))
    last[n]=q
  report[name]=vals
print('SOURCE_BASELINE',json.dumps(report));(p/'work/source_jerk.json').write_text(json.dumps(report,indent=2)+'\n')
