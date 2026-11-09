import bpy,math
from pathlib import Path
P=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/full_20261006')
bpy.ops.wm.open_mainfile(filepath=str(P/'work/native_pilots_v1.blend'))
a=bpy.data.objects['Goblin_Rig'];s=bpy.context.scene
for clip,frames in [('Walk',[14,15,15.5,16,17,33,34,35,36]),('Attack',[14,15,16,22,23,27,28])]:
 action=bpy.data.actions[clip];a.animation_data.action=action;a.animation_data.action_slot=action.slots[0]
 for f in frames:
  s.frame_set(int(f),subframe=f%1);b=a.pose.bones['RightHand']
  print(clip,f,'local',list(b.rotation_quaternion),'norm',b.rotation_quaternion.magnitude,'world',list(b.matrix.to_quaternion()),flush=True)
for n in ['Hips','LeftUpLeg','RightUpLeg','Spine02','Spine01','Spine']:
 print('REST',n,list(a.data.bones[n].head_local),flush=True)

body=bpy.data.objects['Goblin_Body']
for g in body.vertex_groups:
 if g.name not in ['Component_0','Component_5','Component_23','Component_64']:continue
 cloud=[v.co[:] for v in body.data.vertices if any(w.group==g.index for w in v.groups) and abs(v.co.x)<.05 and 1.27<v.co.z<1.39 and v.co.y<-.07]
 print('CHIN',g.name,len(cloud),flush=True)
from mathutils import Vector
from mathutils.bvhtree import BVHTree
action=bpy.data.actions['Standing'];a.animation_data.action=action;a.animation_data.action_slot=action.slots[0];s.frame_set(1)
target=a.pose.bones['Head'].head+Vector((0,-.055,.11));tree=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
for px,py in [(320,455),(320,470),(320,480),(311,475),(329,475)]:
 origin=target+Vector(((px/640-.5)*.56,-2,(.5-py/640)*.56));point,normal,idx,dist=tree.ray_cast(origin,Vector((0,1,0)))
 if idx is not None:
  f=body.data.polygons[idx]
  print('RAY',px,py,'point',list(point),'face',idx,'mat',body.data.materials[f.material_index].name,'verts',[(j,list(body.data.vertices[j].co),{body.vertex_groups[w.group].name:round(w.weight,3) for w in body.data.vertices[j].groups}) for j in f.vertices],flush=True)
