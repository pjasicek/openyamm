import bpy,json,math,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];groups={'arms':['B_L_UpperArm','B_R_UpperArm','B_L_Forearm','B_R_Forearm'],'hands':['B_L_Hand','B_R_Hand'],'spine':['B_Pelvis','B_Spine','B_Spine1','B_Spine2','B_Neck','B_Head']}
def measure(rig,act):
 rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];out={g:{'max_degrees_per_48Hz':0,'frame':0}for g in groups};previous=None
 for f in np.arange(0,act.frame_range[1]+.001,bpy.context.scene.render.fps/48):
  bpy.context.scene.frame_set(int(f),subframe=float(f-int(f)));q={n:rig.pose.bones[n].matrix.to_quaternion()for ns in groups.values()for n in ns if n in rig.pose.bones}
  if previous:
   for g,ns in groups.items():
    for n in ns:
     if n not in q:continue
     angle=math.degrees(previous[n].rotation_difference(q[n]).angle);angle=min(angle,360-angle)
     if angle>out[g]['max_degrees_per_48Hz']:out[g]={'max_degrees_per_48Hz':angle,'frame':float(f),'bone':n}
  previous=q
 return out
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_actions.blend'));rig=bpy.data.objects['Rig'];ref={}
for name in ['Standing','Walking','Running','Attack','Cast','Hit','Fidget','Death']:
 ref[name]=measure(rig,bpy.data.actions['DeathBackward'if name=='Death'else name])
bpy.ops.wm.open_mainfile(filepath=str(P/'work/material_master.blend'));rig=bpy.data.objects['Rig'];groups.update(twist=[n.name for n in rig.pose.bones if 'Twist'in n.name],fingers=[n.name for n in rig.pose.bones if 'Finger'in n.name],equipment=['Spear','Buckler'],cloth=[n.name for n in rig.pose.bones if n.name.startswith('Cloth')]);report={}
for act in bpy.data.actions:
 cur=measure(rig,act);rr=ref.get(act.name,{g:{'max_degrees_per_48Hz':0}for g in ['arms','hands','spine']});limits={g:rr['hands'if g in ['hands','fingers','equipment']else 'arms'if g in ['arms','twist']else 'spine']['max_degrees_per_48Hz']+10 for g in groups};bad=[g for g,v in cur.items()if v['max_degrees_per_48Hz']>limits[g]];report[act.name]={'groups':cur,'limits':limits,'flags':bad};print('MOTION STEPS',act.name,cur,'FLAGS',bad,flush=True)
(P/'review/motion_steps.json').write_text(json.dumps({'sample_hz':48,'source':ref,'fitted':report},indent=2))
