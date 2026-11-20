from pathlib import Path
import bpy,json
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v5.blend'));o=bpy.data.objects['Body']
for i in [758,756,4586,4527]:
 v=o.data.vertices[i];print('VERTEX',i,list(v.co),[(o.vertex_groups[g.group].name,round(g.weight,4)) for g in v.groups])
