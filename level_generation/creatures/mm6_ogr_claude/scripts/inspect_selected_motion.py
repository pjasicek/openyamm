from pathlib import Path
import bpy,json
from mathutils import Vector
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'export/mm6_ogr.blend'))
print('ORIGINAL_RATE',bpy.context.scene.render.fps,bpy.context.scene.render.fps_base)
print('ORIGINAL_ACTIONS',[(a.name,tuple(a.frame_range)) for a in bpy.data.actions])
bpy.ops.wm.open_mainfile(filepath=str(p/'review/motion_options/ogre_motion_options.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Ogre'];sc=bpy.context.scene
rig.animation_data.action=bpy.data.actions['Attack_Downward'];rig.animation_data.action_slot=rig.animation_data.action.slots[0]
g=body.vertex_groups['Sword'].index
ids=[v.index for v in body.data.vertices if any(e.group==g and e.weight>.9 for e in v.groups)]
sc.frame_set(0)
ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
hand=rig.pose.bones['B_R_Hand'].head
idx=max(ids,key=lambda i:(me.vertices[i].co-hand).length)
ev.to_mesh_clear()
rows=[]
for f in range(15,37):
 sc.frame_set(f)
 ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
 tip=me.vertices[idx].co.copy();ev.to_mesh_clear()
 row={'frame':f,'time':f/30,'tip':list(tip),'hand':list(rig.pose.bones['B_R_Hand'].head)}
 rows.append(row);print('STRIKE',row)
(p/'revision_03/checks/attack_tip.json').write_text(json.dumps(rows,indent=2)+'\n')
