"""Distribute the recovery roll over the existing twist bones, with measured skin limits."""
import bpy,sys,os,math,runpy,json
from pathlib import Path
import numpy as np
from mathutils import Quaternion
P=Path(__file__).resolve().parents[1];S=P/'scripts';sys.path.insert(0,str(S));import armik
src=P/'work/forge_slam.blend';sys.argv=['gates.py','--',str(src),'forge_slam_skin_masks'];g=runpy.run_path(str(S/'gates.py'),run_name='__main__');r=g['rig'];sc=bpy.context.scene;a=bpy.data.actions['Forge_Attack'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];b=r.pose.bones['B_R_UpperArmTwist'];upper=r.data.bones['B_R_UpperArm'];fore=r.data.bones['B_R_Forearm'];axis=(upper.matrix_local.inverted()@fore.head_local).normalized();frames=[]
for f in np.arange(62,90.001,.5):
 sc.frame_set(int(f),subframe=float(f%1));frames.append((float(f),b.rotation_quaternion.copy(),math.sin(math.pi*(f-62)/28)**2))
results=[];chosen=None
for degrees in (0,-2,2,-4,4,-6,6,-8,8):
 maximum=0.;hand=0.
 for f,q,w in frames:
  sc.frame_set(int(f),subframe=f%1);b.rotation_quaternion=Quaternion(axis,math.radians(degrees)*w)@q;bpy.context.view_layer.update();pts=g['coords']();e=g['edges'];st=np.linalg.norm(pts[e[:,0]]-pts[e[:,1]],axis=1)/np.maximum(g['L0'],1e-6);maximum=max(maximum,float(np.percentile(st[g['ef']['R']],99)));hand=max(hand,float(st[g['hf']['R']].max()))
 results.append({'degrees':degrees,'arm_p99':maximum,'hand_max':hand});print('SLAM_SKIN',results[-1],flush=True)
 if maximum<=2.045 and hand<=4.5:chosen=degrees;break
assert chosen is not None,results
for f,q,w in frames:
 b.rotation_mode='QUATERNION';b.rotation_quaternion=Quaternion(axis,math.radians(chosen)*w)@q;b.keyframe_insert('rotation_quaternion',frame=f)
r.animation_data.action=None;bpy.ops.wm.save_as_mainfile(filepath=str(src));(P/'review/forge_slam_skin_fit.json').write_text(json.dumps({'chosen_degrees':chosen,'window_frames':[62,90],'trials':results},indent=2)+'\n');sys.stdout.flush();os._exit(0)
