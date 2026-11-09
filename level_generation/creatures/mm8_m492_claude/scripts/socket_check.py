import bpy,json,math
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_uv.blend'))
rig=bpy.data.objects['Rig'];
# Place the release inside the open jaws so adult attacks stay in the native launch envelope.
bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
socket=rig.data.edit_bones['Socket_Mouth'];socket.head.y=-.372;socket.tail.y=-.392
bpy.ops.object.mode_set(mode='OBJECT')
r=rig;s=bpy.context.scene;r.animation_data.action=bpy.data.actions['Attack'];out=[]
for frame in range(41):
 s.frame_set(frame);p=r.matrix_world@r.pose.bones['Socket_Mouth'].head
 out.append({'time':frame/24,'xyz':list(p),'adult_horizontal':math.hypot(p.x,p.y)*1504.2888,'adult_z':p.z*1504.2888,'small_z':p.z*1203.4310})
(P/'review/socket_envelope.json').write_text(json.dumps(out,indent=2)+'\n')
assert max(x['adult_horizontal'] for x in out)<600
assert max(x['small_z'] for x in out)<450
print('MOUTH_ENVELOPE',max(x['adult_horizontal'] for x in out),max(x['adult_z'] for x in out),max(x['small_z'] for x in out),'IMPACT',out[30])
