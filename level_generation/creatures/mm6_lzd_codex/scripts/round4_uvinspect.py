import bpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/round4/round4_shared_baked.blend'))
m=bpy.data.objects['Body'].data
print('UVS',m.uv_layers.active_index,[(u.name,u.active_render)for u in m.uv_layers],flush=True)
for i,mat in enumerate(m.materials):
 loops=[j for f in m.polygons if f.material_index==i for j in f.loop_indices]
 if not loops:continue
 for u in m.uv_layers:
  print(mat.name,u.name,[(min(u.data[j].uv[k]for j in loops),max(u.data[j].uv[k]for j in loops))for k in range(2)],flush=True)
