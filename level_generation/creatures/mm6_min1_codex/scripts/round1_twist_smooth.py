import bpy,runpy,sys,math
import numpy as np
from pathlib import Path
from mathutils import Quaternion
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/round1_clothed.blend'));r=bpy.data.objects['Rig'];sc=bpy.context.scene
for role in ['Attack','Cast']:
 a=bpy.data.actions[role];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];names=[f'B_{s}_UpperArmTwist' for s in 'RL'];cache=[]
 for f in range(int(a.frame_range[1])+1):sc.frame_set(f);cache.append({n:r.pose.bones[n].rotation_quaternion.copy() for n in names})
 prev={}
 for f in range(len(cache)):
  for n in names:
   acc=np.zeros(4)
   for j in range(max(0,f-12),min(len(cache),f+13)):
    sign=1 if cache[j][n].dot(cache[f][n])>=0 else -1;acc+=np.array(cache[j][n])*sign*math.exp(-.5*((j-f)/4)**2)
   q=Quaternion(acc/np.linalg.norm(acc))
   if n in prev and q.dot(prev[n])<0:q.negate()
   prev[n]=q.copy();r.pose.bones[n].rotation_quaternion=q;r.pose.bones[n].keyframe_insert('rotation_quaternion',frame=f)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round1_clothed.blend'))
sys.argv=['g','--','work/round1_clothed.blend'];runpy.run_path(str(P/'scripts/rig_gates_48.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/round1_precision.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/round1_motion_trace.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/round1_blade_audit.py'),run_name='__main__')
