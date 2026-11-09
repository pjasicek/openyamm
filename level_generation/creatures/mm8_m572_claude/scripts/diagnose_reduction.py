import bpy,numpy as np,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for file in ['work/anim_v1.blend','review/reduction/step_01.blend']:
 bpy.ops.wm.open_mainfile(filepath=str(P/file));o=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];r.animation_data.action=bpy.data.actions['Attack'];bpy.context.scene.frame_set(6,subframe=2/3);ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();a=np.array([v.co[:] for v in me.vertices]);target=np.array([-.07769234,.17639959,.4591093]);ids=np.argsort(np.linalg.norm(a-target,axis=1))[:3]
 print(file)
 for i in ids:print(int(i),'part',o.data.attributes['part'].data[int(i)].value,'rest',list(o.data.vertices[int(i)].co),'posed',a[i].tolist())
 ev.to_mesh_clear()
