import bpy,math,json
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];groups={'arms':['B_L_UpperArm','B_R_UpperArm','B_L_Forearm','B_R_Forearm'],'hands':['B_L_Hand','B_R_Hand'],'trunk':['B_Pelvis','B_Spine','B_Spine1','B_Spine2','B_Neck','B_Head'],'legs':['B_L_Thigh','B_R_Thigh','B_L_Calf','B_R_Calf','B_L_Foot','B_R_Foot']}
def read(src,roles=None):
 if str(src).endswith('.blend'):bpy.ops.wm.open_mainfile(filepath=str(src))
 else:bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=30;bpy.ops.import_scene.gltf(filepath=str(src))
 rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');out={}
 for act in bpy.data.actions:
  name=act.name.split('@')[-1].split('|')[-1]
  if roles is not None and name not in roles:continue
  rig.animation_data_create();rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];prev=None;maxima={g:0 for g in groups}
  for t in np.arange(act.frame_range[0],act.frame_range[1]+.001,bpy.context.scene.render.fps/48):
   bpy.context.scene.frame_set(int(t),subframe=float(t%1));q={n:(rig.matrix_world@rig.pose.bones[n].matrix).to_quaternion() for ns in groups.values() for n in ns}
   if prev:
    for g,ns in groups.items():
     for n in ns:
      a=math.degrees(prev[n].rotation_difference(q[n]).angle);maxima[g]=max(maxima[g],min(a,360-a))
   prev=q
  out[name]=maxima
 return out
source=read(P/'work/source_motion.blend',['Standing','Attack','Fidget']);source.update(read(P/'work/source_death.blend',['Death']))
for filename,clip,role in [('Armed','ArmedWalk','Walking'),('Relax','RelaxRunForward','Running'),('Unarmed','UnarmedGetHitF1','Hit')]:source[role]=read(P.parents[2]/f'anim_library/humanoid_set/{filename}.glb',[clip])[clip]
source['Dead']={g:0 for g in groups};final=read(P/'export/mm6_figc_lod0.glb');report={}
for role,row in final.items():
 flags=[g for g,v in row.items() if v>source[role][g]+10];report[role]={'source_max_degrees_per_48hz':source[role],'export_max_degrees_per_48hz':row,'flags':flags};print('TRACE',role,report[role],flush=True)
(P/'work/export_motion_trace.json').write_text(json.dumps(report,indent=2))
