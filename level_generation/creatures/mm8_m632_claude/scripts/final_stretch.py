import bpy,sys,runpy
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
sys.argv=['stretch_heatmap.py','--',str(P/'work/motion_reduced.blend'),'Dead','0',str(P/'review/final_dead_stretch')]
runpy.run_path(str(P/'scripts/stretch_heatmap.py'),run_name='__main__')
rig=bpy.data.objects['Rig'];c=(rig.pose.bones['B_R_UpperArm'].head+rig.pose.bones['B_R_Forearm'].head)*.5;sc=bpy.context.scene
for name,d in [('front',Vector((0,-1,0))),('back',Vector((0,1,0))),('above',Vector((0,0,1)))]:
 cam=common.ortho_camera('review_camera',c+d*3,(0,0,0),.6);cam.rotation_mode='QUATERNION';cam.rotation_quaternion=(-d).to_track_quat('-Z','Y');sc.camera=cam;sc.render.resolution_x=sc.render.resolution_y=600;sc.render.filepath=str(P/f'review/final_dead_shoulder_{name}.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
import numpy as np,json,armik
out={}
for a in bpy.data.actions:
 rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];worst={s:{'swing':0,'twist':0} for s in 'LR'}
 for f in np.arange(a.frame_range[0],a.frame_range[1]+.01,1):
  sc.frame_set(int(f))
  for s in 'LR':
   sw,tw=armik.wrist_cost(rig,s,armik.W(rig,'B_'+s+'_Hand').to_3x3().normalized())
   if sw>worst[s]['swing']:worst[s]['swing']=sw;worst[s]['swing_frame']=float(f)
   if abs(tw)>worst[s]['twist']:worst[s]['twist']=abs(tw);worst[s]['twist_frame']=float(f)
 out[a.name]=worst;print('FINAL WRIST',a.name,worst,flush=True)
(P/'work/final_wrist.json').write_text(json.dumps(out,indent=2))
