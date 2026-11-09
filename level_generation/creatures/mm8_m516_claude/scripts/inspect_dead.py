import bpy,numpy as np,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'export/mm8_m516.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];r.animation_data.action=bpy.data.actions['Dead'];bpy.context.scene.frame_set(1);e=b.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();co=np.array([v.co[:] for v in m.vertices]);e.to_mesh_clear();rows={}
for group in b.vertex_groups:
 ids=[v.index for v in b.data.vertices if any(g.group==group.index and g.weight>.5 for g in v.groups)]
 if ids:rows[group.name]=[co[ids].min(0).tolist(),co[ids].max(0).tolist()]
(P/'work/dead_regions.json').write_text(json.dumps(rows,indent=2));print(rows)

assert rows['Chest'][0][2]<.10 and rows['Head'][0][2]<.08 and rows['Tail8'][0][2]<.10,rows
