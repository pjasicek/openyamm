import bpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'export/mm6_cdr1.blend'));o=bpy.data.objects['Body'];me=o.data
D={'vertices':[list(v.co) for v in me.vertices],'faces':[list(f.vertices) for f in me.polygons],'material':[f.material_index for f in me.polygons],'uv':[[list(me.uv_layers.active.data[i].uv) for i in f.loop_indices] for f in me.polygons],'weights':[{o.vertex_groups[g.group].name:g.weight for g in v.groups} for v in me.vertices]}
(P/'work/mouth_mesh.json').write_text(json.dumps(D));print('DUMP',len(me.vertices),len(me.polygons))
