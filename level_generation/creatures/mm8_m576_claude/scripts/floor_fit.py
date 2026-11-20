"""Keep support soles on z=0 using the actual skinned boot surfaces."""
import bpy,sys,numpy as np
from mathutils import Vector
src,out,*clips=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=str(src));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
pv=np.array([v.value for v in body.data.attributes['piece'].data]);co=np.array([tuple(v.co) for v in body.data.vertices])
foot=(pv==0) & (co[:,2]<.045)
assert foot.sum()>20
root_inv=rig.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted()
for name in clips:
 act=bpy.data.actions[name];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
 rows=[]
 for f in range(int(act.frame_range[1])+1):
  sc.frame_set(f);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
  z=np.array([(body.matrix_world@v.co).z for v in me.vertices]);ev.to_mesh_clear()
  dz=-float(z[foot].min());loc=rig.pose.bones['B_Pelvis'].location.copy()+root_inv@Vector((0,0,dz));rows.append((f,loc,dz))
 for f,loc,dz in rows:
  rig.pose.bones['B_Pelvis'].location=loc;rig.pose.bones['B_Pelvis'].keyframe_insert('location',frame=f)
 print('FLOOR',name,'correction cm',round(min(x[2] for x in rows)*100,2),round(max(x[2] for x in rows)*100,2))
rig.animation_data.action=None;bpy.ops.wm.save_as_mainfile(filepath=str(out))
