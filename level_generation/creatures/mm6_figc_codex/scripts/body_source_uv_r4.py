import bpy,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P/'review/round4'
for i,rel in enumerate(['protected_axe/lod0.blend','lod1_refit/lod1.blend','far_fit_correct/lod2.blend','far_repaired88/lod3.blend']):
 bpy.ops.wm.open_mainfile(filepath=str(P/'review/round3'/rel));o=bpy.data.objects['Body'];m=o.data;m.calc_loop_triangles()
 print('UV_SOURCE',i,len(m.vertices),len(m.loop_triangles),[(a.name,a.domain) for a in m.attributes],[(x.name) for x in m.uv_layers],flush=True)
 pos=np.array([tuple(o.matrix_world@v.co) for v in m.vertices]);pos=pos[:,[0,2,1]]*[1,1,-1];faces=np.array([t.vertices[:] for t in m.loop_triangles]);uv=np.array([[tuple(m.uv_layers.active.data[l].uv) for l in t.loops] for t in m.loop_triangles]);uv[:,:,1]=1-uv[:,:,1]
 charts=np.array([m.attributes['_uv_chart'].data[t.polygon_index].value for t in m.loop_triangles]) if '_uv_chart' in m.attributes else np.zeros(len(faces),int)
 np.savez(R/f'body_source_uv{i}.npz',pos=pos,faces=faces,uv=uv,chart=charts)
