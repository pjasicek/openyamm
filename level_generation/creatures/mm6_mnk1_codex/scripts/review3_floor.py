"""Keep the leg-driven cloth above the floor with six cloth-only offset bones."""
import bpy,json,numpy as np
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/animation_finish.blend'))
r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];me=b.data;sc=bpy.context.scene
r.animation_data.action=None
for pb in r.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.objects.active=r;bpy.ops.object.mode_set(mode='EDIT');names=[]
for sd in ['L','R']:
 for part in ['Thigh','Calf','Foot']:
  src=f'B_{sd}_{part}';name=f'Cloth_{sd}_{part}';names.append((src,name));parent=r.data.edit_bones[src];eb=r.data.edit_bones.new(name);eb.head=parent.head;eb.tail=parent.tail;eb.roll=parent.roll;eb.parent=parent
bpy.ops.object.mode_set(mode='OBJECT');pv=np.array([v.value for v in me.attributes['piece'].data]);ids=np.where(pv==1)[0]
for src,name in names:
 group=b.vertex_groups.new(name=name);gi=b.vertex_groups[src].index
 for i in ids:
  v=me.vertices[int(i)];w=next((g.weight for g in v.groups if g.group==gi),0)
  if w:group.add([int(i)],w,'REPLACE');b.vertex_groups[src].remove([int(i)])
W=np.zeros((len(me.vertices),6))
for j,(_,name) in enumerate(names):
 gi=b.vertex_groups[name].index
 for i in ids:W[i,j]=next((g.weight for g in me.vertices[int(i)].groups if g.group==gi),0)
report={}
for act in bpy.data.actions:
 r.animation_data.action=None
 for _,name in names:r.pose.bones[name].location=Vector()
 r.animation_data.action=act;r.animation_data.action_slot=act.slots[0];rows=[]
 for f in np.arange(0,float(act.frame_range[1])+.01,.5):
  sc.frame_set(int(f),subframe=float(f%1));ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh();Z=np.array([v.co.z for v in em.vertices]);ev.to_mesh_clear();offset=np.zeros(6)
  for _ in range(20):
   deficit=.008-Z-W@offset;active=ids[np.sum(W[ids]*W[ids],axis=1)>1e-5];worst=max(active,key=lambda i:deficit[i])
   if deficit[worst]<=.00001:break
   w=W[worst];assert w@w>1e-5;offset+=w*deficit[worst]/(w@w)
  assert min((Z+W@offset)[ids])>=.003, float(min((Z+W@offset)[ids]))
  pose={}
  for j,(src,name) in enumerate(names):pose[name]=r.pose.bones[src].matrix.to_3x3().inverted()@Vector((0,0,offset[j]))
  rows.append((float(f),pose,float(offset.max())))
 for f,pose,_ in rows:
  for name,l in pose.items():r.pose.bones[name].location=l;r.pose.bones[name].keyframe_insert('location',frame=f)
 for layer in act.layers:
  for st in layer.strips:
   for cb in st.channelbags:
    for fc in cb.fcurves:
     if 'Cloth_' in fc.data_path:
      for key in fc.keyframe_points:key.interpolation='LINEAR'
 report[act.name]={'max_cloth_floor_lift_m':max(row[2] for row in rows)};print('CLOTH_FLOOR',act.name,report[act.name],flush=True)
(p/'work/review3_floor.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/animation_finish.blend'))
