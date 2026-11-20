"""The native hit is grounded: remove the source root's jump using actual boot soles."""
import bpy,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v6t.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];scene=bpy.context.scene
pv=np.array([d.value for d in body.data.attributes['piece'].data]);boot=np.where(np.isin(pv,[13,14]))[0]
ac=bpy.data.actions['Hit'];rig.animation_data.action=ac;rig.animation_data.action_slot=ac.slots[0]
rows=[]
for f in range(int(ac.frame_range[1])+1):
 scene.frame_set(f);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();z=min((body.matrix_world@me.vertices[i].co).z for i in boot);ev.to_mesh_clear();rows.append((f,rig.pose.bones['B_Pelvis'].matrix.copy(),z))
for f,M,z in rows:
 scene.frame_set(f);M.translation.z-=z;pb=rig.pose.bones['B_Pelvis'];pb.matrix=M;bpy.context.view_layer.update();pb.keyframe_insert('location',frame=f)
print('HIT grounded correction cm',min(z for _,_,z in rows)*100,max(z for _,_,z in rows)*100)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_v6t.blend'))
