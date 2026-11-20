"""Loop surfaces, held corpse and source-relative rotation continuity on the selected fitted mesh."""
from pathlib import Path
import bpy,json,math,os,numpy as np
p=Path(__file__).resolve().parents[1]
bones=['B_Head','B_Neck','B_Spine2','B_R_UpperArm','B_R_Forearm','B_R_Hand','B_L_UpperArm','B_L_Forearm','B_L_Hand','B_L_Foot','B_R_Foot']
def select(rig,act):
 rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
def rotations(file):
 bpy.ops.wm.open_mainfile(filepath=str(file));rig=bpy.data.objects['Rig'];sc=bpy.context.scene;fps=sc.render.fps/sc.render.fps_base;out={}
 for role in ['Standing','Walking','Running','Attack','Hit','Death','Fidget']:
  a=bpy.data.actions[role];select(rig,a);q={b:[] for b in bones}
  for t in np.arange(0,a.frame_range[1]/fps+1e-5,1/60):
   f=t*fps;sc.frame_set(int(f),subframe=float(f%1))
   for b in bones:q[b].append(rig.pose.bones[b].matrix.to_quaternion())
  values={}
  for b in bones:
   steps=np.array([math.degrees(x.rotation_difference(y).angle) for x,y in zip(q[b],q[b][1:])]);steps=np.minimum(steps,360-steps);acc=np.abs(np.diff(steps));values[b]={'step_deg':float(steps.max()),'step_time':float(np.argmax(steps)/60),'second_difference_deg':float(acc.max()) if len(acc) else 0}
  out[role]=values
 return out
source=rotations(p/'work/pilot.blend');final=rotations(p/('work/'+os.environ.get('M480_MOTION_FILE','authored.blend')));flags=[]
for role,rows in final.items():
 for bone,values in rows.items():
  if values['step_deg']>source[role][bone]['step_deg']*2+5 or values['second_difference_deg']>source[role][bone]['second_difference_deg']*2+5:flags.append({'clip':role,'bone':bone,'source':source[role][bone],'final':values})
rig=bpy.data.objects['Rig'];sc=bpy.context.scene
objects=[bpy.data.objects['Body'],bpy.data.objects['Club']]
def points(name,frame):
 a=bpy.data.actions[name];select(rig,a);sc.frame_set(int(frame),subframe=float(frame%1));result=[]
 for obj in objects:
  ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();result.extend([tuple(obj.matrix_world@v.co) for v in me.vertices]);ev.to_mesh_clear()
 return np.array(result)
loops={}
for role in ('Standing','Walking','Running'):
 a=bpy.data.actions[role];error=float(np.linalg.norm(points(role,0)-points(role,a.frame_range[1]),axis=1).max());loops[role]=error
loops['Death_to_Dead']=float(np.linalg.norm(points('Death',bpy.data.actions['Death'].frame_range[1])-points('Dead',0),axis=1).max())
report={'sample_hz':60,'loop_maximum_surface_error_m':loops,'source':source,'final':final,'continuity_flags':flags}
(p/'review/motion_quality.json').write_text(json.dumps(report,indent=2));print('QUALITY LOOPS',loops);print('QUALITY FLAGS',json.dumps(flags))
assert max(loops.values())<.004,loops

assert not flags, flags
