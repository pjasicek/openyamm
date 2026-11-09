from pathlib import Path
import bpy,json,numpy as np
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_uv.blend'))
body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];scene=bpy.context.scene
for n in ['Body','BodyHigh','HeadSource','Wand']:
 ob=bpy.data.objects.get(n)
 if ob:print('SMOOTH',n,len(ob.data.polygons),sum(f.use_smooth for f in ob.data.polygons),[(m.name,m.type) for m in ob.modifiers],flush=True)
a=bpy.data.actions['Dead'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];scene.frame_set(0);bpy.context.view_layer.update()
ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();P=np.array([tuple(v.co) for v in me.vertices]);piece=np.array([x.value for x in body.data.attributes['piece'].data]);cape=np.array([x.value for x in body.data.attributes['cape'].data]);loin=np.array([x.value for x in body.data.attributes['loin'].data])
for n,mask in [('skin',np.isin(piece,[0,2,3,4])),('cape',cape>0),('loin',loin>0),('cloth',piece==1)]:print('FLOOR',n,P[mask,2].min(),P[mask,2].max(),flush=True)
ev.to_mesh_clear()

from mathutils import Vector,Quaternion
import math
axes={n:rig.data.bones[n].matrix_local.to_3x3().inverted()@Vector((1,0,0)) for n in ['Cape0','Cape1','Cape2']}
qs={n:rig.pose.bones[n].rotation_quaternion.copy() for n in axes}
rig.animation_data.action=None
for angle in [-90,-60,-30,0,30,60,90]:
 for n in axes:rig.pose.bones[n].rotation_quaternion=qs[n]@Quaternion(axes[n],math.radians(angle if n=='Cape0' else 0))
 bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();P=np.array([tuple(v.co) for v in me.vertices]);ev.to_mesh_clear()
 print('CAPETRIAL',angle,float(P[cape>0,2].min()),float(P[cape>0,2].max()),flush=True)
