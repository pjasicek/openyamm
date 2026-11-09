import bpy,json
from mathutils import Vector
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_equipped.blend'));r=bpy.data.objects['Rig'];a=bpy.data.actions['Attack'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(36)
for n in ['Arrow','BowNock','Bow','Socket_Arrow_Release']:
 b=r.pose.bones[n];print(n,'scale',list(b.scale),'rotation_mode',b.rotation_mode,'axisZ',list(b.matrix.to_3x3()@Vector((0,0,1))),'matrix',[list(row)for row in b.matrix],'basis',[list(row)for row in b.matrix_basis])
for o in bpy.data.objects:
 if o.type=='MESH':print('OBJECT',o.name,'parent',o.parent.name if o.parent else '',[list(row)for row in o.matrix_world])
