"""Remove Attack/Cast's extra yaw reversals without changing the other pose channels."""
from pathlib import Path
import bpy, json, math
import numpy as np
from mathutils import Quaternion, Vector
P=Path(__file__).resolve().parents[1]; OUT=P/'review/motion_v3'
bpy.ops.wm.open_mainfile(filepath=str(P/'work/before_motion_v3/dragon_master.blend'))
rig=bpy.data.objects['Rig']; body=bpy.data.objects['Body']; sc=bpy.context.scene; sc.render.fps=24
old=np.array(json.loads((P/'review/motion_v2/authored.json').read_text())['attack'])
def old_yaw(t):
 xs=old[:,0];ys=old[:,4];i=min(len(xs)-2,max(0,int(np.searchsorted(xs,t,side='right')-1)));dt=xs[i+1]-xs[i];u=np.clip((t-xs[i])/dt,0,1)
 slopes=np.zeros_like(ys);slopes[1:-1]=(ys[2:]-ys[:-2])/(xs[2:]-xs[:-2])
 return (2*u**3-3*u**2+1)*ys[i]+(u**3-2*u**2+u)*dt*slopes[i]+(-2*u**3+3*u**2)*ys[i+1]+(u**3-u**2)*dt*slopes[i+1]
def yaw(t):
 # Hold the strike side through the start of the rise, then settle directly to centre.
 keys=[(0,0),(.25,.36),(1.25,-.30),(1.375,-.30),(40/24,0)]
 for (start,a),(end,b) in zip(keys,keys[1:]):
  if t<=end:
   u=max(0,min(1,(t-start)/(end-start)));return a+(b-a)*u*u*(3-2*u)
 return 0
assert all(yaw(t+.001)<=yaw(t)+1e-9 for t in np.arange(.25,1.375,.001))
assert all(yaw(t+.001)>=yaw(t)-1e-9 for t in np.arange(1.375,40/24-.001,.001))
weights={**{f'Neck{i}':1/6 for i in range(1,4)},'Head':.5,**{f'Tail{i}':-.018 for i in range(1,11)}}
axes={n:rig.data.bones[n].matrix_local.to_3x3().inverted()@Vector((0,0,1)) for n in weights}
for name in ('Attack','Cast'):
 act=bpy.data.actions[name];rig.animation_data.action=act;poses={}
 for f in range(41):
  sc.frame_set(f);poses[f]={n:rig.pose.bones[n].rotation_quaternion.copy() for n in weights}
 for f in range(41):
  sc.frame_set(f);delta=yaw(f/24)-old_yaw(f/24)
  for n,weight in weights.items():
   b=rig.pose.bones[n];b.rotation_quaternion=poses[f][n]@Quaternion(axes[n],float(delta*weight));b.keyframe_insert('rotation_quaternion',frame=f)
rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/motion_v3.blend'))
for o in sc.objects:o.select_set(o in (body,rig))
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(P/'work/motion_v3_clips.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=False,export_attributes=False,export_morph=False,export_image_format='NONE',export_reset_pose_bones=True,export_anim_slide_to_zero=True)
rig.animation_data.action=bpy.data.actions['Attack'];report=[]
for f in range(81):
 sc.frame_set(f//2,subframe=(f%2)/2)
 report.append({'viewer_frame':f,'time':f/48,'old_yaw':float(old_yaw(f/48)),'yaw':yaw(f/48),'head':list(rig.pose.bones['Head'].head),'mouth':list(rig.pose.bones['Socket_Mouth'].head)})
assert all(report[i+1]['mouth'][0]<=report[i]['mouth'][0]+1e-6 for i in range(48,66))
assert all(report[i+1]['mouth'][0]>=report[i]['mouth'][0]-1e-6 for i in range(66,80))
(OUT/'head_path.json').write_text(json.dumps(report,indent=2)+'\n')
print('Single sweep authored; only Attack/Cast head/neck yaw and its tail counter-motion changed.',flush=True)
