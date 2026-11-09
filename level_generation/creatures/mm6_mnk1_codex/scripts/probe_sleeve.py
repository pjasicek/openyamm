import bpy,json
from pathlib import Path
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/anim_pilot.blend'))
b=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];a=bpy.data.actions['Standing'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0)
ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
for v in b.data.vertices:
 if b.data.attributes['piece'].data[v.index].value==0 and abs(v.co.x)>.50:
  print('SLEEVE',v.index,list(v.co),list(me.vertices[v.index].co),[(b.vertex_groups[g.group].name,round(g.weight,4)) for g in v.groups])
for sd in ['L','R']:
 for n in ['UpperArm','Forearm','Hand']:
  bn=f'B_{sd}_{n}';pb=r.pose.bones[bn];print('BONE',bn,'rest',list(r.data.bones[bn].head_local),'pose',list(pb.head),'scale',list(pb.scale),'location',list(pb.location))
print('MODS',[(m.name,m.type) for m in b.modifiers])
