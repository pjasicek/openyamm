"""Ground the complete fallen model including its held bow, after equipment assembly."""
import bpy,json
import numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/master.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];pv=np.array([a.value for a in body.data.attributes['piece'].data]);scene=bpy.context.scene;report={};rootinv=rig.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted()
for name in ['Death','Dead']:
 act=bpy.data.actions[name];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];corrections=[]
 for f in range(int(act.frame_range[1])+1):
  scene.frame_set(f);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();z=min(v.co.z for v in me.vertices if pv[v.index]!=202);ev.to_mesh_clear();dz=max(0,.004-z);corrections.append(dz);pb=rig.pose.bones['B_Pelvis'];pb.location+=rootinv@Vector((0,0,dz));pb.keyframe_insert('location',frame=f)
 report[name]={'complete_geometry_lift_m':[min(corrections),max(corrections)]}
rig.animation_data.action=None;(P/'review/final_floor.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/master.blend'))
