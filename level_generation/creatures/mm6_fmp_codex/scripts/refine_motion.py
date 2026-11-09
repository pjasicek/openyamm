import bpy,runpy,sys,json
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/motion_corrected.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data;scene=bpy.context.scene
# Retain the service's smooth sleeve/shoulder weighting; its hidden-leg estimates were the part needing replacement.
with bpy.data.libraries.load(str(p/'work/rig_v1.blend')) as (data,out):out.objects=['Body']
source=out.objects[0];tree=KDTree(len(source.data.vertices))
for v in source.data.vertices:tree.insert(v.co,v.index)
tree.balance();names={g.index:g.name for g in source.vertex_groups};piece=[v.value for v in me.attributes['piece'].data]
for v in me.vertices:
 if piece[v.index]!=0 or abs(v.co.x+.004)<.08 or v.co.z<1.07 or v.co.z>1.40:continue
 _,vi,d=tree.find(v.co);assert d<1e-5
 for g in body.vertex_groups:g.remove([v.index])
 for e in source.data.vertices[vi].groups:
  if e.weight>1e-5:body.vertex_groups[names[e.group]].add([v.index],e.weight,'REPLACE')
bpy.data.objects.remove(source,do_unlink=True)
def use(a):
 rig.animation_data.action=a
 if a.slots:rig.animation_data.action_slot=a.slots[0]
use(bpy.data.actions['Standing']);scene.frame_set(0);st={b.name:b.rotation_quaternion.copy() for b in rig.pose.bones}
for name,factor in [('Walking',.75),('Run',.60)]:
 a=bpy.data.actions[name];use(a);rows=[]
 for f in range(int(a.frame_range[1])+1):
  scene.frame_set(f);rows.append({b.name:b.rotation_quaternion.copy() for b in rig.pose.bones if any(x in b.name for x in ('UpperArm','Forearm','Hand'))})
 for f,row in enumerate(rows):
  for n,q in row.items():
   b=rig.pose.bones[n];b.rotation_quaternion=st[n].slerp(q,factor);b.keyframe_insert('rotation_quaternion',frame=f)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/motion_arms.blend'))
sys.argv=['death_legs.py','--',str(p/'work/motion_arms.blend'),str(p/'work/motion_corrected.blend')]
runpy.run_path(str(p/'scripts/death_legs.py'),run_name='__main__')
runpy.run_path(str(p/'scripts/skirt_rig.py'),run_name='__main__')
sys.argv=['skirt_sim.py','--',str(p/'work/skirt_rig.blend'),str(p/'work/motion_cloth_v2.blend')]
runpy.run_path(str(p/'scripts/skirt_sim.py'),run_name='__main__')
for view in ('front','left'):
 sys.argv=['clip_sheet.py','--',str(p/'work/motion_cloth_v2.blend'),str(p/'review'/('cloth_v2_'+view)),view,'5','Standing','Walking','Run','Hit','Death']
 runpy.run_path(str(p/'scripts/clip_sheet.py'),run_name='__main__')
