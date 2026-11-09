"""Keep the accepted upper-cloak drape and add a restrained continuous rear flare for the jog."""
import bpy,json,sys,runpy
from pathlib import Path
from mathutils import Matrix,Vector
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'))
src=p/'work/rig_v15_armbase.blend'
assert src.exists(), 'Expected the preserved pre-drape v15 checkpoint'
bpy.ops.wm.open_mainfile(filepath=str(src));r=bpy.data.objects['Rig'];sc=bpy.context.scene
def use(a):r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
use(bpy.data.actions['Standing']);sc.frame_set(0)
names=[b.name for b in r.pose.bones if b.name.startswith(('Cloak_','BackTabard_'))]
arm_names=[f'B_L_{n}' for n in ['Clavicle','UpperArm','Forearm','Hand','UpperArmTwist','ForearmTwist']]
arm_baseline={n:r.pose.bones[n].matrix_basis.copy() for n in arm_names}
baseline={n:r.pose.bones[n].matrix_basis.copy() for n in names}
chains=json.loads(sc['nobl_cloak'])+json.loads(sc['nobl_skirt_back'])
for role in ['Running','Hit']:
 a=bpy.data.actions[role];use(a);end=int(a.frame_range[1])
 # Root clearance accounts for the rigid sole's small 120 Hz interpolation sag.
 if role=='Running':
  poses=[]
  for step in range(end*4+1):
   f=step/4;sc.frame_set(int(f),subframe=f%1);M=r.pose.bones['B_Pelvis'].matrix.copy();M.translation.z+=.0032;poses.append(M)
  for step,M in enumerate(poses):
   f=step/4;sc.frame_set(int(f),subframe=f%1);b=r.pose.bones['B_Pelvis'];b.matrix=M;b.keyframe_insert('location',frame=f)
 for f in range(end+1):
  sc.frame_set(f)
  for n,M in baseline.items():r.pose.bones[n].matrix_basis=M
  if role=='Hit':
   for n,M in arm_baseline.items():
    b=r.pose.bones[n];b.matrix_basis=M;b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('location',frame=f)
  bpy.context.view_layer.update()
  desired={n:r.pose.bones[n].matrix.copy() for n in names}
  if role=='Running':
   chest=r.pose.bones['B_Spine2'];D=chest.matrix@chest.bone.matrix_local.inverted()
   back=(D.to_3x3()@Vector((0,1,0))).normalized()
   for chain in chains:
    import math
    weight=max(0,math.cos(math.radians(chain['deg'])))**.7
    for k,n in enumerate(chain['bones']):
     desired[n].translation+=back*([0,.025,.10,.18][k]*weight)
  for n in names:
   b=r.pose.bones[n];parent=b.parent;pm=desired.get(parent.name,parent.matrix)
   base=pm@parent.bone.matrix_local.inverted()@b.bone.matrix_local
   b.matrix_basis=base.inverted()@desired[n];b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('location',frame=f)
use(bpy.data.actions['Standing']);sc.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_v15.blend'))
sys.argv=['g6_contacts.py','--',str(p/'work/rig_v15.blend'),'Running','Hit'];runpy.run_path(str(p/'scripts/g6_contacts.py'),run_name='__main__')
# The new cloak stays continuous at the upper mantle; retain the stable front-tabard bake.
