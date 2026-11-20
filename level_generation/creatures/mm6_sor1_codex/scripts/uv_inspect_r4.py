import bpy,numpy as np,json
from pathlib import Path
p=Path(__file__).resolve().parents[1]
for tag,file in [('accepted','review/round3/baseline/work/production_master.blend'),*[(f'lod{i}',f'work/round3_lod{i}.blend') for i in range(4)]]:
 bpy.ops.wm.open_mainfile(filepath=str(p/file));o=bpy.data.objects['Body'];m=o.data;m.calc_loop_triangles()
 verts=np.array([v.co[:] for v in m.vertices]);faces=np.array([t.vertices[:] for t in m.loop_triangles]);uv=np.array([[m.uv_layers.active.data[i].uv[:] for i in t.loops] for t in m.loop_triangles]);part=np.array([m.attributes['piece'].data[v].value for v in range(len(m.vertices))]);mat=np.array([t.material_index for t in m.loop_triangles])
 np.savez_compressed(p/'work'/f'uv_{tag}_r4.npz',vertices=verts,faces=faces,uv=uv,part=part,material=mat)
 print(tag,len(faces),'mats',[x.name for x in m.materials],'uvlayers',[(x.name,x.active_render) for x in m.uv_layers],flush=True)
