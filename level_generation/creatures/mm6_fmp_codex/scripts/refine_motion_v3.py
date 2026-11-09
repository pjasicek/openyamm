import bpy,sys,runpy
from pathlib import Path
from mathutils.kdtree import KDTree
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/motion_cloth_v2.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data;scene=bpy.context.scene
with bpy.data.libraries.load(str(p/'work/rig_v1.blend')) as (d,o):o.objects=['Body']
source=o.objects[0];tree=KDTree(len(source.data.vertices))
for v in source.data.vertices:tree.insert(v.co,v.index)
tree.balance();names={g.index:g.name for g in source.vertex_groups};pieces=[v.value for v in me.attributes['piece'].data]
def smooth(t):
 t=max(0,min(1,t));return t*t*(3-2*t)
def trunk(z):
 keys=[(1.075,'B_Pelvis'),(1.14,'B_Spine'),(1.20,'B_Spine1'),(1.285,'B_Spine2'),(1.38,'B_Neck'),(1.445,'B_Head')]
 if z<=keys[0][0]:return {keys[0][1]:1}
 for (a,n),(b,m) in zip(keys,keys[1:]):
  if z<b:
   t=smooth((z-a)/(b-a));return {n:1-t,m:t}
 return {'B_Head':1}
for v in me.vertices:
 if pieces[v.index]!=0:continue
 _,i,d=tree.find(v.co);assert d<1e-5
 arm={names[e.group]:e.weight for e in source.data.vertices[i].groups if any(t in names[e.group] for t in ('Clavicle','UpperArm','Forearm','Hand'))}
 share=sum(arm.values());w={n:x*(1-share) for n,x in trunk(v.co.z).items()};w.update(arm)
 for g in body.vertex_groups:g.remove([v.index])
 for n,x in w.items():
  if x>1e-6:body.vertex_groups[n].add([v.index],x,'REPLACE')
bpy.data.objects.remove(source,do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/motion_weight_fixed.blend'))
sys.argv=['death_legs.py','--',str(p/'work/motion_weight_fixed.blend'),str(p/'work/motion_death_fixed.blend')]
runpy.run_path(str(p/'scripts/death_legs.py'),run_name='__main__')
sys.argv=['skirt_sim.py','--',str(p/'work/motion_death_fixed.blend'),str(p/'work/motion_cloth_v3.blend')]
runpy.run_path(str(p/'scripts/skirt_sim.py'),run_name='__main__')
for view in ('front','left'):
 sys.argv=['clip_sheet.py','--',str(p/'work/motion_cloth_v3.blend'),str(p/'review'/('cloth_v3_'+view)),view,'5','Standing','Walking','Run','Hit','Death']
 runpy.run_path(str(p/'scripts/clip_sheet.py'),run_name='__main__')
