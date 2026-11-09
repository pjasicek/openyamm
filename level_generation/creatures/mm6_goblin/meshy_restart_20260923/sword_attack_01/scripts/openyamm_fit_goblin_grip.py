import bpy,json,math
from pathlib import Path
from mathutils import Vector,Matrix
OUT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923/sword_attack_01');s=bpy.data.scenes['Goblin - Sword and Native Attack'];bpy.context.window.scene=s;r=s.objects['Goblin_Combat_Rig'];m=s.objects['Goblin_Combat_Body'];a=bpy.data.actions['MM6_Goblin_GripRest'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];s.frame_set(1);bpy.context.view_layer.update();ev=m.evaluated_get(bpy.context.evaluated_depsgraph_get());Hand=r.pose.bones['mixamorig:RightHand'].matrix.copy();inv=Hand.inverted();names={g.index:g.name for g in m.vertex_groups};xf={b.name:r.pose.bones[b.name].matrix@b.matrix_local.inverted()@m.matrix_world for b in r.data.bones};changed=0;measure={}
for v in m.data.vertices:
 groups=[(names[g.group],g.weight) for g in v.groups];digits=[name.split('.')[2] for name,w in groups if name.startswith('Finger.R.') and w>.1]
 if not digits:continue
 p=inv@(ev.matrix_world@ev.data.vertices[v.index].co);x,y=p.x-.041,p.y-.100;rad=math.hypot(x,y)
 if abs(p.z)<.082 and .0001<rad<.023:
  q=Vector((.041+x*.023/rad,.100+y*.023/rad,p.z));M=Matrix([[0]*4 for _ in range(4)])
  for name,w in groups:
   if name in xf:M+=xf[name]*w
  v.co=M.inverted()@(Hand@q);changed+=1
m.data.update();bpy.context.view_layer.update();ev=m.evaluated_get(bpy.context.evaluated_depsgraph_get())
for v in m.data.vertices:
 ds=[names[g.group].split('.')[2] for g in v.groups if names[g.group].startswith('Finger.R.') and g.weight>.1]
 if ds:
  p=inv@(ev.matrix_world@ev.data.vertices[v.index].co)
  if abs(p.z)<.082:
   gap=math.hypot(p.x-.041,p.y-.100)-.0205
   for d in ds:measure[d]=min(measure.get(d,1),gap)
report={'fitted_vertices':changed,'minimum_vertex_gap_by_digit_m':measure,'method':'Project pads out of the handle in the grip pose and inverse-skin the adjustment into the editable neutral mesh; all five fingers remain articulated.'};(OUT/'grip_contact.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
# Register current strip membership after the local hand topology edit.
strips=[]
for b in r.data.bones:
 if not b.name.startswith('Skirt_'):continue
 gi=m.vertex_groups[b.name].index;ids=[v.index for v in m.data.vertices if any(g.group==gi and g.weight>.99 for g in v.groups)];pivot=b.head_local;radial=Vector((pivot.x,pivot.y-.035,0)).normalized();strips.append({'name':b.name,'ids':ids,'pivot':list(pivot),'radial':list(radial),'axis':[radial.y,-radial.x,0]})
(OUT/'strips.json').write_text(json.dumps(strips,indent=2))
