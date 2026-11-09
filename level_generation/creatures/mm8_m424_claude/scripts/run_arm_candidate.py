from pathlib import Path
import bpy,sys,runpy,os,json,shutil
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P/'scripts'));import common,armik
from mathutils import Quaternion,Vector
# Keep all fitted fingers/body motion; compare the source right arm before the fixed dagger-carry solve.
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_refined_grip.blend'))
rig=bpy.data.objects['Rig'];a=bpy.data.actions['Running'];rig.animation_data.action=a
if len(a.slots):rig.animation_data.action_slot=a.slots[0]
arm=[f'B_R_{n}' for n in ('Clavicle','UpperArm','Forearm','Hand')];keys=[]
for f in range(int(a.frame_range[1])+1):
 bpy.context.scene.frame_set(f);keys.append({n:rig.pose.bones[n].rotation_quaternion.copy() for n in arm})
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_textured_uv.blend'))
rig=bpy.data.objects['Rig'];a=bpy.data.actions['Running'];rig.animation_data.action=a
if len(a.slots):rig.animation_data.action_slot=a.slots[0]
for f,row in enumerate(keys):
 bpy.context.scene.frame_set(f)
 for n,q in row.items():
  if f==len(keys)-1:q=keys[0][n]
  if n=='B_R_Hand':
   sw,tw=armik.split_swing_twist(q,Vector((0,1,0)));q=sw@Quaternion((0,1,0),tw+1.7453292519943295)
  b=rig.pose.bones[n];b.rotation_quaternion=q;b.keyframe_insert('rotation_quaternion',frame=f)
rig.animation_data.action=None
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_run_source_candidate.blend'))
os.environ['FA']='0.6';os.environ['FA_RAMP']='0.15,0.85'
sys.argv=['twist_bones.py','--',str(P/'work/rig_run_source_candidate.blend'),str(P/'work/rig_run_source_twist.blend')]
runpy.run_path(str(P/'scripts/twist_bones.py'),run_name='__main__')
rig=bpy.data.objects['Rig'];a=bpy.data.actions['Running'];rig.animation_data.action=a
if len(a.slots):rig.animation_data.action_slot=a.slots[0]
for f in (0,5,11,16):
 bpy.context.scene.frame_set(f);common.workbench_clay(bpy.context.scene)
 common.render_views(str(P/f'review/arm_20261016/source_candidate_run_{f}'),1.2,1.2,views=('front','rside60'),resolution=(600,600))
