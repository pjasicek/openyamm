import bpy,numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/anim_pilot.blend'));r=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];pv=np.zeros(len(body.data.vertices),np.int32);body.data.attributes['piece'].data.foreach_get('value',pv)
for a in bpy.data.actions:
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];keys=[]
 for f in np.arange(0,int(a.frame_range[1])+.01,.5):
  bpy.context.scene.frame_set(int(f),subframe=float(f%1));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();lo=min(v.co.z for v in me.vertices if pv[v.index] in (7,8));ev.to_mesh_clear();root=r.pose.bones['B_Pelvis'];m=root.matrix.copy();m.translation.z+=max(0,.0008-lo);root.matrix=m;keys.append((float(f),root.location.copy()))
 for f,l in keys:r.pose.bones['B_Pelvis'].location=l;r.pose.bones['B_Pelvis'].keyframe_insert('location',frame=f)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/anim_pilot.blend'))
