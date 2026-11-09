import bpy,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/pilot_bow.blend'))
r=bpy.data.objects['Rig'];r.animation_data.action=bpy.data.actions['Standing'];r.animation_data.action_slot=r.animation_data.action.slots[0];bpy.context.scene.frame_set(0)
g=json.loads(bpy.context.scene['bow_local']);b=r.pose.bones['Bow'].matrix
for n in ['Bow','StringTop','StringBottom']:
 pb=r.pose.bones[n];rest=r.data.bones[n].matrix_local;D=pb.matrix@rest.inverted();print(n,'REST',list(rest.translation),'start',list(D@Vector((0,0,0))),'end',list(D@Vector((0,0,1))),'scale',list(pb.scale))
print('TIPS',[list(b@Vector(x))for x in g['tips']])
